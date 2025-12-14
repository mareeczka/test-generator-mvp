from flask import Blueprint, request, jsonify
from app.services.material_service import MaterialService
from app.auth import token_required
import traceback

materials_bp = Blueprint('materials', __name__, url_prefix='/materials')

@materials_bp.route('', methods=['POST'])
@token_required
def create_material():
    """
    Upload a plaintext material
    Body: {
        "title": "My Study Material",
        "text": "Content here..."
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        title = data.get('title', '').strip()
        text = data.get('text', '').strip()

        if not title:
            return jsonify({"error": "Title is required"}), 400

        if not text:
            return jsonify({"error": "Text content is required"}), 400

        # Create material - use request.user_id from decorator
        service = MaterialService()
        material = service.create_material(
            user_id=request.user_id,
            title=title,
            text=text,
            material_type='text'
        )

        return jsonify({
            "success": True,
            "material": material
        }), 201

    except Exception as e:
        print(f"Error creating material: {e}")
        traceback.print_exc()
        return jsonify({
            "error": "Failed to create material",
            "details": str(e)
        }), 500


@materials_bp.route('', methods=['GET'])
@token_required
def list_materials():
    """
    Get list of user's materials (metadata only)
    """
    try:
        service = MaterialService()
        materials = service.list_user_materials(request.user_id)

        return jsonify({
            "success": True,
            "materials": materials,
            "count": len(materials)
        }), 200

    except Exception as e:
        print(f"Error listing materials: {e}")
        traceback.print_exc()
        return jsonify({
            "error": "Failed to list materials",
            "details": str(e)
        }), 500


@materials_bp.route('/<material_id>', methods=['GET'])
@token_required
def get_material(material_id):
    """
    Get specific material with full content
    """
    try:
        service = MaterialService()
        material = service.get_material(material_id, request.user_id)

        if not material:
            return jsonify({"error": "Material not found"}), 404

        return jsonify({
            "success": True,
            "material": material
        }), 200

    except Exception as e:
        print(f"Error getting material: {e}")
        traceback.print_exc()
        return jsonify({
            "error": "Failed to get material",
            "details": str(e)
        }), 500


@materials_bp.route('/<material_id>', methods=['DELETE'])
@token_required
def delete_material(material_id):
    """
    Delete a material (cascade deletes in MongoDB handled by service)
    """
    try:
        service = MaterialService()
        success = service.delete_material(material_id, request.user_id)

        if not success:
            return jsonify({"error": "Material not found or unauthorized"}), 404

        return jsonify({
            "success": True,
            "message": "Material deleted successfully"
        }), 200

    except Exception as e:
        print(f"Error deleting material: {e}")
        traceback.print_exc()
        return jsonify({
            "error": "Failed to delete material",
            "details": str(e)
        }), 500
