from flask import Blueprint, jsonify

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/test')
def test_auth():
    return jsonify({'message': 'Auth endpoint works!'})
