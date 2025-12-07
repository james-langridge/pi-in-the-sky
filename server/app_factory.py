"""Flask application factory with clean dependency injection."""

import logging
import os
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from config import AppConfig
from services import CameraService, StreamingService, ControlManager
from motion_services import MotionDetectionService, NotificationService
from storage import SubscriptionStorage
from audio_services import create_audio_service, AudioStreamingService, AudioDetectionService

logger = logging.getLogger(__name__)


def load_vapid_keys():
    """
    Load VAPID keys from file.
    Returns (vapid_obj, vapid_public_key, vapid_email) tuple.
    """
    vapid_private_key_file = os.environ.get('VAPID_PRIVATE_KEY_FILE', 'vapid_private.pem')
    vapid_email = os.environ.get('VAPID_EMAIL', 'admin@example.com')

    # Use file-based approach only (simpler and cleaner)
    key_file_path = os.path.join(os.path.dirname(__file__), vapid_private_key_file)

    try:
        import base64
        from cryptography.hazmat.primitives import serialization
        from py_vapid import Vapid

        vapid_obj = Vapid.from_file(key_file_path)

        # Get public key in application server format (URL-safe base64)
        # This matches how generate_vapid_keys.py does it
        public_key_obj = vapid_obj.public_key
        public_bytes = public_key_obj.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint
        )
        vapid_public_key = base64.urlsafe_b64encode(public_bytes).decode('utf-8').rstrip('=')

        logger.info(f"Loaded VAPID from file: {key_file_path}")
        return vapid_obj, vapid_public_key, vapid_email
    except FileNotFoundError:
        logger.info(f"VAPID key file not found at {key_file_path} - push notifications disabled")
    except ImportError as e:
        logger.info(f"VAPID dependencies not available: {e} - push notifications disabled")
    except Exception as e:
        logger.error(f"Failed to load VAPID from file {key_file_path}: {e}")

    return None, None, vapid_email


def create_services(config: AppConfig):
    """
    Initialize all application services.
    Returns a dictionary of initialized services.
    """
    # Core services
    camera_service = CameraService()
    streaming_service = StreamingService(camera_service, config.frame_delay)
    control_manager = ControlManager(camera_service)

    # Motion detection
    motion_service = MotionDetectionService()
    subscription_storage = SubscriptionStorage()

    # Push notifications
    vapid_obj, vapid_public_key, vapid_email = load_vapid_keys()
    notification_service = None

    if vapid_obj and vapid_public_key:
        try:
            notification_service = NotificationService(
                subscription_storage,
                vapid_obj,
                vapid_public_key,
                vapid_email
            )
            logger.info("Push notification service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize notification service: {e}")
    else:
        logger.warning("VAPID keys not configured - push notifications disabled")

    # Audio services
    audio_capture_service = create_audio_service(use_mock=False)
    audio_detection_service = AudioDetectionService()
    audio_streaming_service = AudioStreamingService(
        audio_capture_service,
        audio_detection_service,
        notification_service
    )
    
    return {
        'camera_service': camera_service,
        'streaming_service': streaming_service,
        'control_manager': control_manager,
        'motion_service': motion_service,
        'subscription_storage': subscription_storage,
        'notification_service': notification_service,
        'audio_capture_service': audio_capture_service,
        'audio_streaming_service': audio_streaming_service,
        'audio_detection_service': audio_detection_service
    }


def create_app(config: AppConfig) -> Flask:
    """
    Factory function to create Flask app with dependency injection.

    Args:
        config: Application configuration

    Returns:
        Configured Flask application
    """
    app = Flask(__name__)

    # Configure CORS
    CORS(app, resources={r"/*": {"origins": config.cors_origins}})

    # Initialize services
    services = create_services(config)

    # Store services in app config for route access
    app.config['services'] = services
    app.config['app_config'] = config

    # Initialize camera on app startup
    with app.app_context():
        result = services['camera_service'].initialize()
        if result.is_success:
            logger.info("Camera initialized on startup")
        else:
            logger.error(f"Failed to initialize camera: {result.error}")

    @app.teardown_appcontext
    def cleanup_camera(error=None):
        """Clean up camera resources on shutdown."""
        if error:
            logger.error(f"App teardown due to error: {error}")

    # Register blueprints
    from routes.camera import camera_bp
    from routes.motion import motion_bp
    from routes.push import push_bp
    from routes.static import static_bp
    from routes.photos import photos_bp
    from routes.system import system_bp
    from routes.audio import audio_bp
    from routes.logs import logs_bp

    app.register_blueprint(camera_bp)
    app.register_blueprint(motion_bp)
    app.register_blueprint(push_bp)
    app.register_blueprint(static_bp)
    app.register_blueprint(photos_bp)
    app.register_blueprint(system_bp)
    app.register_blueprint(audio_bp)
    app.register_blueprint(logs_bp)

    @app.after_request
    def add_smart_caching(response):
        """Professional caching with ETags - no manual versioning needed!"""

        # Service worker must never be cached
        if request.path == '/service-worker.js':
            response.headers['Cache-Control'] = 'no-cache, must-revalidate, max-age=0'
            return response

        # HTML files - no cache
        if response.content_type and 'text/html' in response.content_type:
            response.headers['Cache-Control'] = 'no-cache, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            return response

        # API and streams - no cache
        if '/api/' in request.path or '/video_feed' in request.path:
            response.headers['Cache-Control'] = 'no-store'
            return response

        # Static files - use ETags for automatic cache invalidation
        if any(ext in request.path for ext in ['.js', '.css', '.png', '.jpg', '.svg']):
            # Generate ETag from file content
            response.make_conditional(request)
            # must-revalidate forces check with server when max-age expires
            response.headers['Cache-Control'] = 'public, max-age=300, must-revalidate'
            return response

        return response

    # Simple version endpoint
    @app.route('/api/app-info')
    def app_info():
        """Return app version and update info."""
        import subprocess
        from datetime import datetime

        try:
            # Get git commit if available
            git_hash = subprocess.check_output(
                ['git', 'rev-parse', '--short', 'HEAD'],
                stderr=subprocess.DEVNULL
            ).decode('utf-8').strip()
        except:
            git_hash = 'unknown'

        # Get last modified time of key files
        key_files = ['server.py', 'app.js', 'index.html']
        last_modified = 0
        for filename in key_files:
            for root, dirs, files in os.walk('.'):
                if filename in files:
                    filepath = os.path.join(root, filename)
                    mtime = os.path.getmtime(filepath)
                    last_modified = max(last_modified, mtime)

        return jsonify({
            'version': git_hash,
            'last_modified': datetime.fromtimestamp(last_modified).isoformat(),
            'timestamp': datetime.now().isoformat()
        })

    return app
