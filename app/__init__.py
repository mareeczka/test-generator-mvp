from flask import Flask, jsonify
from app.config import Config
from app.repositories.pg_repo import PostgresRepository

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Инициализация репозитория
    pg_repo = PostgresRepository()

    # Health check эндпоинт
    @app.route('/health')
    def health():
        db_status = "OK" if pg_repo.health_check() else "ERROR"
        return jsonify({
            'status': 'OK',
            'message': 'Server is running',
            'database': db_status
        })

    # Простой тестовый эндпоинт для проверки БД
    @app.route('/test-db')
    def test_db():
        try:
            result = pg_repo.execute_query_one("SELECT version()")
            return jsonify({
                'status': 'OK',
                'postgres_version': result['version'] if result else 'No result'
            })
        except Exception as e:
            return jsonify({
                'status': 'ERROR',
                'error': str(e)
            }), 500

    return app
