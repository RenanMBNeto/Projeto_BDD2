from flask import Blueprint, jsonify, request
from app import db
from app.models import (
    Cliente, 
    Conta, 
    Portfolio, 
    Posicao, 
    RespostaSuitabilityCliente, 
    ProdutoFinanceiro,
    OpcaoResposta,
    Pergunta,
    MovimentacaoConta,
    HistoricoPreco
)
from app.schemas import (
    cliente_schema, 
    conta_schema, 
    portfolio_schema,
    posicoes_schema, 
    respostas_historico_schema,
    resposta_suitability_schema
)
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from sqlalchemy import desc, exc, func, and_ # <-- 1. Importar func e and_
from sqlalchemy.orm import joinedload
from decimal import Decimal

bp = Blueprint('client_portal', __name__)

def get_authenticated_client():
    claims = get_jwt(); role = claims.get("role"); id_str = get_jwt_identity()
    if role != "cliente": raise PermissionError("Acesso não autorizado.")
    try: id_int = int(id_str)
    except: raise ValueError("ID inválido.")
    cliente = Cliente.query.get(id_int)
    if not cliente: raise LookupError("Cliente não encontrado.")
    return cliente

@bp.route('/portal/register', methods=['POST'])
def client_register():
    data = request.get_json()
    required_fields = ["NomeCompleto", "Email", "CPF_CNPJ", "Senha"]
    if not data or not all(field in data for field in required_fields):
        return jsonify(erro="Faltam dados obrigatórios: NomeCompleto, Email, CPF_CNPJ, Senha"), 400
    if Cliente.query.filter_by(Email=data['Email']).first():
        return jsonify(erro="Email já cadastrado"), 409
    if Cliente.query.filter_by(CPF_CNPJ=data['CPF_CNPJ']).first():
        return jsonify(erro="CPF/CNPJ já cadastrado"), 409
    try:
        novo_cliente = Cliente(AssessorID=1, CPF_CNPJ=data['CPF_CNPJ'], NomeCompleto=data['NomeCompleto'], Email=data['Email'], StatusCompliance='Pendente')
        novo_cliente.set_password(data['Senha'])
        db.session.add(novo_cliente)
        db.session.flush() 
        numero_conta_gerado = f"C-{novo_cliente.ClienteID:07d}"
        nova_conta = Conta(ClienteID=novo_cliente.ClienteID, TipoConta='Conta Investimento', Agencia='0001', NumeroConta=numero_conta_gerado, Saldo=0.00)
        db.session.add(nova_conta)
        novo_portfolio = Portfolio(ClienteID=novo_cliente.ClienteID, NomePortfolio='Carteira Principal')
        db.session.add(novo_portfolio)
        db.session.commit()
        return jsonify(mensagem="Cliente registrado com sucesso! Faça o login."), 201
    except exc.IntegrityError as e:
        db.session.rollback(); return jsonify({"erro": "Email ou CPF/CNPJ já existem."}), 409
    except Exception as e:
        db.session.rollback(); return jsonify({"erro": "Erro interno ao registrar cliente.", "detalhes": str(e)}), 500

@bp.route('/portal/login', methods=['POST'])
def client_login():
    data = request.get_json();
    if not data or not data.get('Email') or not data.get('Senha'): 
        return jsonify(erro="Faltam dados"), 400
    cliente = Cliente.query.filter_by(Email=data['Email']).first()
    if not cliente or not cliente.check_password(data['Senha']):
        return jsonify(erro="Email ou senha inválidos"), 401
    access_token = create_access_token(identity=str(cliente.ClienteID), additional_claims={'role': 'cliente'})
    return jsonify(access_token=access_token, cliente=cliente_schema.dump(cliente)), 200

@bp.route('/portal/meu-perfil', methods=['GET'])
@jwt_required()
def get_my_profile():
    try: 
        cliente = get_authenticated_client()
        return cliente_schema.jsonify(cliente), 200
    except Exception as e: 
        return jsonify(erro=str(e)), 403

@bp.route('/portal/minha-conta', methods=['GET'])
@jwt_required()
def get_my_account():
    try: 
        cliente = get_authenticated_client()
        conta = Conta.query.filter_by(ClienteID=cliente.ClienteID).first_or_404()
        return conta_schema.jsonify(conta), 200
    except Exception as e: 
        return jsonify(erro=str(e)), 403

