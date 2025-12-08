"""Motion detection routes."""

import logging
from flask import Blueprint, request, jsonify, current_app
from models import MotionDetectionConfig
from motion_presets import get_motion_preset, get_preset_descriptions, MOTION_PRESETS

logger = logging.getLogger(__name__)

motion_bp = Blueprint('motion', __name__, url_prefix='/api/motion')


@motion_bp.route('/status')
def motion_status():
    """
    Get current motion detection status.
    
    Returns:
        JSON response with motion detection status
    """
    motion_service = current_app.config['services']['motion_service']
    status = motion_service.get_status()
    
    # Get full config for capture_on_motion field
    config = motion_service.get_config()

    # Format response to match frontend expectations
    return jsonify({
        "enabled": status["enabled"],
        "config": {
            "enabled": status["enabled"],
            "sensitivity": status["config"]["sensitivity"],
            "min_area": status["config"]["min_area"],
            "cooldown_seconds": status["config"]["cooldown_seconds"],
            "blur_size": config.blur_size,
            "threshold": config.threshold,
            "capture_on_motion": config.capture_on_motion
        },
        "recent_events": status["recent_events"],
        "triggered_events": status["triggered_events"]
    })


@motion_bp.route('/config', methods=['GET'])
def get_motion_config():
    """
    Get current motion detection configuration.
    
    Returns:
        JSON response with configuration
    """
    motion_service = current_app.config['services']['motion_service']
    config = motion_service.get_config()
    return jsonify({
        "enabled": config.enabled,
        "sensitivity": config.sensitivity,
        "min_area": config.min_area,
        "cooldown_seconds": config.cooldown_seconds,
        "blur_size": config.blur_size,
        "threshold": config.threshold,
        "capture_on_motion": config.capture_on_motion
    })


@motion_bp.route('/config', methods=['POST'])
def update_motion_config():
    """
    Update motion detection configuration.
    
    Expected JSON (all fields optional):
        {
            "enabled": boolean,
            "sensitivity": float (0.0-1.0),
            "min_area": integer,
            "cooldown_seconds": integer,
            "blur_size": integer (odd number),
            "threshold": integer
        }
        
    Returns:
        JSON response with updated configuration
    """
    motion_service = current_app.config['services']['motion_service']
    
    if not request.json:
        return jsonify({
            "status": "error",
            "message": "No JSON data provided"
        }), 400
    
    try:
        current_config = motion_service.get_config()

        # Create updated config with only provided fields
        config_dict = {
            "enabled": request.json.get("enabled", current_config.enabled),
            "sensitivity": request.json.get("sensitivity", current_config.sensitivity),
            "min_area": request.json.get("min_area", current_config.min_area),
            "cooldown_seconds": request.json.get("cooldown_seconds", current_config.cooldown_seconds),
            "blur_size": request.json.get("blur_size", current_config.blur_size),
            "threshold": request.json.get("threshold", current_config.threshold),
            "capture_on_motion": request.json.get("capture_on_motion", current_config.capture_on_motion)
        }

        # Validate and create new config
        new_config = MotionDetectionConfig(**config_dict)

        # Update service
        motion_service.update_config(new_config)

        return jsonify({
            "status": "success",
            "config": {
                "enabled": new_config.enabled,
                "sensitivity": new_config.sensitivity,
                "min_area": new_config.min_area,
                "cooldown_seconds": new_config.cooldown_seconds,
                "blur_size": new_config.blur_size,
                "threshold": new_config.threshold,
                "capture_on_motion": new_config.capture_on_motion
            }
        })
    except (TypeError, ValueError) as e:
        return jsonify({
            "status": "error",
            "message": f"Invalid configuration: {str(e)}"
        }), 400


@motion_bp.route('/events')
def get_motion_events():
    """
    Get recent motion detection events.
    
    Query parameters:
        limit: Maximum number of events to return (default: 10)
        
    Returns:
        JSON response with motion events
    """
    motion_service = current_app.config['services']['motion_service']
    
    limit = request.args.get('limit', 10, type=int)
    limit = min(max(limit, 1), 100)  # Clamp between 1 and 100
    
    events = motion_service.get_recent_events(limit)
    
    # Convert events to JSON-serializable format matching frontend expectations
    events_data = []
    for event in events:
        events_data.append({
            "timestamp": event.timestamp,
            "area": event.area,  # Use the correct field name
            "contours": 1 if event.triggered else 0,  # Frontend expects contours count
            "triggered": event.triggered
        })
    
    return jsonify(events_data)  # Return just the array, not wrapped in object


@motion_bp.route('/presets')
def get_motion_presets():
    """
    Get available motion detection presets.
    
    Returns:
        JSON response with preset names and descriptions
    """
    descriptions = get_preset_descriptions()
    presets = []
    
    for name, description in descriptions.items():
        preset_config = MOTION_PRESETS[name]
        presets.append({
            "name": name,
            "description": description,
            "config": {
                "enabled": preset_config.enabled,
                "sensitivity": preset_config.sensitivity,
                "min_area": preset_config.min_area,
                "cooldown_seconds": preset_config.cooldown_seconds
            }
        })
    
    return jsonify({
        "presets": presets
    })


@motion_bp.route('/preset/<preset_name>', methods=['POST'])
def apply_motion_preset(preset_name):
    """
    Apply a motion detection preset.
    
    Args:
        preset_name: Name of the preset to apply
        
    Returns:
        JSON response with status
    """
    motion_service = current_app.config['services']['motion_service']
    
    if preset_name not in MOTION_PRESETS:
        return jsonify({
            "status": "error",
            "message": f"Unknown preset: {preset_name}"
        }), 404
    
    preset_config = get_motion_preset(preset_name)
    motion_service.update_config(preset_config)
    
    return jsonify({
        "status": "success",
        "message": f"Applied motion preset: {preset_name}",
        "config": {
            "enabled": preset_config.enabled,
            "sensitivity": preset_config.sensitivity,
            "min_area": preset_config.min_area,
            "cooldown_seconds": preset_config.cooldown_seconds,
            "blur_size": preset_config.blur_size,
            "threshold": preset_config.threshold
        }
    })