#!/bin/bash
# Gullyfam Game - Clean Players & Answers Only
#
# This script wipes:
# - All participants and their selfies
# - All answers
#
# KEEPS:
# - All questions
# - Question images (in gs://bucket/questions/)
#
# Use this to reset between rounds while keeping your prepared questions.

set -e

# Colors
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${YELLOW}╔════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║   Clean Players & Answers              ║${NC}"
echo -e "${YELLOW}╚════════════════════════════════════════╝${NC}"
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
echo "  - All answers"
echo "  - All scores"
echo ""
echo -e "${BLUE}This will KEEP:${NC}"
echo "  - All questions"
echo "  - Question images"
echo ""
read -p "Are you sure? Type 'yes' to confirm: " confirm

if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

echo ""
echo -e "${GREEN}[1/3] Deleting Firestore: participants...${NC}"
gcloud firestore documents delete \
    --project=$GCP_PROJECT_ID \
    --collection-ids=participants \
    --recursive \
    --quiet 2>/dev/null || echo "  (collection may be empty)"

echo -e "${GREEN}[2/3] Deleting Firestore: answers...${NC}"
gcloud firestore documents delete \
    --project=$GCP_PROJECT_ID \
    --collection-ids=answers \
    --recursive \
    --quiet 2>/dev/null || echo "  (collection may be empty)"

echo -e "${GREEN}[3/3] Deleting participant selfies from Cloud Storage...${NC}"
gsutil -m rm -r "gs://$BUCKET_NAME/participants/**" 2>/dev/null || echo "  (folder may be empty)"

echo ""
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   Players & answers cleared!           ║${NC}"
echo -e "${GREEN}║   Questions preserved.                 ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""
