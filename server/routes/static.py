"""Static file serving routes."""

import os
import logging
from flask import Blueprint, send_from_directory

logger = logging.getLogger(__name__)

static_bp = Blueprint('static', __name__)


@static_bp.route('/')
def index():
    """Serve the UI HTML file."""
    # First check if we have a built dist directory
    dist_path = os.path.join(os.path.dirname(__file__), '..', '..', 'dist', 'index.html')
    ui_path = os.path.join(os.path.dirname(__file__), '..', '..', 'ui', 'index.html')
    
    # Prefer built version if it exists
    html_path = dist_path if os.path.exists(dist_path) else ui_path
    
    try:
        with open(html_path, 'r') as f:
            content = f.read()
            # Replace the BASE_URL with the actual server URL
            # This makes the UI work regardless of how it's accessed
            content = content.replace(
                "const BASE_URL = window.location.hostname === 'localhost' \n            ? 'http://localhost:8080'\n            : `http://${window.location.hostname}:8080`;",
                "const BASE_URL = window.location.origin;"
            )
            return content
    except FileNotFoundError:
        return "UI file not found. Please ensure ui/index.html or dist/index.html exists.", 404
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
    # Check dist directory first for built assets
    dist_assets = os.path.join(os.path.dirname(__file__), '..', '..', 'dist', 'assets')
    ui_js = os.path.join(os.path.dirname(__file__), '..', '..', 'ui', 'js')
    
    # For built assets, they'll be in dist/assets with hashed names
    if os.path.exists(dist_assets):
        for file in os.listdir(dist_assets):
            if file.endswith('.js'):
                return send_from_directory(dist_assets, file, mimetype='application/javascript')
    
    # Fall back to source files for development
    return send_from_directory(ui_js, filename, mimetype='application/javascript')


@static_bp.route('/css/<path:filename>')
def serve_css(filename):
    """Serve CSS files."""
    return send_from_directory(
        os.path.join(os.path.dirname(__file__), '..', '..', 'ui'),
        filename,
        mimetype='text/css'
    )


@static_bp.route('/assets/<path:filename>')
def serve_assets(filename):
    """Serve Vite built assets."""
    assets_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'dist', 'assets')
    if os.path.exists(assets_dir):
        return send_from_directory(assets_dir, filename)
    return "Asset not found", 404


@static_bp.route('/<path:filename>')
def serve_ui_files(filename):
    """Serve UI files from dist/ or ui/ directory."""
    if filename.endswith(('.css', '.js')):
        mimetype = 'text/css' if filename.endswith('.css') else 'application/javascript'
        
        # Check dist directory first
        dist_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'dist')
        ui_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'ui')
        
        if os.path.exists(os.path.join(dist_dir, filename)):
            return send_from_directory(dist_dir, filename, mimetype=mimetype)
        else:
            return send_from_directory(ui_dir, filename, mimetype=mimetype)