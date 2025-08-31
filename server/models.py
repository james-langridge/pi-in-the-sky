"""Immutable data models for camera configuration."""

from dataclasses import dataclass
from typing import Optional, Union, Tuple
from enum import IntEnum


@dataclass(frozen=True)
class ControlMetadata:
    """Immutable metadata for a camera control."""
    
    name: str
    display_name: str
    control_type: str  # 'slider', 'toggle', 'select'
    min_value: Optional[Union[float, int]] = None
    max_value: Optional[Union[float, int]] = None
    step: Optional[Union[float, int]] = None
    default_value: Optional[Union[float, int, bool]] = None
    options: Optional[dict] = None  # For select controls
    unit: Optional[str] = None
    category: str = "General"


class AeMeteringMode(IntEnum):
    """Auto exposure metering modes."""
    CENTRE_WEIGHTED = 0
    SPOT = 1
    MATRIX = 2
    CUSTOM = 3


class AeExposureMode(IntEnum):
    """Auto exposure modes."""
    NORMAL = 0
    SHORT = 1
    LONG = 2
    CUSTOM = 3


class AwbMode(IntEnum):
    """Auto white balance modes."""
    AUTO = 0
    INCANDESCENT = 1
    TUNGSTEN = 2
    FLUORESCENT = 3
    INDOOR = 4
    DAYLIGHT = 5
    CLOUDY = 6
    CUSTOM = 7


class NoiseReductionMode(IntEnum):
    """Noise reduction modes."""
    OFF = 0
    FAST = 1
    HIGH_QUALITY = 2
    MINIMAL = 3
    ZSL = 4


@dataclass(frozen=True)
class CameraControls:
    """Immutable camera control values."""
    
    # Image Quality
    brightness: Optional[float] = None
    contrast: Optional[float] = None
    saturation: Optional[float] = None
    sharpness: Optional[float] = None
    
    # Exposure
    exposure_time: Optional[int] = None
    analogue_gain: Optional[float] = None
    exposure_value: Optional[float] = None
    ae_enable: Optional[bool] = None
    ae_exposure_mode: Optional[int] = None
    ae_metering_mode: Optional[int] = None
    
    # White Balance
    awb_enable: Optional[bool] = None
    awb_mode: Optional[int] = None
    colour_gains: Optional[Tuple[float, float]] = None
    
    # Advanced
    noise_reduction_mode: Optional[int] = None
    frame_duration_limits: Optional[Tuple[int, int]] = None


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


@dataclass(frozen=True)
class Frame:
    """Immutable frame data."""
    
    data: bytes
    timestamp: str
    width: int
    height: int


@dataclass(frozen=True)
class MotionDetectionConfig:
    """Immutable configuration for motion detection."""
    
    enabled: bool = False
    sensitivity: float = 0.02  # 0-1 scale, lower = more sensitive
    min_area: int = 500  # Minimum contour area in pixels
    cooldown_seconds: int = 30  # Seconds between notifications
    blur_size: int = 21  # Gaussian blur kernel size
    threshold: int = 25  # Binary threshold for motion detection


@dataclass(frozen=True)
class MotionEvent:
    """Immutable motion detection event."""
    
    timestamp: str
    motion_score: float  # 0-1 scale
    area: int  # Total motion area in pixels
    frame_diff_percentage: float  # Percentage of frame with motion
    triggered: bool  # Whether this event triggered a notification


@dataclass(frozen=True)
class PushSubscription:
    """Immutable browser push notification subscription."""
    
    id: str  # Unique subscription ID
    endpoint: str  # Push service endpoint URL
    p256dh: str  # Public key for payload encryption
    auth: str  # Authentication secret
    created_at: str  # ISO format timestamp
    user_agent: Optional[str] = None  # Browser user agent