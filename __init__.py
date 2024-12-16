from flask import Flask
from config import set_config
from dotenv import load_dotenv

def create_app():
    app = Flask(__name__)
    load_dotenv()
    CONFIG = set_config()
    # Set the app configuration.
    for key in CONFIG:
        app.config[key] = CONFIG[key]

    return app