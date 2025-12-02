-- VIEW para Carteira Detalhada do Cliente
IF OBJECT_ID('vw_CarteiraDetalhadaCliente', 'V') IS NOT NULL
    DROP VIEW vw_CarteiraDetalhadaCliente;
GO

CREATE VIEW vw_CarteiraDetalhadaCliente AS
SELECT 
    c.ClienteID,
    c.NomeCompleto AS NomeCliente,
    p.PortfolioID,
    p.NomePortfolio,
    pos.PosicaoID,
    prod.ProdutoID,
    prod.Ticker,
    prod.NomeProduto,
    prod.ClasseAtivo,
    pos.Quantidade,
    pos.CustoMedio,
    (pos.Quantidade * pos.CustoMedio) AS ValorDeCustoTotal
FROM 
    Cliente c
JOIN 
    Portfolio p ON c.ClienteID = p.ClienteID
JOIN 
    Posicao pos ON p.PortfolioID = pos.PortfolioID
JOIN 
    ProdutoFinanceiro prod ON pos.ProdutoID = prod.ProdutoID
LEFT JOIN (
    SELECT ProdutoID, PrecoFechamento, ROW_NUMBER() OVER(PARTITION BY ProdutoID ORDER BY Data DESC) as rn
    FROM HistoricoPreco
) hp ON prod.ProdutoID = hp.ProdutoID AND hp.rn = 1
GO

PRINT 'View vw_CarteiraDetalhadaCliente criada/atualizada com sucesso.';
GO

SELECT * FROM vw_CarteiraDetalhadaCliente WHERE ClienteID = 1;
GO

---