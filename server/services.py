"""Service layer for camera and streaming operations."""

import io
import time
import logging
from typing import Optional, Generator
from picamera2 import Picamera2

from models import CameraPreset, Frame
from calculations import (
    create_timestamp,
    add_timestamp_to_frame,
    encode_frame_to_jpeg,
    decode_jpeg_to_frame,
    create_mjpeg_chunk
)

logger = logging.getLogger(__name__)


class CameraService:
    """Encapsulates all camera I/O operations."""
    
    def __init__(self, camera_factory=None):
        """
        Initialize camera service.
        
        Args:
            camera_factory: Factory function for creating camera instance,
                          defaults to Picamera2
        """
        self._camera_factory = camera_factory or Picamera2
        self._camera: Optional[Picamera2] = None
        self._current_preset: Optional[CameraPreset] = None
        self._initialized = False
    
    def initialize(self) -> None:
        """Lazy initialization of camera hardware."""
        if self._initialized:
            return
            
        try:
            self._camera = self._camera_factory()
            config = self._camera.create_preview_configuration(
                main={"size": (1920, 1080)}
            )
            self._camera.configure(config)
            self._camera.start()
            self._initialized = True
            logger.info("Camera initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize camera: {e}")
            raise RuntimeError(f"Camera initialization failed: {e}")
    
    def cleanup(self) -> None:
        """Clean up camera resources."""
        if self._camera and self._initialized:
            try:
                self._camera.stop()
                self._camera.close()
                self._initialized = False
                logger.info("Camera cleaned up successfully")
            except Exception as e:
                logger.error(f"Error during camera cleanup: {e}")
    
    def capture_raw_frame(self) -> bytes:
        """
        Capture raw JPEG frame from camera.
        
        Returns:
            JPEG encoded frame bytes
            
        Raises:
            RuntimeError: If camera not initialized
        """
        if not self._initialized:
            raise RuntimeError("Camera not initialized")
            
        stream = io.BytesIO()
        self._camera.capture_file(stream, format='jpeg')
        return stream.getvalue()
    
    def apply_preset(self, preset: CameraPreset) -> None:
        """
        Apply camera settings from preset.
        
        Args:
            preset: Camera preset to apply
            
        Raises:
            RuntimeError: If camera not initialized
        """
        if not self._initialized:
            raise RuntimeError("Camera not initialized")
            
        try:
            controls = preset.to_controls_dict()
            self._camera.set_controls(controls)
            self._current_preset = preset
            logger.info(f"Applied camera preset: {preset.name}")
        except Exception as e:
            logger.error(f"Failed to apply preset {preset.name}: {e}")
            raise RuntimeError(f"Failed to apply preset: {e}")
    
    def capture_frame_with_timestamp(self) -> Frame:
        """
        Capture frame with timestamp overlay.
        
        Returns:
            Frame object with processed image data
        """
        # Action: Capture raw frame
        raw_jpeg = self.capture_raw_frame()
        
        # Calculations: Process frame
        raw_frame = decode_jpeg_to_frame(raw_jpeg)
        timestamp = create_timestamp()
        processed_frame = add_timestamp_to_frame(raw_frame, timestamp)
        jpeg_data = encode_frame_to_jpeg(processed_frame)
        
        # Return immutable result
        return Frame(
            data=jpeg_data,
            timestamp=timestamp,
            width=1920,
            height=1080
        )


class StreamingService:
    """Handles video streaming logic."""
    
    def __init__(self, camera_service: CameraService, frame_delay: float = 0.1):
        """
        Initialize streaming service.
        
        Args:
            camera_service: Camera service instance
            frame_delay: Delay between frames in seconds
        """
        self._camera_service = camera_service
        self._frame_delay = frame_delay
    
    def generate_mjpeg_stream(self) -> Generator[bytes, None, None]:
        """
        Generate MJPEG stream chunks.
        
        Yields:
            MJPEG formatted frame chunks
        """
        while True:
            try:
                # Capture and process frame
                frame = self._camera_service.capture_frame_with_timestamp()
                
                # Create MJPEG chunk
                chunk = create_mjpeg_chunk(frame.data)
                
                yield chunk
                
                # Control frame rate
                time.sleep(self._frame_delay)
                
            except Exception as e:
                logger.error(f"Error generating frame: {e}")
                # Could yield error frame or break
                # For now, wait and retry
                time.sleep(1)


class PresetManager:
    """Manages camera preset application."""
    
    def __init__(self, camera_service: CameraService, presets: dict):
        """
        Initialize preset manager.
        
        Args:
            camera_service: Camera service instance
            presets: Dictionary of preset configurations
        """
        self._camera_service = camera_service
        self._presets = presets
    
    def apply_preset(self, preset_name: str) -> dict:
        """
        Apply a named preset.
        
        Args:
            preset_name: Name of preset to apply
            
        Returns:
            Result dictionary with status and message
        """
        if preset_name not in self._presets:
            return {
                "success": False,
                "error": f"Unknown preset: {preset_name}"
            }
        
        try:
            preset = self._presets[preset_name]
            self._camera_service.apply_preset(preset)
            return {
                "success": True,
                "message": f"Applied {preset_name} preset successfully"
            }
        except Exception as e:
            logger.error(f"Failed to apply preset {preset_name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }