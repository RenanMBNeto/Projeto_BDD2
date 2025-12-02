-- Script de Cria��o do Banco de Dados: PrivateBankingDB

CREATE DATABASE PrivateBankingDB;
GO

-- DOM�NIO 1: Clientes, Grupos & Assessores

CREATE TABLE Assessor (
    AssessorID INT IDENTITY(1,1) PRIMARY KEY,
    SuperiorID INT NULL,
    Nome VARCHAR(255) NOT NULL,
    Email VARCHAR(255) NOT NULL UNIQUE,
    Nivel VARCHAR(50),
    CONSTRAINT FK_Assessor_Superior FOREIGN KEY (SuperiorID) REFERENCES Assessor(AssessorID)
);
GO

ALTER TABLE Assessor
ADD SenhaHash VARCHAR(128) NULL;

CREATE TABLE Cliente (
    ClienteID INT IDENTITY(1,1) PRIMARY KEY,
    AssessorID INT NOT NULL,
    CPF_CNPJ VARCHAR(14) NOT NULL UNIQUE,
    NomeCompleto VARCHAR(255) NOT NULL,
    Email VARCHAR(255) NOT NULL UNIQUE,
    StatusCompliance VARCHAR(50) NOT NULL DEFAULT 'Pendente',
    DataUltimaAtualizacao DATETIME DEFAULT GETDATE(),
    CONSTRAINT FK_Cliente_Assessor FOREIGN KEY (AssessorID) REFERENCES Assessor(AssessorID) ON DELETE NO ACTION ON UPDATE CASCADE
);
GO

CREATE TABLE GrupoEconomico (
    GrupoID INT IDENTITY(1,1) PRIMARY KEY,
    NomeGrupo VARCHAR(255) NOT NULL,
    DataCriacao DATETIME DEFAULT GETDATE()
);
GO

CREATE TABLE ClienteGrupoLink (
    ClienteID INT NOT NULL,
    GrupoID INT NOT NULL,
    PapelNoGrupo VARCHAR(100),
    PRIMARY KEY (ClienteID, GrupoID),
    CONSTRAINT FK_Link_Cliente FOREIGN KEY (ClienteID) REFERENCES Cliente(ClienteID) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT FK_Link_Grupo FOREIGN KEY (GrupoID) REFERENCES GrupoEconomico(GrupoID) ON DELETE CASCADE ON UPDATE CASCADE
);
GO

CREATE TABLE AuditoriaCompliance (
    AuditoriaID BIGINT IDENTITY(1,1) PRIMARY KEY,
    ClienteID INT NOT NULL,
    AssessorID INT NULL,
    StatusAnterior VARCHAR(50),
    StatusNovo VARCHAR(50) NOT NULL,
    DataHoraModificacao DATETIME DEFAULT GETDATE(),
    Justificativa VARCHAR(500),
    CONSTRAINT FK_Auditoria_Cliente FOREIGN KEY (ClienteID) REFERENCES Cliente(ClienteID) ON DELETE CASCADE ON UPDATE CASCADE,
    
    CONSTRAINT FK_Auditoria_Assessor FOREIGN KEY (AssessorID) REFERENCES Assessor(AssessorID) 
        ON DELETE NO ACTION ON UPDATE NO ACTION
);
GO

-- DOM�NIO 2: Suitability (Perfil de Risco Temporal)

CREATE TABLE QuestionarioSuitabilityVersao (
    VersaoID INT IDENTITY(1,1) PRIMARY KEY,
    DataVigencia DATE NOT NULL,
    NomeQuestionario VARCHAR(255)
);
GO

CREATE TABLE Pergunta (
    PerguntaID INT IDENTITY(1,1) PRIMARY KEY,
    VersaoID INT NOT NULL,
    TextoPergunta VARCHAR(MAX) NOT NULL,
    CONSTRAINT FK_Pergunta_Versao FOREIGN KEY (VersaoID) REFERENCES QuestionarioSuitabilityVersao(VersaoID) ON DELETE CASCADE ON UPDATE CASCADE
);
GO

CREATE TABLE OpcaoResposta (
    OpcaoID INT IDENTITY(1,1) PRIMARY KEY,
    PerguntaID INT NOT NULL,
    TextoOpcao VARCHAR(MAX) NOT NULL,
    Pontos INT NOT NULL,
    CONSTRAINT FK_Opcao_Pergunta FOREIGN KEY (PerguntaID) REFERENCES Pergunta(PerguntaID) ON DELETE CASCADE ON UPDATE CASCADE
);
GO

