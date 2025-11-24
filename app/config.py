import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    DEBUG = os.getenv('DEBUG', True)

    #pgsql
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'test_mvp_db')
    DB_USER = os.getenv('DB_USER', 'test_mvp_user')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'test_mvp_password')
