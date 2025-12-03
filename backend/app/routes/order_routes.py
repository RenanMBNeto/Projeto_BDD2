from flask import Blueprint, jsonify, request
from app import db
from app.models import (
    Portfolio,
    ProdutoFinanceiro,
    Conta,
    MovimentacaoConta,
    Ordem,
    Posicao,
    Cliente,
    RespostaSuitabilityCliente,
    HistoricoPreco
)
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from sqlalchemy import desc, exc
from decimal import Decimal
from flask import Blueprint, jsonify, request
from app import db
from app.models import Cliente, Assessor, Conta, Portfolio, AuditoriaCompliance
from app.schemas import cliente_schema, clientes_schema
from flask_jwt_extended import jwt_required, get_jwt_identity

bp = Blueprint('client', __name__)


# ... (funções get_clientes, get_cliente, update_cliente, delete_cliente omitidas por brevidade) ...

@bp.route('/clientes', methods=['POST'])
@jwt_required()
def create_cliente():
    data = request.get_json()
    assessor_id_logado_str = get_jwt_identity()
    assessor_id_logado_int = int(assessor_id_logado_str)

    try:
        # NOVO: Exige Senha
        senha = data.get('Senha')
        if not senha:
            return jsonify({"erro": "A senha é obrigatória para o cadastro de conta."}), 400

        novo_cliente = Cliente(
            AssessorID=assessor_id_logado_int,
            CPF_CNPJ=data['CPF_CNPJ'],
            NomeCompleto=data['NomeCompleto'],
            Email=data['Email'],
            StatusCompliance='Pendente'
        )
        # NOVO: Define a Senha Hash
        novo_cliente.set_password(senha)

        db.session.add(novo_cliente)

        db.session.flush()

        numero_conta_gerado = f"C-{novo_cliente.ClienteID:07d}"

        nova_conta = Conta(
            ClienteID=novo_cliente.ClienteID,
            TipoConta='Conta Investimento',
            Agencia='0001',
            NumeroConta=numero_conta_gerado,
            Saldo=0.00
        )
        db.session.add(nova_conta)

        novo_portfolio = Portfolio(
            ClienteID=novo_cliente.ClienteID,
            NomePortfolio='Carteira Principal'
        )
        db.session.add(novo_portfolio)

        db.session.commit()

        return cliente_schema.jsonify(novo_cliente), 201

    except Exception as e:
        db.session.rollback()
        if 'UNIQUE constraint' in str(e) or 'Violation of UNIQUE KEY' in str(e):
            return jsonify({"erro": "Erro ao criar cliente", "detalhes": "CPF/CNPJ ou Email já cadastrado."}), 409

        return jsonify({"erro": "Erro ao criar cliente", "detalhes": str(e)}), 400

bp = Blueprint('order', __name__)


