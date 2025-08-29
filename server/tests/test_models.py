"""Tests for data models and configuration."""

import pytest
from dataclasses import FrozenInstanceError

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import (
    CameraPreset,
    Frame,
    MotionDetectionConfig,
    MotionEvent,
    PushSubscription
)
from config import AppConfig, get_default_presets


class TestCameraPreset:
    """Test CameraPreset immutable data model."""
    
    def test_create_preset_with_defaults(self):
        """Should create preset with default values."""
        preset = CameraPreset(name="test")
        
        assert preset.name == "test"
        assert preset.exposure_time == 0
        assert preset.brightness == 0.0
        assert preset.contrast == 1.0
        assert preset.saturation == 1.0
    
    def test_create_preset_with_values(self):
        """Should create preset with specified values."""
        preset = CameraPreset(
            name="custom",
            exposure_time=50000,
            brightness=0.5,
            analogue_gain=2.0
        )
        
        assert preset.exposure_time == 50000
        assert preset.brightness == 0.5
        assert preset.analogue_gain == 2.0
    
    def test_preset_immutability(self):
        """Should not allow modification after creation."""
        preset = CameraPreset(name="test")
        
        with pytest.raises(FrozenInstanceError):
            preset.brightness = 1.0
    
    def test_to_controls_dict(self):
        """Should convert to PiCamera2 controls format."""
        preset = CameraPreset(
            name="test",
            exposure_time=50000,
            brightness=0.5,
            contrast=1.5,
            analogue_gain=2.0
        )
        
        controls = preset.to_controls_dict()
        
        assert controls['ExposureTime'] == 50000
        assert controls['Brightness'] == 0.5
        assert controls['Contrast'] == 1.5
        assert controls['AnalogueGain'] == 2.0
        # Should not include default values
        assert 'Saturation' not in controls  # Default is 1.0


class TestFrame:
    """Test Frame data model."""
    
    def test_create_frame(self):
        """Should create frame with required fields."""
        frame = Frame(
            data=b"test_data",
            timestamp="2024-01-01 12:00:00",
            width=1920,
            height=1080
        )
        
        assert frame.data == b"test_data"
        assert frame.timestamp == "2024-01-01 12:00:00"
        assert frame.width == 1920
        assert frame.height == 1080
    
    def test_frame_immutability(self):
        """Frame should be immutable."""
        frame = Frame(
            data=b"test",
            timestamp="2024-01-01",
            width=640,
            height=480
        )
        
        with pytest.raises(FrozenInstanceError):
            frame.width = 1920


class TestMotionDetectionConfig:
    """Test motion detection configuration model."""
    
    def test_default_config(self):
        """Should have sensible defaults."""
        config = MotionDetectionConfig()
        
        assert config.enabled == False
        assert config.blur_size == 21
        assert config.threshold == 25
        assert config.min_area == 500
        assert config.trigger_threshold == 0.02
        assert config.cooldown_seconds == 30
    
    def test_custom_config(self):
        """Should accept custom values."""
        config = MotionDetectionConfig(
            enabled=True,
            threshold=50,
            min_area=1000
        )
        
        assert config.enabled == True
        assert config.threshold == 50
        assert config.min_area == 1000
        # Other values should be defaults
        assert config.blur_size == 21


class TestMotionEvent:
    """Test motion event model."""
    
    def test_create_event(self):
        """Should create immutable motion event."""
        event = MotionEvent(
            timestamp="2024-01-01 12:00:00",
            motion_score=0.75,
            contour_count=3,
            total_motion_area=1500
        )
        
        assert event.timestamp == "2024-01-01 12:00:00"
        assert event.motion_score == 0.75
        assert event.contour_count == 3
        assert event.total_motion_area == 1500
    
    def test_event_immutability(self):
        """Event should be immutable."""
        event = MotionEvent(
            timestamp="2024-01-01",
            motion_score=0.5,
            contour_count=1,
            total_motion_area=100
        )
        
        with pytest.raises(FrozenInstanceError):
            event.motion_score = 0.9


class TestPushSubscription:
    """Test push subscription model."""
    
    def test_create_subscription(self):
        """Should create subscription with all fields."""
        sub = PushSubscription(
            id="test-sub-1",
            endpoint="https://example.com/push",
            p256dh="test_key",
            auth="test_auth",
            created_at="2024-01-01 12:00:00"
        )
        
        assert sub.id == "test-sub-1"
        assert sub.endpoint == "https://example.com/push"
        assert sub.p256dh == "test_key"
        assert sub.auth == "test_auth"
        assert sub.created_at == "2024-01-01 12:00:00"


class TestAppConfig:
    """Test application configuration."""
    
    def test_default_config(self):
        """Should have sensible defaults."""
        config = AppConfig()
        
        assert config.host == '0.0.0.0'
        assert config.port == 8080
        assert config.debug == False
        assert config.cors_origins == ['http://localhost:3000']
        assert config.frame_delay == 0.1
    
    def test_config_immutability(self):
        """Config should be immutable."""
        config = AppConfig()
        
        with pytest.raises(FrozenInstanceError):
            config.port = 9000
    
    def test_default_presets(self):
        """Should load default camera presets."""
        presets = get_default_presets()
        
        # Should have essential presets
        assert 'default' in presets
        assert 'low_light' in presets
        assert 'bright' in presets
        assert 'night' in presets
        
        # All should be CameraPreset instances
        for preset in presets.values():
            assert isinstance(preset, CameraPreset)
        
        # Verify a few preset properties
        assert presets['default'].name == 'default'
        assert presets['low_light'].exposure_time == 100000
        assert presets['night'].analogue_gain == 8.0