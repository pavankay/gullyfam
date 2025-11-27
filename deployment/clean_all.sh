#!/bin/bash
# Gullyfam Game - Clean ALL Data
#
# Wipes all Firestore collections and Cloud Storage files.
# Uses Python SDK - no gsutil/gcloud CLI needed.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"
python deployment/clean_all.py
