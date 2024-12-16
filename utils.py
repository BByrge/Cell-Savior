import random, string, jwt
from os import environ
from functools import wraps
from flask import request

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

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


def generate_key_pair():
    '''
    Generate an RSA key pair and save it to disk.
    These keys should be added as environment variables.
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
