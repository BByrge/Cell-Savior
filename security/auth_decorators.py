'''
Decorators to be used for authorization. Any route/function decorated requires authentication and a valid JWT.
Decorators: admin_required, user_required (not implemented), representative_required (not implemented).
Exceptions: ExpiredSignatureError, InvalidTokenError.
'''
from functools import wraps
from flask import request
from jwt import ExpiredSignatureError, InvalidTokenError
from os import environ
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

def admin_required(func):
    '''
    Authorization decorator for admin users. Checks for the 'admin' role in the JWT.
    Arguments:
        func: function
    Returns:
        function: wrapper
    '''
    @wraps(func)
    def wrapper(*args, **kwargs):
        headers = request.headers

        # Check for Authorization header
        if "Authorization" not in headers:
            print("Authorization header is missing")
            return {"Error": "Authorization header is missing"}, 401

        token = headers["Authorization"]

        # Remove "Bearer " prefix from token
        token = token.split(" ")[1]
        PUBLIC_KEY = environ.get("PUBLIC_KEY", "")
        
        if not PUBLIC_KEY:
            return {"Error": "Public key not found"}, 500

        try:
            # Decode the JWT
            decoded = jwt.decode(token, PUBLIC_KEY, algorithms=["RS256"])

            # Check if the user has the 'admin' role
            if "roles" not in decoded or "admin" not in decoded["roles"]:
                return {"error": "Forbidden: Admin role required"}, 403

        except ExpiredSignatureError:
            print("Token has expired")
            return {"error": "Token has expired"}, 401
        except InvalidTokenError:
            print("Invalid token")
            return {"error": "Invalid token"}, 401
        return func(*args, **kwargs)

    return wrapper
