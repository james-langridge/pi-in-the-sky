"""Audio streaming routes."""

import logging
from flask import Blueprint, Response, jsonify, current_app

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