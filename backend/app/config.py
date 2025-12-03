import os
import urllib.parse
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()


class Config:
    # Chave secreta
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'chave_padrao_insegura_dev')

    # Dados do Banco (Lidos do .env)
    server = os.getenv('DB_SERVER')
    database = os.getenv('DB_NAME')
    username = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')

    # Driver ODBC (Tente o 17. Se der erro de driver não encontrado, mude para 18 ou 13)
    driver = 'ODBC Driver 17 for SQL Server'

    # Montagem da String de Conexão Segura
    if server and password:
        connection_string = (
            f'DRIVER={{{driver}}};'
            f'SERVER={server};'
            f'DATABASE={database};'
            f'UID={username};'
            f'PWD={password};'
            'TrustServerCertificate=yes;'  # Ajuda a evitar erros de certificado SSL em desenvolvimento
        )

        # Converte para formato URL exigido pelo SQLAlchemy
        params = urllib.parse.quote_plus(connection_string)
        SQLALCHEMY_DATABASE_URI = f"mssql+pyodbc:///?odbc_connect={params}"

        print(f"--- Configurado para SQL Server: {server} ---")
    else:
        # Fallback de segurança (SQLite) caso o .env esteja vazio
        print("AVISO: Credenciais não encontradas. Usando SQLite local.")
        basedir = os.path.abspath(os.path.dirname(__file__))
        db_path = os.path.join(basedir, '..', 'fallback.db')
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False