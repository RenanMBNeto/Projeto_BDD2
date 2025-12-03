import os
import urllib.parse
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Carrega as variáveis do seu arquivo .env
load_dotenv()


def testar_conexao():
    print("--- Teste de Conexão com SQL Server ---")

    server = os.getenv('DB_SERVER')
    database = os.getenv('DB_NAME')
    username = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    driver = 'ODBC Driver 17 for SQL Server'  # Se der erro, tente trocar 17 por 18

    print(f"Servidor: {server}")
    print(f"Banco: {database}")
    print(f"Usuário: {username}")

    if not password:
        print("ERRO: A senha não foi encontrada no arquivo .env!")
        return

    try:
        # Monta a string de conexão igual ao seu sistema
        params = urllib.parse.quote_plus(
            f'DRIVER={{{driver}}};'
            f'SERVER={server};'
            f'DATABASE={database};'
            f'UID={username};'
            f'PWD={password};'
        )
        conn_str = f"mssql+pyodbc:///?odbc_connect={params}"

        # Tenta conectar
        engine = create_engine(conn_str)
        with engine.connect() as connection:
            result = connection.execute(text("SELECT @@VERSION"))
            version = result.fetchone()[0]
            print("\nSUCESSO! Conexão estabelecida.")
            print(f"Versão do Banco: {version.split('-')[0]}")  # Mostra só a primeira linha da versão

    except Exception as e:
        print("\n❌ FALHA NA CONEXÃO:")
        print(e)
        print("\nDica: Verifique se a senha no .env é exatamente a mesma que você criou.")


if __name__ == "__main__":
    testar_conexao()