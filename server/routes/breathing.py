"""Breathing detection routes."""

import logging
from flask import Blueprint, request, jsonify, current_app
from dataclasses import replace
from models import BreathingZone, BreathingDetectionConfig

logger = logging.getLogger(__name__)

breathing_bp = Blueprint("breathing", __name__, url_prefix="/api/breathing")


@breathing_bp.route("/status")
def breathing_status():
    """
    Get current breathing detection status.

    Returns:
        JSON response with breathing detection status
    """
    breathing_service = current_app.config["services"].get("breathing_service")
    if breathing_service is None:
        return jsonify({"error": "Breathing detection not available"}), 503

    return jsonify(breathing_service.get_status_dict())


@breathing_bp.route("/config", methods=["GET"])
def get_breathing_config():
    """
    Get current breathing detection configuration.

    Returns:
        JSON response with configuration
    """
    breathing_service = current_app.config["services"].get("breathing_service")
    if breathing_service is None:
        return jsonify({"error": "Breathing detection not available"}), 503

    return jsonify(breathing_service.get_config_dict())


@breathing_bp.route("/config", methods=["POST"])
def update_breathing_config():
    """
    Update breathing detection configuration.

    Expected JSON (all fields optional):
        {
            "enabled": boolean,
            "analysis_window_seconds": float,
            "min_frequency_hz": float,
            "max_frequency_hz": float,
            "confidence_threshold": float,
            "alert_after_seconds": float
        }

    Returns:
        JSON response with updated configuration
    """
    breathing_service = current_app.config["services"].get("breathing_service")
    if breathing_service is None:
        return jsonify({"error": "Breathing detection not available"}), 503

    if not request.json:
        return jsonify({"status": "error", "message": "No JSON data provided"}), 400

    try:
        current_config = breathing_service.get_config()

        # Build new config with only provided fields
        new_config = replace(
            current_config,
            enabled=request.json.get("enabled", current_config.enabled),
            analysis_window_seconds=request.json.get(
                "analysis_window_seconds", current_config.analysis_window_seconds
            ),
            min_frequency_hz=request.json.get(
                "min_frequency_hz", current_config.min_frequency_hz
            ),
            max_frequency_hz=request.json.get(
                "max_frequency_hz", current_config.max_frequency_hz
            ),
            confidence_threshold=request.json.get(
                "confidence_threshold", current_config.confidence_threshold
            ),
            alert_after_seconds=request.json.get(
                "alert_after_seconds", current_config.alert_after_seconds
            ),
        )

        breathing_service.update_config(new_config)

        return jsonify({"status": "success", "config": breathing_service.get_config_dict()})

    except (TypeError, ValueError) as e:
        return jsonify({"status": "error", "message": f"Invalid configuration: {e}"}), 400


@breathing_bp.route("/zone", methods=["POST"])
def set_breathing_zone():
    """
    Set the breathing detection zone.

    Expected JSON:
        {
            "x": int,
            "y": int,
            "width": int,
            "height": int,
            "enabled": boolean (optional, defaults to true)
        }

    Returns:
        JSON response with status
    """
    breathing_service = current_app.config["services"].get("breathing_service")
    if breathing_service is None:
        return jsonify({"error": "Breathing detection not available"}), 503

    if not request.json:
        return jsonify({"status": "error", "message": "No JSON data provided"}), 400

    try:
        # Validate required fields
        required = ["x", "y", "width", "height"]
        for field in required:
            if field not in request.json:
                return jsonify(
                    {"status": "error", "message": f"Missing required field: {field}"}
                ), 400

        zone = BreathingZone(
            x=int(request.json["x"]),
            y=int(request.json["y"]),
            width=int(request.json["width"]),
            height=int(request.json["height"]),
            enabled=request.json.get("enabled", True),
        )

        # Validate zone dimensions
        if zone.width <= 0 or zone.height <= 0:
            return jsonify(
                {"status": "error", "message": "Zone dimensions must be positive"}
            ), 400

        breathing_service.set_zone(zone)

        # Enable detection when zone is set
        current_config = breathing_service.get_config()
        if not current_config.enabled:
            new_config = replace(current_config, enabled=True, zone=zone)
            breathing_service.update_config(new_config)

        return jsonify(
            {
                "status": "success",
                "message": "Breathing zone set",
                "zone": {
                    "x": zone.x,
                    "y": zone.y,
                    "width": zone.width,
                    "height": zone.height,
                    "enabled": zone.enabled,
                },
            }
        )

    except (TypeError, ValueError) as e:
        return jsonify({"status": "error", "message": f"Invalid zone data: {e}"}), 400


@breathing_bp.route("/zone", methods=["DELETE"])
def clear_breathing_zone():
    """
    Clear the breathing detection zone.

    Returns:
        JSON response with status
    """
    breathing_service = current_app.config["services"].get("breathing_service")
    if breathing_service is None:
        return jsonify({"error": "Breathing detection not available"}), 503

    breathing_service.clear_zone()

    # Disable detection when zone is cleared
    current_config = breathing_service.get_config()
    new_config = replace(current_config, enabled=False, zone=None)
    breathing_service.update_config(new_config)

    return jsonify({"status": "success", "message": "Breathing zone cleared"})


@breathing_bp.route("/waveform")
def get_waveform():
    """
    Get recent waveform data for visualization.

    Query parameters:
        seconds: Number of seconds of data (default: 10, max: 30)

    Returns:
        JSON response with waveform points
    """
    breathing_service = current_app.config["services"].get("breathing_service")
    if breathing_service is None:
        return jsonify({"error": "Breathing detection not available"}), 503

    seconds = request.args.get("seconds", 10.0, type=float)
    seconds = min(max(seconds, 1.0), 30.0)  # Clamp between 1 and 30

    points = breathing_service.get_waveform_data(seconds)

    return jsonify(
        {
            "points": [
                {"timestamp": p.timestamp, "intensity": p.intensity} for p in points
            ],
            "duration_seconds": seconds,
        }
    )
