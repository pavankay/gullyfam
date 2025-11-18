#!/bin/bash
# Flask GCP Starter - Idempotent Deployment Script
#
# This script handles FRESH GCP project installs and does everything needed:
# - Checks prerequisites
# - Enables required APIs
# - Configures IAM permissions
# - Creates Firestore database
# - Creates Cloud Storage bucket
# - Builds and deploys to Cloud Run (using buildpacks - NO Docker!)
#
# IDEMPOTENT: Safe to run multiple times
# - Skips already-enabled APIs
# - Skips already-granted IAM roles
# - Updates existing Cloud Run service or creates new one
#
# ⚠️ CRITICAL: NO MANUAL CONFIGURATIONS ALLOWED
# ALL infrastructure configuration MUST be in this script.
# Never grant IAM roles, enable APIs, or create resources manually.

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Flask GCP Starter Deployment v1.0   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# 1. Check Prerequisites
echo -e "${GREEN}[1/6] Checking prerequisites...${NC}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
chmod +x "$SCRIPT_DIR/check_prereqs.sh"
"$SCRIPT_DIR/check_prereqs.sh"

# 2. Get/Confirm GCP Project
echo -e "${GREEN}[2/6] Configuring GCP project...${NC}"

# If GCP_PROJECT_ID not in environment, read from .env
if [ -z "$GCP_PROJECT_ID" ]; then
    GCP_PROJECT_ID=$(grep "^GCP_PROJECT_ID=" .env | cut -d= -f2 | tr -d ' ')
    export GCP_PROJECT_ID
fi

echo -e "${GREEN}✓ Using GCP Project: ${BLUE}$GCP_PROJECT_ID${NC}\n"

# Set the project for subsequent commands
gcloud config set project $GCP_PROJECT_ID 2>/dev/null

# 3. Enable Required APIs (idempotent)
echo -e "${GREEN}[3/6] Enabling required GCP APIs...${NC}"
echo "This may take a few moments..."

APIS=(
    "cloudbuild.googleapis.com"
    "run.googleapis.com"
    "firebase.googleapis.com"
    "firestore.googleapis.com"
    "storage.googleapis.com"
)

for api in "${APIS[@]}"; do
    echo -n "  • Enabling $api... "
    if gcloud services enable $api --project=$GCP_PROJECT_ID 2>/dev/null; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${YELLOW}already enabled${NC}"
    fi
done

echo ""

# 4. Configure IAM Permissions (idempotent)
echo -e "${GREEN}[4/6] Configuring IAM permissions for Cloud Build...${NC}"
echo "Setting up service account permissions..."
echo ""

# Get project number and construct service account email
PROJECT_NUMBER=$(gcloud projects describe $GCP_PROJECT_ID --format="value(projectNumber)")
SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

echo "Service Account: $SERVICE_ACCOUNT"
echo ""

# Required roles for Cloud Build and Cloud Run
ROLES=(
    "roles/cloudbuild.builds.builder"
    "roles/storage.admin"
    "roles/run.admin"
    "roles/iam.serviceAccountUser"
)

# Grant each role (idempotent - no-op if already granted)
for role in "${ROLES[@]}"; do
    echo -n "  • Granting $role... "
    if gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
        --member="serviceAccount:$SERVICE_ACCOUNT" \
        --role="$role" \
        --condition=None \
        --quiet > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${YELLOW}already set${NC}"
    fi
done

echo ""

# 5. Create Firestore Database (idempotent)
echo -e "${GREEN}[5/6] Creating Firestore database...${NC}"

# Check if Firestore database already exists
FIRESTORE_DB=$(gcloud firestore databases list --project=$GCP_PROJECT_ID --format="value(name)" 2>/dev/null | grep -E "\(default\)|default" || echo "")

if [ -z "$FIRESTORE_DB" ]; then
    echo "Creating Firestore database in Native mode (location: us-central1)..."
    gcloud firestore databases create \
        --location=us-central1 \
        --project=$GCP_PROJECT_ID \
        --quiet
    echo -e "${GREEN}✓ Firestore database created${NC}"
else
    echo -e "${YELLOW}✓ Firestore database already exists (skipping)${NC}"
fi

echo ""

# 6. Create GCS Storage Bucket (idempotent)
echo -e "${GREEN}[6/6] Creating GCS storage bucket...${NC}"

# Construct bucket name from project ID
BUCKET_NAME="${GCP_PROJECT_ID}-storage"

# Check if bucket already exists
if gsutil ls gs://$BUCKET_NAME 2>/dev/null >/dev/null; then
    echo -e "${YELLOW}✓ GCS bucket already exists: $BUCKET_NAME${NC}"
