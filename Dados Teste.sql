/*
==================================================================================
 PASSO A PASSO SQL: VERSÃO 2 (CORRIGIDA)
==================================================================================
*/

-- Conectar ao banco de dados correto
USE PrivateBankingDB;
GO

/*
----------------------------------------------------------------------------------
 PASSO 1: DESATIVAR TODAS AS CHAVES ESTRANGEIRAS
----------------------------------------------------------------------------------
*/
PRINT '--- 1. Desativando Chaves Estrangeiras ---';
EXEC sp_msforeachtable "ALTER TABLE ? NOCHECK CONSTRAINT all";
GO

/*
----------------------------------------------------------------------------------
 PASSO 2: LIMPAR TODAS AS TABELAS
----------------------------------------------------------------------------------
*/
PRINT '--- 2. Limpando todas as tabelas ---';
DELETE FROM ComposicaoFundo;
DELETE FROM HistoricoPreco;
DELETE FROM ClienteGrupoLink;
DELETE FROM AuditoriaCompliance;
DELETE FROM RespostaSuitabilityCliente;
DELETE FROM OpcaoResposta;
DELETE FROM Pergunta;
DELETE FROM QuestionarioSuitabilityVersao;
DELETE FROM Ordem;
DELETE FROM Posicao;
DELETE FROM Portfolio;
DELETE FROM MovimentacaoConta;
DELETE FROM Conta;
DELETE FROM Cliente;
DELETE FROM Assessor;
DELETE FROM GrupoEconomico;
DELETE FROM Produto_Acao;
DELETE FROM Produto_RendaFixa;
DELETE FROM Produto_Fundo;
DELETE FROM ProdutoFinanceiro;
GO

/*
----------------------------------------------------------------------------------
 PASSO 3: RESETAR OS IDs (IDENTITY) DE TODAS AS TABELAS
----------------------------------------------------------------------------------
*/
PRINT '--- 3. Resetando IDs (Identity) ---';
DBCC CHECKIDENT ('HistoricoPreco', RESEED, 0);
DBCC CHECKIDENT ('AuditoriaCompliance', RESEED, 0);
DBCC CHECKIDENT ('RespostaSuitabilityCliente', RESEED, 0);
DBCC CHECKIDENT ('OpcaoResposta', RESEED, 0);
DBCC CHECKIDENT ('Pergunta', RESEED, 0);
DBCC CHECKIDENT ('QuestionarioSuitabilityVersao', RESEED, 0);
DBCC CHECKIDENT ('Ordem', RESEED, 0);
DBCC CHECKIDENT ('Posicao', RESEED, 0);
DBCC CHECKIDENT ('Portfolio', RESEED, 0);
DBCC CHECKIDENT ('MovimentacaoConta', RESEED, 0);
DBCC CHECKIDENT ('Conta', RESEED, 0);
DBCC CHECKIDENT ('Cliente', RESEED, 0);
DBCC CHECKIDENT ('Assessor', RESEED, 0);
DBCC CHECKIDENT ('GrupoEconomico', RESEED, 0);
DBCC CHECKIDENT ('ProdutoFinanceiro', RESEED, 0);
-- ComposicaoFundo foi removido daqui pois não tem identity
GO

/*
----------------------------------------------------------------------------------
 PASSO 4: INSERIR DADOS DE "ADMIN" (PRÉ-REQUISITOS PARA TESTE)
----------------------------------------------------------------------------------
*/
PRINT '--- 4. Inserindo dados base (Admin) ---';

-- 4.1. Assessor (ID=1)
PRINT 'Inserindo Assessor ID 1...';
SET IDENTITY_INSERT Assessor ON;
INSERT INTO Assessor (AssessorID, Nome, Email, Nivel, SenhaHash, SuperiorID)
VALUES (
    1,
    'Assessor Padrão',
    'assessor@teste.com',
    'Senior',
    '$2b$12$4/aa2.m.sN41B.7F1.nSbeCXD.nJdqeIW.S.eS3.L.wE1Q.x/G/ta', -- Senha: "senha123"
    NULL
);
SET IDENTITY_INSERT Assessor OFF;
GO

-- 4.2. Produtos Financeiros (COM ISIN CORRIGIDO)
PRINT 'Inserindo Produtos...';
SET IDENTITY_INSERT ProdutoFinanceiro ON;

