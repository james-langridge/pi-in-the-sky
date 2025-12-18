"""Pure functions for breathing detection analysis."""

from typing import List, Tuple, Optional
import cv2
import numpy as np

from models import BreathingZone, BreathingStatus, BreathingWaveformPoint


def extract_roi_from_frame(frame: np.ndarray, zone: BreathingZone) -> np.ndarray:
    """
    Extract region of interest from frame.

    Args:
        frame: Input frame as numpy array (BGR or grayscale)
        zone: Breathing zone defining the ROI

    Returns:
        Cropped ROI as numpy array
    """
    height, width = frame.shape[:2]

    # Clamp zone coordinates to frame bounds
    x1 = max(0, min(zone.x, width - 1))
    y1 = max(0, min(zone.y, height - 1))
    x2 = max(0, min(zone.x + zone.width, width))
    y2 = max(0, min(zone.y + zone.height, height))

    # Extract ROI
    return frame[y1:y2, x1:x2].copy()


def prepare_roi_for_analysis(roi: np.ndarray, blur_size: int = 5) -> np.ndarray:
    """
    Prepare ROI for motion analysis by converting to grayscale and blurring.

    Args:
        roi: Input ROI as numpy array
        blur_size: Gaussian blur kernel size (must be odd)

    Returns:
        Processed grayscale blurred ROI
    """
    # Ensure blur_size is odd
    blur_size = blur_size if blur_size % 2 == 1 else blur_size + 1

    # Convert to grayscale if needed
    if len(roi.shape) == 3:
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    else:
        gray = roi.copy()

    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (blur_size, blur_size), 0)

    return blurred


def calculate_zone_motion_intensity(
    current_roi: np.ndarray, previous_roi: np.ndarray
) -> float:
    """
    Calculate subtle motion intensity between two ROIs.

    Args:
        current_roi: Current ROI (grayscale, blurred)
        previous_roi: Previous ROI (grayscale, blurred)

    Returns:
        Motion intensity as float (0-1 scale)
    """
    if current_roi.shape != previous_roi.shape:
        return 0.0

    if current_roi.size == 0:
        return 0.0

    # Calculate absolute difference
    diff = cv2.absdiff(current_roi, previous_roi)

    # Calculate mean intensity change (0-255 scale)
    mean_diff = np.mean(diff)

    # Normalize to 0-1 scale (subtle breathing motion is typically 5-30 pixel diff)
    # Using 50 as max expected diff for breathing motion
    intensity = min(mean_diff / 50.0, 1.0)

    return float(intensity)


def detect_rhythmic_pattern(
    intensities: List[float],
    timestamps: List[float],
    min_freq: float,
    max_freq: float,
) -> Tuple[bool, Optional[float], float]:
    """
    Detect rhythmic breathing pattern using FFT analysis.

    Args:
        intensities: List of motion intensity values (0-1)
        timestamps: List of timestamps in milliseconds
        min_freq: Minimum expected frequency (Hz)
        max_freq: Maximum expected frequency (Hz)

    Returns:
        Tuple of (is_rhythmic, dominant_frequency_hz, confidence)
    """
    n = len(intensities)

    # Need at least 2 seconds of data for meaningful FFT
    if n < 20:
        return False, None, 0.0

    # Convert to numpy array
    signal = np.array(intensities)

    # Estimate sample rate from timestamps
    if len(timestamps) >= 2:
        time_span = (timestamps[-1] - timestamps[0]) / 1000.0  # Convert ms to seconds
        if time_span <= 0:
            return False, None, 0.0
        sample_rate = n / time_span
    else:
        sample_rate = 10.0  # Default assumption of 10 FPS

    # Remove DC component (mean)
    signal = signal - np.mean(signal)

    # Apply Hanning window to reduce spectral leakage
    window = np.hanning(n)
    signal = signal * window

    # Perform FFT (real-valued signal, use rfft for efficiency)
    fft_result = np.fft.rfft(signal)
    fft_magnitude = np.abs(fft_result)

    # Calculate frequency bins
    freqs = np.fft.rfftfreq(n, d=1.0 / sample_rate)

    # Find indices within breathing frequency range
    freq_mask = (freqs >= min_freq) & (freqs <= max_freq)
    valid_indices = np.where(freq_mask)[0]

    if len(valid_indices) == 0:
        return False, None, 0.0

    # Find dominant frequency in breathing range
    breathing_magnitudes = fft_magnitude[valid_indices]
    peak_idx_in_range = np.argmax(breathing_magnitudes)
    peak_idx = valid_indices[peak_idx_in_range]
    peak_magnitude = fft_magnitude[peak_idx]
    dominant_freq = freqs[peak_idx]

    # Calculate confidence based on peak prominence
    # Compare peak to average magnitude in the breathing range
    mean_magnitude = np.mean(breathing_magnitudes)
    if mean_magnitude > 0:
        peak_prominence = peak_magnitude / mean_magnitude
    else:
        peak_prominence = 0.0

    # Also consider overall signal strength (is there any motion at all?)
    signal_strength = np.std(intensities)
    if signal_strength < 0.01:  # Very little motion detected
        return False, None, 0.0

    # Confidence is based on peak prominence (how much it stands out)
    # A prominence of 3+ indicates a clear rhythmic pattern
    confidence = min(peak_prominence / 5.0, 1.0)

    # Require minimum confidence to consider it rhythmic
    is_rhythmic = confidence >= 0.3 and peak_prominence >= 1.5

    return is_rhythmic, float(dominant_freq) if is_rhythmic else None, float(confidence)


