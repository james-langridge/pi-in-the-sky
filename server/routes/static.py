"""Static file serving routes."""

import os
import logging
from flask import Blueprint, send_from_directory

logger = logging.getLogger(__name__)

static_bp = Blueprint('static', __name__)


@static_bp.route('/')
def index():
    """Serve the UI HTML file."""
    ui_path = os.path.join(os.path.dirname(__file__), '..', '..', 'ui', 'index.html')
    try:
        with open(ui_path, 'r') as f:
            content = f.read()
            # Replace the BASE_URL with the actual server URL
            # This makes the UI work regardless of how it's accessed
            content = content.replace(
                "const BASE_URL = window.location.hostname === 'localhost' \n            ? 'http://localhost:8080'\n            : `http://${window.location.hostname}:8080`;",
                "const BASE_URL = window.location.origin;"
            )
            return content
    except FileNotFoundError:
        return "UI file not found. Please ensure ui/index.html exists.", 404
    except Exception as e:
        logger.error(f"Error serving UI: {e}")
        return f"Error loading UI: {str(e)}", 500


@static_bp.route('/manifest.json')
def manifest():
    """Serve the PWA manifest file."""
    return send_from_directory(
        os.path.join(os.path.dirname(__file__), '..', 'ui'),
        'manifest.json',
        mimetype='application/manifest+json'
    )


@static_bp.route('/service-worker.js')
def service_worker():
    """Serve the service worker file."""
    return send_from_directory(
        os.path.join(os.path.dirname(__file__), '..', 'ui'),
        'service-worker.js',
        mimetype='application/javascript'
    )


@static_bp.route('/js/<path:filename>')
def serve_js(filename):
    """Serve JavaScript files."""
    return send_from_directory(
        os.path.join(os.path.dirname(__file__), '..', '..', 'ui', 'js'),
        filename,
        mimetype='application/javascript'
    )


@static_bp.route('/css/<path:filename>')
def serve_css(filename):
    """Serve CSS files."""
    return send_from_directory(
        os.path.join(os.path.dirname(__file__), '..', '..', 'ui'),
        filename,
        mimetype='text/css'
    )


@static_bp.route('/<path:filename>')
def serve_ui_files(filename):
    """Serve UI files directly from ui/ directory."""
    if filename.endswith(('.css', '.js')):
        mimetype = 'text/css' if filename.endswith('.css') else 'application/javascript'
        return send_from_directory(
            os.path.join(os.path.dirname(__file__), '..', '..', 'ui'),
            filename,
            mimetype=mimetype
        )