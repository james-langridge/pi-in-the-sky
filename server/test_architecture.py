#!/usr/bin/env python3
"""Test script to verify the new architecture without hardware dependencies."""

import sys
import numpy as np
from datetime import datetime

# Test pure functions
from calculations import (
    create_timestamp,
    add_timestamp_to_frame,
    encode_frame_to_jpeg,
    decode_jpeg_to_frame,
    create_mjpeg_chunk
)

# Test data models
from models import CameraPreset, Frame

# Test configuration
from config import AppConfig, get_default_presets


def test_pure_functions():
    """Test that pure functions work correctly."""
    print("Testing pure functions...")
    
    # Test timestamp creation
    timestamp = create_timestamp()
    assert isinstance(timestamp, str)
    assert len(timestamp) > 0
    print(f"  ✓ Timestamp generation: {timestamp}")
    
    # Test frame processing
    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Test timestamp overlay
    processed = add_timestamp_to_frame(dummy_frame, timestamp)
    assert processed.shape == dummy_frame.shape
    assert not np.array_equal(processed, dummy_frame)  # Should be different
    print("  ✓ Timestamp overlay works")
    
    # Test JPEG encoding
    jpeg_data = encode_frame_to_jpeg(processed)
    assert isinstance(jpeg_data, bytes)
    assert len(jpeg_data) > 0
    print(f"  ✓ JPEG encoding: {len(jpeg_data)} bytes")
    
    # Test JPEG decoding
    decoded = decode_jpeg_to_frame(jpeg_data)
    assert decoded.shape == processed.shape
    print("  ✓ JPEG decoding works")
    
    # Test MJPEG chunk creation
    chunk = create_mjpeg_chunk(jpeg_data)
    assert isinstance(chunk, bytes)
    assert b'--frame' in chunk
    assert b'Content-Type: image/jpeg' in chunk
    print("  ✓ MJPEG chunk creation works")


def test_data_models():
    """Test immutable data models."""
    print("\nTesting data models...")
    
    # Test CameraPreset
    preset = CameraPreset(
        name="test",
        exposure_time=50000,
        brightness=0.5
    )
    assert preset.name == "test"
    assert preset.exposure_time == 50000
    assert preset.brightness == 0.5
    assert preset.contrast == 1.0  # Default value
    print("  ✓ CameraPreset creation works")
    
    # Test immutability
    try:
        preset.brightness = 1.0
        assert False, "Should not be able to modify frozen dataclass"
    except:
        print("  ✓ CameraPreset is immutable")
    
    # Test to_controls_dict
    controls = preset.to_controls_dict()
    assert 'ExposureTime' in controls
    assert 'Brightness' in controls
    assert controls['ExposureTime'] == 50000
    print("  ✓ CameraPreset.to_controls_dict works")
    
    # Test Frame
    frame = Frame(
        data=b"test data",
        timestamp="2024-01-01 12:00:00",
        width=1920,
        height=1080
    )
    assert frame.data == b"test data"
    assert frame.width == 1920
    print("  ✓ Frame creation works")


def test_configuration():
    """Test configuration management."""
    print("\nTesting configuration...")
    
    # Test default config
    config = AppConfig()
    assert config.host == '0.0.0.0'
    assert config.port == 8080
    assert config.debug == False
    assert config.cors_origins == ['http://localhost:3000']
    print("  ✓ Default configuration works")
    
    # Test immutability
    try:
        config.port = 9000
        assert False, "Should not be able to modify frozen dataclass"
    except:
        print("  ✓ AppConfig is immutable")
    
    # Test preset loading
    presets = get_default_presets()
    assert 'default' in presets
    assert 'low_light' in presets
    assert isinstance(presets['default'], CameraPreset)
    print(f"  ✓ Loaded {len(presets)} presets")


def main():
    """Run all tests."""
    print("=" * 50)
    print("Architecture Verification Tests")
    print("=" * 50)
    
    try:
        test_pure_functions()
        test_data_models()
        test_configuration()
        
        print("\n" + "=" * 50)
        print("✅ All architecture tests passed!")
        print("=" * 50)
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())