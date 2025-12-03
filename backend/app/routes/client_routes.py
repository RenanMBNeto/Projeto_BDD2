from flask import Blueprint, jsonify, request
from app import db
from app.models import Cliente, Assessor, Conta, Portfolio, AuditoriaCompliance
from app.schemas import cliente_schema, clientes_schema
from flask_jwt_extended import jwt_required, get_jwt_identity

bp = Blueprint('client', __name__)


@bp.route('/clientes', methods=['GET'])
@jwt_required()
def get_clientes():
    assessor_id_logado_str = get_jwt_identity()
    assessor_id_logado_int = int(assessor_id_logado_str)

    clientes = Cliente.query.filter_by(AssessorID=assessor_id_logado_int).all()

    return jsonify(clientes_schema.dump(clientes)), 200


@bp.route('/clientes/<int:id>', methods=['GET'])
@jwt_required()
def get_cliente(id):
    assessor_id_logado_str = get_jwt_identity()
    assessor_id_logado_int = int(assessor_id_logado_str)

    cliente = Cliente.query.filter_by(ClienteID=id, AssessorID=assessor_id_logado_int).first_or_404()

    return cliente_schema.jsonify(cliente), 200


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


@bp.route('/clientes/<int:id>', methods=['PUT'])
@jwt_required()
def update_cliente(id):
    assessor_id_logado_str = get_jwt_identity()
    assessor_id_logado_int = int(assessor_id_logado_str)

    cliente = Cliente.query.filter_by(ClienteID=id, AssessorID=assessor_id_logado_int).first_or_404()

    data = request.get_json()

    cliente.NomeCompleto = data.get('NomeCompleto', cliente.NomeCompleto)
    cliente.Email = data.get('Email', cliente.Email)

    db.session.commit()
    return cliente_schema.jsonify(cliente), 200


@bp.route('/clientes/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_cliente(id):
    assessor_id_logado_str = get_jwt_identity()
    assessor_id_logado_int = int(assessor_id_logado_str)

    cliente = Cliente.query.filter_by(ClienteID=id, AssessorID=assessor_id_logado_int).first_or_404()

    try:
        db.session.delete(cliente)
        db.session.commit()
        return jsonify({"mensagem": "Cliente deletado com sucesso"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": "Erro ao deletar cliente",
                        "detalhes": "Não é possível deletar um cliente que possui portfólios ou contas ativas."}), 400


@bp.route('/clientes/<int:id>/status-compliance', methods=['PUT'])
@jwt_required()
def update_cliente_compliance(id):
    assessor_id_logado_str = get_jwt_identity()
    assessor_id_logado_int = int(assessor_id_logado_str)

    cliente = Cliente.query.filter_by(
        ClienteID=id,
        AssessorID=assessor_id_logado_int
    ).first_or_404()

    data = request.get_json()
    novo_status = data.get('status')
    justificativa = data.get('justificativa', 'Atualização de status pelo assessor.')

    valid_status = ['Pendente', 'Aprovado', 'Reprovado', 'Em Análise']

    if not novo_status or novo_status not in valid_status:
        return jsonify(erro=f"Status inválido ou não fornecido. Use um de: {valid_status}"), 400

    status_anterior = cliente.StatusCompliance

    try:
        nova_auditoria = AuditoriaCompliance(
            ClienteID=cliente.ClienteID,
            AssessorID=assessor_id_logado_int,
            StatusAnterior=status_anterior,
            StatusNovo=novo_status,
            Justificativa=justificativa
        )
        db.session.add(nova_auditoria)

        cliente.StatusCompliance = novo_status

        db.session.commit()

        return cliente_schema.jsonify(cliente), 200

    except Exception as e:
        db.session.rollback()
        return jsonify(erro="Erro ao atualizar status de compliance.", detalhes=str(e)), 500