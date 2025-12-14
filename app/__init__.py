from flask import Flask, jsonify
import os
from app.config import Config, DevelopmentConfig, ProductionConfig
from app.repositories.pg_repo import PostgresRepository
from .mongo import mongo, init_mongo
from .mongo_setup import MongoSetup
from app.auth import auth_bp
from app.api.materials import materials_bp

def create_app():
    app = Flask(__name__)
    env = os.getenv('FLASK_ENV', 'development')  # 'development', 'production'
    if env == 'production':
        app.config.from_object(ProductionConfig)
    elif env == 'development':
        app.config.from_object(DevelopmentConfig)
    else:
        app.config.from_object(Config)
    app.secret_key = "dev-secret"
    app.register_blueprint(auth_bp)
    app.register_blueprint(materials_bp)

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

    @app.route('/test-s3')
    def test_s3():
        try:
            from app.repositories.s3_repo import S3Repository
            from io import BytesIO

            s3_repo = S3Repository()

            # Test upload
            test_data = BytesIO(b"Hello MinIO! Test file content.")
            upload_success = s3_repo.upload_file(test_data, "test.txt")

            if not upload_success:
                return jsonify({
                    "status": "ERROR",
                    "error": "Failed to upload test file"
                }), 500

            # Test download
            content = s3_repo.download_file("test.txt")

            # Generate presigned URL
            presigned_url = s3_repo.generate_presigned_url("test.txt", expiration=3600)

            return jsonify({
                "status": "OK",
                "message": "MinIO connection successful",
                "uploaded": True,
                "content": content.decode('utf-8') if content else None,
                "presigned_url": presigned_url,
                "bucket": s3_repo.bucket
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

        # Check S3
        s3_status = "ERROR"
        try:
            from app.repositories.s3_repo import S3Repository
            s3_repo = S3Repository()
            s3_status = "OK"
        except Exception:
            pass

        return jsonify({
            'status': 'OK',
            'message': 'Server is running',
            'database': {
                'postgres': db_status,
                'mongodb': mongo_status,
                's3': s3_status
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

    # use_mock = app.config.get("USE_MOCK_QUESTION_GENERATOR", True)
    # if use_mock:
    #     from app.question_generator.mock_routes import question_bp
    #     app.logger.info("Using MOCK question generator (dev mode)")
    # else:
    #     from app.question_generator.routes import question_bp
    #     model_path = app.config.get("MODEL_PATH")
    #     if not model_path or not os.path.exists(model_path):
    #         app.logger.error(f"MODEL_PATH not set or invalid: {model_path}")
    #         app.logger.error("Real question generator disabled — falling back to mock")
    #         from app.question_generator.mock_routes import question_bp
    #     else:
    #         app.logger.info(f"Using REAL question generator with model at: {model_path}")

    # app.register_blueprint(question_bp)

    return app
