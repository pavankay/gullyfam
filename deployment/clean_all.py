#!/usr/bin/env python3
"""
Gullyfam Game - Clean ALL Data

Fast deletion using Python SDKs. No gsutil, no gcloud CLI.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.cloud import storage
from app.services.firebase_service import initialize_firebase, get_firestore_client
from app.config import Config

COLLECTIONS = [
    Config.Collections.PARTICIPANTS,
    Config.Collections.QUESTIONS,
    Config.Collections.ANSWERS,
    Config.Collections.SETTINGS,
]


def delete_collection(collection_name):
    """Delete all documents in a collection."""
    db = get_firestore_client()
    docs = db.collection(collection_name).stream()

    count = 0
    for doc in docs:
        doc.reference.delete()
        count += 1

    return count


def delete_all_storage_files():
    """Delete all files from Cloud Storage bucket."""
    client = storage.Client(project=Config.GCP_PROJECT_ID)
    bucket = client.bucket(Config.FIREBASE_STORAGE_BUCKET)

    count = 0
    for blob in bucket.list_blobs():
        blob.delete()
        count += 1

    return count


def main():
    print("\n🗑️  Gullyfam - Clean All Data\n")

    # Confirmation
    confirm = input("Delete ALL game data? Type 'yes' to confirm: ")
    if confirm != 'yes':
        print("Aborted.")
        return

    print()
    initialize_firebase()

    # Delete Firestore collections
    total_docs = 0
    for collection in COLLECTIONS:
        count = delete_collection(collection)
        total_docs += count
        print(f"  ✓ {collection}: {count} docs deleted")

    # Delete storage files
    print()
    file_count = delete_all_storage_files()
    print(f"  ✓ Storage: {file_count} files deleted")

    print(f"\n✅ Done! {total_docs} documents, {file_count} files deleted.\n")


if __name__ == '__main__':
    main()
