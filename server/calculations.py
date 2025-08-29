"""Pure functions for frame processing and calculations."""

from datetime import datetime
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