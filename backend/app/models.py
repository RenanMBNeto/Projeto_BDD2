from datetime import datetime
from app import db
from app import bcrypt

# --- DOMÍNIO 1: Clientes, Grupos & Assessores ---

class Assessor(db.Model):
    __tablename__ = 'Assessor'
    AssessorID = db.Column(db.Integer, primary_key=True)

    SuperiorID = db.Column(db.Integer, db.ForeignKey('Assessor.AssessorID'), nullable=True)
    Nome = db.Column(db.String(255), nullable=False)
    Email = db.Column(db.String(255), nullable=False, unique=True)
    Nivel = db.Column(db.String(50))
    SenhaHash = db.Column(db.String(128), nullable=True)
    def set_password(self, password):
        self.SenhaHash = bcrypt.generate_password_hash(password).decode('utf-8')
    def check_password(self, password):
        return bcrypt.check_password_hash(self.SenhaHash, password)

    superior = db.relationship('Assessor', remote_side=[AssessorID], back_populates='subordinados')
    subordinados = db.relationship('Assessor', back_populates='superior')
    
    clientes = db.relationship('Cliente', back_populates='assessor')
    
    auditorias = db.relationship('AuditoriaCompliance', back_populates='assessor')

class Cliente(db.Model):
    __tablename__ = 'Cliente'
    ClienteID = db.Column(db.Integer, primary_key=True)
    AssessorID = db.Column(db.Integer, db.ForeignKey('Assessor.AssessorID'), nullable=False)
    CPF_CNPJ = db.Column(db.String(14), nullable=False, unique=True)
    NomeCompleto = db.Column(db.String(255), nullable=False)
    Email = db.Column(db.String(255), nullable=False, unique=True)

    SenhaHash = db.Column(db.String(128), nullable=True) # Pode ser nulo se o cliente for criado pelo assessor
    
    def set_password(self, password):
        self.SenhaHash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        if self.SenhaHash is None:
            return False
        return bcrypt.check_password_hash(self.SenhaHash, password)
    
    StatusCompliance = db.Column(db.String(50), nullable=False, default='Pendente')
    DataUltimaAtualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    assessor = db.relationship('Assessor', back_populates='clientes')
    auditorias = db.relationship('AuditoriaCompliance', back_populates='cliente')
    grupos = db.relationship('ClienteGrupoLink', back_populates='cliente')
    respostas_suitability = db.relationship('RespostaSuitabilityCliente', back_populates='cliente')
    contas = db.relationship('Conta', back_populates='cliente')
    portfolios = db.relationship('Portfolio', back_populates='cliente')

class GrupoEconomico(db.Model):
    __tablename__ = 'GrupoEconomico'
    GrupoID = db.Column(db.Integer, primary_key=True)
    NomeGrupo = db.Column(db.String(255), nullable=False)
    DataCriacao = db.Column(db.DateTime, default=datetime.utcnow)

    membros = db.relationship('ClienteGrupoLink', back_populates='grupo')

class ClienteGrupoLink(db.Model):
    __tablename__ = 'ClienteGrupoLink'
    ClienteID = db.Column(db.Integer, db.ForeignKey('Cliente.ClienteID'), primary_key=True)
    GrupoID = db.Column(db.Integer, db.ForeignKey('GrupoEconomico.GrupoID'), primary_key=True)
    PapelNoGrupo = db.Column(db.String(100))

    cliente = db.relationship('Cliente', back_populates='grupos')
    grupo = db.relationship('GrupoEconomico', back_populates='membros')

class AuditoriaCompliance(db.Model):
    __tablename__ = 'AuditoriaCompliance'
    AuditoriaID = db.Column(db.BigInteger, primary_key=True)
    ClienteID = db.Column(db.Integer, db.ForeignKey('Cliente.ClienteID'), nullable=False)
    AssessorID = db.Column(db.Integer, db.ForeignKey('Assessor.AssessorID'), nullable=True)
    StatusAnterior = db.Column(db.String(50))
    StatusNovo = db.Column(db.String(50), nullable=False)
    DataHoraModificacao = db.Column(db.DateTime, default=datetime.utcnow)
    Justificativa = db.Column(db.String(500))

    cliente = db.relationship('Cliente', back_populates='auditorias')
    assessor = db.relationship('Assessor', back_populates='auditorias')

