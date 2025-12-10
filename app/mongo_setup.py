#!/usr/bin/env python3

"""
MongoDB коллекции и индексы
"""

from pymongo import ASCENDING, DESCENDING
from pymongo.errors import OperationFailure

class MongoSetup:
    """Управление структурой MongoDB"""

    # Названия коллекций
    COLLECTION_TEST_DOCS = 'test_documents'
    COLLECTION_MATERIALS = 'materials_raw'
    # COLLECTION_FACTS = 'facts'
    # COLLECTION_CACHE = 'test_generation_cache'

    def __init__(self, db):
        """
        Args:
            db: объект базы данных MongoDB
        """
        self.db = db

    def ensure_indexes(self):
        """
        Создает все необходимые индексы (идемпотентная операция)
        Можно вызывать при старте приложения
        """
        try:
            self._create_test_documents_indexes()
            self._create_materials_indexes()
            return True
        except OperationFailure as e:
            print(f"Failed to create indexes: {e}")
            return False

    def _create_test_documents_indexes(self):
        """Создает индексы для коллекции test_documents"""
        collection = self.db[self.COLLECTION_TEST_DOCS]

        # Составной уникальный индекс (test_id, version)
        collection.create_index(
            [("test_id", ASCENDING), ("version", ASCENDING)],
            name="idx_test_id_version",
            unique=True,
            background=True
        )

        # Индекс для поиска по test_id
        collection.create_index(
            [("test_id", ASCENDING)],
            name="idx_test_id",
            background=True
        )

        # Индекс для сортировки по дате
        collection.create_index(
            [("created_at", DESCENDING)],
            name="idx_created_at",
            background=True
        )

    def _create_materials_indexes(self):
        """Создает индексы для коллекции materials_raw"""
        collection = self.db[self.COLLECTION_MATERIALS]

        # Уникальный индекс для material_id
        collection.create_index(
            [("material_id", ASCENDING)],
            name="idx_material_id",
            unique=True,
            background=True
        )

        # Индекс для сортировки по дате
        collection.create_index(
            [("created_at", DESCENDING)],
            name="idx_created_at",
            background=True
        )

    def drop_all_indexes(self):
        """
        ОПАСНО: Удаляет все индексы (кроме _id)
        Использовать только для тестирования
        """
        for collection_name in [self.COLLECTION_TEST_DOCS, self.COLLECTION_MATERIALS]:
            collection = self.db[collection_name]
            for index in collection.list_indexes():
                if index['name'] != '_id_':
                    collection.drop_index(index['name'])

    def get_collection(self, name):
        """Получить коллекцию по имени"""
        return self.db[name]

    @property
    def test_documents(self):
        """Коллекция test_documents"""
        return self.db[self.COLLECTION_TEST_DOCS]

    @property
    def materials_raw(self):
        """Коллекция materials_raw"""
        return self.db[self.COLLECTION_MATERIALS]
