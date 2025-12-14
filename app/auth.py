import secrets
import urllib.parse
import requests
from flask import Blueprint, redirect, request, jsonify, session, current_app
from app.utils.jwt_utils import create_jwt
from functools import wraps
from app.utils.jwt_utils import decode_jwt

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid token"}), 401

        token = auth_header.split(" ")[1]
        payload = decode_jwt(token)

        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401

        # Add user info to request context
        request.user_id = payload["user_id"]
        request.google_id = payload["google_id"]

        return f(*args, **kwargs)
    return decorated

@auth_bp.route("/google/login")
def google_login():
    state = secrets.token_urlsafe(16)
    session["oauth_state"] = state
    params = {
        "client_id": current_app.config["GOOGLE_CLIENT_ID"],
        "redirect_uri": current_app.config["GOOGLE_REDIRECT_URI"],
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "consent",
    }
    url = f"{current_app.config['GOOGLE_AUTH_URL']}?{urllib.parse.urlencode(params)}"
    return redirect(url)

@auth_bp.route("/google/callback")
def google_callback():
    error = request.args.get("error")
    if error:
        return jsonify({"error": error}), 400

    state = request.args.get("state")
    if state != session.get("oauth_state"):
        return jsonify({"error": "Invalid OAuth state"}), 400

    code = request.args.get("code")
    token_data = {
        "client_id": current_app.config["GOOGLE_CLIENT_ID"],
        "client_secret": current_app.config["GOOGLE_CLIENT_SECRET"],
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": current_app.config["GOOGLE_REDIRECT_URI"],
    }

    token_resp = requests.post(
        current_app.config["GOOGLE_TOKEN_URL"], data=token_data
    )
    token_json = token_resp.json()

    if "access_token" not in token_json:
        return jsonify(token_json), 400

    userinfo_resp = requests.get(
        current_app.config["GOOGLE_USERINFO_URL"],
        headers={
            "Authorization": f"Bearer {token_json['access_token']}"
        },
    )
    userinfo = userinfo_resp.json()

    if not userinfo.get("email_verified"):
        return jsonify({"error": "Email not verified"}), 400

    # UPSERT USER TO POSTGRES
    from app.repositories.pg_repo import PostgresRepository
    pg_repo = PostgresRepository()

    google_id = userinfo["sub"]

    try:
        # Try to get existing user
        user = pg_repo.execute_query_one(
            "SELECT id, google_id, created_at FROM users WHERE google_id = %s",
            (google_id,)
        )

        # If doesn't exist, create
        if not user:
            print(f"Creating new user with google_id: {google_id}")
            user = pg_repo.execute_query_one(
                "INSERT INTO users (google_id) VALUES (%s) RETURNING id, google_id, created_at",
                (google_id,),
                commit=True  # <-- ADD THIS
            )
            print(f"User created: {user}")
        else:
            print(f"User found: {user}")

        token = create_jwt(str(user["id"]), user["google_id"])

        return jsonify({
            "status": "success",
            "token": token,
            "user": {
                "user_id": str(user["id"]),
                "google_id": user["google_id"],
                "email": userinfo["email"],
                "name": userinfo.get("name"),
                "picture": userinfo.get("picture"),
            }
        })

    except Exception as e:
        import traceback
        print(f"ERROR: {e}")
        print(traceback.format_exc())
        return jsonify({
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@auth_bp.route("/me")
@token_required
def get_me():
    from app.repositories.pg_repo import PostgresRepository
    pg_repo = PostgresRepository()

    user = pg_repo.execute_query_one(
        "SELECT id, google_id, created_at FROM users WHERE id = %s",
        (request.user_id,)
    )

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "user_id": str(user["id"]),
        "google_id": user["google_id"],
        "created_at": user["created_at"].isoformat()
    })
