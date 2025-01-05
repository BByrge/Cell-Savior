'''
This file contains utility functions that are used by the main application or are one time use functions.
Functions: generate_state, create_user, generate_custom_jwt, generate_key_pair, get_expiration, verify_JWT, get_date_time.
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
    try:
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
    except:
        return 0


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
    try:
        if expiration:
            return datetime.datetime.now(datetime.timezone.utc) <= expiration
        return datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)
    except:
        return 0


def verify_JWT(token):
    '''
    Verify the JWT token.
    '''
    PUBLIC_KEY = app.config['PUBLIC_KEY']
    try:
        decoded = jwt.decode(token, PUBLIC_KEY, algorithms=["RS256"])
        return 1
    # If we want more specific error messages, we can catch the exceptions separately (expired, invalid). If needed add here.
    except:
        return 0
    

def get_date_time(date_time=None):
    '''
    Get the current date and time in UTC if no argument is passed.
    If an argument is passed, return the amount of time that has passed since the argument.
    '''
    try:
        if not date_time:
            return datetime.datetime.now(datetime.timezone.utc)
        return datetime.datetime.now(datetime.timezone.utc) - date_time
    except:
        return 0



# The following functions are one time use functions for development purposes only.
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


def convert_to_int_db():
    '''
    This function is a one time use function for use during development for bugs that cause data to be stored as strings.
    Check that all values in data, talk, text, and hotspot coloumns are integers in plans.
    This checks the entire plans table.
    '''
    query = client.query(kind='plans')
    results = list(query.fetch())
    for plan in results:
        for field in ['data', 'talk', 'text', 'hotspot']:
            if not isinstance(plan[field], int):
                plan[field] = int(plan[field])
        client.put(plan)
    return "All values converted to integers."
