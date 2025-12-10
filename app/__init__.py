from flask import Flask, jsonify
from app.config import Config
from app.repositories.pg_repo import PostgresRepository
from .mongo import mongo, init_mongo

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Инициализация репозитория
    pg_repo = PostgresRepository()

    # Инициализация MongoDB
    mongo_connected = init_mongo(app)

    @app.route('/test-mongo')
    def test_mongo():
        if not mongo_connected:
            return jsonify({
                "status": "ERROR",
                "error": "MongoDB not configured or connection failed"
            }), 500

        try:
            # Пингуем сервер
            result = mongo.db.command("ping")
            return jsonify({
                "status": "OK",
                "message": "MongoDB connection successful",
                "result": result
            })
        except Exception as e:
            return jsonify({
                "status": "ERROR",
                "error": str(e)
            }), 500

    @app.route('/health')
    def health():
        db_status = "OK" if pg_repo.health_check() else "ERROR"
        mongo_status = "OK" if mongo_connected and mongo.db is not None else "ERROR"

        return jsonify({
            'status': 'OK',
            'message': 'Server is running',
            'database': {
                'postgres': db_status,
                'mongodb': mongo_status
            }
        })

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
