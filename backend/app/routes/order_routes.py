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
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt  # Adicionado get_jwt
from sqlalchemy import desc, exc
from decimal import Decimal

bp = Blueprint('order', __name__)


@bp.route('/ordem', methods=['POST'])
@jwt_required()
def execute_order():
    # 1. Obter Dados, Identidade e Role do Usuário Logado
    data = request.get_json()
    if not data:
        return jsonify({"erro": "Corpo da requisição vazio ou inválido"}), 400

    claims = get_jwt()
    role = claims.get("role")
    user_id_str = get_jwt_identity()
    user_id_int = int(user_id_str)

    required_fields = ["portfolio_id", "produto_id", "tipo_ordem", "quantidade", "preco_unitario"]
    if not all(field in data for field in required_fields):
        return jsonify({"erro": f"Campos obrigatórios em falta: {required_fields}"}), 400

    portfolio_id = data.get("portfolio_id")
    produto_id = data.get("produto_id")
    tipo_ordem = data.get("tipo_ordem", "").strip().capitalize()
    try:
        quantidade = Decimal(str(data.get("quantidade", 0)))
        preco_unitario = Decimal(str(data.get("preco_unitario", 0)))
    except Exception:
        return jsonify({"erro": "Quantidade ou Preço Unitário inválidos."}), 400

    valor_total_ordem = quantidade * preco_unitario

    if quantidade <= 0 or preco_unitario <= 0:
        return jsonify({"erro": "Quantidade e Preço Unitário devem ser positivos."}), 400

    if tipo_ordem not in ["Compra", "Venda"]:
        return jsonify({"erro": "Tipo de Ordem inválido. Use 'Compra' ou 'Venda'."}), 400

    try:
        portfolio_query = Portfolio.query.filter(Portfolio.PortfolioID == portfolio_id)

        if role == 'assessor':
            # Assessor só pode operar em portfólios de seus clientes
            portfolio = portfolio_query.join(Cliente).filter(
                Cliente.AssessorID == user_id_int
            ).first()
        elif role == 'cliente':
            # Cliente só pode operar em seus próprios portfólios
            portfolio = portfolio_query.filter(
                Portfolio.ClienteID == user_id_int
            ).first()
        else:
            return jsonify({"erro": "Role de usuário não reconhecida."}), 403

        if not portfolio:
            return jsonify({"erro": "Portfólio não encontrado ou não autorizado para este usuário."}), 404

        cliente_id = portfolio.ClienteID

        produto = ProdutoFinanceiro.query.get(produto_id)
        if not produto:
            return jsonify({"erro": f"Produto com ID {produto_id} não encontrado."}), 404

        # Busca o preço mais recente no banco para evitar fraudes ou defasagem
        ultimo_preco = HistoricoPreco.query.filter_by(ProdutoID=produto_id) \
            .order_by(desc(HistoricoPreco.Data)).first()

        if ultimo_preco:
            # Margem de tolerância de 5%
            preco_banco = ultimo_preco.PrecoFechamento
            diferenca = abs(preco_banco - preco_unitario)
            if diferenca > (preco_banco * Decimal('0.05')):
                return jsonify({
                    "erro": "Preço defasado.",
                    "preco_atual": str(preco_banco),
                    "mensagem": "O preço mudou significativamente (mais de 5%). Por favor, recarregue a cotação."
                }), 400

        resposta_recente = RespostaSuitabilityCliente.query.filter_by(
            ClienteID=cliente_id
        ).order_by(desc(RespostaSuitabilityCliente.DataResposta)).first()

        if not resposta_recente:
            return jsonify({"erro": "Cliente não possui perfil de risco (Suitability) definido."}), 400

        perfil_cliente = resposta_recente.PerfilCalculado
        risco_produto = produto.NivelRiscoProduto or 3

        permitido = False
        if perfil_cliente == 'Conservador' and risco_produto <= 2: permitido = True
        if perfil_cliente == 'Moderado' and risco_produto <= 4: permitido = True
        if perfil_cliente == 'Agressivo': permitido = True

        if not permitido:
            return jsonify({
                "erro": f"Produto (Risco {risco_produto}) incompatível com o perfil '{perfil_cliente}' do cliente."}), 400

        conta = Conta.query.filter_by(ClienteID=cliente_id).first()
        if not conta:
            return jsonify({"erro": "Cliente não possui conta associada para liquidação."}), 400

        if tipo_ordem == "Compra":
            if conta.Saldo < valor_total_ordem:
                return jsonify(
                    {"erro": f"Saldo insuficiente. Saldo: {conta.Saldo:.2f}, Necessário: {valor_total_ordem:.2f}"}), 400

            conta.Saldo -= valor_total_ordem
            tipo_mov = 'Aplicacao'
            conta_origem_id = conta.ContaID
            conta_destino_id = None

        else:
            posicao_existente = Posicao.query.filter_by(
                PortfolioID=portfolio_id,
                ProdutoID=produto_id
            ).first()

            if not posicao_existente or posicao_existente.Quantidade < quantidade:
                qtd_disponivel = posicao_existente.Quantidade if posicao_existente else 0
                return jsonify({
                    "erro": f"Quantidade insuficiente para venda. Disponível: {qtd_disponivel}, Tentando vender: {quantidade}"}), 400

            posicao_existente.Quantidade -= quantidade
            tipo_mov = 'Resgate'
            conta_origem_id = None
            conta_destino_id = conta.ContaID
            conta.Saldo += valor_total_ordem

        nova_movimentacao = MovimentacaoConta(
            ContaOrigemID=conta_origem_id,
            ContaDestinoID=conta_destino_id,
            TipoMovimentacao=tipo_mov,
            Valor=valor_total_ordem,
            Status='Processada'
        )
        db.session.add(nova_movimentacao)
        db.session.flush()

        nova_ordem = Ordem(
            PortfolioID=portfolio_id,
            ProdutoID=produto_id,
            MovimentacaoID_Liquidacao=nova_movimentacao.MovimentacaoID,
            TipoOrdem=tipo_ordem,
            Quantidade=quantidade,
            PrecoUnitario=preco_unitario,
            StatusOrdem='Executada'
        )
        db.session.add(nova_ordem)

        if tipo_ordem == "Compra":
            posicao_existente = Posicao.query.filter_by(
                PortfolioID=portfolio_id,
                ProdutoID=produto_id
            ).with_for_update().first()

            if posicao_existente:

                custo_total_antigo = posicao_existente.Quantidade * posicao_existente.CustoMedio
                custo_total_novo = valor_total_ordem
                quantidade_total_nova = posicao_existente.Quantidade + quantidade

                if quantidade_total_nova > 0:
                    posicao_existente.CustoMedio = (custo_total_antigo + custo_total_novo) / quantidade_total_nova

                posicao_existente.Quantidade += quantidade
            else:
                nova_posicao = Posicao(
                    PortfolioID=portfolio_id,
                    ProdutoID=produto_id,
                    Quantidade=quantidade,
                    CustoMedio=preco_unitario
                )
                db.session.add(nova_posicao)
        else:
            if posicao_existente.Quantidade == 0:
                db.session.delete(posicao_existente)

        db.session.commit()

        return jsonify(
            {"mensagem": f"Ordem de {tipo_ordem} executada com sucesso!", "ordem_id": nova_ordem.OrdemID}), 201

    except exc.IntegrityError as e:
        db.session.rollback()
        print(f"Erro de Integridade: {e}")
        return jsonify({"erro": "Erro de integridade no banco de dados."}), 400
    except Exception as e:
        db.session.rollback()
        print(f"Erro inesperado ao executar ordem: {e}")
        return jsonify({"erro": "Erro interno ao processar a ordem."}), 500