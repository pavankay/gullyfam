"""
Firebase Service

Minimal Firebase initialization and Firestore client access.
Provides thin helper functions for consistent Firestore operations.
All business logic should be in domain-specific services (auth, etc.).
"""

import firebase_admin
from firebase_admin import firestore
from google.cloud.firestore_v1.base_query import FieldFilter


def initialize_firebase():
    """
    Initialize Firebase Admin SDK with Application Default Credentials (ADC).

    ADC automatically uses:
    - Local development: gcloud auth application-default login credentials
    - Cloud Run: Service's attached service account

    Project selection is controlled by gcloud config:
    - Production: gcloud config set project your-project-id
    """
    if firebase_admin._apps:
        # Already initialized
        return

    # Always use Application Default Credentials
    firebase_admin.initialize_app()


def get_firestore_client():
    """
    Get Firestore database client.

    Returns:
        firestore.Client: Firestore client instance
    """
    return firestore.client()


# ============================================================================
# Thin Firestore Helper Functions
# ============================================================================


def get_doc(collection_name, doc_id):
    """
    Get document by ID.

    Args:
        collection_name: Firestore collection name
        doc_id: Document ID

    Returns:
        dict: Document data or None if not found
    """
    db = get_firestore_client()
    doc = db.collection(collection_name).document(doc_id).get()
    return doc.to_dict() if doc.exists else None


def create_doc(collection_name, data, id_field='id'):
    """
    Create document with auto-generated ID.

    Args:
        collection_name: Firestore collection name
        data: Document data dict (ID will be added)
        id_field: Field name for the auto-generated ID (default: 'id')

    Returns:
        dict: Document data with ID field added
    """
    db = get_firestore_client()
    doc_ref = db.collection(collection_name).document()
    data_with_id = {**data, id_field: doc_ref.id}
    doc_ref.set(data_with_id)
    return data_with_id


def update_doc(collection_name, doc_id, updates):
    """
    Update document fields.

    Args:
        collection_name: Firestore collection name
        doc_id: Document ID
        updates: Dict of fields to update

    Raises:
        google.cloud.exceptions.NotFound: If document doesn't exist
    """
    db = get_firestore_client()
    db.collection(collection_name).document(doc_id).update(updates)


def delete_doc(collection_name, doc_id):
    """
    Delete document by ID.

    Args:
        collection_name: Firestore collection name
        doc_id: Document ID
    """
    db = get_firestore_client()
    db.collection(collection_name).document(doc_id).delete()


def query_docs(collection_name, filters=None, limit=None, order_by=None):
    """
    Query collection with filters.

    Args:
        collection_name: Firestore collection name
        filters: List of (field, operator, value) tuples
                 Example: [('status', '==', 'active'), ('year', '>', 2020)]
        limit: Max results (int)
        order_by: Tuple of (field, direction)
                  Example: ('created_at', 'DESCENDING')

    Returns:
        list: List of document dicts
    """
    db = get_firestore_client()
    query = db.collection(collection_name)

    if filters:
        for field, op, value in filters:
            query = query.where(filter=FieldFilter(field, op, value))

    if order_by:
        query = query.order_by(order_by[0], direction=order_by[1])

    if limit:
        query = query.limit(limit)

    return [doc.to_dict() for doc in query.stream()]


def query_one(collection_name, filters):
    """
    Query for a single document matching filters.

    Args:
        collection_name: Firestore collection name
        filters: List of (field, operator, value) tuples

    Returns:
        dict: First matching document or None if not found
    """
    results = query_docs(collection_name, filters=filters, limit=1)
    return results[0] if results else None
