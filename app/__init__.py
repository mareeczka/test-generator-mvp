from flask import Flask, jsonify
from app.config import Config
from app.repositories.pg_repo import PostgresRepository
from .mongo import mongo, init_mongo  # импортируем функцию init_mongo
from .mongo_setup import MongoSetup

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Инициализация репозитория
    pg_repo = PostgresRepository()

    mongo_connected = init_mongo(app)

    # Создание индексов MongoDB при старте
    if mongo_connected:
        mongo_setup = MongoSetup(mongo.db)
        if mongo_setup.ensure_indexes():
            app.logger.info("MongoDB indexes created successfully")
        else:
            app.logger.warning("Failed to create some MongoDB indexes")

    @app.route('/test-mongo')
    def test_mongo():
        if not mongo_connected:
            return jsonify({
                "status": "ERROR",
                "error": "MongoDB not configured or connection failed"
            }), 500

        try:
            result = mongo.db.command("ping")
            collections = mongo.db.list_collection_names()

            # Информация об индексах
            indexes_info = {}
            for coll_name in ['test_documents', 'materials_raw']:
                if coll_name in collections:
                    indexes = list(mongo.db[coll_name].list_indexes())
                    indexes_info[coll_name] = [idx['name'] for idx in indexes]

            return jsonify({
                "status": "OK",
                "message": "MongoDB connection successful",
                "database": mongo.db.name,
                "ping_result": result,
                "collections": collections,
                "indexes": indexes_info
            })
        except Exception as e:
            import traceback
            return jsonify({
                "status": "ERROR",
                "error": str(e),
                "traceback": traceback.format_exc()
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
