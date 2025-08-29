"""Configuration management for the application."""

import os
from dataclasses import dataclass
from typing import List, Dict
from libcamera import controls

from models import CameraPreset


@dataclass(frozen=True)
class AppConfig:
    """Immutable application configuration."""
    
    host: str = '0.0.0.0'
    port: int = 8080
    debug: bool = False
    cors_origins: List[str] = None
    frame_delay: float = 0.1
    
    def __post_init__(self):
        """Set default values for mutable defaults."""
        if self.cors_origins is None:
            object.__setattr__(self, 'cors_origins', ['http://localhost:3000'])
    
    @classmethod
    def from_env(cls) -> 'AppConfig':
        """
        Create configuration from environment variables.
        
        Returns:
            AppConfig instance with values from environment
        """
        cors_origins_str = os.getenv('CORS_ORIGINS', 'http://localhost:3000')
        cors_origins = [origin.strip() for origin in cors_origins_str.split(',')]
        
        return cls(
            host=os.getenv('HOST', '0.0.0.0'),
            port=int(os.getenv('FLASK_PORT', '8080')),
            debug=os.getenv('FLASK_DEBUG', 'false').lower() == 'true',
            cors_origins=cors_origins,
            frame_delay=float(os.getenv('FRAME_DELAY', '0.1'))
        )


def get_default_presets() -> Dict[str, CameraPreset]:
    """
    Get default camera presets.
    
    Returns:
        Dictionary of preset name to CameraPreset instances
    """
    return {
        'default': CameraPreset(
            name='default',
            exposure_time=None,
            analogue_gain=None,
            awb_mode=controls.AwbModeEnum.Auto,
            brightness=0.0,
            contrast=1.0,
            saturation=1.0,
            sharpness=1.0,
            hdr_mode=controls.HdrModeEnum.Off,
            ae_exposure_mode=controls.AeExposureModeEnum.Normal,
            ae_metering_mode=controls.AeMeteringModeEnum.CentreWeighted
        ),
        'low_light': CameraPreset(
            name='low_light',
            exposure_time=100000,
            analogue_gain=4.0,
            awb_mode=controls.AwbModeEnum.Tungsten,
            brightness=0.1,
            contrast=1.2,
            saturation=1.1,
            sharpness=0.8,
            hdr_mode=controls.HdrModeEnum.Night,
            ae_exposure_mode=controls.AeExposureModeEnum.Long,
            ae_metering_mode=controls.AeMeteringModeEnum.Matrix
        )
    }