from flask import Blueprint, jsonify, request
from app import db
from app.models import ProdutoFinanceiro, Produto_Acao, Produto_RendaFixa, Produto_Fundo, HistoricoPreco
from app.schemas import (
    produto_schema,
    produto_acao_schema,
    produto_rf_schema,
    produto_fundo_schema
)
from flask_jwt_extended import jwt_required
from sqlalchemy import exc, desc, func, and_
from datetime import date
from decimal import Decimal

bp = Blueprint('product', __name__)


@bp.route('/produtos', methods=['GET'])
@jwt_required()
def get_produtos():
    try:
        produtos = ProdutoFinanceiro.query.all()
        resultado = []
        produto_ids = [p.ProdutoID for p in produtos]

        # Buscar o preço mais recente para todos os produtos
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

        mapa_precos = {p.ProdutoID: float(p.PrecoFechamento) for p in precos_atuais}

        # Serialização manual para usar o schema correto conforme o tipo
        for prod in produtos:
            prod_data = None
            if prod.ClasseAtivo == 'Acao':
                prod_data = produto_acao_schema.dump(prod)
            elif prod.ClasseAtivo == 'RendaFixa':
                prod_data = produto_rf_schema.dump(prod)
            elif prod.ClasseAtivo == 'Fundo':
                prod_data = produto_fundo_schema.dump(prod)
            else:
                prod_data = produto_schema.dump(prod)

            # Adicionar o preço atual ao resultado
            prod_data['PrecoAtual'] = mapa_precos.get(prod.ProdutoID, 0.00)

            resultado.append(prod_data)

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

    # Preço inicial para registro no Histórico (default: 50.00)
    preco_inicial = Decimal(str(data.get('PrecoInicial', 50.00)))

    try:
        novo_produto = None

        # Assume Acao como padrão para o formulário do assessor
        if classe == 'Acao':
            novo_produto = Produto_Acao(
                Ticker=data['Ticker'].upper(),
                NomeProduto=data['NomeProduto'],
                NivelRiscoProduto=data.get('NivelRiscoProduto'),
                Emissor=data.get('Emissor', 'Mercado'),
                CNPJ_Empresa=data.get('CNPJ_Empresa', '00000000000000'),
                SetorAtuacao=data.get('SetorAtuacao', 'Outros')
            )
        elif classe == 'RendaFixa':
            novo_produto = Produto_RendaFixa(
                Ticker=data['Ticker'].upper(),
                NomeProduto=data['NomeProduto'],  # CORREÇÃO: Estava NomeProduto=data['NomeProduto')
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
        db.session.flush()

        # Inserir preço inicial no histórico
        novo_preco = HistoricoPreco(
            ProdutoID=novo_produto.ProdutoID,
            Data=date.today(),
            PrecoFechamento=preco_inicial
        )
        db.session.add(novo_preco)

        db.session.commit()

        return jsonify({"mensagem": "Produto criado com sucesso!", "id": novo_produto.ProdutoID,
                        "preco_inicial": float(preco_inicial)}), 201

    except exc.IntegrityError as e:
        db.session.rollback()
        if 'UNIQUE constraint' in str(e) or 'Violation of UNIQUE KEY' in str(e):
            return jsonify({"erro": "Já existe um produto com este Ticker ou CNPJ/ISIN."}), 409
        return jsonify({"erro": "Erro ao criar produto", "detalhes": str(e)}), 500
    except Exception as e:
        db.session.rollback()
        print(f"Erro inesperado ao criar produto: {e}")
        return jsonify({"erro": "Erro interno ao criar produto", "detalhes": str(e)}), 500