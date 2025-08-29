"""Flask server for Raspberry Pi camera streaming."""

import logging
import os
import json
from flask import Flask, Response, request, jsonify, send_from_directory
from flask_cors import CORS

from config import AppConfig, get_default_presets
from services import CameraService, StreamingService, PresetManager, ControlManager
from motion_services import MotionDetectionService, NotificationService
from storage import SubscriptionStorage
from models import MotionDetectionConfig
from calculations import create_timestamp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


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
    camera_service = CameraService()
    streaming_service = StreamingService(camera_service, config.frame_delay)
    preset_manager = PresetManager(camera_service, get_default_presets())
    control_manager = ControlManager(camera_service)
    
    # Initialize motion detection and notification services
    motion_service = MotionDetectionService()
    subscription_storage = SubscriptionStorage()
    
    # Get VAPID keys from environment or generate them
    vapid_private_key = os.environ.get('VAPID_PRIVATE_KEY', '')
    vapid_public_key = os.environ.get('VAPID_PUBLIC_KEY', '')
    vapid_email = os.environ.get('VAPID_EMAIL', 'admin@example.com')
    
    notification_service = None
    if vapid_private_key and vapid_public_key:
        notification_service = NotificationService(
            subscription_storage,
            vapid_private_key,
            vapid_public_key,
            vapid_email
        )
        logger.info("Push notification service initialized")
    else:
        logger.warning("VAPID keys not configured - push notifications disabled")
    
    # Initialize camera on app startup
    @app.before_first_request
    def initialize_camera():
        """Initialize camera before handling first request."""
        try:
            camera_service.initialize()
            logger.info("Camera initialized on startup")
        except Exception as e:
            logger.error(f"Failed to initialize camera: {e}")
            # Could implement fallback or mock mode here
    
    @app.teardown_appcontext
    def cleanup_camera(error=None):
        """Clean up camera resources on shutdown."""
        if error:
            logger.error(f"App teardown due to error: {error}")
        # Cleanup will be called when app shuts down
    
    @app.route('/')
    def index():
        """Serve the UI HTML file."""
        import os
        ui_path = os.path.join(os.path.dirname(__file__), '..', 'ui', 'index.html')
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
    
    @app.route('/manifest.json')
    def manifest():
        """Serve the PWA manifest file."""
        import os
        return send_from_directory(
            os.path.join(os.path.dirname(__file__), 'ui'),
            'manifest.json',
            mimetype='application/manifest+json'
        )
    
    @app.route('/service-worker.js')
    def service_worker():
        """Serve the service worker file."""
        import os
        return send_from_directory(
            os.path.join(os.path.dirname(__file__), 'ui'),
            'service-worker.js',
            mimetype='application/javascript'
        )
    
    @app.route('/js/<path:filename>')
    def serve_js(filename):
        """Serve JavaScript files."""
        import os
        return send_from_directory(
            os.path.join(os.path.dirname(__file__), '..', 'ui', 'js'),
            filename,
            mimetype='application/javascript'
        )
    
    @app.route('/video_feed')
    def video_feed():
        """
        Stream video feed as MJPEG with motion detection.
        
        Returns:
            MJPEG stream response
        """
        def generate_with_motion_detection():
            """Generate MJPEG stream with motion detection."""
            for chunk in streaming_service.generate_mjpeg_stream():
                # Extract frame data for motion detection if enabled
                if motion_service.is_enabled():
                    try:
                        # Extract JPEG data from chunk (skip MJPEG headers)
                        jpeg_start = chunk.find(b'\xff\xd8')
                        jpeg_end = chunk.find(b'\xff\xd9')
                        if jpeg_start != -1 and jpeg_end != -1:
                            jpeg_data = chunk[jpeg_start:jpeg_end + 2]
                            
                            # Process frame for motion
                            motion_event = motion_service.process_frame(jpeg_data)
                            
                            # Send notification if triggered
                            if motion_event and motion_event.triggered and notification_service:
                                notification_service.send_motion_notification(motion_event)
                    except Exception as e:
                        logger.error(f"Motion detection error: {e}")
                
                yield chunk
        
        return Response(
            generate_with_motion_detection(),
            mimetype='multipart/x-mixed-replace; boundary=frame'
        )
    
    @app.route('/apply_preset', methods=['POST'])
    def apply_preset():
        """
        Apply camera preset settings.
        
        Expected JSON:
            {"preset": "preset_name"}
            
        Returns:
            JSON response with status
        """
        if not request.json:
            return jsonify({
                "status": "error",
                "message": "No JSON data provided"
            }), 400
        
        preset_name = request.json.get('preset')
        if not preset_name:
            return jsonify({
                "status": "error",
                "message": "No preset specified"
            }), 400
        
        result = preset_manager.apply_preset(preset_name)
        
        if result["success"]:
            return jsonify({
                "status": "success",
                "message": result["message"]
            })
        else:
            return jsonify({
                "status": "error",
                "message": result["error"]
            }), 400
    
    @app.route('/health')
    def health():
        """
        Health check endpoint.
        
        Returns:
            JSON response with health status
        """
        return jsonify({
            "status": "healthy",
            "timestamp": create_timestamp(),
            "config": {
                "host": config.host,
                "port": config.port,
                "debug": config.debug,
                "cors_origins": config.cors_origins
            }
        })
    
    @app.route('/presets')
    def list_presets():
        """
        List available camera presets.
        
        Returns:
            JSON response with preset names
        """
        presets = list(preset_manager._presets.keys())
        return jsonify({
            "presets": presets,
            "current": None  # Could track current preset in service
        })
    
    @app.route('/controls')
    def get_controls():
        """
        Get all available camera controls with metadata.
        
        Returns:
            JSON response with control metadata grouped by category
        """
        categories = control_manager.get_controls_by_category()
        
        # Convert to JSON-serializable format
        result = {}
        for category, controls in categories.items():
            result[category] = []
            for control in controls:
                control_dict = {
                    "name": control.name,
                    "display_name": control.display_name,
                    "type": control.control_type,
                    "category": control.category
                }
                
                # Add type-specific fields
                if control.control_type == "slider":
                    control_dict.update({
                        "min": control.min_value,
                        "max": control.max_value,
                        "step": control.step,
                        "default": control.default_value
                    })
                    if control.unit:
                        control_dict["unit"] = control.unit
                elif control.control_type == "toggle":
                    control_dict["default"] = control.default_value
                elif control.control_type == "select":
                    control_dict["options"] = control.options
                    control_dict["default"] = control.default_value
                
                result[category].append(control_dict)
        
        return jsonify(result)
    
    @app.route('/control/<control_name>', methods=['GET'])
    def get_control_value(control_name):
        """
        Get current value of a specific control.
        
        Args:
            control_name: Name of the control
            
        Returns:
            JSON response with control value
        """
        result = control_manager.get_control_value(control_name)
        
        if result["success"]:
            return jsonify(result)
        else:
            return jsonify({
                "status": "error",
                "message": result["error"]
            }), 400
    
    @app.route('/control/<control_name>', methods=['POST'])
    def update_control(control_name):
        """
        Update a specific camera control.
        
        Expected JSON:
            {"value": <new_value>}
            
        Args:
            control_name: Name of the control
            
        Returns:
            JSON response with status
        """
        if not request.json:
            return jsonify({
                "status": "error",
                "message": "No JSON data provided"
            }), 400
        
        value = request.json.get('value')
        if value is None:
            return jsonify({
                "status": "error",
                "message": "No value specified"
            }), 400
        
        result = control_manager.update_control(control_name, value)
        
        if result["success"]:
            return jsonify({
                "status": "success",
                "message": result["message"],
                "value": result["value"]
            })
        else:
            return jsonify({
                "status": "error",
                "message": result["error"]
            }), 400
    
    # Motion Detection Endpoints
    
    @app.route('/api/motion/status')
    def motion_status():
        """
        Get motion detection status.
        
        Returns:
            JSON response with motion detection status
        """
        return jsonify(motion_service.get_status())
    
    @app.route('/api/motion/config', methods=['GET'])
    def get_motion_config():
        """
        Get motion detection configuration.
        
        Returns:
            JSON response with configuration
        """
        config = motion_service.get_config()
        return jsonify({
            "enabled": config.enabled,
            "sensitivity": config.sensitivity,
            "min_area": config.min_area,
            "cooldown_seconds": config.cooldown_seconds,
            "threshold": config.threshold,
            "blur_size": config.blur_size
        })
    
    @app.route('/api/motion/config', methods=['POST'])
    def update_motion_config():
        """
        Update motion detection configuration.
        
        Expected JSON:
            {
                "enabled": bool,
                "sensitivity": float,
                "min_area": int,
                "cooldown_seconds": int,
                "threshold": int,
                "blur_size": int
            }
            
        Returns:
            JSON response with status
        """
        if not request.json:
            return jsonify({
                "status": "error",
                "message": "No JSON data provided"
            }), 400
        
        try:
            # Get current config and update with provided values
            current_config = motion_service.get_config()
            
            new_config = MotionDetectionConfig(
                enabled=request.json.get('enabled', current_config.enabled),
                sensitivity=request.json.get('sensitivity', current_config.sensitivity),
                min_area=request.json.get('min_area', current_config.min_area),
                cooldown_seconds=request.json.get('cooldown_seconds', current_config.cooldown_seconds),
                threshold=request.json.get('threshold', current_config.threshold),
                blur_size=request.json.get('blur_size', current_config.blur_size)
            )
            
            motion_service.update_config(new_config)
            
            return jsonify({
                "status": "success",
                "message": "Motion detection configuration updated"
            })
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500
    
    @app.route('/api/motion/events')
    def get_motion_events():
        """
        Get recent motion events.
        
        Query params:
            limit: Maximum number of events to return (default: 10)
            
        Returns:
            JSON response with motion events
        """
        limit = request.args.get('limit', 10, type=int)
        events = motion_service.get_recent_events(limit)
        
        events_data = [{
            "timestamp": event.timestamp,
            "motion_score": event.motion_score,
            "area": event.area,
            "frame_diff_percentage": event.frame_diff_percentage,
            "triggered": event.triggered
        } for event in events]
        
        return jsonify({"events": events_data})
    
    # Push Notification Endpoints
    
    @app.route('/api/push/vapid-key')
    def get_vapid_key():
        """
        Get VAPID public key for push notifications.
        
        Returns:
            JSON response with public key
        """
        if notification_service:
            return jsonify({
                "publicKey": notification_service.get_vapid_public_key()
            })
        else:
            return jsonify({
                "error": "Push notifications not configured"
            }), 503
    
    @app.route('/api/push/subscribe', methods=['POST'])
    def subscribe_push():
        """
        Subscribe to push notifications.
        
        Expected JSON:
            {
                "endpoint": "https://...",
                "keys": {
                    "p256dh": "...",
                    "auth": "..."
                }
            }
            
        Returns:
            JSON response with subscription status
        """
        if not notification_service:
            return jsonify({
                "status": "error",
                "message": "Push notifications not configured"
            }), 503
        
        if not request.json:
            return jsonify({
                "status": "error",
                "message": "No subscription data provided"
            }), 400
        
        try:
            subscription_info = request.json
            endpoint = subscription_info.get('endpoint')
            keys = subscription_info.get('keys', {})
            p256dh = keys.get('p256dh')
            auth = keys.get('auth')
            
            if not all([endpoint, p256dh, auth]):
                return jsonify({
                    "status": "error",
                    "message": "Missing required subscription data"
                }), 400
            
            user_agent = request.headers.get('User-Agent')
            
            subscription = subscription_storage.add_subscription(
                endpoint=endpoint,
                p256dh=p256dh,
                auth=auth,
                user_agent=user_agent
            )
            
            return jsonify({
                "status": "success",
                "message": "Subscription created",
                "subscription_id": subscription.id
            })
        except Exception as e:
            logger.error(f"Failed to create subscription: {e}")
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500
    
    @app.route('/api/push/unsubscribe', methods=['POST'])
    def unsubscribe_push():
        """
        Unsubscribe from push notifications.
        
        Expected JSON:
            {"endpoint": "https://..."}
            
        Returns:
            JSON response with status
        """
        if not request.json:
            return jsonify({
                "status": "error",
                "message": "No endpoint provided"
            }), 400
        
        endpoint = request.json.get('endpoint')
        if not endpoint:
            return jsonify({
                "status": "error",
                "message": "Endpoint required"
            }), 400
        
        if subscription_storage.remove_subscription(endpoint):
            return jsonify({
                "status": "success",
                "message": "Subscription removed"
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Subscription not found"
            }), 404
    
    @app.route('/api/push/test', methods=['POST'])
    def test_notification():
        """
        Send a test push notification.
        
        Expected JSON:
            {"endpoint": "https://..."}
            
        Returns:
            JSON response with status
        """
        if not notification_service:
            return jsonify({
                "status": "error",
                "message": "Push notifications not configured"
            }), 503
        
        if not request.json:
            return jsonify({
                "status": "error",
                "message": "No endpoint provided"
            }), 400
        
        endpoint = request.json.get('endpoint')
        if not endpoint:
            return jsonify({
                "status": "error",
                "message": "Endpoint required"
            }), 400
        
        if notification_service.test_notification(endpoint):
            return jsonify({
                "status": "success",
                "message": "Test notification sent"
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to send test notification"
            }), 500
    
    return app


def main():
    """Application entry point with proper initialization."""
    # Load configuration
    config = AppConfig.from_env()
    
    logger.info(f"Starting server with config: {config}")
    
    # Create app
    app = create_app(config)
    
    # Run server
    try:
        app.run(
            host=config.host,
            port=config.port,
            threaded=True,
            debug=config.debug
        )
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
    finally:
        logger.info("Server shutting down")


if __name__ == '__main__':
    main()