CREATE TABLE RespostaSuitabilityCliente (
    RespostaID INT IDENTITY(1,1) PRIMARY KEY,
    ClienteID INT NOT NULL,
    VersaoID INT NOT NULL,
    DataResposta DATETIME DEFAULT GETDATE(),
    PontuacaoTotal INT NOT NULL,
    PerfilCalculado VARCHAR(50) NOT NULL,
    CONSTRAINT FK_Resposta_Cliente FOREIGN KEY (ClienteID) REFERENCES Cliente(ClienteID) ON DELETE NO ACTION ON UPDATE CASCADE,
    CONSTRAINT FK_Resposta_Versao FOREIGN KEY (VersaoID) REFERENCES QuestionarioSuitabilityVersao(VersaoID) ON DELETE NO ACTION ON UPDATE CASCADE
);
GO

-- DOM�NIO 3: Produtos Financeiros (EER e Recursivo)

CREATE TABLE ProdutoFinanceiro (
    ProdutoID INT IDENTITY(1,1) PRIMARY KEY,
    Ticker VARCHAR(20) NOT NULL UNIQUE,
    ISIN VARCHAR(12) UNIQUE,
    NomeProduto VARCHAR(255) NOT NULL,
    ClasseAtivo VARCHAR(50) NOT NULL,
    NivelRiscoProduto INT,
    Emissor VARCHAR(255)
);
GO

CREATE TABLE Produto_Acao (
    ProdutoID INT PRIMARY KEY,
    CNPJ_Empresa VARCHAR(14) NOT NULL,
    SetorAtuacao VARCHAR(100),
    CONSTRAINT FK_Acao_Produto FOREIGN KEY (ProdutoID) REFERENCES ProdutoFinanceiro(ProdutoID) ON DELETE CASCADE ON UPDATE CASCADE
);
GO

CREATE TABLE Produto_RendaFixa (
    ProdutoID INT PRIMARY KEY,
    Tipo VARCHAR(50),
    DataVencimento DATE NOT NULL,
    Indexador VARCHAR(20),
    TaxaContratada DECIMAL(10, 4),
    CONSTRAINT FK_RendaFixa_Produto FOREIGN KEY (ProdutoID) REFERENCES ProdutoFinanceiro(ProdutoID) ON DELETE CASCADE ON UPDATE CASCADE
);
GO

CREATE TABLE Produto_Fundo (
    ProdutoID INT PRIMARY KEY,
    CNPJ_Fundo VARCHAR(14) NOT NULL UNIQUE,
    Gestor VARCHAR(255),
    Administrador VARCHAR(255),
    TaxaAdm DECIMAL(5, 2),
    TaxaPerf DECIMAL(5, 2),
    CONSTRAINT FK_Fundo_Produto FOREIGN KEY (ProdutoID) REFERENCES ProdutoFinanceiro(ProdutoID) ON DELETE CASCADE ON UPDATE CASCADE
);
GO

CREATE TABLE HistoricoPreco (
    PrecoID BIGINT IDENTITY(1,1) PRIMARY KEY,
    ProdutoID INT NOT NULL,
    Data DATE NOT NULL,
    PrecoFechamento DECIMAL(18, 8) NOT NULL,
    CONSTRAINT UQ_Produto_Data UNIQUE (ProdutoID, Data),
    CONSTRAINT FK_Preco_Produto FOREIGN KEY (ProdutoID) REFERENCES ProdutoFinanceiro(ProdutoID) ON DELETE CASCADE ON UPDATE CASCADE
);
GO

CREATE TABLE ComposicaoFundo (
    FundoProdutoID INT NOT NULL,
    AtivoComponenteID INT NOT NULL,
    PercentualAlocacao DECIMAL(5, 2) NOT NULL,
    DataPosicao DATE NOT NULL,
    PRIMARY KEY (FundoProdutoID, AtivoComponenteID, DataPosicao),

    CONSTRAINT FK_Composicao_Fundo FOREIGN KEY (FundoProdutoID) REFERENCES Produto_Fundo(ProdutoID) 
        ON DELETE NO ACTION ON UPDATE NO ACTION,
    CONSTRAINT FK_Composicao_Ativo FOREIGN KEY (AtivoComponenteID) REFERENCES ProdutoFinanceiro(ProdutoID) 
        ON DELETE NO ACTION ON UPDATE NO ACTION
);
GO

-- DOM�NIO 4: Contas & Transa��es

