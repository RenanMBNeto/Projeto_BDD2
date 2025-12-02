import os
import urllib
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()


class Config:
    # Lê a chave do .env, ou usa uma padrão insegura apenas se não encontrar (fallback)
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'chave_padrao_insegura_dev')

    server = os.getenv('DB_SERVER', 'localhost')
    database = os.getenv('DB_NAME', 'PrivateBankingDB')
    username = os.getenv('DB_USER', 'sa')
    password = os.getenv('DB_PASSWORD')
    driver = 'ODBC Driver 17 for SQL Server'

    # Monta a string de conexão apenas se a senha existir
    if password:
        params = urllib.parse.quote_plus(
            f'DRIVER={{{driver}}};'
            f'SERVER={server};'
            f'DATABASE={database};'
            f'UID={username};'
            f'PWD={password};'
        )
        SQLALCHEMY_DATABASE_URI = f"mssql+pyodbc:///?odbc_connect={params}"
    else:
        # Fallback ou erro se não houver senha configurada
        print("AVISO: Senha do banco de dados não encontrada no .env")
        SQLALCHEMY_DATABASE_URI = "sqlite:///fallback.db"  # Apenas para não crashar na inicialização se esquecer o .env

    SQLALCHEMY_TRACK_MODIFICATIONS = False