import psycopg2
from psycopg2.extras import RealDictCursor
import os
from contextlib import contextmanager
from app.config import Config

class PostgresRepository:
    def __init__(self):
        self.config = Config()

    @contextmanager
    def get_connection(self):
        """Контекстный менеджер для соединения с БД"""
        conn = None
        try:
            conn = psycopg2.connect(
                host=self.config.DB_HOST,
                port=self.config.DB_PORT,
                dbname=self.config.DB_NAME,
                user=self.config.DB_USER,
                password=self.config.DB_PASSWORD
            )
            yield conn
        except Exception as e:
            print(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()

    @contextmanager
    def get_cursor(self, commit=False):
        """Контекстный менеджер для курсора"""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            try:
                yield cursor
                if commit:
                    conn.commit()
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                cursor.close()

    def execute_query(self, query, params=None, commit=False):
        """Выполнить запрос и вернуть результат"""
        with self.get_cursor(commit=commit) as cursor:
            cursor.execute(query, params or ())
            if query.strip().upper().startswith(('SELECT', 'WITH')):
                return cursor.fetchall()
            return None

    def execute_query_one(self, query, params=None):
        """Выполнить запрос и вернуть одну строку"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchone()

    def health_check(self):
        """Проверка подключения к БД"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT 1")
                return True
        except Exception as e:
            print(f"Health check failed: {e}")
            return False
