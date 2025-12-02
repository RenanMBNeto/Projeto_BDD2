# app/schemas.py (COMPLETO E ATUALIZADO)

from app import ma
from app.models import (
    Cliente,
    Assessor,
    Portfolio,
    Posicao,
    ProdutoFinanceiro,
    Conta,
    QuestionarioSuitabilityVersao,
    Pergunta,
    OpcaoResposta,
    RespostaSuitabilityCliente,
    GrupoEconomico,
    ClienteGrupoLink
)
from marshmallow import fields

class OpcaoRespostaSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = OpcaoResposta
        fields = ("OpcaoID", "TextoOpcao", "Pontos")

class PerguntaSchema(ma.SQLAlchemyAutoSchema):
    opcoes = fields.Nested(OpcaoRespostaSchema, many=True)
    class Meta:
        model = Pergunta
        fields = ("PerguntaID", "TextoPergunta", "opcoes")

class QuestionarioSchema(ma.SQLAlchemyAutoSchema):
    perguntas = fields.Nested(PerguntaSchema, many=True)
    class Meta:
        model = QuestionarioSuitabilityVersao
        fields = ("VersaoID", "DataVigencia", "NomeQuestionario", "perguntas")

class RespostaSuitabilitySchema(ma.SQLAlchemyAutoSchema):
    versao = fields.Nested(QuestionarioSchema, only=("VersaoID", "NomeQuestionario"))
    class Meta:
        model = RespostaSuitabilityCliente
        load_instance = True
        include_fk = True
        fields = ("RespostaID", "ClienteID", "VersaoID", "DataResposta", "PontuacaoTotal", "PerfilCalculado", "versao")

class AssessorSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Assessor
        load_instance = True
        exclude = ('SenhaHash', 'subordinados', 'clientes', 'auditorias')

class ContaSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Conta
        fields = ("ContaID", "TipoConta", "Agencia", "NumeroConta", "Saldo")

class ProdutoFinanceiroSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ProdutoFinanceiro
        fields = ("ProdutoID", "Ticker", "NomeProduto", "ClasseAtivo", "NivelRiscoProduto")

class PosicaoSchema(ma.SQLAlchemyAutoSchema):
    produto = fields.Nested(ProdutoFinanceiroSchema())
    portfolio = fields.Nested("PortfolioSchema", only=("PortfolioID", "NomePortfolio"))
    
    valor_mercado = fields.Decimal(dump_only=True, as_string=True)
    resultado_financeiro = fields.Decimal(dump_only=True, as_string=True)
    
    class Meta:
        model = Posicao
        load_instance = True
        include_relationships = True
        include_fk = True
        fields = (
            "PosicaoID", "PortfolioID", "ProdutoID", "Quantidade", "CustoMedio", 
            "produto", "portfolio", 
            "valor_mercado", "resultado_financeiro"
        )

class PortfolioSchema(ma.SQLAlchemyAutoSchema):
    posicoes = fields.Nested("PosicaoSchema", many=True, exclude=("portfolio",))

    valor_mercado_total = fields.Decimal(dump_only=True, as_string=True)
    resultado_total_financeiro = fields.Decimal(dump_only=True, as_string=True)

    class Meta:
        model = Portfolio
        load_instance = True
        include_relationships = True
        include_fk = True
        fields = (
            "PortfolioID", "ClienteID", "NomePortfolio", "posicoes",
            "valor_mercado_total", "resultado_total_financeiro"
        )

class GrupoEconomicoSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = GrupoEconomico
        load_instance = True
        fields = ("GrupoID", "NomeGrupo", "DataCriacao")

class ClienteGrupoLinkSchema(ma.SQLAlchemyAutoSchema):
    grupo = fields.Nested(GrupoEconomicoSchema, only=("NomeGrupo",))
    cliente = fields.Nested("ClienteSchema", only=("ClienteID", "NomeCompleto"))
    class Meta:
        model = ClienteGrupoLink
        load_instance = True
        include_fk = True
        include_relationships = True
        fields = ("ClienteID", "GrupoID", "PapelNoGrupo", "cliente", "grupo")

class ClienteSchema(ma.SQLAlchemyAutoSchema):
    assessor = fields.Nested(AssessorSchema, only=("Nome", "Email"))
    contas = fields.Nested(ContaSchema, many=True)
    portfolios = fields.Nested("PortfolioSchema", only=("PortfolioID", "NomePortfolio"), many=True)
    respostas_suitability = fields.Nested("RespostaSuitabilitySchema", many=True)

    grupos = fields.Nested(ClienteGrupoLinkSchema, many=True, exclude=("cliente",))

    class Meta:
        model = Cliente
        load_instance = True
        include_fk = True
        include_relationships = True
        fields = (
            "ClienteID", "AssessorID", "CPF_CNPJ", "NomeCompleto", "Email",
            "StatusCompliance", "DataUltimaAtualizacao",
            "assessor", "contas", "portfolios", "respostas_suitability",
            "grupos"
        )

cliente_schema = ClienteSchema()
clientes_schema = ClienteSchema(many=True)
assessor_schema = AssessorSchema()
portfolio_schema = PortfolioSchema()
portfolios_schema = PortfolioSchema(many=True)
posicao_schema = PosicaoSchema()
posicoes_schema = PosicaoSchema(many=True)
produto_schema = ProdutoFinanceiroSchema()
produtos_schema = ProdutoFinanceiroSchema(many=True)
conta_schema = ContaSchema()
contas_schema = ContaSchema(many=True)

opcao_resposta_schema = OpcaoRespostaSchema()
opcoes_resposta_schema = OpcaoRespostaSchema(many=True)
pergunta_schema = PerguntaSchema()
perguntas_schema = PerguntaSchema(many=True)
questionario_schema = QuestionarioSchema()
resposta_suitability_schema = RespostaSuitabilitySchema()
respostas_historico_schema = RespostaSuitabilitySchema(many=True)

grupo_economico_schema = GrupoEconomicoSchema()
grupos_economico_schema = GrupoEconomicoSchema(many=True)
cliente_grupo_link_schema = ClienteGrupoLinkSchema()