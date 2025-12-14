from app.mongo import mongo


class MongoRepository:

    def __init__(self):
        self.db = mongo.db

    def insert_one(self, collection: str, document: dict):
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