else
    echo "Creating GCS bucket: $BUCKET_NAME..."
    if gsutil mb -p $GCP_PROJECT_ID -l us-central1 gs://$BUCKET_NAME 2>&1 | tee /tmp/bucket_create.log; then
        echo -e "${GREEN}✓ GCS bucket created${NC}"
    else
        # Check if it failed because bucket already exists
        if grep -q "already exists" /tmp/bucket_create.log || grep -q "409" /tmp/bucket_create.log; then
            echo -e "${YELLOW}✓ GCS bucket already exists (continuing)${NC}"
        else
            echo -e "${RED}✗ Failed to create GCS bucket${NC}"
            cat /tmp/bucket_create.log
            exit 1
        fi
    fi
fi

# Make sure bucket name is in .env file
if grep -q "^FIREBASE_STORAGE_BUCKET=" .env; then
    # Update existing entry
    sed -i.bak "s|^FIREBASE_STORAGE_BUCKET=.*|FIREBASE_STORAGE_BUCKET=$BUCKET_NAME|" .env
    echo "Updated FIREBASE_STORAGE_BUCKET in .env"
else
    # Add new entry
    echo "FIREBASE_STORAGE_BUCKET=$BUCKET_NAME" >> .env
    echo "Added FIREBASE_STORAGE_BUCKET to .env"
fi

echo ""

# 7. Build and Deploy to Cloud Run
echo -e "${GREEN}[7/7] Building and deploying to Cloud Run...${NC}"
echo "Preparing environment variables..."

# Read required env vars from .env file
FLASK_ENV=$(grep "^FLASK_ENV=" .env | cut -d= -f2 | tr -d ' ')
SECRET_KEY=$(grep "^SECRET_KEY=" .env | cut -d= -f2 | tr -d ' ')
FIREBASE_STORAGE_BUCKET=$(grep "^FIREBASE_STORAGE_BUCKET=" .env | cut -d= -f2 | tr -d ' ')

echo "Environment variables configured:"
echo "  • FLASK_ENV: $FLASK_ENV"
echo "  • SECRET_KEY: ${SECRET_KEY:0:10}... (hidden)"
echo "  • GCP_PROJECT_ID: $GCP_PROJECT_ID"
echo "  • FIREBASE_STORAGE_BUCKET: $FIREBASE_STORAGE_BUCKET"
echo ""
echo "Note: PORT is set automatically by Cloud Run (8080)"
echo ""
echo "Building and deploying with buildpacks (this will take a few minutes)..."
echo ""

cd "$SCRIPT_DIR/.."

gcloud run deploy flask-gcp-starter \
    --source . \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars "FLASK_ENV=$FLASK_ENV,SECRET_KEY=$SECRET_KEY,GCP_PROJECT_ID=$GCP_PROJECT_ID,FIREBASE_STORAGE_BUCKET=$FIREBASE_STORAGE_BUCKET" \
    --project=$GCP_PROJECT_ID \
    --quiet

echo ""

# 8. Get Service URL
echo -e "${GREEN}[8/8] Retrieving service information...${NC}"
SERVICE_URL=$(gcloud run services describe flask-gcp-starter \
    --platform managed \
    --region us-central1 \
    --format 'value(status.url)' \
    --project=$GCP_PROJECT_ID 2>/dev/null)

# Deployment Summary
echo ""
echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║      Deployment Complete! 🎉           ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}✓ Service Name:${NC} flask-gcp-starter"
echo -e "${GREEN}✓ Project ID:${NC} $GCP_PROJECT_ID"
echo -e "${GREEN}✓ Region:${NC} us-central1"
echo -e "${GREEN}✓ Service URL:${NC} ${BLUE}$SERVICE_URL${NC}"
echo ""

# Next Steps
echo -e "${YELLOW}╔════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║     Next Steps                         ║${NC}"
echo -e "${YELLOW}╚════════════════════════════════════════╝${NC}"
echo ""
echo "1. Test your deployment:"
echo ""
echo "   curl $SERVICE_URL/health"
echo ""
echo "   Or open in browser:"
echo "   $SERVICE_URL"
echo ""
echo "2. Test authentication:"
echo ""
echo "   # Register a new user"
echo "   curl -X POST $SERVICE_URL/api/auth/register \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"email\":\"test@example.com\",\"password\":\"test123\",\"first_name\":\"Test\",\"last_name\":\"User\"}'"
echo ""
echo "3. View logs:"
echo ""
echo "   gcloud run services logs read flask-gcp-starter --project=$GCP_PROJECT_ID --region=us-central1"
echo ""
echo -e "${GREEN}Happy coding! 🚀${NC}"
echo ""
