import random, string, jwt
from google.cloud import datastore
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError


client = datastore.Client()


def generate_state():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=16))

def create_user(id_info):
    new_user = datastore.Entity(client.key('users'))
    required_fields = ["sub", "email", "name"]
    for field in required_fields:
        if field not in id_info:
            return 0
    new_user.update({
        "sub": id_info["sub"],
        "email": id_info["email"],
        "name": id_info["name"],
        "roles": ["user"]
    })
    client.put(new_user)
    return new_user

def verify_jwt(token):
    SECRET_KEY = "your-secret-key"
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return decoded  # Token is valid
    except ExpiredSignatureError:
        return {"error": "Token has expired"}
    except InvalidTokenError:
        return {"error": "Invalid token"}
    
