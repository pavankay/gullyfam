"""
Integration tests for Flask GCP Starter.

These tests use REAL GCP services (Firestore, Cloud Storage).
Run these after authenticating with:
  gcloud auth application-default login
  gcloud config set project your-project-id
"""

import pytest
import uuid
from app.services import auth_service, firebase_service
from app.config import Config


@pytest.fixture(scope='session', autouse=True)
def setup_firebase():
    """Initialize Firebase once for all integration tests."""
    firebase_service.initialize_firebase()


@pytest.fixture
def test_user_email():
    """Generate unique test user email."""
    return f"test-{uuid.uuid4()}@example.com"


class TestAuthIntegration:
    """Integration tests for authentication."""

    def test_create_and_get_user(self, test_user_email):
        """Test creating a user in Firestore and retrieving it."""
        # Create user
        user = auth_service.create_user(
            email=test_user_email,
            password='test123',
            first_name='Integration',
            last_name='Test',
            role=Config.UserRoles.USER
        )

        assert user['email'] == test_user_email
        assert user['first_name'] == 'Integration'
        assert 'uid' in user

        # Retrieve user
        retrieved_user = auth_service.get_user(user['uid'])
        assert retrieved_user is not None
        assert retrieved_user['email'] == test_user_email

        # Clean up - delete test user
        auth_service.delete_user(user['uid'])

    def test_verify_password_integration(self, test_user_email):
        """Test password verification with real Firestore."""
        # Create user
        user = auth_service.create_user(
            email=test_user_email,
            password='test123',
            first_name='Integration',
            last_name='Test'
        )

        # Verify correct password
        uid = auth_service.verify_password(test_user_email, 'test123')
        assert uid == user['uid']

        # Verify wrong password raises error
        with pytest.raises(ValueError):
            auth_service.verify_password(test_user_email, 'wrongpassword')

        # Clean up
        auth_service.delete_user(user['uid'])

    def test_jwt_token_flow(self, test_user_email):
        """Test complete JWT token generation and validation."""
        import jwt

        # Create user
        user = auth_service.create_user(
            email=test_user_email,
            password='test123',
            first_name='Integration',
            last_name='Test'
        )

        # Generate token
        token = auth_service.generate_jwt_token(user['uid'], user['role'])
        assert token is not None

        # Decode and verify token
        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
        assert payload['uid'] == user['uid']
        assert payload['role'] == user['role']

        # Clean up
        auth_service.delete_user(user['uid'])
