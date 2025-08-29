"""Flask server for Raspberry Pi camera streaming."""

import logging
from flask import Flask, Response, request, jsonify, send_from_directory
from flask_cors import CORS

from config import AppConfig, get_default_presets
from services import CameraService, StreamingService, PresetManager, ControlManager
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
        Stream video feed as MJPEG.
        
        Returns:
            MJPEG stream response
        """
        return Response(
            streaming_service.generate_mjpeg_stream(),
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