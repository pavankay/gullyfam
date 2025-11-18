# Claude Code Project Rules for Flask GCP Starter

## Tech Stack

- **Backend:** Python Flask (vanilla - no complex extensions)
- **GCP:** Cloud Run, Firestore, Cloud Storage
- **Authentication:** bcrypt + JWT
- **Testing:** pytest (simple, no .ini, no params, no marks)
- **Deployment:** Buildpacks (NO Docker!)

---

## ⚠️ CORE RULES - MUST FOLLOW

### 1. Simplicity

**Keep it simple and typical**
- Follow intuitive patterns
- Don't overcomplicate
- Clean, readable code over clever code
- No over-engineering

### 2. No Hidden Defaults

**NEVER EVER HAVE ANY FALLBACKS FOR ANY .env VARIABLES**

- Use `.env` for environment parameters
- If required env var missing → raise error, NO fallback values
- For non-env config → constants at top of file

**❌ BAD:**
```python
DB = os.getenv('DB_NAME', 'default')
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
```

**✅ GOOD:**
```python
DB = os.getenv('DB_NAME')
if not DB:
    raise ValueError("DB_NAME required")

# Or use direct access with try/except
SECRET_KEY = os.environ['SECRET_KEY']  # Raises KeyError if missing
```

**Why?**
- Prevents running with insecure defaults
- Forces explicit configuration
- Catches configuration errors early
- Avoids accidental production issues

**Important: config.py should be self-sufficient**
```python
# config.py - loads its own .env file
from dotenv import load_dotenv
load_dotenv()  # Load at module level immediately

# Now read env vars
DB = os.getenv('DB_NAME')
if not DB:
    raise ValueError("DB_NAME required")
```

### 3. Configuration Placement Rule

**Where should configuration values live?**

**1. One module cares → Top of that file**

If only one module uses a constant, define it at the top of that file.

**2. More than one module cares (but not .env candidate) → config.py**

If multiple modules need the same constant, and it's not an environment variable, put it in config.py.

**3. True .env candidate → .env file**

If it's a secret, environment-specific, or deployment variable, it belongs in .env.

Examples:
- Secrets: `SECRET_KEY`, API keys, credentials
- Environment-specific: `GCP_PROJECT_ID`, `FIREBASE_STORAGE_BUCKET`
- Deployment settings: `FLASK_ENV`

### 4. Exception Handling - The Simple Approach

**PHILOSOPHY: Let it crash. We're in rapid iteration mode.**

**Core Principles:**
1. **Never swallow exceptions** - Let them bubble up
2. **Only catch to add value** - Add context, then re-raise with `from e`
3. **Preserve stack traces** - Always use `from e` when re-raising
4. **No dev/prod complexity** - Keep it simple
5. **Flash messages are for success/warnings** - NOT for exception handling

**Exception Handling by Layer:**

#### Services & Business Logic: Let It Bubble

Services should let exceptions bubble up naturally. Only catch if you can add meaningful context.

```python
def process_data(user_id):
    """Process data - let errors bubble naturally."""
    if not user_id:
        raise ValueError("User ID required")

    data = firestore_db.get(user_id)  # Let Firestore errors bubble
    return data
```

#### API Routes: Try/Catch with Full Details

API routes should catch all exceptions and return full error details in JSON format.

```python
@bp.route('/api/data', methods=['POST'])
def process_data():
    try:
        result = service.process(request.json)
        return jsonify(result), 200
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'type': type(e).__name__,
            'traceback': traceback.format_exc()
        }), 500
```

---

## Code Structure

### Routes (Thin)
- Routes should be thin controllers
- Delegate to services
- Handle request/response only
- No business logic in routes

```python
# ✅ GOOD
@bp.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    result = upload_service.process_upload(file, current_user.id)
    return jsonify(result)
```

### Services (Business Logic)
- Clean, cohesive, independently testable
- All business logic in services, not routes
- Services should be pure functions when possible
- Easy to unit test without Flask context

```python
# services/upload_service.py
def process_upload(file, user_id):
    validate_file(file)
    file_path = save_to_storage(file, user_id)
    create_metadata(file_path, user_id)
    return {'success': True, 'path': file_path}
```

### Project Organization

