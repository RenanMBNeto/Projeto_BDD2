import os
import urllib

class Config:
    JWT_SECRET_KEY = 'diegosegredos'
    
    server = 'DESKTOP-FDSVF2E'
    database = 'PrivateBankingDB'
    username = 'sa'
    password = 'senha'
    driver = 'ODBC Driver 17 for SQL Server'
    
    params = urllib.parse.quote_plus(
         f'DRIVER={{{driver}}};'
         f'SERVER={server};'
         f'DATABASE={database};'
         f'UID={username};'
         f'PWD={password};'
    )
    SQLALCHEMY_DATABASE_URI = f"mssql+pyodbc:///?odbc_connect={params}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False