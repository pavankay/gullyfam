"""
Flask GCP Starter Application

Minimal Flask app factory with GCP integration.
"""

from flask import Flask
from app.config import Config
from app.services import firebase_service


def create_app():
    """
    Flask application factory.

    Initializes:
    - Flask app with configuration
    - Firebase Admin SDK (Firestore)
    - Routes (health check, authentication)
    """
    app = Flask(__name__)
    app.config.from_object(Config)
    app.secret_key = Config.SECRET_KEY

    # Initialize Firebase Admin SDK
    firebase_service.initialize_firebase()

    # Register route blueprints
    from app.routes import health_routes, auth_routes
    app.register_blueprint(health_routes.bp)
    app.register_blueprint(auth_routes.bp)

    return app
