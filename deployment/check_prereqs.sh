#!/bin/bash
# Flask GCP Starter - Prerequisites Check Script

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "Checking prerequisites for deployment..."
echo ""

# Check for gcloud CLI
echo -n "Checking for gcloud CLI... "
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ NOT FOUND${NC}"
    echo ""
    echo "══════════════════════════════════════════════════════════"
    echo "ERROR: gcloud CLI not installed"
    echo "══════════════════════════════════════════════════════════"
    echo ""
    echo "Install gcloud CLI:"
    echo ""
    echo "macOS (Homebrew):"
    echo "    brew install google-cloud-sdk"
    echo ""
    echo "Other platforms:"
    echo "    https://cloud.google.com/sdk/docs/install"
    echo ""
    echo "After installation, restart your terminal."
    echo ""
    exit 1
else
    GCLOUD_VERSION=$(gcloud version --format="value(core)" 2>/dev/null | head -n 1)
    echo -e "${GREEN}✓ Found (version: $GCLOUD_VERSION)${NC}"
fi

# Check gcloud authentication
echo -n "Checking gcloud authentication... "
ACTIVE_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null)
if [ -z "$ACTIVE_ACCOUNT" ]; then
    echo -e "${RED}❌ NOT AUTHENTICATED${NC}"
    echo ""
    echo "══════════════════════════════════════════════════════════"
    echo "ERROR: Not authenticated with gcloud"
    echo "══════════════════════════════════════════════════════════"
    echo ""
    echo "Run this command to authenticate:"
    echo ""
    echo "    gcloud auth login"
    echo ""
    echo "This will open your browser to sign in."
    echo ""
    exit 1
else
    echo -e "${GREEN}✓ Authenticated as: $ACTIVE_ACCOUNT${NC}"
fi

# Check for current gcloud project
echo -n "Checking gcloud project configuration... "
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null)
if [ -z "$CURRENT_PROJECT" ] || [ "$CURRENT_PROJECT" = "(unset)" ]; then
    echo -e "${RED}❌ No project configured${NC}"
    echo ""
    echo "══════════════════════════════════════════════════════════"
    echo "ERROR: No gcloud project configured"
    echo "══════════════════════════════════════════════════════════"
    echo ""
    echo "Set your GCP project with this command:"
    echo ""
    echo "    gcloud config set project YOUR_PROJECT_ID"
    echo ""
    echo "To see available projects:"
    echo ""
    echo "    gcloud projects list"
    echo ""
    exit 1
else
    echo -e "${GREEN}✓ Current project: $CURRENT_PROJECT${NC}"
fi

# Check that .env project matches gcloud project
echo -n "Checking .env and gcloud project match... "

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ .env file not found${NC}"
    echo ""
    echo "══════════════════════════════════════════════════════════"
    echo "ERROR: .env file not found"
    echo "══════════════════════════════════════════════════════════"
    echo ""
    echo "Create .env file by copying the example:"
    echo ""
    echo "    cp .env.example .env"
    echo ""
    echo "Then edit .env and set your configuration values."
    echo ""
    exit 1
fi

# Read GCP_PROJECT_ID from .env
ENV_PROJECT=$(grep "^GCP_PROJECT_ID=" .env | cut -d= -f2 | tr -d ' ')
if [ -z "$ENV_PROJECT" ]; then
    echo -e "${RED}❌ GCP_PROJECT_ID not set in .env${NC}"
    echo ""
    echo "══════════════════════════════════════════════════════════"
    echo "ERROR: GCP_PROJECT_ID missing in .env"
    echo "══════════════════════════════════════════════════════════"
    echo ""
    echo "Edit .env and add this line:"
    echo ""
    echo "    GCP_PROJECT_ID=your-project-id"
    echo ""
    exit 1
fi

# Compare with gcloud active project
if [ "$ENV_PROJECT" != "$CURRENT_PROJECT" ]; then
    echo -e "${RED}❌ PROJECT MISMATCH!${NC}"
    echo ""
    echo -e "${RED}╔════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║  DANGER: .env and gcloud projects don't match!    ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "  .env file specifies:     ${YELLOW}$ENV_PROJECT${NC}"
    echo "  gcloud is configured for: ${YELLOW}$CURRENT_PROJECT${NC}"
    echo ""
    echo "This could cause you to accidentally deploy to the wrong project."
    echo ""
    echo -e "${YELLOW}To fix, choose ONE:${NC}"
    echo ""
    echo "══════════════════════════════════════════════════════════"
    echo "OPTION 1: Update gcloud to match .env"
    echo "══════════════════════════════════════════════════════════"
    echo ""
    echo "Run this command:"
    echo ""
    echo "    gcloud config set project $ENV_PROJECT"
    echo ""
    echo "══════════════════════════════════════════════════════════"
    echo "OPTION 2: Update .env to match gcloud"
    echo "══════════════════════════════════════════════════════════"
    echo ""
    echo "Edit .env and change this line:"
    echo ""
    echo "    GCP_PROJECT_ID=$CURRENT_PROJECT"
    echo ""
    echo "══════════════════════════════════════════════════════════"
    echo ""
    exit 1
else
    echo -e "${GREEN}✓ Projects match: $ENV_PROJECT${NC}"
fi

echo ""
echo -e "${GREEN}✅ All prerequisites met!${NC}"
echo ""
