"""Pure functions for frame processing and calculations."""

from datetime import datetime
from typing import Union, Tuple, Optional, List, Dict, Any
import cv2
import numpy as np
from models import MotionDetectionConfig, MotionEvent, CameraControls, CameraPreset


def create_timestamp() -> str:
    """Generate timestamp string for current time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def add_timestamp_to_frame(frame_data: np.ndarray, timestamp: str) -> np.ndarray:
    """
    Add timestamp overlay to frame without mutating input.
    
    Args:
        frame_data: Input frame as numpy array
        timestamp: Timestamp string to overlay
        
    Returns:
        New frame with timestamp overlay
    """
    # Create copy to avoid mutation
    result = frame_data.copy()
    
    # Add timestamp overlay
    cv2.putText(
        result,
        timestamp,
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (255, 255, 255),
        2,
        cv2.LINE_AA
    )
    
    return result


def encode_frame_to_jpeg(frame_data: np.ndarray) -> bytes:
    """
    Encode frame as JPEG bytes.
    
    Args:
        frame_data: Frame as numpy array
        
    Returns:
        JPEG encoded bytes
    """
    success, buffer = cv2.imencode('.jpg', frame_data)
    if not success:
        raise ValueError("Failed to encode frame as JPEG")
    return buffer.tobytes()


def decode_jpeg_to_frame(jpeg_data: bytes) -> np.ndarray:
    """
    Decode JPEG bytes to frame.
    
    Args:
        jpeg_data: JPEG encoded bytes
        
    Returns:
        Frame as numpy array
    """
    frame = cv2.imdecode(
        np.frombuffer(jpeg_data, np.uint8),
        cv2.IMREAD_COLOR
    )
    if frame is None:
        raise ValueError("Failed to decode JPEG data")
    return frame


def create_mjpeg_chunk(jpeg_data: bytes) -> bytes:
    """
    Create MJPEG stream chunk from JPEG data.
    
    Args:
        jpeg_data: JPEG encoded frame
        
    Returns:
        MJPEG stream chunk with headers
    """
    return (
        b'--frame\r\n'
        b'Content-Type: image/jpeg\r\n\r\n' + 
        jpeg_data + 
        b'\r\n'
    )


def clamp_value(value: Union[float, int], min_val: Union[float, int], max_val: Union[float, int]) -> Union[float, int]:
    """
    Clamp a value between min and max bounds.
    
    Args:
        value: Value to clamp
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        
    Returns:
        Clamped value
    """
    return max(min_val, min(value, max_val))


def validate_control_value(value: Union[float, int, bool], control_type: str, 
                          min_val: Optional[Union[float, int]] = None, 
                          max_val: Optional[Union[float, int]] = None) -> Union[float, int, bool]:
    """
    Validate and normalize a control value based on its type and constraints.
    
    Args:
        value: Input value to validate
        control_type: Type of control ('slider', 'toggle', 'select')
        min_val: Minimum value for numeric controls
        max_val: Maximum value for numeric controls
        
    Returns:
        Validated and normalized value
    """
    if control_type == 'toggle':
        return bool(value)
    elif control_type in ('slider', 'select'):
        if min_val is not None and max_val is not None:
            return clamp_value(value, min_val, max_val)
        return value
    return value


def parse_colour_gains(red_gain: float, blue_gain: float) -> Tuple[float, float]:
    """
    Parse and validate colour gain values.
    
    Args:
        red_gain: Red channel gain
        blue_gain: Blue channel gain
        
    Returns:
        Tuple of validated (red_gain, blue_gain)
    """
    red_clamped = clamp_value(red_gain, 0.0, 32.0)
    blue_clamped = clamp_value(blue_gain, 0.0, 32.0)
    return (red_clamped, blue_clamped)


def calculate_exposure_compensation(ev_value: float, base_exposure: int) -> int:
    """
    Calculate adjusted exposure time based on EV compensation.
    
    Args:
        ev_value: Exposure value compensation (-8 to +8)
        base_exposure: Base exposure time in microseconds
        
    Returns:
        Adjusted exposure time
    """
    clamped_ev = clamp_value(ev_value, -8.0, 8.0)
    multiplier = 2.0 ** clamped_ev
    adjusted = int(base_exposure * multiplier)
    return clamp_value(adjusted, 100, 10000000)


def normalize_frame_duration(min_duration: int, max_duration: int) -> Tuple[int, int]:
    """
    Normalize and validate frame duration limits.
    
    Args:
        min_duration: Minimum frame duration in microseconds
        max_duration: Maximum frame duration in microseconds
        
    Returns:
        Tuple of (min, max) validated durations
    """
    min_clamped = clamp_value(min_duration, 1000, 1000000)
    max_clamped = clamp_value(max_duration, min_clamped, 10000000)
    return (min_clamped, max_clamped)


def prepare_frame_for_motion_detection(frame: np.ndarray, blur_size: int) -> np.ndarray:
    """
    Prepare frame for motion detection by converting to grayscale and blurring.
    
    Args:
        frame: Input frame as numpy array
        blur_size: Gaussian blur kernel size (must be odd)
        
    Returns:
        Processed grayscale blurred frame
    """
    # Ensure blur_size is odd
    blur_size = blur_size if blur_size % 2 == 1 else blur_size + 1
    
    # Convert to grayscale
    if len(frame.shape) == 3:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    else:
        gray = frame.copy()
    
    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (blur_size, blur_size), 0)
    
    return blurred


def calculate_frame_difference(frame1: np.ndarray, frame2: np.ndarray, 
                              threshold: int) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate absolute difference between two frames and apply threshold.
    
    Args:
        frame1: First frame (grayscale)
        frame2: Second frame (grayscale)
        threshold: Binary threshold for motion detection
        
    Returns:
        Tuple of (difference frame, thresholded binary frame)
    """
    # Calculate absolute difference
    frame_diff = cv2.absdiff(frame1, frame2)
    
    # Apply threshold to get binary image
    _, thresh = cv2.threshold(frame_diff, threshold, 255, cv2.THRESH_BINARY)
    
    return frame_diff, thresh