@bp.route('/portal/meu-portfolio', methods=['GET'])
@jwt_required()
def get_my_portfolio():
    try: 
        cliente = get_authenticated_client()
        portfolio = Portfolio.query.options(
            db.joinedload(Portfolio.posicoes).joinedload(Posicao.produto)
        ).filter_by(ClienteID=cliente.ClienteID).first_or_404()
        
        posicoes = portfolio.posicoes
        if not posicoes:

            portfolio.valor_mercado_total = Decimal(0)
            portfolio.resultado_total_financeiro = Decimal(0)
            return portfolio_schema.jsonify(portfolio), 200

        produto_ids = [p.ProdutoID for p in posicoes]

        subquery_precos = db.session.query(
            HistoricoPreco.ProdutoID,
            func.max(HistoricoPreco.Data).label('MaxData')
        ).filter(
            HistoricoPreco.ProdutoID.in_(produto_ids)
        ).group_by(
            HistoricoPreco.ProdutoID
        ).subquery('precos_recentes')

        precos_atuais = db.session.query(
            HistoricoPreco.ProdutoID,
            HistoricoPreco.PrecoFechamento
        ).join(
            subquery_precos,
            and_(
                HistoricoPreco.ProdutoID == subquery_precos.c.ProdutoID,
                HistoricoPreco.Data == subquery_precos.c.MaxData
            )
        ).all()
        
        mapa_precos = {p.ProdutoID: p.PrecoFechamento for p in precos_atuais}

        valor_mercado_total_portfolio = Decimal(0)
        custo_total_portfolio = Decimal(0)
        
        for p in posicoes:
            quantidade = Decimal(p.Quantidade)
            custo_medio = Decimal(p.CustoMedio)
            custo_total_posicao = quantidade * custo_medio
            
            preco_atual = Decimal(mapa_precos.get(p.ProdutoID, 0))
            
            valor_mercado_posicao = quantidade * preco_atual
            resultado_posicao = valor_mercado_posicao - custo_total_posicao
            
            p.valor_mercado = valor_mercado_posicao
            p.resultado_financeiro = resultado_posicao
            
            valor_mercado_total_portfolio += valor_mercado_posicao
            custo_total_portfolio += custo_total_posicao

        portfolio.valor_mercado_total = valor_mercado_total_portfolio
        portfolio.resultado_total_financeiro = valor_mercado_total_portfolio - custo_total_portfolio
        
        return portfolio_schema.jsonify(portfolio), 200
        
    except Exception as e: 
        print(f"Erro ao buscar portfolio: {e}")
        return jsonify(erro="Erro ao buscar portfolio", detalhes=str(e)), 500

@bp.route('/portal/meu-suitability', methods=['GET'])
@jwt_required()
def get_my_suitability_history():
    try: 
        cliente = get_authenticated_client()
        historico = RespostaSuitabilityCliente.query.filter_by(ClienteID=cliente.ClienteID).order_by(desc(RespostaSuitabilityCliente.DataResposta)).all()
        return jsonify(respostas_historico_schema.dump(historico)), 200
    except Exception as e: 
        return jsonify(erro=str(e)), 403

