"""Audio streaming routes."""

import logging
from flask import Blueprint, Response, jsonify, request, current_app
from models import AudioDetectionConfig

logger = logging.getLogger(__name__)

audio_bp = Blueprint('audio', __name__)


@audio_bp.route('/audio_feed')
def audio_feed():
    """
    Stream audio as WAV format.
    
    Returns:
        WAV audio stream response
    """
    services = current_app.config['services']
    audio_streaming_service = services.get('audio_streaming_service')
    
    if not audio_streaming_service:
        logger.error("Audio streaming service not available")
        return "Audio service not available", 503
    
    def generate():
        """Generate WAV audio stream."""
        try:
            for chunk in audio_streaming_service.generate_wav_stream():
                yield chunk
        except Exception as e:
            logger.error(f"Audio streaming error: {e}")
    
    return Response(
        generate(),
        mimetype='audio/wav',
        headers={
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'  # Disable Nginx buffering
        }
    )


@audio_bp.route('/api/audio/level')
def audio_level():
    """
    Get current audio level for visualization.
    
    Returns:
        JSON with audio level (0.0 to 1.0)
    """
    services = current_app.config['services']
    audio_streaming_service = services.get('audio_streaming_service')
    
    if not audio_streaming_service:
        return jsonify({
            "status": "error",
            "message": "Audio service not available"
        }), 503
    
    level = audio_streaming_service.get_audio_level()
    
    return jsonify({
        "status": "success",
        "level": level
    })


@audio_bp.route('/api/audio/status')
def audio_status():
    """
    Get audio service status.
    
    Returns:
        JSON with audio service status
    """
    services = current_app.config['services']
    audio_service = services.get('audio_capture_service')
    
    if not audio_service:
        return jsonify({
            "status": "error",
            "message": "Audio service not configured",
            "available": False
        })
    
    # Check if using mock
    is_mock = type(audio_service).__name__ == 'MockAudioService'
    
    return jsonify({
        "status": "success",
        "available": True,
        "mock": is_mock,
        "device": audio_service._config.device if not is_mock else "mock",
        "sample_rate": audio_service._config.sample_rate,
        "channels": audio_service._config.channels
    })


@audio_bp.route('/api/audio/detection/status')
def audio_detection_status():
    """
    Get audio detection status.
    
    Returns:
        JSON with detection status and configuration
    """
    services = current_app.config['services']
    audio_detection_service = services.get('audio_detection_service')
    
    if not audio_detection_service:
        return jsonify({
            "status": "error",
            "message": "Audio detection service not available"
        }), 503
    
    status = audio_detection_service.get_status()
    return jsonify({
        "status": "success",
        **status
    })


@audio_bp.route('/api/audio/detection/config', methods=['GET', 'POST'])
def audio_detection_config():
    """
    Get or update audio detection configuration.
    
    GET: Returns current configuration
    POST: Updates configuration with JSON body
    
    Returns:
        JSON with configuration or operation status
    """
    services = current_app.config['services']
    audio_detection_service = services.get('audio_detection_service')
    
    if not audio_detection_service:
        return jsonify({
            "status": "error",
            "message": "Audio detection service not available"
        }), 503
    
    if request.method == 'GET':
        # Get current config
        config = audio_detection_service._config
        return jsonify({
            "status": "success",
            "enabled": config.enabled,
            "threshold": config.threshold,
            "duration_threshold": config.duration_threshold,
            "cooldown_seconds": config.cooldown_seconds,
            "frequency_min": config.frequency_min,
            "frequency_max": config.frequency_max
        })
    
    # POST - Update config
    if not request.json:
        return jsonify({
            "status": "error",
            "message": "No JSON data provided"
        }), 400
    
    try:
        # Create new config from request
        new_config = AudioDetectionConfig(
            enabled=request.json.get('enabled', False),
            threshold=float(request.json.get('threshold', 0.05)),
            duration_threshold=float(request.json.get('duration_threshold', 0.5)),
            cooldown_seconds=int(request.json.get('cooldown_seconds', 30)),
            frequency_min=float(request.json.get('frequency_min', 100.0)),
            frequency_max=float(request.json.get('frequency_max', 8000.0))
        )
        
        # Update service
        audio_detection_service.update_config(new_config)
        
        logger.info(f"Audio detection config updated: enabled={new_config.enabled}, threshold={new_config.threshold}")
        
        return jsonify({
            "status": "success",
            "message": "Configuration updated",
            "config": {
                "enabled": new_config.enabled,
                "threshold": new_config.threshold,
                "duration_threshold": new_config.duration_threshold,
                "cooldown_seconds": new_config.cooldown_seconds
            }
        })
        
    except (ValueError, TypeError) as e:
        return jsonify({
            "status": "error",
            "message": f"Invalid configuration: {str(e)}"
        }), 400


@audio_bp.route('/api/audio/detection/events')
def audio_detection_events():
    """
    Get recent audio detection events.
    
    Returns:
        JSON with list of recent events
    """
    services = current_app.config['services']
    audio_detection_service = services.get('audio_detection_service')
    
    if not audio_detection_service:
        return jsonify({
            "status": "error",
            "message": "Audio detection service not available"
        }), 503
    
    limit = request.args.get('limit', 10, type=int)
    events = audio_detection_service.get_recent_events(limit)
    
    # Convert events to JSON-serializable format
    events_data = []
    for event in events:
        events_data.append({
            "timestamp": event.timestamp,
            "rms_level": event.rms_level,
            "peak_level": event.peak_level,
            "duration": event.duration,
            "triggered": event.triggered
        })
    
    return jsonify({
        "status": "success",
        "events": events_data,
        "count": len(events_data)
    })