# --- DOMÍNIO 2: Suitability (Perfil de Risco Temporal) ---

class QuestionarioSuitabilityVersao(db.Model):
    __tablename__ = 'QuestionarioSuitabilityVersao'
    VersaoID = db.Column(db.Integer, primary_key=True)
    DataVigencia = db.Column(db.Date, nullable=False)
    NomeQuestionario = db.Column(db.String(255))

    perguntas = db.relationship('Pergunta', back_populates='versao')
    respostas_cliente = db.relationship('RespostaSuitabilityCliente', back_populates='versao')

class Pergunta(db.Model):
    __tablename__ = 'Pergunta'
    PerguntaID = db.Column(db.Integer, primary_key=True)
    VersaoID = db.Column(db.Integer, db.ForeignKey('QuestionarioSuitabilityVersao.VersaoID'), nullable=False)
    TextoPergunta = db.Column(db.Text, nullable=False)

    versao = db.relationship('QuestionarioSuitabilityVersao', back_populates='perguntas')
    opcoes = db.relationship('OpcaoResposta', back_populates='pergunta')

class OpcaoResposta(db.Model):
    __tablename__ = 'OpcaoResposta'
    OpcaoID = db.Column(db.Integer, primary_key=True)
    PerguntaID = db.Column(db.Integer, db.ForeignKey('Pergunta.PerguntaID'), nullable=False)
    TextoOpcao = db.Column(db.Text, nullable=False)
    Pontos = db.Column(db.Integer, nullable=False)

    pergunta = db.relationship('Pergunta', back_populates='opcoes')

class RespostaSuitabilityCliente(db.Model):
    __tablename__ = 'RespostaSuitabilityCliente'
    RespostaID = db.Column(db.Integer, primary_key=True)
    ClienteID = db.Column(db.Integer, db.ForeignKey('Cliente.ClienteID'), nullable=False)
    VersaoID = db.Column(db.Integer, db.ForeignKey('QuestionarioSuitabilityVersao.VersaoID'), nullable=False)
    DataResposta = db.Column(db.DateTime, default=datetime.utcnow)
    PontuacaoTotal = db.Column(db.Integer, nullable=False)
    PerfilCalculado = db.Column(db.String(50), nullable=False)

    cliente = db.relationship('Cliente', back_populates='respostas_suitability')
    versao = db.relationship('QuestionarioSuitabilityVersao', back_populates='respostas_cliente')


from sqlalchemy.schema import UniqueConstraint

# --- DOMÍNIO 3: Produtos Financeiros (EER e Recursivo) ---

class ProdutoFinanceiro(db.Model):
    __tablename__ = 'ProdutoFinanceiro'
    ProdutoID = db.Column(db.Integer, primary_key=True)
    Ticker = db.Column(db.String(20), nullable=False, unique=True)
    ISIN = db.Column(db.String(12), unique=True, nullable=True)
    NomeProduto = db.Column(db.String(255), nullable=False)
    NivelRiscoProduto = db.Column(db.Integer)
    Emissor = db.Column(db.String(255))
    
    ClasseAtivo = db.Column(db.String(50), nullable=False) 

    historico_precos = db.relationship('HistoricoPreco', back_populates='produto')
    ordens = db.relationship('Ordem', back_populates='produto')
    posicoes = db.relationship('Posicao', back_populates='produto')
    
    presente_em_fundos = db.relationship('ComposicaoFundo', 
                                         foreign_keys='ComposicaoFundo.AtivoComponenteID', 
                                         back_populates='ativo_componente')

    __mapper_args__ = {
        'polymorphic_on': ClasseAtivo,
        'polymorphic_identity': 'produto_financeiro'
    }

