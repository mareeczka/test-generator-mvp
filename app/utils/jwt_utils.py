import jwt
from datetime import datetime, timedelta
from flask import current_app

def create_jwt(user_id, google_id):
    payload = {
        "user_id": user_id,
        "google_id": google_id,
        "exp": datetime.utcnow() + timedelta(hours=current_app.config["JWT_EXPIRATION_HOURS"])
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET"], algorithm=current_app.config["JWT_ALGORITHM"])

def decode_jwt(token):
    try:
        return jwt.decode(token, current_app.config["JWT_SECRET"], algorithms=[current_app.config["JWT_ALGORITHM"]])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
