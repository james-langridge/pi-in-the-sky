"""Camera-related routes."""

import logging
from flask import Blueprint, Response, request, jsonify, current_app
from calculations import create_timestamp

logger = logging.getLogger(__name__)

camera_bp = Blueprint('camera', __name__)


@camera_bp.route('/video_feed')
def video_feed():
    """
    Stream video feed as MJPEG with motion detection.
    
    Returns:
        MJPEG stream response
    """
    services = current_app.config['services']
    streaming_service = services['streaming_service']
    motion_service = services['motion_service']
    notification_service = services['notification_service']
    
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


@camera_bp.route('/apply_preset', methods=['POST'])
def apply_preset():
    """
    Apply camera preset settings.
    
    Expected JSON:
        {"preset": "preset_name"}
        
    Returns:
        JSON response with status
    """
    preset_manager = current_app.config['services']['preset_manager']
    
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


@camera_bp.route('/presets')
def list_presets():
    """
    List available camera presets.
    
    Returns:
        JSON response with preset names
    """
    preset_manager = current_app.config['services']['preset_manager']
    presets = list(preset_manager._presets.keys())
    return jsonify({
        "presets": presets,
        "current": None  # Could track current preset in service
    })


@camera_bp.route('/controls')
def get_controls():
    """
    Get all available camera controls with metadata.
    
    Returns:
        JSON response with control metadata grouped by category
    """
    control_manager = current_app.config['services']['control_manager']
    categories = control_manager.get_controls_by_category()
    
    # Convert to JSON-serializable format
    result = {}
    for category, controls in categories.items():
        result[category] = []
        for control in controls:
            control_data = {
                "name": control.name,
                "label": control.label,
                "type": control.type,
                "category": control.category
            }
            
            # Add type-specific metadata
            if control.min is not None:
                control_data["min"] = control.min
            if control.max is not None:
                control_data["max"] = control.max
            if control.step is not None:
                control_data["step"] = control.step
            if control.options:
                control_data["options"] = control.options
            if control.default is not None:
                control_data["default"] = control.default
                
            result[category].append(control_data)
    
    return jsonify(result)


@camera_bp.route('/control/<control_name>', methods=['GET'])
def get_control(control_name):
    """
    Get current value of a camera control.
    
    Args:
        control_name: Name of the control to get
        
    Returns:
        JSON response with control value
    """
    control_manager = current_app.config['services']['control_manager']
    result = control_manager.get_control_value(control_name)
    
    if result["success"]:
        return jsonify({
            "status": "success",
            "value": result["value"]
        })
    else:
        return jsonify({
            "status": "error",
            "message": result["error"]
        }), 400


@camera_bp.route('/control/<control_name>', methods=['POST'])
def set_control(control_name):
    """
    Set value of a camera control.
    
    Args:
        control_name: Name of the control to set
        
    Expected JSON:
        {"value": <control_value>}
        
    Returns:
        JSON response with status
    """
    control_manager = current_app.config['services']['control_manager']
    
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
    
    result = control_manager.set_control_value(control_name, value)
    
    if result["success"]:
        return jsonify({
            "status": "success",
            "message": result.get("message", "Control updated"),
            "actual_value": result.get("actual_value", value)
        })
    else:
        return jsonify({
            "status": "error",
            "message": result["error"]
        }), 400


@camera_bp.route('/health')
def health():
    """
    Health check endpoint.
    
    Returns:
        JSON response with health status
    """
    config = current_app.config['app_config']
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