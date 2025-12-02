-- FUNCTION para Calcular Perfil de Risco

IF OBJECT_ID('fn_CalcularPerfilRisco', 'FN') IS NOT NULL
    DROP FUNCTION fn_CalcularPerfilRisco;
GO

CREATE FUNCTION fn_CalcularPerfilRisco (@PontuacaoTotal INT)
RETURNS VARCHAR(50)
AS
BEGIN
    DECLARE @Perfil VARCHAR(50);
    IF @PontuacaoTotal IS NULL RETURN 'Indefinido';

    IF @PontuacaoTotal < 50 SET @Perfil = 'Conservador';
    ELSE IF @PontuacaoTotal <= 80 SET @Perfil = 'Moderado';
    ELSE SET @Perfil = 'Agressivo';

    RETURN @Perfil;
END;
GO

PRINT 'Function fn_CalcularPerfilRisco criada/atualizada com sucesso.';
GO

SELECT dbo.fn_CalcularPerfilRisco(60);
GO

SELECT ClienteID, PontuacaoTotal, dbo.fn_CalcularPerfilRisco(PontuacaoTotal) AS Perfil 
FROM RespostaSuitabilityCliente;
GO