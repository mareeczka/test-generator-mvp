import uuid
from datetime import datetime
from app.repositories.pg_repo import PostgresRepository
from app.repositories.mongo_repo import MongoRepository


class MaterialService:
    def __init__(self):
        self.pg_repo = PostgresRepository()
        self.mongo_repo = MongoRepository()

    def create_material(self, user_id: str, title: str, text: str, material_type: str = 'text'):
        """
        Create a new material:
        1. Store raw text in MongoDB
        2. Store metadata in PostgreSQL
        """
        # Generate UUID for material
        material_id = str(uuid.uuid4())

        # Store raw content in MongoDB
        mongo_doc = {
            "material_id": material_id,
            "raw_text": text,
            "metadata": {
                "source": "upload",
                "char_count": len(text),
                "word_count": len(text.split())
            },
            "created_at": datetime.utcnow()
        }

        mongo_result = self.mongo_repo.insert_one('materials_raw', mongo_doc)
        mongo_id = str(mongo_result.inserted_id)

        # Store metadata in PostgreSQL
        query = """
            INSERT INTO materials (id, user_id, title, type, mongo_id, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
            RETURNING id, title, type, created_at, updated_at
        """
        result = self.pg_repo.execute_query_one(
            query,
            (material_id, user_id, title, material_type, mongo_id),
            commit=True  # IMPORTANT: Commit the transaction!
        )

        if result:
            return {
                "id": result['id'],
                "title": result['title'],
                "type": result['type'],
                "char_count": len(text),
                "word_count": len(text.split()),
                "created_at": result['created_at'].isoformat(),
                "updated_at": result['updated_at'].isoformat()
            }

        return None

    def list_user_materials(self, user_id: str):
        """
        Get list of user's materials (metadata only)
        """
        query = """
            SELECT id, title, type, created_at, updated_at
            FROM materials
            WHERE user_id = %s
            ORDER BY created_at DESC
        """
        results = self.pg_repo.execute_query(query, (user_id,))

        materials = []
        for row in results:
            materials.append({
                "id": row['id'],
                "title": row['title'],
                "type": row['type'],
                "created_at": row['created_at'].isoformat(),
                "updated_at": row['updated_at'].isoformat()
            })

        return materials

    def get_material(self, material_id: str, user_id: str):
        """
        Get full material with content
        """
        # Get metadata from PostgreSQL
        query = """
            SELECT id, title, type, mongo_id, created_at, updated_at
            FROM materials
            WHERE id = %s AND user_id = %s
        """
        result = self.pg_repo.execute_query_one(query, (material_id, user_id))

        if not result:
            return None

        # Get content from MongoDB
        mongo_doc = self.mongo_repo.find_one(
            'materials_raw',
            {"material_id": material_id}
        )

        if not mongo_doc:
            # Metadata exists but content missing - data inconsistency
            return {
                "id": result['id'],
                "title": result['title'],
                "type": result['type'],
                "text": "",
                "error": "Content not found in database",
                "created_at": result['created_at'].isoformat(),
                "updated_at": result['updated_at'].isoformat()
            }

        return {
            "id": result['id'],
            "title": result['title'],
            "type": result['type'],
            "text": mongo_doc.get('raw_text', ''),
            "metadata": mongo_doc.get('metadata', {}),
            "created_at": result['created_at'].isoformat(),
            "updated_at": result['updated_at'].isoformat()
        }

    def delete_material(self, material_id: str, user_id: str):
        """
        Delete material (both PostgreSQL and MongoDB)
        """
        # First check if material exists and belongs to user
        query = "SELECT mongo_id FROM materials WHERE id = %s AND user_id = %s"
        result = self.pg_repo.execute_query_one(query, (material_id, user_id))

        if not result:
            return False

        # Delete from MongoDB
        self.mongo_repo.delete_one('materials_raw', {"material_id": material_id})

        # Delete from PostgreSQL (will cascade to related tests if ON DELETE CASCADE)
        delete_query = "DELETE FROM materials WHERE id = %s AND user_id = %s"
        self.pg_repo.execute_query(delete_query, (material_id, user_id), commit=True)

        return True

    def get_material_text(self, material_id: str):
        """
        Quick method to get just the text content (for generation)
        No user_id check - used internally by services
        """
        mongo_doc = self.mongo_repo.find_one(
            'materials_raw',
            {"material_id": material_id}
        )

        if not mongo_doc:
            return None

        return mongo_doc.get('raw_text', '')