CREATE TABLE Conta (
    ContaID INT IDENTITY(1,1) PRIMARY KEY,
    ClienteID INT NOT NULL,
    TipoConta VARCHAR(50) NOT NULL DEFAULT 'Conta Investimento',
    Agencia VARCHAR(10) NOT NULL,
    NumeroConta VARCHAR(20) NOT NULL UNIQUE,
    Saldo DECIMAL(18, 2) NOT NULL DEFAULT 0.00,
    CONSTRAINT FK_Conta_Cliente FOREIGN KEY (ClienteID) REFERENCES Cliente(ClienteID) ON DELETE NO ACTION ON UPDATE CASCADE
);
GO

CREATE TABLE Portfolio (
    PortfolioID INT IDENTITY(1,1) PRIMARY KEY,
    ClienteID INT NOT NULL,
    NomePortfolio VARCHAR(100) NOT NULL,
    CONSTRAINT FK_Portfolio_Cliente FOREIGN KEY (ClienteID) REFERENCES Cliente(ClienteID) ON DELETE NO ACTION ON UPDATE CASCADE
);
GO

CREATE TABLE MovimentacaoConta (
    MovimentacaoID BIGINT IDENTITY(1,1) PRIMARY KEY,
    ContaOrigemID INT NULL,
    ContaDestinoID INT NULL,
    TipoMovimentacao VARCHAR(50) NOT NULL,
    Valor DECIMAL(18, 2) NOT NULL,
    DataHora DATETIME DEFAULT GETDATE(),
    Status VARCHAR(20) NOT NULL DEFAULT 'Processada',
    CONSTRAINT FK_Mov_ContaOrigem FOREIGN KEY (ContaOrigemID) REFERENCES Conta(ContaID) ON DELETE NO ACTION ON UPDATE NO ACTION,
    CONSTRAINT FK_Mov_ContaDestino FOREIGN KEY (ContaDestinoID) REFERENCES Conta(ContaID) ON DELETE NO ACTION ON UPDATE NO ACTION
);
GO

CREATE TABLE Ordem (
    OrdemID BIGINT IDENTITY(1,1) PRIMARY KEY,
    PortfolioID INT NOT NULL,
    ProdutoID INT NOT NULL,
    MovimentacaoID_Liquidacao BIGINT NULL,
    TipoOrdem VARCHAR(10) NOT NULL,
    Quantidade DECIMAL(18, 8) NOT NULL,
    PrecoUnitario DECIMAL(18, 2) NOT NULL,
    DataExecucao DATETIME DEFAULT GETDATE(),
    StatusOrdem VARCHAR(20) NOT NULL DEFAULT 'Executada',
    CONSTRAINT FK_Ordem_Portfolio FOREIGN KEY (PortfolioID) REFERENCES Portfolio(PortfolioID) ON DELETE NO ACTION ON UPDATE CASCADE,
    CONSTRAINT FK_Ordem_Produto FOREIGN KEY (ProdutoID) REFERENCES ProdutoFinanceiro(ProdutoID) ON DELETE NO ACTION ON UPDATE CASCADE,
    CONSTRAINT FK_Ordem_Movimentacao FOREIGN KEY (MovimentacaoID_Liquidacao) REFERENCES MovimentacaoConta(MovimentacaoID) ON DELETE NO ACTION ON UPDATE NO ACTION
);
GO

CREATE TABLE Posicao (
    PosicaoID INT IDENTITY(1,1) PRIMARY KEY,
    PortfolioID INT NOT NULL,
    ProdutoID INT NOT NULL,
    Quantidade DECIMAL(18, 8) NOT NULL,
    CustoMedio DECIMAL(18, 2) NOT NULL,
    CONSTRAINT UQ_Portfolio_Produto UNIQUE (PortfolioID, ProdutoID),
    CONSTRAINT FK_Posicao_Portfolio FOREIGN KEY (PortfolioID) REFERENCES Portfolio(PortfolioID) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT FK_Posicao_Produto FOREIGN KEY (ProdutoID) REFERENCES ProdutoFinanceiro(ProdutoID) ON DELETE CASCADE ON UPDATE CASCADE
);
GO

-- TRIGGER de Auditoria

CREATE TRIGGER trg_Cliente_Compliance_Audit
ON Cliente
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    IF UPDATE(StatusCompliance)
    BEGIN
        INSERT INTO AuditoriaCompliance (
            ClienteID,
            AssessorID,
            StatusAnterior,
            StatusNovo
        )
        SELECT
            i.ClienteID,
            NULL, 
            d.StatusCompliance,
            i.StatusCompliance
        FROM
            inserted i
        JOIN
            deleted d ON i.ClienteID = d.ClienteID
        WHERE
            i.StatusCompliance <> d.StatusCompliance;
    END
END;
GO