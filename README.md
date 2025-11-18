# Flask GCP Starter

A production-ready Flask starter template with Google Cloud Platform integration, following proven patterns and best practices.

## Features

- **Flask App Factory** - Clean application structure with blueprints
- **GCP Integration** - Firestore (database), Cloud Storage (files), Cloud Run (hosting)
- **Authentication** - bcrypt password hashing + JWT tokens
- **Idempotent Deployment** - Zero manual configuration, fully automated deployment
- **Testing** - Unit tests with mocks + integration tests with real GCP
- **Buildpacks Deployment** - No Docker needed, automatic Python detection
- **Security First** - No default values, fail-fast configuration, proper error handling

## Tech Stack

- **Backend:** Python 3.11+ with Flask 3.0
- **Database:** Google Cloud Firestore (NoSQL)
- **Storage:** Google Cloud Storage
- **Hosting:** Google Cloud Run (serverless containers)
- **Auth:** bcrypt + JWT
- **Testing:** pytest
- **Deployment:** Google Cloud buildpacks (no Docker!)

## Project Structure

```
flask-gcp-starter/
├── run.py                          # Local dev entry point
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variables template
├── app/
│   ├── __init__.py                 # Flask app factory
│   ├── config.py                   # Configuration with strict validation
│   ├── services/                   # Business logic layer
│   │   ├── firebase_service.py     # Firestore client & helpers
│   │   ├── storage_service.py      # Cloud Storage operations
│   │   └── auth_service.py         # Authentication & user management
│   └── routes/                     # API endpoints (thin controllers)
│       ├── health_routes.py        # Health check
│       └── auth_routes.py          # Login, register, get user
├── tests/                          # Unit tests (with mocks)
│   ├── test_auth_service.py
│   └── test_firebase_service.py
├── tests_integration/              # Integration tests (real GCP)
│   └── test_integration.py
└── deployment/                     # Deployment automation
    ├── check_prereqs.sh            # Prerequisites checker
    └── deploy_all.sh               # Idempotent full deployment

```

## Quick Start

### 1. Prerequisites

