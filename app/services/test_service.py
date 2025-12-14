import uuid
from datetime import datetime
from app.repositories.pg_repo import PostgresRepository
from app.repositories.mongo_repo import MongoRepository
from app.services.material_service import MaterialService
from app.llm.generator import get_generator
from flask import current_app


class TestService:
    def __init__(self):
        self.pg_repo = PostgresRepository()
        self.mongo_repo = MongoRepository()
        self.material_service = MaterialService()

    def create_test(self, user_id: str, title: str, description: str = None, material_id: str = None):
        """
        Create a new test (empty, draft state)
        """
        test_id = str(uuid.uuid4())

        # Create empty document in MongoDB
        mongo_doc = {
            "test_id": test_id,
            "version": 1,
            "questions": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        mongo_result = self.mongo_repo.insert_one('test_documents', mongo_doc)

        # Create metadata in PostgreSQL
        query = """
            INSERT INTO tests (id, user_id, material_id, title, description, status, current_version, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, 'draft', 1, NOW(), NOW())
            RETURNING id, title, description, status, current_version, created_at, updated_at
        """

        result = self.pg_repo.execute_query_one(
            query,
            (test_id, user_id, material_id, title, description),
            commit=True
        )

        if result:
            return {
                "id": result['id'],
                "title": result['title'],
                "description": result['description'],
                "status": result['status'],
                "version": result['current_version'],
                "material_id": material_id,
                "question_count": 0,
                "created_at": result['created_at'].isoformat(),
                "updated_at": result['updated_at'].isoformat()
            }

        return None

    def list_user_tests(self, user_id: str):
        query = """
            SELECT t.id, t.title, t.description, t.status, t.current_version,
                   t.material_id, m.title as material_title, t.created_at, t.updated_at
            FROM tests t
            LEFT JOIN materials m ON t.material_id = m.id
            WHERE t.user_id = %s
            ORDER BY t.created_at DESC
        """

        results = self.pg_repo.execute_query(query, (user_id,))

        tests = []
        for row in results:
            # Get question count from MongoDB
            mongo_doc = self.mongo_repo.find_one('test_documents', {"test_id": row['id']})
            question_count = len(mongo_doc.get('questions', [])) if mongo_doc else 0

            tests.append({
                "id": row['id'],
                "title": row['title'],
                "description": row['description'],
                "status": row['status'],
                "version": row['current_version'],
                "material_id": row['material_id'],
                "material_title": row['material_title'],
                "question_count": question_count,
                "created_at": row['created_at'].isoformat(),
                "updated_at": row['updated_at'].isoformat()
            })

        return tests

    def get_test(self, test_id: str, user_id: str):
        query = """
            SELECT t.id, t.title, t.description, t.status, t.current_version,
                   t.material_id, m.title as material_title, t.created_at, t.updated_at
            FROM tests t
            LEFT JOIN materials m ON t.material_id = m.id
            WHERE t.id = %s AND t.user_id = %s
        """

        result = self.pg_repo.execute_query_one(query, (test_id, user_id))

        if not result:
            return None

        # Get questions from MongoDB
        mongo_doc = self.mongo_repo.find_one('test_documents', {"test_id": test_id})

        questions = mongo_doc.get('questions', []) if mongo_doc else []

        return {
            "id": result['id'],
            "title": result['title'],
            "description": result['description'],
            "status": result['status'],
            "version": result['current_version'],
            "material_id": result['material_id'],
            "material_title": result['material_title'],
            "questions": questions,
            "question_count": len(questions),
            "created_at": result['created_at'].isoformat(),
            "updated_at": result['updated_at'].isoformat()
        }

    def generate_test_questions(self, test_id: str, user_id: str, material_id: str, question_count: int = 10):
        test_check = self.pg_repo.execute_query_one(
            "SELECT id FROM tests WHERE id = %s AND user_id = %s",
            (test_id, user_id)
        )

        if not test_check:
            return None, "Test not found or unauthorized"

        # Get material text
        material_text = self.material_service.get_material_text(material_id)

        if not material_text:
            return None, "Material not found"

        # Get generator based on config
        use_mock = current_app.config.get('USE_MOCK_QUESTION_GENERATOR', True)

        if use_mock:
            delay = current_app.config.get('MOCK_GENERATION_DELAY', 2.0)
            generator = get_generator(use_mock=True, delay=delay)
        else:
            model_path = current_app.config.get('MODEL_PATH')
            if not model_path:
                return None, "MODEL_PATH not configured"
            generator = get_generator(use_mock=False, model_path=model_path)

        # Extract facts
        try:
            facts = generator.extract_facts(material_text)
        except Exception as e:
            return None, f"Fact extraction failed: {str(e)}"

        # Generate questions
        try:
            # Get test title for test_set_name
            test_info = self.pg_repo.execute_query_one(
                "SELECT title FROM tests WHERE id = %s",
                (test_id,)
            )
            test_set_name = test_info['title'] if test_info else "Test"

            questions = generator.generate_questions(
                facts=facts,
                test_set_name=test_set_name,
                question_count=question_count
            )
        except Exception as e:
            return None, f"Question generation failed: {str(e)}"

        # Store questions in MongoDB
        self.mongo_repo.update_one(
            'test_documents',
            {"test_id": test_id},
            {
                "$set": {
                    "questions": questions,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        # Update PostgreSQL metadata
        self.pg_repo.execute_query(
            "UPDATE tests SET updated_at = NOW() WHERE id = %s",
            (test_id,),
            commit=True
        )

        return questions, None

    def update_test_content(self, test_id: str, user_id: str, questions: list):
        """
        Update test questions (editing)
        """
        # Verify ownership
        test_check = self.pg_repo.execute_query_one(
            "SELECT id, current_version FROM tests WHERE id = %s AND user_id = %s",
            (test_id, user_id)
        )

        if not test_check:
            return False

        # Update questions in MongoDB
        self.mongo_repo.update_one(
            'test_documents',
            {"test_id": test_id},
            {
                "$set": {
                    "questions": questions,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        # Update timestamp in PostgreSQL
        self.pg_repo.execute_query(
            "UPDATE tests SET updated_at = NOW() WHERE id = %s",
            (test_id,),
            commit=True
        )

        return True

    def delete_test(self, test_id: str, user_id: str):
        # Check ownership
        test_check = self.pg_repo.execute_query_one(
            "SELECT id FROM tests WHERE id = %s AND user_id = %s",
            (test_id, user_id)
        )

        if not test_check:
            return False

        # Delete from MongoDB
        self.mongo_repo.delete_one('test_documents', {"test_id": test_id})

        # Delete from PostgreSQL
        self.pg_repo.execute_query(
            "DELETE FROM tests WHERE id = %s",
            (test_id,),
            commit=True
        )

        return True
