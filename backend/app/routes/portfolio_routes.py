from flask import Blueprint, jsonify
from app import db
from app.models import (
    Portfolio, 
    Posicao, 
    Cliente, 
    Assessor,
    HistoricoPreco,
    ProdutoFinanceiro
)
from app.schemas import (
    portfolio_schema, 
    portfolios_schema, 
    posicoes_schema, 
    PosicaoSchema
)
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.orm import joinedload
from sqlalchemy import desc, func, and_
from decimal import Decimal

bp = Blueprint('portfolio', __name__)

@bp.route('/portfolios/cliente/<int:cliente_id>', methods=['GET'])
@jwt_required()
def get_portfolios_by_cliente(cliente_id):
    assessor_id_logado_str = get_jwt_identity()
    assessor_id_logado_int = int(assessor_id_logado_str)

    cliente = Cliente.query.filter_by(
        ClienteID=cliente_id, 
        AssessorID=assessor_id_logado_int
    ).first()

    if not cliente:
        return jsonify({"erro": "Cliente não encontrado ou não autorizado"}), 404

    portfolios = Portfolio.query.filter_by(ClienteID=cliente_id).all()
    
    return jsonify(portfolios_schema.dump(portfolios)), 200

@bp.route('/posicoes/portfolio/<int:portfolio_id>', methods=['GET'])
@jwt_required()
def get_posicoes_by_portfolio(portfolio_id):
    assessor_id_logado_str = get_jwt_identity()
    assessor_id_logado_int = int(assessor_id_logado_str)

    portfolio = Portfolio.query \
        .join(Cliente, Portfolio.ClienteID == Cliente.ClienteID) \
        .filter(
            Portfolio.PortfolioID == portfolio_id,
            Cliente.AssessorID == assessor_id_logado_int
        ).first()

    if not portfolio:
        return jsonify({"erro": "Portfólio não encontrado ou não autorizado"}), 404

    posicoes = Posicao.query.options(joinedload(Posicao.produto)).filter_by(PortfolioID=portfolio_id).all()
    
    return jsonify(posicoes_schema.dump(posicoes)), 200

@bp.route('/portfolios/<int:portfolio_id>/valorizado', methods=['GET'])
@jwt_required()
def get_portfolio_valorizado(portfolio_id):
    assessor_id_logado_str = get_jwt_identity()
    assessor_id_logado_int = int(assessor_id_logado_str)

    portfolio = Portfolio.query \
        .join(Cliente, Portfolio.ClienteID == Cliente.ClienteID) \
        .options(db.joinedload(Portfolio.posicoes).joinedload(Posicao.produto)) \
        .filter(
            Portfolio.PortfolioID == portfolio_id,
            Cliente.AssessorID == assessor_id_logado_int
        ).first()

    if not portfolio:
        return jsonify({"erro": "Portfólio não encontrado ou não autorizado"}), 404
    
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