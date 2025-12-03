from flask import Blueprint, jsonify, request
from app import db
from app.models import ProdutoFinanceiro, Produto_Acao, Produto_RendaFixa, Produto_Fundo
from app.schemas import (
    produto_schema,
    produto_acao_schema,
    produto_rf_schema,
    produto_fundo_schema
)
from flask_jwt_extended import jwt_required
from sqlalchemy import exc

bp = Blueprint('product', __name__)


@bp.route('/produtos', methods=['GET'])
@jwt_required()
def get_produtos():
    try:
        produtos = ProdutoFinanceiro.query.all()
        resultado = []

        # Serialização manual para usar o schema correto conforme o tipo
        for prod in produtos:
            if prod.ClasseAtivo == 'Acao':
                resultado.append(produto_acao_schema.dump(prod))
            elif prod.ClasseAtivo == 'RendaFixa':
                resultado.append(produto_rf_schema.dump(prod))
            elif prod.ClasseAtivo == 'Fundo':
                resultado.append(produto_fundo_schema.dump(prod))
            else:
                resultado.append(produto_schema.dump(prod))

        return jsonify(resultado), 200

    except Exception as e:
        return jsonify({"erro": "Erro ao buscar produtos", "detalhes": str(e)}), 500


@bp.route('/produtos', methods=['POST'])
@jwt_required()
def create_produto():
    data = request.get_json()

    # Validações básicas
    if not data or not data.get('Ticker') or not data.get('NomeProduto') or not data.get('ClasseAtivo'):
        return jsonify({"erro": "Campos obrigatórios: Ticker, NomeProduto, ClasseAtivo"}), 400

    classe = data.get('ClasseAtivo')

    try:
        novo_produto = None

        # Assume Acao como padrão para o formulário do assessor
        if classe == 'Acao':
            novo_produto = Produto_Acao(
                Ticker=data['Ticker'].upper(),  # Normaliza Ticker
                NomeProduto=data['NomeProduto'],
                NivelRiscoProduto=data.get('NivelRiscoProduto'),
                Emissor=data.get('Emissor', 'Mercado'),
                CNPJ_Empresa=data.get('CNPJ_Empresa', '00000000000000'),  # CNPJ Fictício se não informado
                SetorAtuacao=data.get('SetorAtuacao', 'Outros')
            )
        elif classe == 'RendaFixa':
            novo_produto = Produto_RendaFixa(
                Ticker=data['Ticker'].upper(),
                NomeProduto=data['NomeProduto'],
                NivelRiscoProduto=data.get('NivelRiscoProduto'),
                Emissor=data.get('Emissor'),
                Tipo=data.get('Tipo'),
                DataVencimento=data.get('DataVencimento'),
                Indexador=data.get('Indexador'),
                TaxaContratada=data.get('TaxaContratada')
            )
        elif classe == 'Fundo':
            novo_produto = Produto_Fundo(
                Ticker=data['Ticker'].upper(),
                NomeProduto=data['NomeProduto'],
                NivelRiscoProduto=data.get('NivelRiscoProduto'),
                Emissor=data.get('Emissor'),
                CNPJ_Fundo=data.get('CNPJ_Fundo'),
                Gestor=data.get('Gestor'),
                Administrador=data.get('Administrador'),
                TaxaAdm=data.get('TaxaAdm'),
                TaxaPerf=data.get('TaxaPerf')
            )
        else:
            return jsonify({"erro": "ClasseAtivo inválida. Use: Acao, RendaFixa ou Fundo"}), 400

        db.session.add(novo_produto)
        db.session.commit()

        return jsonify({"mensagem": "Produto criado com sucesso!", "id": novo_produto.ProdutoID}), 201

    except exc.IntegrityError as e:
        db.session.rollback()
        if 'UNIQUE constraint' in str(e) or 'Violation of UNIQUE KEY' in str(e):
            return jsonify({"erro": "Já existe um produto com este Ticker ou CNPJ/ISIN."}), 409
        return jsonify({"erro": "Erro ao criar produto", "detalhes": str(e)}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": "Erro ao criar produto", "detalhes": str(e)}), 500


@bp.route('/produtos/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_produto(id):
    try:
        produto = ProdutoFinanceiro.query.get(id)
        if not produto:
            return jsonify({"erro": "Produto não encontrado"}), 404

        db.session.delete(produto)
        db.session.commit()
        return jsonify({"mensagem": "Produto eliminado com sucesso"}), 200
    except exc.IntegrityError:
        db.session.rollback()
        return jsonify({"erro": "Não é possível eliminar: existem ordens ou posições associadas a este produto."}), 400