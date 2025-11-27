"""Health check routes."""

from flask import Blueprint, jsonify
from app.config import Config

bp = Blueprint('health', __name__)


@bp.route('/health')
def health_check():
    """
    Health check endpoint.

    Returns:
        JSON response with status and configuration info
    """
    return jsonify({
        'status': 'healthy',
        'service': 'flask-gcp-starter',
        'environment': Config.FLASK_ENV,
        'project_id': Config.GCP_PROJECT_ID
    })
