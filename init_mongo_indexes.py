#!/usr/bin/env python3

from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, OperationFailure
import os
from dotenv import load_dotenv

load_dotenv()

def create_indexes():
    """Создает необходимые индексы для коллекций MongoDB"""

    # Подключение к MongoDB
    mongo_uri = os.getenv('MONGO_URI')
    mongo_dbname = os.getenv('MONGO_DBNAME')

    if not mongo_uri or not mongo_dbname:
        print("❌ Error: MONGO_URI or MONGO_DBNAME not set in .env")
        return False

    try:
        print(f"🔌 Connecting to MongoDB: {mongo_uri}")
        client = MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000
        )

        # Проверка подключения
        client.admin.command('ping')
        print("✅ Connected to MongoDB successfully")

        db = client[mongo_dbname]
        print(f"📊 Using database: {mongo_dbname}")

        # ==========================================
        # 1. Индексы для test_documents
        # ==========================================
        print("\n📝 Creating indexes for 'test_documents' collection...")
        test_docs = db['test_documents']

        # Составной индекс (test_id, version)
        # Уникальный, чтобы избежать дублирования версий
        test_docs.create_index(
            [("test_id", ASCENDING), ("version", ASCENDING)],
            name="idx_test_id_version",
            unique=True
        )
        print("  ✓ Created unique index: test_id + version")

        # Индекс для поиска по test_id (для получения всех версий)
        test_docs.create_index(
            [("test_id", ASCENDING)],
            name="idx_test_id"
        )
        print("  ✓ Created index: test_id")

        # Индекс для сортировки по дате создания
        test_docs.create_index(
            [("created_at", DESCENDING)],
            name="idx_created_at"
        )
        print("  ✓ Created index: created_at (descending)")

        # ==========================================
        # 2. Индексы для materials_raw
        # ==========================================
        print("\n📚 Creating indexes for 'materials_raw' collection...")
        materials = db['materials_raw']

        # Уникальный индекс для material_id
        materials.create_index(
            [("material_id", ASCENDING)],
            name="idx_material_id",
            unique=True
        )
        print("  ✓ Created unique index: material_id")

        # Индекс для сортировки по дате создания
        materials.create_index(
            [("created_at", DESCENDING)],
            name="idx_created_at"
        )
        print("  ✓ Created index: created_at (descending)")

        # ==========================================
        # Вывод информации об индексах
        # ==========================================
        print("\n" + "="*60)
        print("📋 Summary of created indexes:")
        print("="*60)

        print("\n🔹 test_documents:")
        for idx in test_docs.list_indexes():
            print(f"  - {idx['name']}: {idx['key']}")

        print("\n🔹 materials_raw:")
        for idx in materials.list_indexes():
            print(f"  - {idx['name']}: {idx['key']}")

        print("\n✅ All indexes created successfully!")
        return True

    except ConnectionFailure as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        return False
    except OperationFailure as e:
        print(f"❌ Failed to create indexes: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'client' in locals():
            client.close()
            print("\n🔌 MongoDB connection closed")

if __name__ == "__main__":
    print("="*60)
    print("MongoDB Index Initialization Script")
    print("="*60)
    success = create_indexes()
    exit(0 if success else 1)
