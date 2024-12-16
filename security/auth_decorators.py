from functools import wraps
from flask import request
from jwt import ExpiredSignatureError, InvalidTokenError
from os import environ
import jwt

def admin_required(func):
    @wraps(func)
    def wrapper():
        headers = request.headers

        # Check for Authorization header
        if "Authorization" not in headers:
            return {"error": "Authorization header is missing"}, 401

        token = headers["Authorization"]

        # Remove "Bearer " prefix from token
        token = token.split(" ")[1]
        PUBLIC_KEY = environ.get("PUBLIC_KEY", "").replace("\\n", "\n")
        
        if not PUBLIC_KEY:
            return {"error": "Public key not found"}, 500

        try:
            # Decode the JWT
            decoded = jwt.decode(token, PUBLIC_KEY, algorithms=["RS256"])

            # Check if the user has the 'admin' role
            if "roles" not in decoded or "admin" not in decoded["roles"]:
                return {"error": "Forbidden: Admin role required"}, 403

        except ExpiredSignatureError:
            return {"error": "Token has expired"}, 401
        except InvalidTokenError:
            return {"error": "Invalid token"}, 401
        return func()

    return wrapper
