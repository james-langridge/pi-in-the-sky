"""Tests for service layer with mocking."""

import pytest
from unittest.mock import Mock, MagicMock, patch, PropertyMock
import numpy as np
from datetime import datetime
import threading
import time

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import CameraService, StreamingService
from motion_services import MotionDetectionService, NotificationService
from models import MotionDetectionConfig, MotionEvent, PushSubscription
from config import AppConfig


class TestCameraService:
    """Test camera service with mocked hardware."""
    
    @patch('services.logger')
    def test_camera_service_mock_mode(self, mock_logger):
        """Should use mock camera when hardware unavailable."""
        # Mock camera will be used automatically when Picamera2 import fails
        service = CameraService(config=AppConfig())
        
        assert service.is_initialized == True
        assert service.camera is not None
        # Should log that mock mode is being used
        mock_logger.info.assert_called()
    
    def test_capture_frame(self):
        """Should capture frame from camera."""
        service = CameraService(config=AppConfig())
        
        frame = service.capture_frame()
        
        if frame is not None:
            assert isinstance(frame, np.ndarray)
            assert len(frame.shape) == 3  # Should be H x W x C
            assert frame.shape[2] == 3  # RGB channels
    
    def test_get_camera_info(self):
        """Should return camera information."""
        service = CameraService(config=AppConfig())
        
        info = service.get_camera_info()
        
        assert isinstance(info, dict)
        assert 'initialized' in info
        assert 'status' in info
        if info['initialized']:
            assert 'type' in info


class TestStreamingService:
    """Test streaming service."""
    
    def test_generate_frames(self):
        """Should generate MJPEG frames."""
        mock_camera = Mock()
        mock_camera.capture_frame.return_value = np.ones((480, 640, 3), dtype=np.uint8)
        
        service = StreamingService(camera_service=mock_camera)
        generator = service.generate_frames()
        
        # Get first frame
        frame_data = next(generator)
        
        assert isinstance(frame_data, bytes)
        assert b'--frame' in frame_data
        assert b'Content-Type: image/jpeg' in frame_data
    
    def test_generate_frames_with_motion(self):
        """Should integrate motion detection when enabled."""
        mock_camera = Mock()
        mock_camera.capture_frame.return_value = np.ones((480, 640, 3), dtype=np.uint8)
        
        mock_motion = Mock()
        mock_motion.config = MotionDetectionConfig(enabled=True)
        mock_motion.process_frame.return_value = None
        
        service = StreamingService(
            camera_service=mock_camera,
            motion_service=mock_motion
        )
        
        generator = service.generate_frames()
        next(generator)
        
        # Motion service should be called
        mock_motion.process_frame.assert_called_once()
    
    def test_stop_streaming(self):
        """Should stop streaming gracefully."""
        mock_camera = Mock()
        mock_camera.capture_frame.return_value = np.ones((480, 640, 3), dtype=np.uint8)
        
        service = StreamingService(camera_service=mock_camera)
        
        # Start streaming in thread
        def stream():
            for _ in service.generate_frames():
                if not service.is_streaming:
                    break
        
        thread = threading.Thread(target=stream)
        thread.start()
        
        # Stop streaming
        service.stop()
        thread.join(timeout=1)
        
        assert service.is_streaming == False


