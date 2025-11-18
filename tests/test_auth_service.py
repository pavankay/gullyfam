"""Unit tests for auth service."""

import pytest
from unittest.mock import Mock, patch
from app.services import auth_service
from app.config import Config


class TestAuthService:
    """Test cases for authentication service."""

    @patch('app.services.auth_service.get_firestore_client')
    @patch('app.services.auth_service.get_user_by_email')
    def test_create_user_success(self, mock_get_by_email, mock_firestore):
        """Test successful user creation."""
        # Setup mocks
        mock_get_by_email.return_value = None  # Email doesn't exist
        mock_db = Mock()
        mock_firestore.return_value = mock_db

        # Create user
        user = auth_service.create_user(
            email='test@example.com',
            password='password123',
            first_name='Test',
            last_name='User'
        )

        # Assertions
        assert user['email'] == 'test@example.com'
        assert user['first_name'] == 'Test'
        assert user['last_name'] == 'User'
        assert user['role'] == Config.UserRoles.USER
        assert 'uid' in user
        assert 'password_hash' not in user  # Should be removed from response
        mock_db.collection.assert_called_once_with(Config.Collections.USERS)

    @patch('app.services.auth_service.get_user_by_email')
    def test_create_user_duplicate_email(self, mock_get_by_email):
        """Test creating user with existing email raises error."""
        # Setup mock - email already exists
        mock_get_by_email.return_value = {'email': 'test@example.com', 'uid': '123'}

        # Attempt to create user
        with pytest.raises(ValueError, match='Email already exists'):
            auth_service.create_user(
                email='test@example.com',
                password='password123',
                first_name='Test',
                last_name='User'
            )

    @patch('app.services.auth_service.get_user_by_email')
    def test_verify_password_success(self, mock_get_by_email):
        """Test successful password verification."""
        import bcrypt

        # Create a test password hash
        password = 'password123'
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Setup mock
        mock_get_by_email.return_value = {
            'uid': 'test-uid',
            'email': 'test@example.com',
            'password_hash': password_hash
        }

        # Verify password
        uid = auth_service.verify_password('test@example.com', password)

        assert uid == 'test-uid'

    @patch('app.services.auth_service.get_user_by_email')
    def test_verify_password_wrong_password(self, mock_get_by_email):
        """Test password verification with wrong password."""
        import bcrypt

        # Create a test password hash
        password_hash = bcrypt.hashpw('password123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Setup mock
        mock_get_by_email.return_value = {
            'uid': 'test-uid',
            'email': 'test@example.com',
            'password_hash': password_hash
        }

        # Attempt to verify with wrong password
        with pytest.raises(ValueError, match='Invalid email or password'):
            auth_service.verify_password('test@example.com', 'wrongpassword')

    def test_generate_jwt_token(self):
        """Test JWT token generation."""
        import jwt

        # Generate token
        token = auth_service.generate_jwt_token('test-uid', Config.UserRoles.USER)

        # Decode and verify
        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
        assert payload['uid'] == 'test-uid'
        assert payload['role'] == Config.UserRoles.USER
        assert 'exp' in payload
