"""Flask server for Raspberry Pi camera streaming."""

import logging
from flask import Flask, Response, request, jsonify
from flask_cors import CORS

from config import AppConfig, get_default_presets
from services import CameraService, StreamingService, PresetManager
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