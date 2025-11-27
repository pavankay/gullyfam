#!/bin/bash
# Gullyfam Game - Clean ALL Data
#
# This script COMPLETELY wipes:
# - All Firestore collections (participants, questions, answers)
# - All Cloud Storage files (selfies, question images)
#
# Use this for a full reset before the party starts.

set -e

# Colors
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${RED}╔════════════════════════════════════════╗${NC}"
echo -e "${RED}║   DANGER: Full Database Wipe           ║${NC}"
echo -e "${RED}╚════════════════════════════════════════╝${NC}"
echo ""

# Get project from .env or environment
if [ -z "$GCP_PROJECT_ID" ]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    GCP_PROJECT_ID=$(grep "^GCP_PROJECT_ID=" "$SCRIPT_DIR/../.env" | cut -d= -f2 | tr -d ' ')
fi

BUCKET_NAME="${GCP_PROJECT_ID}-storage"

echo "Project: $GCP_PROJECT_ID"
echo "Bucket: $BUCKET_NAME"
echo ""
echo -e "${YELLOW}This will DELETE:${NC}"
echo "  - All participants (and their selfies)"
echo "  - All questions (and their images)"
echo "  - All answers"
echo ""
read -p "Are you sure? Type 'yes' to confirm: " confirm

if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

echo ""
echo -e "${GREEN}[1/4] Deleting Firestore: participants...${NC}"
gcloud firestore documents delete \
    --project=$GCP_PROJECT_ID \
    --collection-ids=participants \
    --recursive \
    --quiet 2>/dev/null || echo "  (collection may be empty)"

echo -e "${GREEN}[2/4] Deleting Firestore: questions...${NC}"
gcloud firestore documents delete \
    --project=$GCP_PROJECT_ID \
    --collection-ids=questions \
    --recursive \
    --quiet 2>/dev/null || echo "  (collection may be empty)"

echo -e "${GREEN}[3/4] Deleting Firestore: answers...${NC}"
gcloud firestore documents delete \
    --project=$GCP_PROJECT_ID \
    --collection-ids=answers \
    --recursive \
    --quiet 2>/dev/null || echo "  (collection may be empty)"

echo -e "${GREEN}[4/4] Deleting all files from Cloud Storage...${NC}"
gsutil -m rm -r "gs://$BUCKET_NAME/**" 2>/dev/null || echo "  (bucket may be empty)"

echo ""
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   All data wiped successfully!         ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""
