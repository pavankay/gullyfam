"""
Auth Service

Handles user authentication and user management.
Uses bcrypt for password hashing and JWT for API tokens.
"""

import bcrypt
import jwt
import uuid
from datetime import datetime, timedelta, timezone
from app.services.firebase_service import get_firestore_client, get_doc, query_one, update_doc, delete_doc
from app.config import Config


def create_user(email, password, first_name, last_name, role=None):
    """
    Create new user with bcrypt password hashing.

    Args:
        email: User email (must be unique)
        password: Plain text password (will be hashed with bcrypt)
        first_name: User's first name
        last_name: User's last name
        role: User role (default: 'user')

    Returns:
        dict: Created user {uid, email, first_name, last_name, role, ...}

    Raises:
        ValueError: If email already exists
        Exception: If Firestore operation fails
    """
    db = get_firestore_client()

    # Default role
    if role is None:
        role = Config.UserRoles.USER

    # Validate role
    if not Config.UserRoles.is_valid(role):
        raise ValueError(f'Invalid role: {role}')

    # Check if email already exists
    existing_user = get_user_by_email(email)
    if existing_user:
        raise ValueError(f'Email already exists: {email}')

    # Generate unique UID
    uid = str(uuid.uuid4())

    # Hash password with bcrypt
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Create user document in Firestore
    user_data = {
        'uid': uid,
        'email': email,
        'password_hash': password_hash,
        'first_name': first_name,
        'last_name': last_name,
        'role': role,
        'created_at': datetime.now(timezone.utc),
        'updated_at': datetime.now(timezone.utc)
    }
    db.collection(Config.Collections.USERS).document(uid).set(user_data)

    # Return user data (without password_hash)
    user_data_safe = user_data.copy()
    del user_data_safe['password_hash']
    return user_data_safe


def verify_password(email, password):
    """
    Verify user credentials using bcrypt.

    Args:
        email: User email
        password: Plain text password

    Returns:
        str: User UID if credentials are valid

    Raises:
        ValueError: If credentials are invalid
    """
    user = get_user_by_email(email)

    if not user:
        raise ValueError('Invalid email or password')

    # Verify password with bcrypt
    password_hash = user.get('password_hash', '').encode('utf-8')
    password_bytes = password.encode('utf-8')

    if not bcrypt.checkpw(password_bytes, password_hash):
        raise ValueError('Invalid email or password')

    return user['uid']


def generate_jwt_token(uid, role):
    """
    Generate JWT token for API authentication.

    Token contains:
    - uid: User ID
    - role: User role
    - exp: Expiration time (30 days from now)

    Args:
        uid: User ID
        role: User role

    Returns:
        str: JWT token signed with SECRET_KEY
    """
    payload = {
        'uid': uid,
        'role': role,
        'exp': datetime.now(timezone.utc) + timedelta(days=Config.JWT_EXPIRATION_DAYS)
    }

    token = jwt.encode(payload, Config.SECRET_KEY, algorithm='HS256')
    return token


def get_user(uid):
    """
    Get user metadata by UID.

    Args:
        uid: User UID

    Returns:
        dict: User metadata from Firestore or None if not found
    """
    return get_doc(Config.Collections.USERS, uid)


def get_user_by_email(email):
    """
    Get user metadata by email.

    Args:
        email: User email

    Returns:
        dict: User metadata from Firestore or None if not found
    """
    return query_one(Config.Collections.USERS, filters=[('email', '==', email)])


def update_password(uid, new_password):
    """
    Update user password with bcrypt hashing.

    Args:
        uid: User UID
        new_password: New plain text password (will be hashed with bcrypt)

    Raises:
        ValueError: If user not found
    """
    # Check if user exists
    user = get_user(uid)
    if not user:
        raise ValueError(f'User not found: {uid}')

    # Hash new password with bcrypt
    password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Update password and timestamp in Firestore
    update_doc(Config.Collections.USERS, uid, {
        'password_hash': password_hash,
        'updated_at': datetime.now(timezone.utc)
    })


def delete_user(uid):
    """
    Delete user from Firestore.

    Args:
        uid: User UID

    Raises:
        ValueError: If user not found
    """
    # Check if user exists
    user = get_user(uid)
    if not user:
        raise ValueError(f'User not found: {uid}')

    # Delete from Firestore
    delete_doc(Config.Collections.USERS, uid)
