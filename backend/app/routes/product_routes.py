from flask import Blueprint, jsonify
from app import db
from app.models import ProdutoFinanceiro
from app.schemas import ProdutoFinanceiroSchema 
from flask_jwt_extended import jwt_required

bp = Blueprint('product', __name__)

produtos_schema = ProdutoFinanceiroSchema(many=True)

@bp.route('/produtos', methods=['GET'])
@jwt_required()
def get_produtos():
    try:
        todos_produtos = ProdutoFinanceiro.query.all()
        resultado = produtos_schema.dump(todos_produtos)
        return jsonify(resultado), 200
        
    except Exception as e:
        return jsonify({"erro": "Erro ao buscar produtos", "detalhes": str(e)}), 500