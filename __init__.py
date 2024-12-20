'''
This file is used to create the Flask app instance. The app configuration is set in this file.
'''
from flask import Flask
from flask_cors import CORS
from config import set_config
from dotenv import load_dotenv

def create_app():
    '''
    Create the Flask app instance. Load the configuration from the config.py file.
    '''
    load_dotenv(override=True)
    app = Flask(__name__)
    # Enable CORS. This can be disabled in production if everything is on the same domain.
    CORS(app)
    CONFIG = set_config()
    # Set the app configuration.
    for key in CONFIG:
        app.config[key] = CONFIG[key]
    return app