-- Produto 1: Renda Fixa (Conservador)
INSERT INTO ProdutoFinanceiro (ProdutoID, Ticker, ISIN, NomeProduto, NivelRiscoProduto, Emissor, ClasseAtivo)
VALUES (1, 'TESOURO2030', 'BRSTNCLTN7M0', 'Tesouro IPCA+ 2030', 1, 'Tesouro Nacional', 'RendaFixa');
INSERT INTO Produto_RendaFixa (ProdutoID, Tipo, DataVencimento, Indexador, TaxaContratada)
VALUES (1, 'Tesouro Direto', '2030-01-01', 'IPCA', 6.50);

-- Produto 2: Fundo (Moderado)
INSERT INTO ProdutoFinanceiro (ProdutoID, Ticker, ISIN, NomeProduto, NivelRiscoProduto, Emissor, ClasseAtivo)
VALUES (2, 'FUNDOMOD11', 'BRFMODCTF001', 'Fundo Moderado Ações', 3, 'Gestora X', 'Fundo');
INSERT INTO Produto_Fundo (ProdutoID, CNPJ_Fundo, Gestor, Administrador, TaxaAdm, TaxaPerf)
VALUES (2, '11222333000144', 'Gestora X', 'Banco Y', 1.5, 20.0);

-- Produto 3: Ação (Agressivo)
INSERT INTO ProdutoFinanceiro (ProdutoID, Ticker, ISIN, NomeProduto, NivelRiscoProduto, Emissor, ClasseAtivo)
VALUES (3, 'PETR4', 'BRPETRACNPR6', 'Petrobras PN', 5, 'Petrobras SA', 'Acao');
INSERT INTO Produto_Acao (ProdutoID, CNPJ_Empresa, SetorAtuacao)
VALUES (3, '33000167000101', 'Petróleo e Gás');

SET IDENTITY_INSERT ProdutoFinanceiro OFF;
GO

-- 4.3. Histórico de Preços (para Valorização)
PRINT 'Inserindo Preços...';
INSERT INTO HistoricoPreco (ProdutoID, Data, PrecoFechamento)
VALUES
(1, GETDATE(), 1050.00), -- Tesouro
(2, GETDATE(), 150.00),  -- Fundo Moderado (o que será comprado no teste)
(3, GETDATE(), 38.50);   -- Petrobras
GO

-- 4.4. Questionário de Suitability
PRINT 'Inserindo Questionário...';

-- Versão 1 (Ativa)
SET IDENTITY_INSERT QuestionarioSuitabilityVersao ON;
INSERT INTO QuestionarioSuitabilityVersao (VersaoID, DataVigencia, NomeQuestionario)
VALUES (1, '2025-01-01', 'Questionário Anual 2025');
SET IDENTITY_INSERT QuestionarioSuitabilityVersao OFF;

-- Pergunta 1
SET IDENTITY_INSERT Pergunta ON;
INSERT INTO Pergunta (PerguntaID, VersaoID, TextoPergunta)
VALUES (1, 1, 'Qual seu objetivo com este investimento?');
SET IDENTITY_INSERT Pergunta OFF;

-- Opções da Pergunta 1
SET IDENTITY_INSERT OpcaoResposta ON;
INSERT INTO OpcaoResposta (OpcaoID, PerguntaID, TextoOpcao, Pontos)
VALUES
(1, 1, 'Preservar capital (baixo risco)', 10),
(2, 1, 'Aumentar capital (moderado)', 30),
(3, 1, 'Especular (alto risco)', 50);
SET IDENTITY_INSERT OpcaoResposta OFF;

-- Pergunta 2
SET IDENTITY_INSERT Pergunta ON;
INSERT INTO Pergunta (PerguntaID, VersaoID, TextoPergunta)
VALUES (2, 1, 'Por quanto tempo pretende investir?');
SET IDENTITY_INSERT Pergunta OFF;

-- Opções da Pergunta 2
SET IDENTITY_INSERT OpcaoResposta ON;
INSERT INTO OpcaoResposta (OpcaoID, PerguntaID, TextoOpcao, Pontos)
VALUES
(4, 2, 'Menos de 1 ano', 10),
(5, 2, '1 a 3 anos', 20),
(6, 2, 'Mais de 3 anos', 40);
SET IDENTITY_INSERT OpcaoResposta OFF;
GO

/*
----------------------------------------------------------------------------------
 PASSO 5: REATIVAR TODAS AS CHAVES ESTRANGEIRAS
----------------------------------------------------------------------------------
*/
PRINT '--- 5. Reativando Chaves Estrangeiras ---';
EXEC sp_msforeachtable "ALTER TABLE ? WITH CHECK CHECK CONSTRAINT all";
GO

PRINT '--- SCRIPT CONCLUÍDO ---';
PRINT 'Banco de dados resetado e pronto para testes.';