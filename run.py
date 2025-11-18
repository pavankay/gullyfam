#!/usr/bin/env python3
"""
Flask GCP Starter - Local Development Entry Point

This script runs the Flask development server for local testing.
For production, use gunicorn (automatically configured by Cloud Run buildpacks).
"""

import os
from app import create_app

# Local development port (Cloud Run sets this automatically in production)
LOCAL_PORT = 8000

# Create Flask app
app = create_app()

if __name__ == '__main__':
    # Get required environment variables (no fallbacks!)
    try:
        flask_env = os.environ['FLASK_ENV']
        debug = flask_env == 'development'
    except KeyError as e:
        print(f"\n❌ ERROR: Required environment variable {e} is not set!")
        print("Please ensure your .env file is configured properly.")
        print("Copy .env.example to .env and fill in the values.\n")
        exit(1)

    print(f"\n{'='*50}")
    print(f"🚀 Starting Flask GCP Starter Development Server")
    print(f"{'='*50}")
    print(f"Environment: {flask_env}")
    print(f"Debug Mode: {debug}")
    print(f"Port: {LOCAL_PORT}")
    print(f"URL: http://localhost:{LOCAL_PORT}")
    print(f"{'='*50}\n")

    # Run the development server with threading enabled
    app.run(
        host='0.0.0.0',
        port=LOCAL_PORT,
        debug=debug,
        threaded=True  # Enable threading to handle concurrent requests
    )
