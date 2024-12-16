from os import environ

def set_config():
    # Set the app configuration.
    CONFIG = {
        'DEBUG': False,
        'TESTING': False,
        'SECRET_KEY': environ.get('PRIVATE_KEY'),
        'GOOGLE_AUTH_CLIENT_ID': environ.get('GOOGLE_AUTH_CLIENT_ID'),
        'GOOGLE_AUTH_CLIENT_SECRET': environ.get('GOOGLE_AUTH_CLIENT_SECRET'),
        # Note: This needs to match the redirect URI in the Google Cloud Console
        # It can be a list of URIs
        'GOOGLE_AUTH_REDIRECT_URIS': ['http://127.0.0.1:5000/auth/callback'],
        'GOOGLE_AUTH_TOKEN_URI': 'https://oauth2.googleapis.com/token',
        'GOOGLE_AUTH_URI': 'https://accounts.google.com/o/oauth2/auth',
        'GOOGLE_AUTH_SCOPE': 'https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email',
        'JWT_ALGORITHM': 'RS256',
        'PRIVATE_KEY': environ.get('PRIVATE_KEY'),
        'PUBLIC_KEY': environ.get('PUBLIC_KEY'),
    }
    
    return CONFIG