"""Cloud Storage service for file operations."""

import uuid
import os
from datetime import timedelta
from google.cloud import storage
from google.oauth2 import service_account
from app.config import Config


# Module-level storage client (lazy initialization)
_storage_client = None


def get_storage_client():
    """Get or initialize Cloud Storage client with service account if available."""
    global _storage_client
    if _storage_client is None:
        # Try to use service account credentials if available (needed for signed URLs)
        credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if credentials_path and os.path.exists(credentials_path):
            credentials = service_account.Credentials.from_service_account_file(credentials_path)
            _storage_client = storage.Client(project=Config.GCP_PROJECT_ID, credentials=credentials)
        else:
            # Fall back to default credentials (ADC) - used for Cloud Run
            _storage_client = storage.Client(project=Config.GCP_PROJECT_ID)
    return _storage_client


def upload_file(user_id, file_obj, filename):
    """
    Upload file to GCS.

    Args:
        user_id: User ID for path
        file_obj: File object from request.files
        filename: Original filename

    Returns:
        tuple: (gcs_path, file_size, content_type)

    Raises:
        RuntimeError: If upload fails
    """
    try:
        client = get_storage_client()
        bucket = client.bucket(Config.FIREBASE_STORAGE_BUCKET)

        # Generate unique filename with original extension
        file_ext = ''
        if '.' in filename:
            file_ext = filename[filename.rindex('.'):]

        unique_filename = f"{uuid.uuid4()}{file_ext}"
        gcs_path = Config.GCS_USER_PATH_TEMPLATE.format(user_id=user_id, filename=unique_filename)

        # Create blob and upload
        blob = bucket.blob(gcs_path)

        # Get file info
        file_obj.seek(0, 2)  # Seek to end
        file_size = file_obj.tell()
        file_obj.seek(0)  # Reset to beginning

        # Upload with content type
        content_type = file_obj.content_type or 'application/octet-stream'
        blob.upload_from_file(file_obj, content_type=content_type)

        return gcs_path, file_size, content_type

    except Exception as e:
        raise RuntimeError(f"Failed to upload file to GCS: {str(e)}") from e


def get_download_url(gcs_path, expiration_minutes=None):
    """
    Generate signed URL for file download.

    Args:
        gcs_path: Full GCS path (e.g., users/user123/file.pdf)
        expiration_minutes: URL validity duration

    Returns:
        str: Signed URL, or None if signing not available (e.g., in dev with ADC)

    Raises:
        RuntimeError: If URL generation fails for reasons other than missing private key
    """
    try:
        if expiration_minutes is None:
            expiration_minutes = Config.DOWNLOAD_URL_EXPIRATION_MINUTES

        client = get_storage_client()
        bucket = client.bucket(Config.FIREBASE_STORAGE_BUCKET)
        blob = bucket.blob(gcs_path)

        # Generate signed URL
        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=expiration_minutes),
            method="GET"
        )

        return url

    except AttributeError as e:
        # Development environment using ADC doesn't have private key
        # This is expected - signed URLs require service account with private key
        if "private key" in str(e).lower():
            return None
        raise RuntimeError(f"Failed to generate download URL: {str(e)}") from e

    except Exception as e:
        raise RuntimeError(f"Failed to generate download URL: {str(e)}") from e


def delete_file(gcs_path):
    """
    Delete file from GCS.

    Args:
        gcs_path: Full GCS path

    Returns:
        bool: True if deleted successfully

    Raises:
        RuntimeError: If deletion fails
    """
    try:
        client = get_storage_client()
        bucket = client.bucket(Config.FIREBASE_STORAGE_BUCKET)
        blob = bucket.blob(gcs_path)

        # Delete only if exists
        if blob.exists():
            blob.delete()
            return True
        return False

    except Exception as e:
        raise RuntimeError(f"Failed to delete file from GCS: {str(e)}") from e


def file_exists(gcs_path):
    """
    Check if file exists in GCS.

    Args:
        gcs_path: Full GCS path

    Returns:
        bool: True if file exists

    Raises:
        RuntimeError: If unable to check file existence
    """
    try:
        client = get_storage_client()
        bucket = client.bucket(Config.FIREBASE_STORAGE_BUCKET)
        blob = bucket.blob(gcs_path)
        return blob.exists()
    except Exception as e:
        raise RuntimeError(f"Failed to check file existence for {gcs_path}: {str(e)}") from e
