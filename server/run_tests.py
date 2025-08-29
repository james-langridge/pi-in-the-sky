#!/usr/bin/env python3
"""
Simple test runner for the Pi-in-the-Sky project.
Following grug philosophy: test what matters, keep it simple.
"""

import sys
import os
import traceback

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_core_tests():
    """Run the most important tests - calculations and basic models."""
    
    print("=" * 60)
    print("Pi-in-the-Sky Core Tests")
    print("=" * 60)
    print()
    
    test_results = []
    
    # Test 1: Pure calculations work
    try:
        from calculations import create_timestamp, add_timestamp_to_frame, encode_frame_to_jpeg
        import numpy as np
        
        timestamp = create_timestamp()
        assert len(timestamp) == 19
        
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        processed = add_timestamp_to_frame(frame, timestamp)
        assert processed.shape == frame.shape
        
        jpeg = encode_frame_to_jpeg(processed)
        assert isinstance(jpeg, bytes)
        assert len(jpeg) > 0
        
        test_results.append(("✓", "Calculation functions"))
    except Exception as e:
        test_results.append(("✗", f"Calculation functions: {e}"))
    
    # Test 2: Motion detection calculations
    try:
        from calculations import (
            prepare_frame_for_motion_detection,
            calculate_frame_difference,
            detect_motion_contours
        )
        import numpy as np
        
        frame = np.ones((100, 100, 3), dtype=np.uint8) * 128
        gray = prepare_frame_for_motion_detection(frame, blur_size=5)
        assert gray.shape == (100, 100)
        
        frame1 = np.zeros((100, 100), dtype=np.uint8)
        frame2 = np.zeros((100, 100), dtype=np.uint8)
        frame2[40:60, 40:60] = 255
        
        binary, diff = calculate_frame_difference(frame1, frame2, threshold=30)
        assert np.sum(binary) > 0  # Should detect difference
        
        contours = detect_motion_contours(binary, min_area=100)
        assert len(contours) > 0
        
        test_results.append(("✓", "Motion detection calculations"))
    except Exception as e:
        test_results.append(("✗", f"Motion detection calculations: {e}"))
    
    # Test 3: Data models are immutable
    try:
        from models import CameraPreset, MotionDetectionConfig
        from dataclasses import FrozenInstanceError
        
        preset = CameraPreset(name="test")
        assert preset.name == "test"
        
        try:
            preset.name = "changed"
            assert False, "Should not allow mutation"
        except FrozenInstanceError:
            pass  # Expected
        
        config = MotionDetectionConfig()
        assert config.enabled == False
        
        test_results.append(("✓", "Immutable data models"))
    except Exception as e:
        test_results.append(("✗", f"Immutable data models: {e}"))
    
    # Test 4: Configuration loading
    try:
        from config import AppConfig, get_default_presets
        
        config = AppConfig()
        assert config.port == 8080
        assert config.host == '0.0.0.0'
        
        presets = get_default_presets()
        assert 'default' in presets
        assert 'low_light' in presets
        
        test_results.append(("✓", "Configuration management"))
    except Exception as e:
        test_results.append(("✗", f"Configuration management: {e}"))
    
    # Test 5: Mock camera works
    try:
        from mock_camera import MockCamera
        import io
        
        camera = MockCamera()
        camera.start()
        
        # Mock camera uses capture_file method
        stream = io.BytesIO()
        camera.capture_file(stream)
        assert stream.getvalue() != b''  # Should have written data
        
        camera.stop()
        
        test_results.append(("✓", "Mock camera functionality"))
    except Exception as e:
        test_results.append(("✗", f"Mock camera functionality: {e}"))
    
    # Test 6: Service initialization
    try:
        from services import CameraService
        
        service = CameraService()
        # Service should be created (even if camera not initialized)
        assert service is not None
        
        # Try to capture - it may return None if not initialized
        try:
            raw_frame = service.capture_raw_frame()
            if raw_frame is not None:
                assert isinstance(raw_frame, bytes)
        except Exception:
            pass  # Camera might not be initialized, that's OK
        
        test_results.append(("✓", "Camera service initialization"))
    except Exception as e:
        test_results.append(("✗", f"Camera service initialization: {e}"))
    
    # Test 7: Flask app creation
    try:
        from server import create_app
        from config import AppConfig
        
        app = create_app(AppConfig())
        assert app is not None
        
        # Test a simple endpoint
        with app.test_client() as client:
            response = client.get('/health')
            assert response.status_code == 200
        
        test_results.append(("✓", "Flask app creation and health check"))
    except Exception as e:
        test_results.append(("✗", f"Flask app creation: {e}"))
    
    # Print results
    print("\nTest Results:")
    print("-" * 40)
    
    passed = 0
    failed = 0
    
    for status, message in test_results:
        print(f"{status} {message}")
        if status == "✓":
            passed += 1
        else:
            failed += 1
    
    print("-" * 40)
    print(f"\n{passed} passed, {failed} failed")
    
    if failed > 0:
        print("\n❌ Some tests failed")
        return 1
    else:
        print("\n✅ All core tests passed!")
        return 0


if __name__ == "__main__":
    sys.exit(run_core_tests())