- **Python 3.11+** - [Download](https://www.python.org/downloads/)
- **Google Cloud CLI** - [Install](https://cloud.google.com/sdk/docs/install)
- **GCP Project** - [Create one](https://console.cloud.google.com/projectcreate)

### 2. Clone & Setup

```bash
# Clone or copy this starter template
git clone <your-repo-url> my-project
cd my-project

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
```

### 3. Configure Environment

Edit `.env` with your values:

```bash
# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-secret-key-change-in-production

# GCP Configuration
GCP_PROJECT_ID=your-gcp-project-id
FIREBASE_STORAGE_BUCKET=your-gcp-project-id-storage
```

### 4. Authenticate with GCP

```bash
# Login to Google Cloud
gcloud auth login

# Set your project
gcloud config set project your-gcp-project-id

# Authenticate for local development
gcloud auth application-default login
```

### 5. Deploy to GCP

```bash
# Run the idempotent deployment script
./deployment/deploy_all.sh
```

This script will:
- ✅ Check prerequisites
- ✅ Enable required GCP APIs
- ✅ Configure IAM permissions
- ✅ Create Firestore database
- ✅ Create Cloud Storage bucket
- ✅ Build and deploy to Cloud Run

**Total deployment time:** ~3-5 minutes

### 6. Test Your Deployment

```bash
# Get your service URL from deployment output, then:
SERVICE_URL="https://flask-gcp-starter-xxx.run.app"

# Health check
curl $SERVICE_URL/health

# Register a user
curl -X POST $SERVICE_URL/api/auth/register \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "test@example.com",
    "password": "test123",
    "first_name": "Test",
    "last_name": "User"
  }'

# Login
curl -X POST $SERVICE_URL/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "test@example.com",
    "password": "test123"
  }'

# Get current user (use token from login response)
curl $SERVICE_URL/api/auth/me \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN'
```

## Local Development

### Running Locally

```bash
# Activate virtual environment
source .venv/bin/activate

# Run development server
python3 run.py
```

The app will be available at `http://localhost:8000`

**Local development uses real GCP services** (Firestore, Cloud Storage) via Application Default Credentials.

### Running Tests

```bash
# Run unit tests (with mocks)
pytest tests/

# Run integration tests (with real GCP)
pytest tests_integration/

# Run all tests
pytest

# Run with coverage
pytest --cov=app
```

## API Endpoints

### Health Check

```
GET /
GET /health
```

Response:
```json
{
  "status": "healthy",
  "service": "flask-gcp-starter",
  "environment": "development",
  "project_id": "your-project-id"
}
```

### Authentication

#### Register

```
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123",
  "first_name": "John",
  "last_name": "Doe",
  "role": "user"  // optional, defaults to 'user'
}
```

#### Login

```
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

Returns:
```json
{
  "user": {
    "uid": "...",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "user"
  },
  "token": "eyJ..."
}
```

#### Get Current User

```
GET /api/auth/me
Authorization: Bearer <jwt_token>
```

## Architecture Decisions

### Why No Docker?

We use **Google Cloud buildpacks** instead of Docker:
- ✅ Simpler - no Dockerfile to maintain
- ✅ Automatic Python detection
- ✅ Automatic dependency installation
- ✅ Automatic gunicorn configuration
- ✅ One less thing to manage

Deployment command:
```bash
gcloud run deploy --source .
```

That's it! Buildpacks handle the rest.

### Why Application Default Credentials?

We use **ADC** (gcloud auth application-default login) instead of service account keys:
- ✅ More secure - no key files to manage
- ✅ Works locally and in production
- ✅ Automatic in Cloud Run
- ✅ Easy to switch between projects

### Why Idempotent Deployment Scripts?

All infrastructure is code:
- ✅ Zero manual GCP Console steps
- ✅ Reproducible deployments
- ✅ Safe to run multiple times
- ✅ Version controlled
- ✅ Easy to understand and modify

### Why No Hidden Defaults?

Configuration must be explicit:
- ✅ App crashes immediately if env vars missing
- ✅ No insecure defaults
- ✅ No surprises in production
- ✅ Clear error messages

## Configuration

All configuration lives in `app/config.py` and `.env`.

### Required Environment Variables

```bash
FLASK_ENV           # development or production
SECRET_KEY          # Flask secret key (change in production!)
GCP_PROJECT_ID      # Your GCP project ID
FIREBASE_STORAGE_BUCKET  # GCS bucket name (auto-created by deploy script)
```

### Adding New Configuration

**1. Environment-specific values** (secrets, project IDs):
- Add to `.env` file
- Add to `.env.example` with placeholder
- Add to `config.py` with `get_required_env()`

**2. Application constants** (roles, limits, collection names):
- Add to `Config` class in `config.py`

**See Claude.md for complete configuration rules.**

## Testing Strategy

### Unit Tests (`tests/`)

- Mock external dependencies (Firestore, GCS)
- Fast execution
- Test business logic in isolation
- Run before every commit

```bash
pytest tests/
```

### Integration Tests (`tests_integration/`)

- Use **real GCP services**
- Verify end-to-end functionality
- Clean up test data after each test
- Run before deployment

```bash
pytest tests_integration/
```

## Deployment

### Initial Deployment

```bash
./deployment/deploy_all.sh
```

### Redeployment (after code changes)

```bash
./deployment/deploy_all.sh
```

Same script - it's idempotent!

### View Logs

```bash
gcloud run services logs read flask-gcp-starter \
  --project=your-project-id \
  --region=us-central1
```

### Update Environment Variables

Edit `.env`, then redeploy:

```bash
./deployment/deploy_all.sh
```

## Extending the Starter

### Adding a New Service

1. Create `app/services/my_service.py`
2. Implement business logic functions
3. Add unit tests in `tests/test_my_service.py`
4. Import and use in routes

### Adding a New Route

1. Create `app/routes/my_routes.py`
2. Create blueprint and add routes
3. Register blueprint in `app/__init__.py`
4. Keep routes thin - delegate to services

### Adding New Firestore Collections

1. Add collection name to `Config.Collections` in `config.py`
2. Use `firebase_service` helpers (get_doc, create_doc, etc.)
3. Add business logic in a new service

## Core Principles

1. **Simplicity** - Clean, readable code over clever code
2. **No Hidden Defaults** - All env vars required, no fallbacks
3. **Let It Crash** - Fast failure for easy debugging
4. **Services First** - Business logic in services, not routes
5. **Idempotent Scripts** - All infrastructure as code
6. **Test Coverage** - Unit tests + integration tests

**Read `Claude.md` for complete development guidelines.**

## Common Issues

### "Required environment variable not set"

- Copy `.env.example` to `.env`
- Fill in all required values
- Restart the app

### "gcloud: command not found"

- Install Google Cloud CLI
- Restart your terminal

### "Not authenticated with gcloud"

```bash
gcloud auth login
gcloud auth application-default login
```

### ".env and gcloud projects don't match"

```bash
# Option 1: Update gcloud to match .env
gcloud config set project your-project-id

# Option 2: Update .env to match gcloud
# Edit .env file manually
```

### "Failed to create GCS bucket"

- Bucket names must be globally unique
- Try a different name in `.env`

## Cost Estimate

**GCP Free Tier** (as of 2024):
- **Cloud Run:** 2 million requests/month free
- **Firestore:** 1GB storage, 50K reads, 20K writes/day free
- **Cloud Storage:** 5GB storage, 5K class A ops, 50K class B ops/month free

**Expected costs for small apps:**
- **Development:** $0 (stays within free tier)
- **Low traffic production:** $0-5/month
- **Medium traffic:** $10-50/month

## Security Best Practices

- ✅ Never commit `.env` to git
- ✅ Rotate `SECRET_KEY` in production
- ✅ Use strong passwords for users
- ✅ Validate all user inputs
- ✅ Use HTTPS (automatic with Cloud Run)
- ✅ Follow principle of least privilege for IAM

## License

This starter template is provided as-is. Use it freely for your projects.

## Contributing

This is a starter template. Fork it and make it your own!

## Support

- **GCP Documentation:** https://cloud.google.com/docs
- **Flask Documentation:** https://flask.palletsprojects.com/
- **Issues:** See Claude.md for development guidelines

---

**Built with ❤️ using best practices from production Flask applications.**
