from flask import Blueprint, jsonify, request
from app import db
from app.models import (
    Cliente, 
    Assessor, 
    QuestionarioSuitabilityVersao, 
    Pergunta, 
    OpcaoResposta, 
    RespostaSuitabilityCliente
)
from app.schemas import (
    questionario_schema, 
    respostas_historico_schema
)
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import desc
from sqlalchemy.orm import joinedload

bp = Blueprint('suitability', __name__)

@bp.route('/suitability/questionario/ativo', methods=['GET'])
@jwt_required() # Requer login (qualquer tipo)
def get_active_questionnaire():
    latest_version = QuestionarioSuitabilityVersao.query.order_by(
        desc(QuestionarioSuitabilityVersao.DataVigencia)
    ).options(
        db.joinedload(QuestionarioSuitabilityVersao.perguntas)
        .joinedload(Pergunta.opcoes)
    ).first()

    if not latest_version:
        return jsonify({"erro": "Nenhuma versão do questionário encontrada"}), 404

    return questionario_schema.jsonify(latest_version), 200

@bp.route('/clientes/<int:cliente_id>/suitability/historico', methods=['GET'])
@jwt_required()
def get_suitability_history(cliente_id):
    assessor_id_logado_str = get_jwt_identity()
    try:
         assessor_id_logado_int = int(assessor_id_logado_str)
    except:
         return jsonify({"erro": "Token inválido para esta operação."}), 401

    cliente = Cliente.query.filter_by(
        ClienteID=cliente_id, 
        AssessorID=assessor_id_logado_int
    ).first()

    if not cliente:
        return jsonify({"erro": "Cliente não encontrado ou não autorizado"}), 404

    historico = RespostaSuitabilityCliente.query.filter_by(
        ClienteID=cliente_id
    ).order_by(
        desc(RespostaSuitabilityCliente.DataResposta)
    ).all()

    return jsonify(respostas_historico_schema.dump(historico)), 200