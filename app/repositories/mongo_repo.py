from app.mongo import mongo
import pymongo

class MongoRepository:
    def __init__(self):
        self.db = mongo.db
        self._verify_connection()

    def _verify_connection(self):
        try:
            self.db.client.admin.command('ping')
        except pymongo.errors.ConnectionFailure as e:
            raise ConnectionError(f"Failed to connect to MongoDB: {e}")

    def insert_one(self, collection: str, document: dict, add_version: bool = False):
        if add_version:
            document['version'] = 1  # В текущей итерации версия всегда 1
        return self.db[collection].insert_one(document)

    def find_one(self, collection: str, query: dict):
        return self.db[collection].find_one(query)

    def find_many(self, collection: str, query: dict, sort=None, limit=None):
        cursor = self.db[collection].find(query)
        if sort:
            cursor = cursor.sort(sort)
        if limit:
            cursor = cursor.limit(limit)
        return list(cursor)

    def update_one(self, collection: str, query: dict, update: dict):
        return self.db[collection].update_one(query, update)

    def delete_one(self, collection: str, query: dict):
        return self.db[collection].delete_one(query)

    def delete_many(self, collection: str, query: dict):
        return self.db[collection].delete_many(query)

    def count(self, collection: str, query: dict):
        return self.db[collection].count_documents(query)

    def create_test_document(self, data: dict):
        """
        Создание документа в коллекции test_documents.
        Добавляем поле version = 1.
        :param data: Словарь с данными (должен включать 'test_id').
        :return: ID вставленного документа.
        """
        return self.insert_one('test_documents', data, add_version=True)

    def get_by_test_id(self, test_id: str):
        """
        Получение документа из test_documents по test_id.
        :param test_id: ID теста.
        :return: Документ или None, если не найден.
        """
        return self.find_one('test_documents', {'test_id': test_id})

    def create_material_raw(self, data: dict):
        """
        Создание документа в коллекции materials_raw.
        Добавляем поле version = 1.
        :param data: Словарь с данными (должен включать 'material_id').
        :return: ID вставленного документа.
        """
        return self.insert_one('materials_raw', data, add_version=True)

    def get_by_material_id(self, material_id: str):
        """
        Получение документа из materials_raw по material_id.
        :param material_id: ID материала.
        :return: Документ или None, если не найден.
        """
        return self.find_one('materials_raw', {'material_id': material_id})