class Produto_Acao(ProdutoFinanceiro):
    __tablename__ = 'Produto_Acao'
    ProdutoID = db.Column(db.Integer, db.ForeignKey('ProdutoFinanceiro.ProdutoID'), primary_key=True)
    CNPJ_Empresa = db.Column(db.String(14), nullable=False)
    SetorAtuacao = db.Column(db.String(100))

    __mapper_args__ = {
        'polymorphic_identity': 'Acao',
    }

class Produto_RendaFixa(ProdutoFinanceiro):
    __tablename__ = 'Produto_RendaFixa'
    ProdutoID = db.Column(db.Integer, db.ForeignKey('ProdutoFinanceiro.ProdutoID'), primary_key=True)
    Tipo = db.Column(db.String(50))
    DataVencimento = db.Column(db.Date, nullable=False)
    Indexador = db.Column(db.String(20))
    TaxaContratada = db.Column(db.Numeric(10, 4))

    __mapper_args__ = {
        'polymorphic_identity': 'RendaFixa',
    }

class Produto_Fundo(ProdutoFinanceiro):
    __tablename__ = 'Produto_Fundo'
    ProdutoID = db.Column(db.Integer, db.ForeignKey('ProdutoFinanceiro.ProdutoID'), primary_key=True)
    CNPJ_Fundo = db.Column(db.String(14), nullable=False, unique=True)
    Gestor = db.Column(db.String(255))
    Administrador = db.Column(db.String(255))
    TaxaAdm = db.Column(db.Numeric(5, 2))
    TaxaPerf = db.Column(db.Numeric(5, 2))

    composicao = db.relationship('ComposicaoFundo', 
                                 foreign_keys='ComposicaoFundo.FundoProdutoID', 
                                 back_populates='fundo')

    __mapper_args__ = {
        'polymorphic_identity': 'Fundo',
    }

class HistoricoPreco(db.Model):
    __tablename__ = 'HistoricoPreco'
    PrecoID = db.Column(db.BigInteger, primary_key=True)
    ProdutoID = db.Column(db.Integer, db.ForeignKey('ProdutoFinanceiro.ProdutoID'), nullable=False)
    Data = db.Column(db.Date, nullable=False)
    PrecoFechamento = db.Column(db.Numeric(18, 8), nullable=False)

    produto = db.relationship('ProdutoFinanceiro', back_populates='historico_precos')
    
    __table_args__ = (UniqueConstraint('ProdutoID', 'Data', name='uq_produto_data'),)

class ComposicaoFundo(db.Model):
    __tablename__ = 'ComposicaoFundo'
    FundoProdutoID = db.Column(db.Integer, db.ForeignKey('Produto_Fundo.ProdutoID'), primary_key=True)
    AtivoComponenteID = db.Column(db.Integer, db.ForeignKey('ProdutoFinanceiro.ProdutoID'), primary_key=True)
    PercentualAlocacao = db.Column(db.Numeric(5, 2), nullable=False)
    DataPosicao = db.Column(db.Date, primary_key=True) # A composição é por data

    fundo = db.relationship('Produto_Fundo', foreign_keys=[FundoProdutoID], back_populates='composicao')
    ativo_componente = db.relationship('ProdutoFinanceiro', foreign_keys=[AtivoComponenteID], back_populates='presente_em_fundos')

# --- DOMÍNIO 4: Contas, Portfólios & Transações ---

class Conta(db.Model):
    __tablename__ = 'Conta'
    ContaID = db.Column(db.Integer, primary_key=True)
    ClienteID = db.Column(db.Integer, db.ForeignKey('Cliente.ClienteID'), nullable=False)
    TipoConta = db.Column(db.String(50), nullable=False, default='Conta Investimento')
    Agencia = db.Column(db.String(10), nullable=False)
    NumeroConta = db.Column(db.String(20), nullable=False, unique=True)
    Saldo = db.Column(db.Numeric(18, 2), nullable=False, default=0.00)

    cliente = db.relationship('Cliente', back_populates='contas')
    
    movimentacoes_origem = db.relationship('MovimentacaoConta', 
                                           foreign_keys='MovimentacaoConta.ContaOrigemID', 
                                           back_populates='conta_origem')
    movimentacoes_destino = db.relationship('MovimentacaoConta', 
                                            foreign_keys='MovimentacaoConta.ContaDestinoID', 
                                            back_populates='conta_destino')

