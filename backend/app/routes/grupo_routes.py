from flask import Blueprint, jsonify, request
from app import db
from app.models import (
    Cliente, 
    Assessor, 
    GrupoEconomico, 
    ClienteGrupoLink,
    Portfolio,
    Posicao,
    ProdutoFinanceiro,
    HistoricoPreco
)
from app.schemas import (
    grupo_economico_schema, 
    grupos_economico_schema, 
    cliente_grupo_link_schema,
    posicoes_schema
)
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import desc, func, and_
from decimal import Decimal

bp = Blueprint('grupo', __name__)

@bp.route('/grupos', methods=['POST'])
@jwt_required()
def create_grupo_economico():
    assessor_id_logado_str = get_jwt_identity()
    data = request.get_json()
    
    if not data or not data.get('NomeGrupo'):
        return jsonify(erro="NomeGrupo é obrigatório"), 400

    assessor = Assessor.query.get(int(assessor_id_logado_str))
    if not assessor:
        return jsonify(erro="Assessor não autorizado"), 401

    try:
        novo_grupo = GrupoEconomico(
            NomeGrupo=data['NomeGrupo']
        )
        db.session.add(novo_grupo)
        db.session.commit()
        return grupo_economico_schema.jsonify(novo_grupo), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify(erro="Erro ao criar grupo", detalhes=str(e)), 500

@bp.route('/grupos', methods=['GET'])
@jwt_required()
def get_grupos_economicos():
    grupos = GrupoEconomico.query.all()
    return jsonify(grupos_economico_schema.dump(grupos)), 200

@bp.route('/grupos/<int:grupo_id>/vincular-cliente', methods=['POST'])
@jwt_required()
def link_cliente_to_grupo(grupo_id):
    assessor_id_logado_str = get_jwt_identity()
    assessor_id_logado_int = int(assessor_id_logado_str)
    
    data = request.get_json()
    if not data or not data.get('cliente_id'):
        return jsonify(erro="cliente_id é obrigatório"), 400
        
    cliente_id = data['cliente_id']
    papel_no_grupo = data.get('papel', 'Membro')

    cliente = Cliente.query.filter_by(
        ClienteID=cliente_id, 
        AssessorID=assessor_id_logado_int
    ).first()
    
    if not cliente:
        return jsonify(erro="Cliente não encontrado ou não autorizado para este assessor"), 404

    grupo = GrupoEconomico.query.get(grupo_id)
    if not grupo:
        return jsonify(erro="Grupo Econômico não encontrado"), 404
        
    try:
        link_existente = ClienteGrupoLink.query.get((cliente_id, grupo_id))
        if link_existente:
            return jsonify(erro="Cliente já está neste grupo"), 409
            
        novo_link = ClienteGrupoLink(
            ClienteID=cliente_id,
            GrupoID=grupo_id,
            PapelNoGrupo=papel_no_grupo
        )
        db.session.add(novo_link)
        db.session.commit()
        
        return cliente_grupo_link_schema.jsonify(novo_link), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify(erro="Erro ao vincular cliente", detalhes=str(e)), 500

@bp.route('/grupos/<int:grupo_id>/posicao-consolidada', methods=['GET'])
@jwt_required()
def get_grupo_posicao_consolidada(grupo_id):
    assessor_id_logado_str = get_jwt_identity()
    assessor_id_logado_int = int(assessor_id_logado_str)

    links = ClienteGrupoLink.query.filter_by(GrupoID=grupo_id).all()
    if not links:
        return jsonify(erro="Grupo não encontrado ou sem clientes"), 404
        
    cliente_ids_do_grupo = [link.ClienteID for link in links]
    
    auth_cliente = Cliente.query.filter(
        Cliente.ClienteID.in_(cliente_ids_do_grupo),
        Cliente.AssessorID == assessor_id_logado_int
    ).first()
    
    if not auth_cliente:
        return jsonify(erro="Assessor não autorizado a ver este grupo"), 403

    posicoes_raw = db.session.query(
        Posicao.ProdutoID,
        func.sum(Posicao.Quantidade).label('QuantidadeTotal'),
        func.sum(Posicao.Quantidade * Posicao.CustoMedio).label('CustoTotal')
    ).join(Portfolio, Posicao.PortfolioID == Portfolio.PortfolioID
    ).filter(
        Portfolio.ClienteID.in_(cliente_ids_do_grupo)
    ).group_by(
        Posicao.ProdutoID
    ).all()
    
    if not posicoes_raw:
        return jsonify([]), 200
        
    produto_ids = [p.ProdutoID for p in posicoes_raw]

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

    posicoes_consolidadas = []
    
    for p_raw in posicoes_raw:
        produto = ProdutoFinanceiro.query.get(p_raw.ProdutoID)
        
        quantidade = Decimal(p_raw.QuantidadeTotal)
        custo_total = Decimal(p_raw.CustoTotal)
        custo_medio = (custo_total / quantidade) if quantidade > 0 else Decimal(0)
        
        preco_atual = Decimal(mapa_precos.get(p_raw.ProdutoID, 0))
        
        valor_mercado = quantidade * preco_atual
        resultado_financeiro = valor_mercado - custo_total

        posicao_obj_virtual = Posicao(
            ProdutoID=p_raw.ProdutoID,
            Quantidade=quantidade,
            CustoMedio=custo_medio,
            produto=produto
        )

        posicao_obj_virtual.valor_mercado = valor_mercado
        posicao_obj_virtual.resultado_financeiro = resultado_financeiro
        
        posicoes_consolidadas.append(posicao_obj_virtual)

    return jsonify(posicoes_schema.dump(posicoes_consolidadas)), 200