def detect_motion_contours(binary_frame: np.ndarray, min_area: int) -> List[np.ndarray]:
    """
    Find contours in binary frame that exceed minimum area.
    
    Args:
        binary_frame: Binary thresholded frame
        min_area: Minimum contour area to consider as motion
        
    Returns:
        List of contours that exceed minimum area
    """
    # Find all contours
    contours, _ = cv2.findContours(
        binary_frame.copy(),
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )
    
    # Filter contours by area
    significant_contours = [
        contour for contour in contours
        if cv2.contourArea(contour) >= min_area
    ]
    
    return significant_contours


def calculate_motion_metrics(contours: List[np.ndarray], 
                            frame_shape: Tuple[int, int]) -> Tuple[float, int, float]:
    """
    Calculate motion metrics from detected contours.
    
    Args:
        contours: List of motion contours
        frame_shape: Shape of the frame (height, width)
        
    Returns:
        Tuple of (motion_score, total_area, frame_diff_percentage)
    """
    if not contours:
        return 0.0, 0, 0.0
    
    # Calculate total motion area
    total_area = sum(cv2.contourArea(contour) for contour in contours)
    
    # Calculate frame coverage percentage
    frame_area = frame_shape[0] * frame_shape[1]
    frame_diff_percentage = (total_area / frame_area) * 100 if frame_area > 0 else 0.0
    
    # Calculate motion score (0-1 scale)
    # Combines area coverage and number of motion regions
    area_score = min(frame_diff_percentage / 10, 1.0)  # Max at 10% coverage
    contour_score = min(len(contours) / 10, 1.0)  # Max at 10 contours
    motion_score = (area_score * 0.7 + contour_score * 0.3)  # Weighted average
    
    return motion_score, int(total_area), frame_diff_percentage


def should_trigger_motion_event(motion_score: float, 
                               config: MotionDetectionConfig,
                               time_since_last_trigger: float) -> bool:
    """
    Determine if motion event should trigger notification.
    
    Args:
        motion_score: Current motion score (0-1)
        config: Motion detection configuration
        time_since_last_trigger: Seconds since last triggered event
        
    Returns:
        True if event should trigger notification
    """
    # Check if motion detection is enabled
    if not config.enabled:
        return False
    
    # Check if motion exceeds sensitivity threshold
    if motion_score < config.sensitivity:
        return False
    
    # Check cooldown period
    if time_since_last_trigger < config.cooldown_seconds:
        return False
    
    return True


