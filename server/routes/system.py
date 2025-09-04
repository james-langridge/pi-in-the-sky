"""System control routes for power operations."""

import logging
import subprocess
from flask import Blueprint, jsonify, request, current_app
from calculations import create_timestamp

logger = logging.getLogger(__name__)

system_bp = Blueprint('system', __name__)


@system_bp.route('/api/system/shutdown', methods=['POST'])
def shutdown():
    """
    Shutdown the Raspberry Pi system.
    
    Expected JSON:
        {"confirm": true}
    
    Returns:
        JSON response with status
    """
    if not request.json or not request.json.get('confirm'):
        return jsonify({
            "status": "error",
            "message": "Confirmation required"
        }), 400
    
    try:
        # Check if running on actual Pi or mock mode
        camera_service = current_app.config['services']['camera_service']
        if hasattr(camera_service, 'mock_mode') and camera_service.mock_mode:
            logger.info("Mock mode: Simulating shutdown")
            return jsonify({
                "status": "success",
                "message": "Mock shutdown initiated",
                "timestamp": create_timestamp()
            })
        
        # Execute shutdown command (delayed by 1 second to allow response)
        logger.info("Initiating system shutdown")
        subprocess.Popen(['sudo', 'shutdown', '-h', '+0'])
        
        return jsonify({
            "status": "success",
            "message": "System shutdown initiated",
            "timestamp": create_timestamp()
        })
        
    except Exception as e:
        logger.error(f"Shutdown error: {e}")
        return jsonify({
            "status": "error",
            "message": f"Failed to initiate shutdown: {str(e)}"
        }), 500


@system_bp.route('/api/system/restart', methods=['POST'])
def restart():
    """
    Restart the Raspberry Pi system.
    
    Expected JSON:
        {"confirm": true}
    
    Returns:
        JSON response with status
    """
    if not request.json or not request.json.get('confirm'):
        return jsonify({
            "status": "error",
            "message": "Confirmation required"
        }), 400
    
    try:
        # Check if running on actual Pi or mock mode
        camera_service = current_app.config['services']['camera_service']
        if hasattr(camera_service, 'mock_mode') and camera_service.mock_mode:
            logger.info("Mock mode: Simulating restart")
            return jsonify({
                "status": "success",
                "message": "Mock restart initiated",
                "timestamp": create_timestamp()
            })
        
        # Execute restart command (delayed by 1 second to allow response)
        logger.info("Initiating system restart")
        subprocess.Popen(['sudo', 'reboot'])
        
        return jsonify({
            "status": "success",
            "message": "System restart initiated",
            "timestamp": create_timestamp()
        })
        
    except Exception as e:
        logger.error(f"Restart error: {e}")
        return jsonify({
            "status": "error",
            "message": f"Failed to initiate restart: {str(e)}"
        }), 500


@system_bp.route('/api/system/status')
def system_status():
    """
    Get current system status and information.
    
    Returns:
        JSON response with system information
    """
    try:
        # Check if running on actual Pi
        camera_service = current_app.config['services']['camera_service']
        is_mock = hasattr(camera_service, 'mock_mode') and camera_service.mock_mode
        
        return jsonify({
            "status": "healthy",
            "timestamp": create_timestamp(),
            "mock_mode": is_mock,
            "platform": "mock" if is_mock else "raspberry-pi"
        })
        
    except Exception as e:
        logger.error(f"Status error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500