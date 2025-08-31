"""Service layer for camera and streaming operations."""

import io
import time
import logging
from typing import Optional, Generator, Union, Tuple

try:
    from picamera2 import Picamera2
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("PiCamera2 not available, using mock camera")
    from mock_camera import MockPicamera2 as Picamera2

from models import CameraPreset, Frame, CameraControls, ControlMetadata
from calculations import camera_preset_to_controls_dict
from result import Result, StringResult
from calculations import (
    create_timestamp,
    add_timestamp_to_frame,
    encode_frame_to_jpeg,
    decode_jpeg_to_frame,
    create_mjpeg_chunk,
    validate_control_value,
    parse_colour_gains
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
    
    def apply_preset(self, preset: Union[CameraPreset, str]) -> StringResult[str]:
        """
        Apply camera settings from preset.
        
        Args:
            preset: Camera preset object or preset name string
            
        Returns:
            Result with success message or error
        """
        if not self._initialized:
            return Result.failure("Camera not initialized")
        
        # Handle string preset names
        if isinstance(preset, str):
            from config import get_default_presets
            presets = get_default_presets()
            if preset not in presets:
                return Result.failure(f"Unknown preset: {preset}")
            preset_obj = presets[preset]
            preset_name = preset
        else:
            preset_obj = preset
            preset_name = preset.name
            
        try:
            controls = camera_preset_to_controls_dict(preset_obj)
            self._camera.set_controls(controls)
            self._current_preset = preset_obj
            logger.info(f"Applied camera preset: {preset_name}")
            return Result.success(f"Applied {preset_name} preset successfully")
        except Exception as e:
            logger.error(f"Failed to apply preset {preset_name}: {e}")
            return Result.failure(f"Failed to apply preset: {str(e)}")
    
    def update_control(self, control_name: str, value: Union[float, int, bool, Tuple]) -> None:
        """
        Update a single camera control.
        
        Args:
            control_name: Name of the control to update
            value: New value for the control
            
        Raises:
            RuntimeError: If camera not initialized
            ValueError: If control name is invalid
        """
        if not self._initialized:
            raise RuntimeError("Camera not initialized")
        
        # Map friendly names to PiCamera2 control names
        control_mapping = {
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
        
        if control_name not in control_mapping:
            raise ValueError(f"Unknown control: {control_name}")
        
        try:
            picamera_control = control_mapping[control_name]
            self._camera.set_controls({picamera_control: value})
            logger.info(f"Updated {control_name} to {value}")
        except Exception as e:
            logger.error(f"Failed to update {control_name}: {e}")
            raise RuntimeError(f"Failed to update control: {e}")
    
    def get_control_value(self, control_name: str) -> Optional[Union[float, int, bool, Tuple]]:
        """
        Get current value of a camera control.
        
        Args:
            control_name: Name of the control
            
        Returns:
            Current value of the control, or None if not available
        """
        if not self._initialized:
            return None
        
        try:
            # Get current controls from camera
            controls = self._camera.capture_metadata()
            
            control_mapping = {
                'brightness': 'Brightness',
                'contrast': 'Contrast',
                'saturation': 'Saturation',
                'sharpness': 'Sharpness',
                'exposure_time': 'ExposureTime',
                'analogue_gain': 'AnalogueGain',
                'ae_enable': 'AeEnable',
                'ae_exposure_mode': 'AeExposureMode',
                'ae_metering_mode': 'AeMeteringMode',
                'awb_enable': 'AwbEnable',
                'awb_mode': 'AwbMode',
                'colour_gains': 'ColourGains',
                'noise_reduction_mode': 'NoiseReductionMode'
            }
            
            if control_name in control_mapping:
                picamera_control = control_mapping[control_name]
                return controls.get(picamera_control)
        except Exception as e:
            logger.error(f"Failed to get control value for {control_name}: {e}")
        
        return None
    
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


class ControlManager:
    """Manages individual camera control operations."""
    
    def __init__(self, camera_service: CameraService):
        """
        Initialize control manager.
        
        Args:
            camera_service: Camera service instance
        """
        self._camera_service = camera_service
        self._control_metadata = self._initialize_control_metadata()
    
    def _initialize_control_metadata(self) -> dict:
        """Initialize control metadata definitions."""
        return {
            # Image Quality Controls
            'brightness': ControlMetadata(
                name='brightness',
                display_name='Brightness',
                control_type='slider',
                min_value=-1.0,
                max_value=1.0,
                step=0.1,
                default_value=0.0,
                category='Image Quality'
            ),
            'contrast': ControlMetadata(
                name='contrast',
                display_name='Contrast',
                control_type='slider',
                min_value=0.0,
                max_value=32.0,
                step=0.5,
                default_value=1.0,
                category='Image Quality'
            ),
            'saturation': ControlMetadata(
                name='saturation',
                display_name='Saturation',
                control_type='slider',
                min_value=0.0,
                max_value=32.0,
                step=0.5,
                default_value=1.0,
                category='Image Quality'
            ),
            'sharpness': ControlMetadata(
                name='sharpness',
                display_name='Sharpness',
                control_type='slider',
                min_value=0.0,
                max_value=16.0,
                step=0.5,
                default_value=1.0,
                category='Image Quality'
            ),
            
            # Exposure Controls
            'exposure_time': ControlMetadata(
                name='exposure_time',
                display_name='Exposure Time',
                control_type='slider',
                min_value=1000,
                max_value=1000000,
                step=1000,
                default_value=33333,
                unit='μs',
                category='Exposure'
            ),
            'analogue_gain': ControlMetadata(
                name='analogue_gain',
                display_name='ISO/Gain',
                control_type='slider',
                min_value=1.0,
                max_value=16.0,
                step=0.5,
                default_value=1.0,
                category='Exposure'
            ),
            'exposure_value': ControlMetadata(
                name='exposure_value',
                display_name='EV Compensation',
                control_type='slider',
                min_value=-8.0,
                max_value=8.0,
                step=0.5,
                default_value=0.0,
                unit='EV',
                category='Exposure'
            ),
            'ae_enable': ControlMetadata(
                name='ae_enable',
                display_name='Auto Exposure',
                control_type='toggle',
                default_value=True,
                category='Exposure'
            ),
            'ae_exposure_mode': ControlMetadata(
                name='ae_exposure_mode',
                display_name='AE Mode',
                control_type='select',
                options={
                    0: 'Normal',
                    1: 'Short',
                    2: 'Long',
                    3: 'Custom'
                },
                default_value=0,
                category='Exposure'
            ),
            'ae_metering_mode': ControlMetadata(
                name='ae_metering_mode',
                display_name='Metering Mode',
                control_type='select',
                options={
                    0: 'Centre Weighted',
                    1: 'Spot',
                    2: 'Matrix',
                    3: 'Custom'
                },
                default_value=0,
                category='Exposure'
            ),
            
            # White Balance Controls
            'awb_enable': ControlMetadata(
                name='awb_enable',
                display_name='Auto White Balance',
                control_type='toggle',
                default_value=True,
                category='White Balance'
            ),
            'awb_mode': ControlMetadata(
                name='awb_mode',
                display_name='WB Mode',
                control_type='select',
                options={
                    0: 'Auto',
                    1: 'Incandescent',
                    2: 'Tungsten',
                    3: 'Fluorescent',
                    4: 'Indoor',
                    5: 'Daylight',
                    6: 'Cloudy',
                    7: 'Custom'
                },
                default_value=0,
                category='White Balance'
            ),
            
            # Advanced Controls
            'noise_reduction_mode': ControlMetadata(
                name='noise_reduction_mode',
                display_name='Noise Reduction',
                control_type='select',
                options={
                    0: 'Off',
                    1: 'Fast',
                    2: 'High Quality',
                    3: 'Minimal',
                    4: 'ZSL'
                },
                default_value=1,
                category='Advanced'
            )
        }
    
    def get_control_metadata(self, control_name: str) -> Optional[ControlMetadata]:
        """Get metadata for a specific control."""
        return self._control_metadata.get(control_name)
    
    def get_all_control_metadata(self) -> dict:
        """Get metadata for all controls."""
        return self._control_metadata
    
    def get_controls_by_category(self) -> dict:
        """Get controls grouped by category."""
        categories = {}
        for control_name, metadata in self._control_metadata.items():
            category = metadata.category
            if category not in categories:
                categories[category] = []
            categories[category].append(metadata)
        return categories
    
    def update_control(self, control_name: str, value: Union[float, int, bool]) -> dict:
        """
        Update a camera control with validation.
        
        Args:
            control_name: Name of the control
            value: New value
            
        Returns:
            Result dictionary with status
        """
        metadata = self.get_control_metadata(control_name)
        if not metadata:
            return {
                "success": False,
                "error": f"Unknown control: {control_name}"
            }
        
        try:
            # Validate value based on control type
            validated_value = validate_control_value(
                value, 
                metadata.control_type,
                metadata.min_value,
                metadata.max_value
            )
            
            # Special handling for colour gains
            if control_name == 'colour_gains' and isinstance(value, (list, tuple)):
                validated_value = parse_colour_gains(value[0], value[1])
            
            # Apply the control
            self._camera_service.update_control(control_name, validated_value)
            
            return {
                "success": True,
                "message": f"Updated {metadata.display_name} to {validated_value}",
                "value": validated_value
            }
        except Exception as e:
            logger.error(f"Failed to update control {control_name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_control_value(self, control_name: str) -> dict:
        """
        Get current value of a control.
        
        Args:
            control_name: Name of the control
            
        Returns:
            Result dictionary with value
        """
        metadata = self.get_control_metadata(control_name)
        if not metadata:
            return {
                "success": False,
                "error": f"Unknown control: {control_name}"
            }
        
        try:
            value = self._camera_service.get_control_value(control_name)
            return {
                "success": True,
                "control": control_name,
                "value": value,
                "metadata": {
                    "display_name": metadata.display_name,
                    "type": metadata.control_type,
                    "category": metadata.category
                }
            }
        except Exception as e:
            logger.error(f"Failed to get control value for {control_name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }


