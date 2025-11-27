import os
import sys
from dotenv import load_dotenv

# Load .env file immediately when config is imported
load_dotenv()


def get_required_env(var_name):
    """Get required environment variable or fail with clear error."""
    value = os.getenv(var_name)
    if value is None:
        print(f"❌ ERROR: Required environment variable '{var_name}' is not set!", file=sys.stderr)
        print(f"Please set it in your .env file or environment.", file=sys.stderr)
        sys.exit(1)
    return value


class Config:
    """Application configuration from environment variables and constants."""

    # Flask settings - REQUIRED
    FLASK_ENV = get_required_env('FLASK_ENV')
    SECRET_KEY = get_required_env('SECRET_KEY')

    # GCP and Firebase settings - REQUIRED
    GCP_PROJECT_ID = get_required_env('GCP_PROJECT_ID')
    FIREBASE_STORAGE_BUCKET = get_required_env('FIREBASE_STORAGE_BUCKET')

    # Admin secret for admin panel access
    ADMIN_SECRET = get_required_env('ADMIN_SECRET')

    # Firestore Collection Names
    class Collections:
        """Firestore collection name constants"""
        USERS = 'users'
        PARTICIPANTS = 'participants'
        QUESTIONS = 'questions'
        ANSWERS = 'answers'
        SETTINGS = 'settings'

    # User Role Constants
    class UserRoles:
        """User role constants"""
        USER = 'user'
        ADMIN = 'admin'

        @staticmethod
        def is_valid(role):
            """Check if role is valid."""
            return role in [Config.UserRoles.USER, Config.UserRoles.ADMIN]

        @staticmethod
        def all():
            """Get all valid roles."""
            return [Config.UserRoles.USER, Config.UserRoles.ADMIN]

    # Storage Configuration
    GCS_USER_PATH_TEMPLATE = "users/{user_id}/{filename}"
    DOWNLOAD_URL_EXPIRATION_MINUTES = 60

    # Authentication Configuration
    JWT_EXPIRATION_DAYS = 30

    # Query Limits (safety)
    MAX_QUERY_LIMIT = 1000
