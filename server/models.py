"""Immutable data models for camera configuration."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CameraPreset:
    """Immutable camera configuration preset."""
    
    name: str
    exposure_time: Optional[int] = None
    analogue_gain: Optional[float] = None
    awb_mode: Optional[int] = None
    brightness: float = 0.0
    contrast: float = 1.0
    saturation: float = 1.0
    sharpness: float = 1.0
    hdr_mode: Optional[int] = None
    ae_exposure_mode: Optional[int] = None
    ae_metering_mode: Optional[int] = None
    
    def to_controls_dict(self) -> dict:
        """Convert to dictionary for picamera2 controls, excluding None values."""
        controls = {}
        
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
            value = getattr(self, field_name)
            if value is not None:
                controls[control_name] = value
                
        return controls


@dataclass(frozen=True)
class Frame:
    """Immutable frame data."""
    
    data: bytes
    timestamp: str
    width: int
    height: int