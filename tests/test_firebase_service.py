"""Unit tests for Firebase service."""

import pytest
from unittest.mock import Mock, patch
from app.services import firebase_service


class TestFirebaseService:
    """Test cases for Firebase service."""

    @patch('firebase_admin._apps', {})
    @patch('firebase_admin.initialize_app')
    def test_initialize_firebase(self, mock_init):
        """Test Firebase initialization."""
        firebase_service.initialize_firebase()
        mock_init.assert_called_once()

    @patch('firebase_admin._apps', {'default': Mock()})
    @patch('firebase_admin.initialize_app')
    def test_initialize_firebase_already_initialized(self, mock_init):
        """Test Firebase initialization when already initialized."""
        firebase_service.initialize_firebase()
        mock_init.assert_not_called()

    @patch('app.services.firebase_service.get_firestore_client')
    def test_get_doc_exists(self, mock_get_client):
        """Test getting an existing document."""
        # Setup mocks
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {'id': 'test-id', 'name': 'Test'}

        mock_collection = Mock()
        mock_collection.document.return_value.get.return_value = mock_doc

        mock_db = Mock()
        mock_db.collection.return_value = mock_collection
        mock_get_client.return_value = mock_db

        # Get document
        result = firebase_service.get_doc('users', 'test-id')

        # Assertions
        assert result == {'id': 'test-id', 'name': 'Test'}
        mock_db.collection.assert_called_once_with('users')
        mock_collection.document.assert_called_once_with('test-id')

    @patch('app.services.firebase_service.get_firestore_client')
    def test_get_doc_not_exists(self, mock_get_client):
        """Test getting a non-existent document."""
        # Setup mocks
        mock_doc = Mock()
        mock_doc.exists = False

        mock_collection = Mock()
        mock_collection.document.return_value.get.return_value = mock_doc

        mock_db = Mock()
        mock_db.collection.return_value = mock_collection
        mock_get_client.return_value = mock_db

        # Get document
        result = firebase_service.get_doc('users', 'nonexistent')

        # Assertions
        assert result is None

    @patch('app.services.firebase_service.get_firestore_client')
    def test_create_doc(self, mock_get_client):
        """Test creating a document."""
        # Setup mocks
        mock_doc_ref = Mock()
        mock_doc_ref.id = 'auto-generated-id'

        mock_collection = Mock()
        mock_collection.document.return_value = mock_doc_ref

        mock_db = Mock()
        mock_db.collection.return_value = mock_collection
        mock_get_client.return_value = mock_db

        # Create document
        data = {'name': 'Test', 'email': 'test@example.com'}
        result = firebase_service.create_doc('users', data)

        # Assertions
        assert result['name'] == 'Test'
        assert result['email'] == 'test@example.com'
        assert result['id'] == 'auto-generated-id'
        mock_doc_ref.set.assert_called_once()