def create_motion_event(timestamp: str, motion_score: float, 
                       total_area: int, frame_diff_percentage: float,
                       triggered: bool) -> MotionEvent:
    """
    Create an immutable motion event from detection results.
    
    Args:
        timestamp: Event timestamp
        motion_score: Motion score (0-1)
        total_area: Total motion area in pixels
        frame_diff_percentage: Percentage of frame with motion
        triggered: Whether this event triggered a notification
        
    Returns:
        Immutable MotionEvent instance
    """
    return MotionEvent(
        timestamp=timestamp,
        motion_score=motion_score,
        area=total_area,
        frame_diff_percentage=frame_diff_percentage,
        triggered=triggered
    )


def detect_motion_between_frames(current_frame: np.ndarray, 
                                previous_frame: np.ndarray,
                                config: MotionDetectionConfig) -> Tuple[float, int, float]:
    """
    Perform complete motion detection between two frames.
    
    Args:
        current_frame: Current frame
        previous_frame: Previous frame
        config: Motion detection configuration
        
    Returns:
        Tuple of (motion_score, total_area, frame_diff_percentage)
    """
    # Prepare frames for comparison
    current_processed = prepare_frame_for_motion_detection(
        current_frame, config.blur_size
    )
    previous_processed = prepare_frame_for_motion_detection(
        previous_frame, config.blur_size
    )
    
    # Calculate difference
    _, binary_diff = calculate_frame_difference(
        current_processed, previous_processed, config.threshold
    )
    
    # Find motion contours
    contours = detect_motion_contours(binary_diff, config.min_area)
    
    # Calculate metrics
    motion_score, total_area, frame_diff_percentage = calculate_motion_metrics(
        contours, current_processed.shape
    )
    
    return motion_score, total_area, frame_diff_percentage


def camera_controls_to_picamera2_dict(controls: CameraControls) -> Dict[str, Any]:
    """
    Transform CameraControls to dictionary for picamera2, excluding None values.
    
    Args:
        controls: CameraControls instance
        
    Returns:
        Dictionary with picamera2 control names
    """
    result = {}
    
    field_mapping = {
        'brightness': 'Brightness',
        'contrast': 'Contrast',
        'saturation': 'Saturation',
        'sharpness': 'Sharpness',
        'exposure_time': 'ExposureTime',
        'analogue_gain': 'AnalogueGain',
        'exposure_value': 'ExposureValue',
        'ae_enable': 'AeEnable',
        'ae_exposure_mode': 'AeExposureMode',
        'ae_metering_mode': 'AeMeteringMode',
        'awb_enable': 'AwbEnable',
        'awb_mode': 'AwbMode',
        'colour_gains': 'ColourGains',
        'noise_reduction_mode': 'NoiseReductionMode',
        'frame_duration_limits': 'FrameDurationLimits'
    }
    
    for field_name, control_name in field_mapping.items():
        value = getattr(controls, field_name)
        if value is not None:
            result[control_name] = value
            
    return result


def camera_preset_to_controls_dict(preset: CameraPreset) -> Dict[str, Any]:
    """
    Transform CameraPreset to dictionary for picamera2 controls, excluding None values.
    
    Args:
        preset: CameraPreset instance
        
    Returns:
        Dictionary with picamera2 control names
    """
    result = {}
    
    field_mapping = {
        'exposure_time': 'ExposureTime',
        'analogue_gain': 'AnalogueGain',
        'awb_mode': 'AwbMode',
        'brightness': 'Brightness',
        'contrast': 'Contrast',
        'saturation': 'Saturation',
        'sharpness': 'Sharpness',
        'hdr_mode': 'HdrMode',
        'ae_exposure_mode': 'AeExposureMode',
        'ae_metering_mode': 'AeMeteringMode'
    }
    
    for field_name, control_name in field_mapping.items():
        value = getattr(preset, field_name)
        if value is not None:
            result[control_name] = value
            
    return result