@bp.route('/ordem', methods=['POST'])
@jwt_required()
def execute_order():
    # 1. Obter Dados e Identificar Usuário
    data = request.get_json()
    if not data:
        return jsonify({"erro": "Dados inválidos."}), 400

    required = ["portfolio_id", "produto_id", "tipo_ordem", "quantidade", "preco_unitario"]
    if not all(f in data for f in required):
        return jsonify({"erro": "Campos obrigatórios faltando."}), 400

    # Identificação do Usuário (Cliente ou Assessor?)
    claims = get_jwt()
    role = claims.get('role', 'cliente')  # Assume cliente se não tiver role
    user_id = int(get_jwt_identity())

    portfolio_id = data.get("portfolio_id")
    produto_id = data.get("produto_id")
    tipo_ordem = data.get("tipo_ordem", "").strip().capitalize()

    try:
        qtd = Decimal(str(data.get("quantidade", 0)))
        preco = Decimal(str(data.get("preco_unitario", 0)))
    except:
        return jsonify({"erro": "Valores numéricos inválidos."}), 400

    if qtd <= 0 or preco <= 0:
        return jsonify({"erro": "Valores devem ser positivos."}), 400

    try:
        # 2. Validação de Segurança (O portfólio pertence ao usuário?)
        portfolio = Portfolio.query.get(portfolio_id)
        if not portfolio:
            return jsonify({"erro": "Portfólio não encontrado."}), 404

        cliente_dono = Cliente.query.get(portfolio.ClienteID)

        if role == 'cliente':
            # Se for cliente, só pode mexer no próprio portfólio
            if portfolio.ClienteID != user_id:
                return jsonify({"erro": "Acesso negado a este portfólio."}), 403
        else:
            # Se for assessor, o cliente dono do portfólio deve ser dele
            if cliente_dono.AssessorID != user_id:
                return jsonify({"erro": "Este portfólio não pertence a um cliente seu."}), 403

        # 3. Validação do Produto e Preço
        produto = ProdutoFinanceiro.query.get(produto_id)
        if not produto:
            return jsonify({"erro": "Produto não encontrado."}), 404

        # 4. Validação de Saldo (Conta)
        conta = Conta.query.filter_by(ClienteID=cliente_dono.ClienteID).first()
        if not conta:
            return jsonify({"erro": "Conta não encontrada."}), 404

        valor_total = qtd * preco

        if tipo_ordem == "Compra":
            if conta.Saldo < valor_total:
                return jsonify({"erro": f"Saldo insuficiente. Disponível: R$ {conta.Saldo}"}), 400

            conta.Saldo -= valor_total
            tipo_mov = 'Aplicacao'
            conta_origem = conta.ContaID
            conta_destino = None

        elif tipo_ordem == "Venda":
            posicao = Posicao.query.filter_by(PortfolioID=portfolio_id, ProdutoID=produto_id).first()
            if not posicao or posicao.Quantidade < qtd:
                return jsonify({"erro": "Quantidade insuficiente para venda."}), 400

            tipo_mov = 'Resgate'
            conta_origem = None
            conta_destino = conta.ContaID
            conta.Saldo += valor_total

        else:
            return jsonify({"erro": "Tipo de ordem inválido."}), 400

        # 5. Execução (Movimentação e Ordem)
        mov = MovimentacaoConta(
            ContaOrigemID=conta_origem,
            ContaDestinoID=conta_destino,
            TipoMovimentacao=tipo_mov,
            Valor=valor_total,
            Status='Processada'
        )
        db.session.add(mov)
        db.session.flush()  # Gera o ID da movimentação

        nova_ordem = Ordem(
            PortfolioID=portfolio_id,
            ProdutoID=produto_id,
            MovimentacaoID_Liquidacao=mov.MovimentacaoID,
            TipoOrdem=tipo_ordem,
            Quantidade=qtd,
            PrecoUnitario=preco,
            StatusOrdem='Executada'
        )
        db.session.add(nova_ordem)

        # 6. Atualização da Posição (Upsert)
        posicao = Posicao.query.filter_by(PortfolioID=portfolio_id, ProdutoID=produto_id).first()

        if tipo_ordem == "Compra":
            if posicao:
                # Preço Médio Ponderado
                total_antigo = posicao.Quantidade * posicao.CustoMedio
                total_novo = valor_total
                nova_qtd_total = posicao.Quantidade + qtd

                posicao.CustoMedio = (total_antigo + total_novo) / nova_qtd_total
                posicao.Quantidade += qtd
            else:
                nova_posicao = Posicao(
                    PortfolioID=portfolio_id,
                    ProdutoID=produto_id,
                    Quantidade=qtd,
                    CustoMedio=preco
                )
                db.session.add(nova_posicao)

        elif tipo_ordem == "Venda":
            posicao.Quantidade -= qtd
            if posicao.Quantidade == 0:
                db.session.delete(posicao)

        db.session.commit()
        return jsonify({"mensagem": "Ordem executada com sucesso!"}), 201

    except exc.IntegrityError as e:
        db.session.rollback()
        return jsonify({"erro": "Erro de integridade (Duplicidade ou Dados Inválidos). Tente novamente."}), 400
    except Exception as e:
        db.session.rollback()
        print(f"Erro interno: {e}")
        return jsonify({"erro": "Erro interno no servidor."}), 500