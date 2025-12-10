from flask_pymongo import PyMongo
import logging

mongo = PyMongo()

def init_mongo(app):
    """Инициализация MongoDB"""
    logger = app.logger

    # Получаем конфигурацию
    mongo_uri = app.config.get("MONGO_URI")
    mongo_dbname = app.config.get("MONGO_DBNAME")

    logger.info(f"Attempting to connect to MongoDB...")
    logger.info(f"MONGO_URI: {mongo_uri}")
    logger.info(f"MONGO_DBNAME: {mongo_dbname}")

    if not mongo_uri:
        logger.error("MONGO_URI not configured")
        return False

    # Устанавливаем конфигурацию
    app.config["MONGO_URI"] = mongo_uri
    if mongo_dbname:
        app.config["MONGO_DBNAME"] = mongo_dbname

    try:
        # Инициализируем PyMongo
        mongo.init_app(app)

        # Проверяем, что db объект создан
        if mongo.db is None:
            logger.error("mongo.db is None after init_app")
            return False

        logger.info(f"mongo.db object: {mongo.db}")
        logger.info(f"mongo.db.name: {mongo.db.name}")

        # Проверяем подключение
        result = mongo.db.command("ping")
        logger.info(f"MongoDB ping successful: {result}")
        return True

    except Exception as e:
        logger.error(f"MongoDB connection failed: {type(e).__name__}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def get_db():
    """Получить объект базы данных"""
    return mongo.db
