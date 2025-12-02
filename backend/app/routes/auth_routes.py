from flask import Blueprint, jsonify, request
from app import db
from app.models import Assessor, Cliente
from app.schemas import assessor_schema, cliente_schema
from flask_jwt_extended import create_access_token

bp = Blueprint('auth', __name__)

@bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data or not data.get('Email') or not data.get('Senha') or not data.get('Nome'):
        return jsonify({"erro": "Campos incompletos"}), 400

    if Assessor.query.filter_by(Email=data['Email']).first():
        return jsonify({"erro": "Email já cadastrado"}), 400
        
    novo_assessor = Assessor(
        Nome=data['Nome'],
        Email=data['Email'],
        Nivel='Junior'
    )
    novo_assessor.set_password(data['Senha'])
    
    db.session.add(novo_assessor)
    db.session.commit()
    
    return jsonify({"mensagem": "Assessor registrado com sucesso!"}), 201

@bp.route('/unified-login', methods=['POST'])
def unified_login():
    data = request.get_json()
    if not data or not data.get('Email') or not data.get('Senha'):
        return jsonify({"erro": "Email ou senha não fornecidos"}), 400

    email = data['Email']
    senha = data['Senha']

    assessor = Assessor.query.filter_by(Email=email).first()
    if assessor and assessor.check_password(senha):
        access_token = create_access_token(
            identity=str(assessor.AssessorID),
            additional_claims={'role': 'assessor'}
        )
        return jsonify(
            access_token=access_token,
            role='assessor',
            user=assessor_schema.dump(assessor)
        ), 200

    cliente = Cliente.query.filter_by(Email=email).first()
    if cliente and cliente.check_password(senha):
        access_token = create_access_token(
            identity=str(cliente.ClienteID),
            additional_claims={'role': 'cliente'}
        )
        return jsonify(
            access_token=access_token,
            role='cliente',
            user=cliente_schema.dump(cliente)
        ), 200

    return jsonify({"erro": "Email ou senha inválidos"}), 401