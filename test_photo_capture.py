#!/usr/bin/env python3
"""Test the photo capture functionality."""

import sys
import os

# Add server directory to path
sys.path.insert(0, 'server')

try:
    from services import CameraService
    from mock_camera import MockPicamera2
    
    print("Testing photo capture with mock camera...")
    print("-" * 40)
    
    # Initialize camera service with mock camera
    camera_service = CameraService(camera_factory=MockPicamera2)
    
    # Initialize camera
    init_result = camera_service.initialize()
    if init_result.is_success:
        print("✓ Camera initialized successfully")
    else:
        print(f"✗ Failed to initialize camera: {init_result.error}")
        sys.exit(1)
    
    # Capture a photo
    photo_result = camera_service.capture_photo()
    if photo_result.is_success:
        print(f"✓ Photo captured successfully: {photo_result.value}")
        
        # Check if file exists
        photo_path = os.path.join("photos", photo_result.value)
        if os.path.exists(photo_path):
            file_size = os.path.getsize(photo_path)
            print(f"✓ Photo file exists at {photo_path}")
            print(f"  File size: {file_size:,} bytes")
        else:
            print(f"✗ Photo file not found at {photo_path}")
    else:
        print(f"✗ Failed to capture photo: {photo_result.error}")
    
    # Cleanup
    camera_service.cleanup()
    print("✓ Camera cleaned up")
    
    print("-" * 40)
    print("Photo capture test completed!")
    
except ImportError as e:
    print(f"Import error: {e}")
    print("Note: This test requires the mock camera implementation.")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()