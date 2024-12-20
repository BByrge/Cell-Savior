'''
This file contains utility functions that are used by the main application or are one time use functions.
Functions: generate_state, create_user, generate_custom_jwt, generate_key_pair
Exceptions: All functions return 0 if error occurs.
'''
import random, string, jwt, datetime
from flask import current_app as app

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from google.cloud import datastore

client = datastore.Client()


def generate_state():
    '''
    Generate a random state string for OAuth2.0 authorization.
    '''
    return ''.join(random.choices(string.ascii_letters + string.digits, k=16))


def create_user(id_info):
    '''
    Create a new user in the database. The user is assigned the role 'user' by default.
    Arguments:
        id_info: dict
    Returns:
        datastore.Entity: user entity
        0 if error occurs
    '''
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


def generate_custom_jwt(id_info):
    '''
    Generate a custom JWT token for the user.
    '''
    SECRET_KEY = app.config['SECRET_KEY']

    # Check if user exists in database
    query = client.query(kind='users')
    query.add_filter(filter=datastore.query.PropertyFilter('sub', '=', id_info["sub"]))
    results = list(query.fetch())

    if not results:
        # Create user with role user
        user = create_user(id_info)
        if user == 0:
            return 0
        # Role is set to user by default. Changing this requires manual admin action.
        roles = ["user"]
    elif len(results) > 1:
        return 0
    elif 'roles' not in results[0]:
        roles = ["user"]
    else:
        roles = results[0]['roles']

    # Refresh token will be added later
    payload = {
        "sub": id_info["sub"],
        "email": id_info["email"],
        "name": id_info["name"],
        "roles": roles,
        "iat": datetime.datetime.now(datetime.timezone.utc),
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="RS256")


def get_expiration(expiration=None):
    '''
    Get the expiration time for state if no argument is passed.
    Check if the state has expired if an argument is passed.
    '''
    # The datetime module supports comparison operators for non-naive datetime objects.
    if expiration:
        return datetime.datetime.now(datetime.timezone.utc) <= expiration
    return datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)


def generate_key_pair():
    '''
    Generate an RSA key pair and save it to disk. This function should never be used in the code.
    This function is only used to generate a new key pair for the application.
    These keys should be added as environment variables and never hardcoded or committed to source control.
    Returns:
        str: message
    '''
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    public_key = private_key.public_key()

    with open("private_key.pem", "wb") as private_file:
        private_file.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()  # No password
            )
        )

    # Extract and save the public key
    public_key = private_key.public_key()
    with open("public_key.pem", "wb") as public_file:
        public_file.write(
            public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
        )

    return "Key pair generated and saved to disk."