class Portfolio(db.Model):
    __tablename__ = 'Portfolio'
    PortfolioID = db.Column(db.Integer, primary_key=True)
    ClienteID = db.Column(db.Integer, db.ForeignKey('Cliente.ClienteID'), nullable=False)
    NomePortfolio = db.Column(db.String(100), nullable=False, default='Carteira Principal')

    cliente = db.relationship('Cliente', back_populates='portfolios')
    ordens = db.relationship('Ordem', back_populates='portfolio')
    posicoes = db.relationship('Posicao', back_populates='portfolio')

class MovimentacaoConta(db.Model):
    __tablename__ = 'MovimentacaoConta'
    MovimentacaoID = db.Column(db.BigInteger, primary_key=True)

    ContaOrigemID = db.Column(db.Integer, db.ForeignKey('Conta.ContaID'), nullable=True)
    ContaDestinoID = db.Column(db.Integer, db.ForeignKey('Conta.ContaID'), nullable=True)

    TipoMovimentacao = db.Column(db.String(50), nullable=False)
    
    Valor = db.Column(db.Numeric(18, 2), nullable=False)
    DataHora = db.Column(db.DateTime, default=datetime.utcnow)
    Status = db.Column(db.String(20), nullable=False, default='Processada')

    conta_origem = db.relationship('Conta', foreign_keys=[ContaOrigemID], back_populates='movimentacoes_origem')
    conta_destino = db.relationship('Conta', foreign_keys=[ContaDestinoID], back_populates='movimentacoes_destino')

    ordem_liquidada = db.relationship('Ordem', back_populates='movimentacao_liquidacao')


class Ordem(db.Model):
    __tablename__ = 'Ordem'
    OrdemID = db.Column(db.BigInteger, primary_key=True)
    PortfolioID = db.Column(db.Integer, db.ForeignKey('Portfolio.PortfolioID'), nullable=False)
    ProdutoID = db.Column(db.Integer, db.ForeignKey('ProdutoFinanceiro.ProdutoID'), nullable=False)

    MovimentacaoID_Liquidacao = db.Column(db.BigInteger, db.ForeignKey('MovimentacaoConta.MovimentacaoID'), nullable=True)
    
    TipoOrdem = db.Column(db.String(10), nullable=False)
    Quantidade = db.Column(db.Numeric(18, 8), nullable=False)
    PrecoUnitario = db.Column(db.Numeric(18, 2), nullable=False)
    DataExecucao = db.Column(db.DateTime, default=datetime.utcnow)
    StatusOrdem = db.Column(db.String(20), nullable=False, default='Executada')

    portfolio = db.relationship('Portfolio', back_populates='ordens')
    produto = db.relationship('ProdutoFinanceiro', back_populates='ordens')
    movimentacao_liquidacao = db.relationship('MovimentacaoConta', back_populates='ordem_liquidada')

class Posicao(db.Model):
    __tablename__ = 'Posicao'
    PosicaoID = db.Column(db.Integer, primary_key=True)
    PortfolioID = db.Column(db.Integer, db.ForeignKey('Portfolio.PortfolioID'), nullable=False)
    ProdutoID = db.Column(db.Integer, db.ForeignKey('ProdutoFinanceiro.ProdutoID'), nullable=False)
    Quantidade = db.Column(db.Numeric(18, 8), nullable=False)
    CustoMedio = db.Column(db.Numeric(18, 2), nullable=False)

    portfolio = db.relationship('Portfolio', back_populates='posicoes')
    produto = db.relationship('ProdutoFinanceiro', back_populates='posicoes')

    __table_args__ = (UniqueConstraint('PortfolioID', 'ProdutoID', name='uq_portfolio_produto'),)