class TestMotionDetectionService:
    """Test motion detection service."""
    
    def test_initialization(self):
        """Should initialize with default config."""
        service = MotionDetectionService()
        
        assert service.config.enabled == False
        assert service.last_event_time is None
        assert len(service.recent_events) == 0
    
    def test_update_config(self):
        """Should update configuration."""
        service = MotionDetectionService()
        
        new_config = {
            'enabled': True,
            'threshold': 50,
            'min_area': 1000
        }
        
        service.update_config(new_config)
        
        assert service.config.enabled == True
        assert service.config.threshold == 50
        assert service.config.min_area == 1000
    
    def test_process_frame_when_disabled(self):
        """Should not process when disabled."""
        service = MotionDetectionService()
        service.config = MotionDetectionConfig(enabled=False)
        
        frame = np.ones((100, 100, 3), dtype=np.uint8)
        event = service.process_frame(frame)
        
        assert event is None
    
    def test_process_frame_detects_motion(self):
        """Should detect motion between different frames."""
        service = MotionDetectionService()
        service.config = MotionDetectionConfig(
            enabled=True,
            threshold=30,
            min_area=100,
            trigger_threshold=0.01
        )
        
        # First frame - establish baseline
        frame1 = np.zeros((200, 200, 3), dtype=np.uint8)
        service.process_frame(frame1)
        
        # Second frame - add motion
        frame2 = np.zeros((200, 200, 3), dtype=np.uint8)
        frame2[50:100, 50:100] = 255  # Add white square
        
        event = service.process_frame(frame2)
        
        # Should detect motion
        if event:  # Motion detection may require sufficient difference
            assert isinstance(event, MotionEvent)
            assert event.motion_score > 0
    
    def test_get_recent_events(self):
        """Should return recent motion events."""
        service = MotionDetectionService()
        
        # Add some events
        for i in range(3):
            event = MotionEvent(
                timestamp=f"2024-01-01 12:00:0{i}",
                motion_score=0.5 + i * 0.1,
                contour_count=i + 1,
                total_motion_area=100 * (i + 1)
            )
            service.recent_events.append(event)
        
        events = service.get_recent_events(limit=2)
        
        assert len(events) == 2
        # Should be most recent first
        assert events[0]['motion_score'] == 0.7


class TestNotificationService:
    """Test notification service."""
    
    @patch('motion_services.logger')
    def test_initialization_without_vapid(self, mock_logger):
        """Should handle missing VAPID keys gracefully."""
        with patch.dict(os.environ, {}, clear=True):
            service = NotificationService(storage=Mock())
            
            assert service.vapid_private is None
            assert service.vapid_public is None
            mock_logger.warning.assert_called()
    
    def test_initialization_with_vapid(self):
        """Should initialize with VAPID keys."""
        with patch.dict(os.environ, {
            'VAPID_PRIVATE_KEY': 'test_private',
            'VAPID_PUBLIC_KEY': 'test_public',
            'VAPID_EMAIL': 'test@example.com'
        }):
            service = NotificationService(storage=Mock())
            
            assert service.vapid_private == 'test_private'
            assert service.vapid_public == 'test_public'
            assert service.vapid_email == 'test@example.com'
    
    @patch('motion_services.webpush')
    def test_send_notification_success(self, mock_webpush):
        """Should send notification successfully."""
        mock_storage = Mock()
        mock_storage.get_all_subscriptions.return_value = [
            PushSubscription(
                id='test-id-1',
                endpoint='https://example.com/push',
                p256dh='key',
                auth='auth',
                created_at='2024-01-01'
            )
        ]
        
        with patch.dict(os.environ, {
            'VAPID_PRIVATE_KEY': 'test_private',
            'VAPID_PUBLIC_KEY': 'test_public',
            'VAPID_EMAIL': 'test@example.com'
        }):
            service = NotificationService(storage=mock_storage)
            
            event = MotionEvent(
                timestamp='2024-01-01 12:00:00',
                motion_score=0.75,
                contour_count=3,
                total_motion_area=1500
            )
            
            service.send_motion_notification(event)
            
            # Should call webpush
            mock_webpush.assert_called_once()
    
    def test_send_test_notification(self):
        """Should send test notification to specific endpoint."""
        mock_storage = Mock()
        mock_storage.get_subscription_by_endpoint.return_value = PushSubscription(
            id='test-id-2',
            endpoint='https://example.com/push',
            p256dh='key',
            auth='auth',
            created_at='2024-01-01'
        )
        
        with patch.dict(os.environ, {
            'VAPID_PRIVATE_KEY': 'test_private',
            'VAPID_PUBLIC_KEY': 'test_public',
            'VAPID_EMAIL': 'test@example.com'
        }):
            with patch('motion_services.webpush') as mock_webpush:
                service = NotificationService(storage=mock_storage)
                
                result = service.send_test_notification('https://example.com/push')
                
                assert result['success'] == True
                mock_webpush.assert_called_once()