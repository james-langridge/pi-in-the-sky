"""Pure functions for frame processing and calculations."""

from datetime import datetime
from typing import Union, Tuple, Optional
import cv2
import numpy as np


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