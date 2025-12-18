"""Service for breathing detection using zone motion analysis."""

import time
import logging
from typing import Optional, Dict, Any, List
from collections import deque
from dataclasses import replace

from models import (
    BreathingZone,
    BreathingDetectionConfig,
    BreathingStatus,
    BreathingWaveformPoint,
)
from breathing_calculations import (
    extract_roi_from_frame,
    prepare_roi_for_analysis,
    calculate_zone_motion_intensity,
    detect_rhythmic_pattern,
    calculate_breathing_rate,
    should_trigger_breathing_alert,
    create_breathing_status,
    create_waveform_point,
    validate_zone_bounds,
)
from calculations import decode_jpeg_to_frame, create_timestamp

logger = logging.getLogger(__name__)


class BreathingDetectionService:
    """Orchestrates breathing detection using zone motion analysis."""

    def __init__(self, config: Optional[BreathingDetectionConfig] = None):
        """
        Initialize breathing detection service.

        Args:
            config: Breathing detection configuration
        """
        self._config = config or BreathingDetectionConfig()

        # Buffer for motion intensity values (~20s at 10 FPS)
        self._intensity_buffer: deque = deque(maxlen=200)
        self._timestamp_buffer: deque = deque(maxlen=200)

        # Previous frame ROI for comparison
        self._previous_roi: Optional[Any] = None

        # Detection state
        self._last_detected_time: Optional[float] = None
        self._last_analysis_time: float = 0.0
        self._current_status: Optional[BreathingStatus] = None

        # Frame dimensions (set on first frame)
        self._frame_width: int = 0
        self._frame_height: int = 0

    def update_config(self, config: BreathingDetectionConfig) -> None:
        """Update breathing detection configuration."""
        old_zone = self._config.zone
        self._config = config

        # Reset buffers if zone changed
        if old_zone != config.zone:
            self._reset_buffers()

        logger.info(
            f"Breathing detection {'enabled' if config.enabled else 'disabled'}"
        )

    def get_config(self) -> BreathingDetectionConfig:
        """Get current breathing detection configuration."""
        return self._config

    def is_enabled(self) -> bool:
        """Check if breathing detection is enabled."""
        return self._config.enabled and self._config.zone is not None

    def set_zone(self, zone: BreathingZone) -> None:
        """
        Set the breathing detection zone.

        Args:
            zone: New breathing zone
        """
        # Validate zone bounds if we know frame dimensions
        if self._frame_width > 0 and self._frame_height > 0:
            zone = validate_zone_bounds(zone, self._frame_width, self._frame_height)

        self._config = replace(self._config, zone=zone)
        self._reset_buffers()
        logger.info(f"Breathing zone set: {zone}")

    def clear_zone(self) -> None:
        """Clear the breathing detection zone."""
        self._config = replace(self._config, zone=None)
        self._reset_buffers()
        logger.info("Breathing zone cleared")

    def process_frame(self, jpeg_frame: bytes) -> Optional[BreathingWaveformPoint]:
        """
        Process a frame for breathing detection.

        Args:
            jpeg_frame: JPEG encoded frame bytes

        Returns:
            BreathingWaveformPoint if zone is configured, None otherwise
        """
        if not self.is_enabled():
            return None

        zone = self._config.zone
        if zone is None:
            return None

        try:
            # Decode JPEG to numpy array
            frame = decode_jpeg_to_frame(jpeg_frame)

            # Store frame dimensions
            self._frame_height, self._frame_width = frame.shape[:2]

            # Extract and prepare ROI
            roi = extract_roi_from_frame(frame, zone)
            prepared_roi = prepare_roi_for_analysis(roi)

            # Get current timestamp
            current_time = time.time() * 1000  # Convert to milliseconds

            # Calculate motion intensity if we have a previous ROI
            intensity = 0.0
            if self._previous_roi is not None:
                if prepared_roi.shape == self._previous_roi.shape:
                    intensity = calculate_zone_motion_intensity(
                        prepared_roi, self._previous_roi
                    )

            # Store current ROI for next comparison
            self._previous_roi = prepared_roi

            # Add to buffers
            self._intensity_buffer.append(intensity)
            self._timestamp_buffer.append(current_time)

            # Run rhythm analysis every second
            time_since_analysis = (current_time - self._last_analysis_time) / 1000.0
            if time_since_analysis >= 1.0:
                self._analyze_rhythm(current_time)
                self._last_analysis_time = current_time

            # Create waveform point
            return create_waveform_point(current_time, intensity)

        except Exception as e:
            logger.error(f"Error processing frame for breathing detection: {e}")
            return None

    def _analyze_rhythm(self, current_time: float) -> None:
        """
        Analyze intensity buffer for rhythmic breathing pattern.

        Args:
            current_time: Current timestamp in milliseconds
        """
        intensities = list(self._intensity_buffer)
        timestamps = list(self._timestamp_buffer)

        # Detect rhythmic pattern
        is_rhythmic, freq_hz, confidence = detect_rhythmic_pattern(
            intensities,
            timestamps,
            self._config.min_frequency_hz,
            self._config.max_frequency_hz,
        )

        # Calculate breathing rate if detected
        rate_bpm = None
        if is_rhythmic and freq_hz is not None:
            rate_bpm = calculate_breathing_rate(freq_hz)
            self._last_detected_time = current_time

        # Check for alert condition
        alert_active = should_trigger_breathing_alert(
            self._last_detected_time,
            current_time,
            self._config.alert_after_seconds,
            self._config.enabled,
        )

        # Format last detected time
        last_detected_str = None
        if self._last_detected_time is not None:
            last_detected_str = create_timestamp()

        # Update status
        detected = is_rhythmic and confidence >= self._config.confidence_threshold
        self._current_status = create_breathing_status(
            detected=detected,
            rate_bpm=rate_bpm,
            confidence=confidence,
            last_detected_time=last_detected_str,
            alert_active=alert_active,
            enabled=self._config.enabled,
        )

        if detected:
            logger.debug(f"Breathing detected: {rate_bpm:.1f} BPM, confidence={confidence:.2f}")
        elif alert_active:
            logger.warning("No breathing detected - alert active")

    def get_status(self) -> BreathingStatus:
        """
        Get current breathing detection status.

        Returns:
            Current BreathingStatus
        """
        if self._current_status is not None:
            return self._current_status

        # Return default status if not yet analyzed
        return create_breathing_status(
            detected=False,
            rate_bpm=None,
            confidence=0.0,
            last_detected_time=None,
            alert_active=False,
            enabled=self._config.enabled,
        )

    def get_status_dict(self) -> Dict[str, Any]:
        """
        Get breathing detection status as dictionary.

        Returns:
            Dictionary with status information
        """
        status = self.get_status()
        zone = self._config.zone

        return {
            "detected": status.detected,
            "rate_bpm": status.rate_bpm,
            "confidence": status.confidence,
            "last_detected_time": status.last_detected_time,
            "alert_active": status.alert_active,
            "status": status.status,
            "zone": {
                "x": zone.x,
                "y": zone.y,
                "width": zone.width,
                "height": zone.height,
                "enabled": zone.enabled,
            }
            if zone
            else None,
        }

    def get_config_dict(self) -> Dict[str, Any]:
        """
        Get breathing detection configuration as dictionary.

        Returns:
            Dictionary with configuration
        """
        zone = self._config.zone
        return {
            "enabled": self._config.enabled,
            "zone": {
                "x": zone.x,
                "y": zone.y,
                "width": zone.width,
                "height": zone.height,
                "enabled": zone.enabled,
            }
            if zone
            else None,
            "analysis_window_seconds": self._config.analysis_window_seconds,
            "min_frequency_hz": self._config.min_frequency_hz,
            "max_frequency_hz": self._config.max_frequency_hz,
            "confidence_threshold": self._config.confidence_threshold,
            "alert_after_seconds": self._config.alert_after_seconds,
        }

    def get_waveform_data(self, seconds: float = 10.0) -> List[BreathingWaveformPoint]:
        """
        Get recent waveform data for visualization.

        Args:
            seconds: Number of seconds of data to return

        Returns:
            List of BreathingWaveformPoint objects
        """
        if not self._timestamp_buffer:
            return []

        current_time = time.time() * 1000
        cutoff_time = current_time - (seconds * 1000)

        points = []
        for ts, intensity in zip(self._timestamp_buffer, self._intensity_buffer):
            if ts >= cutoff_time:
                points.append(create_waveform_point(ts, intensity))

        return points

    def _reset_buffers(self) -> None:
        """Reset all detection buffers."""
        self._intensity_buffer.clear()
        self._timestamp_buffer.clear()
        self._previous_roi = None
        self._last_detected_time = None
        self._last_analysis_time = 0.0
        self._current_status = None
        logger.info("Breathing detection buffers reset")

    def reset(self) -> None:
        """Reset breathing detection state."""
        self._reset_buffers()
        logger.info("Breathing detection state reset")
