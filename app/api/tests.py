from flask import Blueprint, request, jsonify
from app.services.test_service import TestService
from app.auth import token_required
import traceback

tests_bp = Blueprint('tests', __name__, url_prefix='/tests')


@tests_bp.route('', methods=['POST'])
@token_required
def create_test():
    """
    Create a new test
    Body: {
        "title": "My Test",
        "description": "Optional description",
        "material_id": "uuid-of-material" (optional)
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        title = data.get('title', '').strip()
        description = data.get('description', '').strip()
        material_id = data.get('material_id')

        if not title:
            return jsonify({"error": "Title is required"}), 400

        service = TestService()
        test = service.create_test(
            user_id=request.user_id,
            title=title,
            description=description if description else None,
            material_id=material_id
        )

        return jsonify({
            "success": True,
            "test": test
        }), 201

    except Exception as e:
        print(f"Error creating test: {e}")
        traceback.print_exc()
        return jsonify({
            "error": "Failed to create test",
            "details": str(e)
        }), 500


@tests_bp.route('', methods=['GET'])
@token_required
def list_tests():
    """
    Get list of user's tests
    """
    try:
        service = TestService()
        tests = service.list_user_tests(request.user_id)

        return jsonify({
            "success": True,
            "tests": tests,
            "count": len(tests)
        }), 200

    except Exception as e:
        print(f"Error listing tests: {e}")
        traceback.print_exc()
        return jsonify({
            "error": "Failed to list tests",
            "details": str(e)
        }), 500


@tests_bp.route('/<test_id>', methods=['GET'])
@token_required
def get_test(test_id):
    """
    Get specific test with full content
    """
    try:
        service = TestService()
        test = service.get_test(test_id, request.user_id)

        if not test:
            return jsonify({"error": "Test not found"}), 404

        return jsonify({
            "success": True,
            "test": test
        }), 200

    except Exception as e:
        print(f"Error getting test: {e}")
        traceback.print_exc()
        return jsonify({
            "error": "Failed to get test",
            "details": str(e)
        }), 500


@tests_bp.route('/<test_id>/generate', methods=['POST'])
@token_required
def generate_test(test_id):
    """
    Generate questions for a test from a material
    Body: {
        "material_id": "uuid-of-material",
        "question_count": 10 (optional, default 10)
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        material_id = data.get('material_id')
        question_count = data.get('question_count', 10)

        if not material_id:
            return jsonify({"error": "material_id is required"}), 400

        try:
            question_count = int(question_count)
            if question_count < 1 or question_count > 50:
                return jsonify({"error": "question_count must be between 1 and 50"}), 400
        except ValueError:
            return jsonify({"error": "question_count must be an integer"}), 400

        service = TestService()
        questions, error = service.generate_test_questions(
            test_id=test_id,
            user_id=request.user_id,
            material_id=material_id,
            question_count=question_count
        )

        if error:
            return jsonify({
                "success": False,
                "error": error
            }), 400

        return jsonify({
            "success": True,
            "message": "Questions generated successfully",
            "questions": questions,
            "question_count": len(questions)
        }), 200

    except Exception as e:
        print(f"Error generating test: {e}")
        traceback.print_exc()
        return jsonify({
            "error": "Failed to generate test",
            "details": str(e)
        }), 500


@tests_bp.route('/<test_id>/content', methods=['GET'])
@token_required
def get_test_content(test_id):
    """
    Get just the questions array
    """
    try:
        service = TestService()
        test = service.get_test(test_id, request.user_id)

        if not test:
            return jsonify({"error": "Test not found"}), 404

        return jsonify({
            "success": True,
            "questions": test['questions']
        }), 200

    except Exception as e:
        print(f"Error getting test content: {e}")
        traceback.print_exc()
        return jsonify({
            "error": "Failed to get test content",
            "details": str(e)
        }), 500


@tests_bp.route('/<test_id>/content', methods=['PATCH'])
@token_required
def update_test_content(test_id):
    """
    Update test questions
    Body: {
        "questions": [ ... array of question objects ... ]
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        questions = data.get('questions')

        if not isinstance(questions, list):
            return jsonify({"error": "questions must be an array"}), 400

        service = TestService()
        success = service.update_test_content(
            test_id=test_id,
            user_id=request.user_id,
            questions=questions
        )

        if not success:
            return jsonify({"error": "Test not found or unauthorized"}), 404

        return jsonify({
            "success": True,
            "message": "Test content updated successfully",
            "question_count": len(questions)
        }), 200

    except Exception as e:
        print(f"Error updating test content: {e}")
        traceback.print_exc()
        return jsonify({
            "error": "Failed to update test content",
            "details": str(e)
        }), 500


@tests_bp.route('/<test_id>', methods=['DELETE'])
@token_required
def delete_test(test_id):
    """
    Delete a test
    """
    try:
        service = TestService()
        success = service.delete_test(test_id, request.user_id)

        if not success:
            return jsonify({"error": "Test not found or unauthorized"}), 404

        return jsonify({
            "success": True,
            "message": "Test deleted successfully"
        }), 200

    except Exception as e:
        print(f"Error deleting test: {e}")
        traceback.print_exc()
        return jsonify({
            "error": "Failed to delete test",
            "details": str(e)
        }), 500
