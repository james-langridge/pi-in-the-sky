"""Flask application factory with clean dependency injection."""

import logging
import os
from flask import Flask
from flask_cors import CORS
from config import AppConfig
from services import CameraService, StreamingService, ControlManager
from motion_services import MotionDetectionService, NotificationService
from storage import SubscriptionStorage

logger = logging.getLogger(__name__)


def load_vapid_keys():
    """
    Load VAPID keys from file or environment.
    Returns (vapid_obj, vapid_public_key, vapid_email) tuple.
    """
    vapid_private_key_file = os.environ.get('VAPID_PRIVATE_KEY_FILE', '')
    vapid_private_key = os.environ.get('VAPID_PRIVATE_KEY', '')
    vapid_public_key = os.environ.get('VAPID_PUBLIC_KEY', '')
    vapid_email = os.environ.get('VAPID_EMAIL', 'admin@example.com')
    
    vapid_obj = None
    
    # Try file-based approach first (recommended)
    if vapid_private_key_file:
        key_file_path = os.path.join(os.path.dirname(__file__), vapid_private_key_file)
        try:
            from py_vapid import Vapid
            vapid_obj = Vapid.from_file(key_file_path)
            logger.info(f"Loaded VAPID from file: {key_file_path}")
            return vapid_obj, vapid_public_key, vapid_email
        except Exception as e:
            logger.error(f"Failed to load VAPID from file {key_file_path}: {e}")
    
    # Fall back to environment variable (legacy support)
    if vapid_private_key and not vapid_obj:
        vapid_private_key = vapid_private_key.strip('"').strip("'")
        if '\\\\n' in vapid_private_key:
            vapid_private_key = vapid_private_key.replace('\\\\n', '\n')
        elif '\\n' in vapid_private_key:
            vapid_private_key = vapid_private_key.replace('\\n', '\n')
        
        try:
            from py_vapid import Vapid
            vapid_obj = Vapid.from_string(vapid_private_key)
            logger.info("Loaded VAPID from environment variable")
            return vapid_obj, vapid_public_key, vapid_email
        except Exception as e:
            logger.error(f"Failed to create VAPID from environment variable: {e}")
    
    if not vapid_obj:
        logger.warning("VAPID keys not configured - push notifications disabled")
    
    return vapid_obj, vapid_public_key, vapid_email


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
    
    return {
        'camera_service': camera_service,
        'streaming_service': streaming_service,
        'control_manager': control_manager,
        'motion_service': motion_service,
        'subscription_storage': subscription_storage,
        'notification_service': notification_service
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
        try:
            services['camera_service'].initialize()
            logger.info("Camera initialized on startup")
        except Exception as e:
            logger.error(f"Failed to initialize camera: {e}")
    
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
    
    app.register_blueprint(camera_bp)
    app.register_blueprint(motion_bp)
    app.register_blueprint(push_bp)
    app.register_blueprint(static_bp)
    
    return app