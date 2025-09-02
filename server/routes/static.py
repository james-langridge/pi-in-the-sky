"""Static file serving routes for React PWA frontend."""

import os
import logging
from flask import Blueprint, send_from_directory, send_file

logger = logging.getLogger(__name__)

static_bp = Blueprint('static', __name__)


def get_ui_path():
    """Get the path to the UI directory."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    ui_dist = os.path.join(base_dir, 'ui', 'dist')
    
    if os.path.exists(os.path.join(ui_dist, 'index.html')):
        logger.info(f"Serving React frontend from {ui_dist}")
        return ui_dist
    else:
        logger.warning(f"UI build not found at {ui_dist}. Run 'npm run build' in ui/ directory.")
        return None


@static_bp.route('/')
def index():
    """Serve the UI HTML file."""
    ui_dir = get_ui_path()
    
    if not ui_dir:
        return """
        <h1>Frontend not built</h1>
        <p>Please build the React frontend:</p>
        <pre>
        cd ui
        npm install
        npm run build
        </pre>
        """, 503
    
    return send_file(os.path.join(ui_dir, 'index.html'))


@static_bp.route('/assets/<path:filename>')
def serve_assets(filename):
    """Serve built assets (JS, CSS, etc)."""
    ui_dir = get_ui_path()
    
    if not ui_dir:
        return "Frontend not built", 503
    
    assets_dir = os.path.join(ui_dir, 'assets')
    
    if os.path.exists(os.path.join(assets_dir, filename)):
        return send_from_directory(assets_dir, filename)
    
    return "Asset not found", 404


@static_bp.route('/manifest.json')
def manifest():
    """Serve the PWA manifest file."""
    ui_dir = get_ui_path()
    
    if ui_dir:
        manifest_path = os.path.join(ui_dir, 'manifest.json')
        if os.path.exists(manifest_path):
            return send_file(manifest_path, mimetype='application/manifest+json')
    
    # Return a basic manifest if build doesn't exist
    return {
        "name": "Pi Camera Stream",
        "short_name": "PiCam",
        "display": "standalone",
        "theme_color": "#1f2937",
        "background_color": "#111827",
        "start_url": "/"
    }, 200, {'Content-Type': 'application/manifest+json'}


@static_bp.route('/service-worker.js')
@static_bp.route('/sw.js')
def service_worker():
    """Serve the service worker file."""
    ui_dir = get_ui_path()
    
    if ui_dir:
        # Vite PWA plugin generates sw.js
        sw_path = os.path.join(ui_dir, 'sw.js')
        if os.path.exists(sw_path):
            return send_file(sw_path, mimetype='application/javascript')
        
        # Fallback to service-worker.js
        sw_path = os.path.join(ui_dir, 'service-worker.js')
        if os.path.exists(sw_path):
            return send_file(sw_path, mimetype='application/javascript')
    
    # Return minimal service worker if build doesn't exist
    return """
    self.addEventListener('install', e => e.waitUntil(self.skipWaiting()));
    self.addEventListener('activate', e => e.waitUntil(clients.claim()));
    """, 200, {'Content-Type': 'application/javascript'}


@static_bp.route('/<path:filename>')
def serve_static_files(filename):
    """Catch-all for other static files."""
    # Security check - prevent directory traversal
    if '..' in filename or filename.startswith('/'):
        return "Invalid file path", 400
    
    ui_dir = get_ui_path()
    
    if not ui_dir:
        return "Frontend not built", 503
    
    file_path = os.path.join(ui_dir, filename)
    
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return send_file(file_path)
    
    # For client-side routing, return index.html for non-asset routes
    if not filename.startswith(('assets/', 'api/', 'video_feed')):
        return send_file(os.path.join(ui_dir, 'index.html'))
    
    return "File not found", 404