@bp.route('/portal/suitability/responder', methods=['POST'])
@jwt_required()
def submit_my_suitability_answers():
    try:
        cliente = get_authenticated_client()
        cliente_id = cliente.ClienteID 
        data = request.get_json()
        if not data or 'respostas' not in data or not isinstance(data['respostas'], list):
            return jsonify({"erro": "Formato inválido."}), 400
        pontuacao_total = 0
        versao_id_respondida = None
        opcao_ids_selecionadas = [r.get('opcao_id') for r in data['respostas'] if r.get('opcao_id')]
        if not opcao_ids_selecionadas: return jsonify({"erro": "Nenhuma opção."}), 400
        opcoes_escolhidas = OpcaoResposta.query.filter(OpcaoResposta.OpcaoID.in_(opcao_ids_selecionadas)).options(db.joinedload(OpcaoResposta.pergunta)).all()
        if not opcoes_escolhidas or len(opcoes_escolhidas) != len(data['respostas']):
            return jsonify({"erro": "Opções inválidas."}), 400
        versoes_ids = set()
        perguntas_respondidas = set()
        for opcao in opcoes_escolhidas:
            pontuacao_total += opcao.Pontos
            if opcao.pergunta:
                if opcao.pergunta.PerguntaID in perguntas_respondidas: return jsonify({"erro": "Pergunta repetida."}), 400
                perguntas_respondidas.add(opcao.pergunta.PerguntaID)
                versoes_ids.add(opcao.pergunta.VersaoID)
            else: return jsonify({"erro": "Erro pergunta."}), 500
        if len(versoes_ids) > 1: return jsonify({"erro": "Versões diferentes."}), 400
        elif len(versoes_ids) == 1: versao_id_respondida = versoes_ids.pop()
        else: return jsonify({"erro": "Versão indeterminada."}), 500
        num_perguntas_versao = Pergunta.query.filter_by(VersaoID=versao_id_respondida).count()
        if len(perguntas_respondidas) != num_perguntas_versao: return jsonify({"erro": "Questionário incompleto."}), 400
        perfil_calculado = 'Conservador' 
        if 50 <= pontuacao_total <= 80: perfil_calculado = 'Moderado'
        elif pontuacao_total > 80: perfil_calculado = 'Agressivo'
        nova_resposta = RespostaSuitabilityCliente(ClienteID=cliente_id, VersaoID=versao_id_respondida, PontuacaoTotal=pontuacao_total, PerfilCalculado=perfil_calculado)
        db.session.add(nova_resposta)
        db.session.commit()
        return resposta_suitability_schema.jsonify(nova_resposta), 201
    except (PermissionError, ValueError) as e: db.session.rollback(); return jsonify({"erro": str(e)}), 403
    except LookupError as e: db.session.rollback(); return jsonify({"erro": str(e)}), 404
    except exc.IntegrityError as e: db.session.rollback(); return jsonify({"erro": "Erro ao salvar."}), 400
    except Exception as e: db.session.rollback(); return jsonify({"erro": "Erro interno."}), 500

@bp.route('/portal/deposito', methods=['POST'])
@jwt_required()
def client_make_deposit():
    try:
        cliente = get_authenticated_client()
        data = request.get_json(); valor_deposito = Decimal(str(data['valor']))
        if valor_deposito <= 0: return jsonify(erro="Valor deve ser positivo"), 400
        conta = Conta.query.filter_by(ClienteID=cliente.ClienteID).with_for_update().first_or_404()
        conta.Saldo += valor_deposito
        nova_movimentacao = MovimentacaoConta(ContaOrigemID=None, ContaDestinoID=conta.ContaID, TipoMovimentacao='Deposito', Valor=valor_deposito, Status='Processada')
        db.session.add(nova_movimentacao)
        db.session.commit()
        return jsonify(mensagem="Depósito recebido com sucesso", novo_saldo=conta.Saldo), 200
    except (PermissionError, ValueError, LookupError) as e: db.session.rollback(); return jsonify(erro=str(e)), 403
    except Exception as e: db.session.rollback(); return jsonify(erro="Erro interno ao processar depósito", detalhes=str(e)), 500

@bp.route('/portal/saque', methods=['POST'])
@jwt_required()
def client_make_withdrawal():
    try:
        cliente = get_authenticated_client()
        data = request.get_json(); valor_saque = Decimal(str(data['valor']))
        if valor_saque <= 0: return jsonify(erro="Valor deve ser positivo"), 400
        conta = Conta.query.filter_by(ClienteID=cliente.ClienteID).with_for_update().first_or_404()
        if conta.Saldo < valor_saque: return jsonify(erro=f"Saldo insuficiente. Saldo: {conta.Saldo:.2f}"), 400
        conta.Saldo -= valor_saque
        nova_movimentacao = MovimentacaoConta(ContaOrigemID=conta.ContaID, ContaDestinoID=None, TipoMovimentacao='Saque', Valor=valor_saque, Status='Processada')
        db.session.add(nova_movimentacao)
        db.session.commit()
        return jsonify(mensagem="Saque processado com sucesso", novo_saldo=conta.Saldo), 200
    except (PermissionError, ValueError, LookupError) as e: db.session.rollback(); return jsonify(erro=str(e)), 403
    except Exception as e: db.session.rollback(); return jsonify(erro="Erro interno ao processar saque", detalhes=str(e)), 500

@bp.app_errorhandler(PermissionError)
def handle_permission_error(e): return jsonify(erro=str(e)), 403
@bp.app_errorhandler(ValueError)
def handle_value_error(e): return jsonify(erro=str(e)), 400
@bp.app_errorhandler(LookupError)
def handle_lookup_error(e): return jsonify(erro=str(e)), 404