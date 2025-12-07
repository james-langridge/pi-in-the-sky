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
        camera_service = services['camera_service']
        motion_capture_count = 0

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

                        # Handle triggered motion event
                        if motion_event and motion_event.triggered:
                            # Send notification
                            if notification_service:
                                notification_service.send_motion_notification(motion_event)

                            # Capture photo if enabled
                            config = motion_service.get_config()
                            if config.capture_on_motion:
                                result = camera_service.capture_photo(source="motion")
                                if result.is_success:
                                    motion_capture_count += 1
                                    # Cleanup every 10th capture to avoid work in stream loop
                                    if motion_capture_count % 10 == 0:
                                        camera_service.cleanup_motion_photos(max_count=100)
                                else:
                                    logger.warning(f"Motion photo capture failed: {result.error}")
                except Exception as e:
                    logger.error(f"Motion detection error: {e}")

            yield chunk

    return Response(
        generate_with_motion_detection(),
        mimetype='multipart/x-mixed-replace; boundary=frame',
        headers={
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0',
            'Connection': 'keep-alive',  # Required for continuous streaming
            'X-Accel-Buffering': 'no'  # Disable Nginx buffering if using reverse proxy
        }
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
    camera_service = current_app.config['services']['camera_service']

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

    result = camera_service.apply_preset(preset_name)

    if result.is_success:
        return jsonify({
            "status": "success",
            "message": result.value
        })
    else:
        return jsonify({
            "status": "error",
            "message": result.error
        }), 400


@camera_bp.route('/presets')
def list_presets():
    """
    List available camera presets.

    Returns:
        JSON response with preset names
    """
    from config import get_default_presets
    presets = list(get_default_presets().keys())
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
        return jsonify(result)
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

    result = control_manager.update_control(control_name, value)

    if result["success"]:
        return jsonify({
            "status": "success",
            "message": result.get("message", "Control updated"),
            "actual_value": result.get("value", value)
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


@camera_bp.route('/api/stream/timestamp')
def stream_timestamp():
    """
    Get comprehensive stream status including timestamp and health.

    Returns:
        JSON response with stream status and timestamp
    """
    streaming_service = current_app.config['services']['streaming_service']
    stream_status = streaming_service.get_stream_status()
    
    # Determine overall status based on stream health
    if stream_status["healthy"]:
        status = "streaming"
    elif stream_status["timestamp"] and stream_status["frame_age_seconds"] is not None:
        if stream_status["frame_age_seconds"] > 10:
            status = "stale"
        else:
            status = "degraded"
    else:
        status = "waiting"
    
    return jsonify({
        "timestamp": stream_status["timestamp"],
        "status": status,
        "healthy": stream_status["healthy"],
        "active_streams": stream_status["active_streams"],
        "frame_age_seconds": stream_status["frame_age_seconds"]
    })


@camera_bp.route('/api/capture-photo', methods=['POST'])
def capture_photo():
    """
    Capture a photo and save it to the photos directory.
    
    Returns:
        JSON response with filename or error
    """
    camera_service = current_app.config['services']['camera_service']
    
    try:
        result = camera_service.capture_photo()
        
        if result.is_success:
            return jsonify({
                "status": "success",
                "filename": result.value,
                "message": f"Photo saved as {result.value}"
            })
        else:
            return jsonify({
                "status": "error",
                "message": result.error
            }), 500
            
    except Exception as e:
        logger.error(f"Error capturing photo: {e}")
        return jsonify({
            "status": "error",
            "message": f"Failed to capture photo: {str(e)}"
        }), 500