```
flask-gcp-starter/
├── run.py                      # Local dev entry point
├── app/
│   ├── __init__.py             # Flask app factory
│   ├── config.py               # Configuration
│   ├── routes/                 # Thin route handlers
│   │   ├── health_routes.py
│   │   └── auth_routes.py
│   └── services/               # Business logic
│       ├── firebase_service.py
│       ├── storage_service.py
│       └── auth_service.py
├── tests/                      # Unit tests
├── tests_integration/          # Integration tests with real GCP
├── deployment/                 # Deployment scripts
│   ├── check_prereqs.sh
│   └── deploy_all.sh
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## Testing

### Principles
- Write unit/integration tests when meaningful
- Don't overcomplicate testing
- `pytest` command runs all tests - no .ini, no params, no marks
- Test services independently
- Mock external dependencies for unit tests
- Use real GCP services for integration tests

### Examples

```python
# tests/test_services.py
def test_create_user():
    with pytest.raises(ValueError):
        auth_service.create_user(email='', password='test')

# tests_integration/test_integration.py
def test_create_user_integration():
    user = auth_service.create_user(
        email='test@example.com',
        password='test123',
        first_name='Test',
        last_name='User'
    )
    assert user['email'] == 'test@example.com'
    # Clean up
    auth_service.delete_user(user['uid'])
```

---

## Deployment Scripts

### ⚠️ CRITICAL RULE: NO MANUAL CONFIGURATIONS

**ALL infrastructure configuration MUST be in idempotent deployment scripts.**

**Why this matters:**
- Manual configurations create configuration drift
- Manual steps get forgotten during redeployments
- Manual changes are lost when IAM policies change
- Manual setup is not reproducible

**Examples of what MUST be in scripts:**
- ✅ API enablement (cloudbuild, run, firestore, storage, etc.)
- ✅ IAM role bindings for service accounts
- ✅ Firestore database creation
- ✅ GCS bucket creation
- ✅ Environment variables in Cloud Run

**NEVER do these manually:**
- ❌ Enabling APIs in GCP Console
- ❌ Granting IAM roles via Console
- ❌ Creating resources via Console
- ❌ "Just this one time" fixes

**If you need to do something manually:**
1. Stop
2. Add it to the deployment script FIRST
3. Then run the script
4. Commit the script change

### ALL SCRIPTS MUST BE IDEMPOTENT

**Requirements for ALL scripts:**
1. Clearly documented with header comments
2. Meaningful terminal output at each step
3. Dev-friendly: show errors with info, don't hide
4. Check prerequisites (auth, project, tools)
5. Automate everything possible
6. NO manual steps (see rule above)

---

## Deployment to Cloud Run

### Using Buildpacks (NO Docker!)

We use Google Cloud buildpacks instead of Docker for simpler deployment:

```bash
gcloud run deploy flask-gcp-starter \
    --source . \
    --platform managed \
    --region us-central1 \
    --set-env-vars "FLASK_ENV=$FLASK_ENV,SECRET_KEY=$SECRET_KEY,..."
```

**Benefits:**
- No Dockerfile to maintain
- Automatic Python detection
- Automatic dependency installation from requirements.txt
- Automatic gunicorn configuration
- Less complexity, same result

**For production server:**
- Buildpacks automatically use gunicorn
- Gunicorn is in requirements.txt
- Cloud Run sets PORT environment variable automatically
- No manual configuration needed

---

## Important Reminders

### When Making Changes

1. **Modifying deployment flow** → update deployment scripts
2. **Adding env vars** → update `.env.example` immediately
3. **Adding routes** → create corresponding service
4. **Adding business logic** → put in service, not route
5. **Keep it simple, typical, testable**

### Development Workflow

1. All environment variables must be documented in `.env.example`
2. Never commit `.env` to git
3. Application must fail immediately if required env vars are missing
4. Tests should mock environment variables explicitly
5. Run tests before committing: `pytest`
6. Deployment scripts must remain idempotent

---

## Security

- No secrets in code
- All sensitive config via environment variables
- Fail fast on missing configuration
- Use Firebase Admin SDK with Application Default Credentials
- Validate all user inputs
- Sanitize file uploads

---

## Code Style

- Follow PEP 8 for Python
- Use meaningful variable names
- Add docstrings to functions
- Keep functions focused and small
- Prefer explicit over implicit
- Comments explain "why", not "what"

---

**Remember: Simplicity, clarity, and reliability over cleverness.**
