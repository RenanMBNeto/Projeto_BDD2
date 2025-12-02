-- STORED PROCEDURE para Executar Ordem

IF OBJECT_ID('sp_ExecutarOrdem', 'P') IS NOT NULL
    DROP PROCEDURE sp_ExecutarOrdem;
GO

CREATE PROCEDURE sp_ExecutarOrdem (
    @PortfolioID INT,
    @ProdutoID INT,
    @TipoOrdem VARCHAR(10), -- 'Compra' ou 'Venda'
    @Quantidade DECIMAL(18, 8),
    @PrecoUnitario DECIMAL(18, 2),
    @AssessorID INT -- ID do assessor que está a executar (para auditoria futura, não usado agora)
)
AS
BEGIN
    SET NOCOUNT ON; -- Evita mensagens "X rows affected"
    DECLARE @ClienteID INT;
    DECLARE @ContaID INT;
    DECLARE @SaldoAtual DECIMAL(18, 2);
    DECLARE @ValorTotalOrdem DECIMAL(18, 2) = @Quantidade * @PrecoUnitario;
    DECLARE @MovimentacaoID BIGINT;
    DECLARE @PosicaoQuantidadeAtual DECIMAL(18, 8);
    DECLARE @PosicaoCustoMedioAtual DECIMAL(18, 2);
    DECLARE @Erro VARCHAR(500) = NULL;

    -- Inicia a transação
    BEGIN TRANSACTION;

    BEGIN TRY
        -- Validações (Simplificadas - Suitability e outras deveriam estar aqui)
        SELECT @ClienteID = ClienteID FROM Portfolio WHERE PortfolioID = @PortfolioID;
        IF @ClienteID IS NULL 
        BEGIN 
            SET @Erro = 'Portfólio não encontrado.'; 
            RAISERROR(@Erro, 16, 1); 
        END;

        SELECT @ContaID = ContaID, @SaldoAtual = Saldo FROM Conta WHERE ClienteID = @ClienteID; -- Assume conta única
        IF @ContaID IS NULL 
        BEGIN 
            SET @Erro = 'Conta não encontrada para o cliente.'; 
            RAISERROR(@Erro, 16, 1); 
        END;

        IF @TipoOrdem = 'Compra'
        BEGIN
            IF @SaldoAtual < @ValorTotalOrdem 
            BEGIN 
                SET @Erro = 'Saldo insuficiente.'; 
                RAISERROR(@Erro, 16, 1); 
            END;

            -- Atualiza Saldo
            UPDATE Conta SET Saldo = Saldo - @ValorTotalOrdem WHERE ContaID = @ContaID;

            -- Regista Movimentação
            INSERT INTO MovimentacaoConta (ContaOrigemID, TipoMovimentacao, Valor)
            VALUES (@ContaID, 'Aplicacao', @ValorTotalOrdem);
            SET @MovimentacaoID = SCOPE_IDENTITY();

            -- Atualiza/Insere Posição
            SELECT @PosicaoQuantidadeAtual = Quantidade, @PosicaoCustoMedioAtual = CustoMedio 
            FROM Posicao WHERE PortfolioID = @PortfolioID AND ProdutoID = @ProdutoID;

            IF @@ROWCOUNT > 0 -- Posição existe
            BEGIN
                DECLARE @NovoCustoMedio DECIMAL(18, 2) = ((@PosicaoQuantidadeAtual * @PosicaoCustoMedioAtual) + @ValorTotalOrdem) / (@PosicaoQuantidadeAtual + @Quantidade);
                UPDATE Posicao 
                SET Quantidade = Quantidade + @Quantidade, CustoMedio = @NovoCustoMedio
                WHERE PortfolioID = @PortfolioID AND ProdutoID = @ProdutoID;
            END
            ELSE -- Posição não existe
            BEGIN
                INSERT INTO Posicao (PortfolioID, ProdutoID, Quantidade, CustoMedio)
                VALUES (@PortfolioID, @ProdutoID, @Quantidade, @PrecoUnitario);
            END
        END
        ELSE IF @TipoOrdem = 'Venda'
        BEGIN
            SELECT @PosicaoQuantidadeAtual = Quantidade 
            FROM Posicao WHERE PortfolioID = @PortfolioID AND ProdutoID = @ProdutoID;

            IF @@ROWCOUNT = 0 OR @PosicaoQuantidadeAtual < @Quantidade
            BEGIN
                SET @Erro = 'Quantidade insuficiente para venda.'; 
                RAISERROR(@Erro, 16, 1); 
            END;

            -- Atualiza Saldo
            UPDATE Conta SET Saldo = Saldo + @ValorTotalOrdem WHERE ContaID = @ContaID;

            -- Regista Movimentação
            INSERT INTO MovimentacaoConta (ContaDestinoID, TipoMovimentacao, Valor)
            VALUES (@ContaID, 'Resgate', @ValorTotalOrdem);
            SET @MovimentacaoID = SCOPE_IDENTITY();

            -- Atualiza Posição
            UPDATE Posicao SET Quantidade = Quantidade - @Quantidade
            WHERE PortfolioID = @PortfolioID AND ProdutoID = @ProdutoID;

            -- Opcional: Remover posição se quantidade for zero
            IF (@PosicaoQuantidadeAtual - @Quantidade) = 0
                DELETE FROM Posicao WHERE PortfolioID = @PortfolioID AND ProdutoID = @ProdutoID;
        END
        ELSE
        BEGIN
            SET @Erro = 'Tipo de Ordem inválido.'; 
            RAISERROR(@Erro, 16, 1); 
        END;

        -- Regista a Ordem
        INSERT INTO Ordem (PortfolioID, ProdutoID, MovimentacaoID_Liquidacao, TipoOrdem, Quantidade, PrecoUnitario)
        VALUES (@PortfolioID, @ProdutoID, @MovimentacaoID, @TipoOrdem, @Quantidade, @PrecoUnitario);

        -- Se chegou aqui, tudo OK
        COMMIT TRANSACTION;
        PRINT 'Ordem executada com sucesso.';

    END TRY
    BEGIN CATCH
        -- Se deu erro, desfaz tudo
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;

        -- Regista ou retorna o erro
        SET @Erro = ERROR_MESSAGE();
        PRINT 'Erro ao executar ordem: ' + @Erro;
        -- Re-lança o erro para a aplicação saber que falhou
        RAISERROR(@Erro, 16, 1); 
    END CATCH
END;
GO

PRINT 'Stored Procedure sp_ExecutarOrdem criada/atualizada com sucesso.';
GO

EXEC sp_ExecutarOrdem @PortfolioID=2, @ProdutoID=1, @TipoOrdem='Compra', @Quantidade=5, @PrecoUnitario=30, @AssessorID=1;
GO