def calculate_breathing_rate(frequency_hz: float) -> float:
    """
    Convert frequency to breaths per minute.

    Args:
        frequency_hz: Breathing frequency in Hz

    Returns:
        Breaths per minute
    """
    return frequency_hz * 60.0


def should_trigger_breathing_alert(
    last_detected_time: Optional[float],
    current_time: float,
    threshold_seconds: float,
    enabled: bool,
) -> bool:
    """
    Check if breathing alert should trigger due to no detection.

    Args:
        last_detected_time: Unix timestamp of last breathing detection (ms)
        current_time: Current unix timestamp (ms)
        threshold_seconds: Alert threshold in seconds
        enabled: Whether breathing detection is enabled

    Returns:
        True if alert should trigger
    """
    if not enabled:
        return False

    if last_detected_time is None:
        return False

    time_since_detection = (current_time - last_detected_time) / 1000.0
    return time_since_detection >= threshold_seconds


def create_breathing_status(
    detected: bool,
    rate_bpm: Optional[float],
    confidence: float,
    last_detected_time: Optional[str],
    alert_active: bool,
    enabled: bool,
) -> BreathingStatus:
    """
    Create immutable breathing status from detection results.

    Args:
        detected: Whether breathing is currently detected
        rate_bpm: Estimated breathing rate in BPM
        confidence: Detection confidence (0-1)
        last_detected_time: ISO timestamp of last detection
        alert_active: Whether no-breathing alert is active
        enabled: Whether detection is enabled

    Returns:
        Immutable BreathingStatus instance
    """
    if not enabled:
        status = "disabled"
    elif alert_active:
        status = "alert"
    elif detected:
        status = "detected"
    elif confidence > 0.3:
        status = "monitoring"
    else:
        status = "warning"

    return BreathingStatus(
        detected=detected,
        rate_bpm=rate_bpm,
        confidence=confidence,
        last_detected_time=last_detected_time,
        alert_active=alert_active,
        status=status,
    )


def create_waveform_point(timestamp: float, intensity: float) -> BreathingWaveformPoint:
    """
    Create immutable waveform point.

    Args:
        timestamp: Unix timestamp in milliseconds
        intensity: Motion intensity (0-1)

    Returns:
        Immutable BreathingWaveformPoint instance
    """
    return BreathingWaveformPoint(timestamp=timestamp, intensity=intensity)


def validate_zone_bounds(
    zone: BreathingZone, frame_width: int, frame_height: int
) -> BreathingZone:
    """
    Validate and clamp zone bounds to frame dimensions.

    Args:
        zone: Input breathing zone
        frame_width: Frame width in pixels
        frame_height: Frame height in pixels

    Returns:
        New BreathingZone with clamped coordinates
    """
    x = max(0, min(zone.x, frame_width - 1))
    y = max(0, min(zone.y, frame_height - 1))
    width = max(1, min(zone.width, frame_width - x))
    height = max(1, min(zone.height, frame_height - y))

    return BreathingZone(
        x=x, y=y, width=width, height=height, enabled=zone.enabled
    )
