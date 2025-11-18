"""Authentication routes."""

from flask import Blueprint, request, jsonify
import traceback
from app.services import auth_service

bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user.

    Request JSON:
        {
            "email": "user@example.com",
            "password": "password123",
            "first_name": "John",
            "last_name": "Doe",
            "role": "user"  // optional, defaults to 'user'
        }

    Returns:
        201: User created successfully
        400: Missing required fields or invalid data
        409: Email already exists
        500: Server error
    """
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['email', 'password', 'first_name', 'last_name']
        missing_fields = [field for field in required_fields if not data.get(field)]

        if missing_fields:
            return jsonify({
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400

        # Create user
        user = auth_service.create_user(
            email=data['email'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            role=data.get('role')  # Optional
        )

        # Generate JWT token
        token = auth_service.generate_jwt_token(user['uid'], user['role'])

        return jsonify({
            'user': user,
            'token': token
        }), 201

    except ValueError as e:
        # Email already exists or invalid role
        return jsonify({'error': str(e)}), 409

    except Exception as e:
        return jsonify({
            'error': str(e),
            'type': type(e).__name__,
            'traceback': traceback.format_exc()
        }), 500


@bp.route('/login', methods=['POST'])
def login():
    """
    Login with email and password.

    Request JSON:
        {
            "email": "user@example.com",
            "password": "password123"
        }

    Returns:
        200: Login successful
        400: Missing required fields
        401: Invalid credentials
        500: Server error
    """
    try:
        data = request.get_json()

        # Validate required fields
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password are required'}), 400

        # Verify credentials
        uid = auth_service.verify_password(data['email'], data['password'])

        # Get user data
        user = auth_service.get_user(uid)

        # Remove password hash from response
        user_safe = user.copy()
        if 'password_hash' in user_safe:
            del user_safe['password_hash']

        # Generate JWT token
        token = auth_service.generate_jwt_token(uid, user['role'])

        return jsonify({
            'user': user_safe,
            'token': token
        }), 200

    except ValueError as e:
        # Invalid credentials
        return jsonify({'error': str(e)}), 401

    except Exception as e:
        return jsonify({
            'error': str(e),
            'type': type(e).__name__,
            'traceback': traceback.format_exc()
        }), 500


@bp.route('/me', methods=['GET'])
def get_current_user():
    """
    Get current user info from JWT token.

    Headers:
        Authorization: Bearer <jwt_token>

    Returns:
        200: User data
        401: Missing or invalid token
        500: Server error
    """
    try:
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid Authorization header'}), 401

        token = auth_header.replace('Bearer ', '')

        # Decode token
        import jwt
        from app.config import Config

        try:
            payload = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401

        # Get user data
        user = auth_service.get_user(payload['uid'])

        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Remove password hash from response
        user_safe = user.copy()
        if 'password_hash' in user_safe:
            del user_safe['password_hash']

        return jsonify({'user': user_safe}), 200

    except Exception as e:
        return jsonify({
            'error': str(e),
            'type': type(e).__name__,
            'traceback': traceback.format_exc()
        }), 500
