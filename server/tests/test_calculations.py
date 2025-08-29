"""Tests for calculation layer - pure functions only."""

import pytest
import numpy as np
from datetime import datetime, timedelta
import cv2

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calculations import (
    create_timestamp,
    add_timestamp_to_frame,
    encode_frame_to_jpeg,
    decode_jpeg_to_frame,
    create_mjpeg_chunk,
    clamp_value,
    prepare_frame_for_motion_detection,
    calculate_frame_difference,
    detect_motion_contours,
    calculate_motion_metrics,
    should_trigger_motion_event,
    create_motion_event,
    detect_motion_between_frames
)


class TestTimestampFunctions:
    """Test timestamp-related pure functions."""
    
    def test_create_timestamp(self):
        """Timestamp should be formatted correctly."""
        timestamp = create_timestamp()
        assert isinstance(timestamp, str)
        assert len(timestamp) == 19  # YYYY-MM-DD HH:MM:SS
        # Verify it can be parsed back
        datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
    
    def test_add_timestamp_to_frame(self):
        """Should overlay timestamp on frame without mutating original."""
        original_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        timestamp = "2024-01-01 12:00:00"
        
        result = add_timestamp_to_frame(original_frame, timestamp)
        
        # Original should be unchanged (immutability test)
        assert np.array_equal(original_frame, np.zeros((480, 640, 3), dtype=np.uint8))
        # Result should be different from original
        assert not np.array_equal(result, original_frame)
        # Shape should be preserved
        assert result.shape == original_frame.shape


class TestImageEncoding:
    """Test JPEG encoding/decoding functions."""
    
    def test_encode_decode_roundtrip(self):
        """Should encode and decode frame with reasonable fidelity."""
        # Create test frame with some pattern
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        jpeg = encode_frame_to_jpeg(frame)
        decoded = decode_jpeg_to_frame(jpeg)
        
        assert isinstance(jpeg, bytes)
        assert len(jpeg) > 0
        assert decoded.shape == frame.shape
        # JPEG is lossy, so we can't expect exact match
        # Just verify it's reasonably close
        diff = np.mean(np.abs(frame.astype(float) - decoded.astype(float)))
        assert diff < 30  # Average pixel difference should be small
    
    def test_create_mjpeg_chunk(self):
        """Should create valid MJPEG chunk with boundaries."""
        jpeg_data = b"fake_jpeg_data"
        chunk = create_mjpeg_chunk(jpeg_data)
        
        assert isinstance(chunk, bytes)
        assert b'--frame\r\n' in chunk
        assert b'Content-Type: image/jpeg\r\n' in chunk
        assert b'fake_jpeg_data' in chunk


class TestValueValidation:
    """Test value clamping and validation functions."""
    
    def test_clamp_value(self):
        """Should clamp values to specified range."""
        assert clamp_value(5, 0, 10) == 5  # Within range
        assert clamp_value(-5, 0, 10) == 0  # Below minimum
        assert clamp_value(15, 0, 10) == 10  # Above maximum
        assert clamp_value(0.5, 0.0, 1.0) == 0.5  # Float values
        assert clamp_value(1.5, 0.0, 1.0) == 1.0


class TestMotionDetection:
    """Test motion detection pure functions."""
    
    def test_prepare_frame_for_motion(self):
        """Should convert frame to grayscale and apply blur."""
        color_frame = np.ones((100, 100, 3), dtype=np.uint8) * 128
        
        result = prepare_frame_for_motion_detection(color_frame, blur_size=5)
        
        assert result.shape == (100, 100)  # Should be grayscale
        assert result.dtype == np.uint8
    
    def test_calculate_frame_difference(self):
        """Should detect differences between frames."""
        frame1 = np.zeros((100, 100), dtype=np.uint8)
        frame2 = np.zeros((100, 100), dtype=np.uint8)
        # Add a rectangle in frame2
        frame2[40:60, 40:60] = 255
        
        binary, diff = calculate_frame_difference(frame1, frame2, threshold=30)
        
        assert binary.shape == frame1.shape
        assert diff.shape == frame1.shape
        # Should detect the rectangle area
        assert np.sum(binary) > 0
    
    def test_detect_motion_contours(self):
        """Should find contours above minimum area."""
        # Create binary image with rectangles of different sizes
        binary = np.zeros((100, 100), dtype=np.uint8)
        binary[10:20, 10:20] = 255  # Small square (100 pixels)
        binary[40:70, 40:70] = 255  # Large square (900 pixels)
        
        contours = detect_motion_contours(binary, min_area=500)
        
        # Should only detect the large square
        assert len(contours) == 1
        area = cv2.contourArea(contours[0])
        assert area >= 500
    
    def test_calculate_motion_metrics(self):
        """Should calculate motion score from contours."""
        # Create some test contours
        contour1 = np.array([[0, 0], [10, 0], [10, 10], [0, 10]], dtype=np.int32)
        contour2 = np.array([[20, 20], [40, 20], [40, 40], [20, 40]], dtype=np.int32)
        contours = [contour1, contour2]
        
        score, total_area, count = calculate_motion_metrics(
            contours,
            frame_area=10000,
            weight_area=0.7,
            weight_count=0.3
        )
        
        assert score > 0
        assert total_area == 500  # 100 + 400
        assert count == 2
    
    def test_should_trigger_motion_event(self):
        """Should determine if motion event should trigger."""
        last_time = datetime.now() - timedelta(seconds=30)
        
        # High score, enough time passed
        assert should_trigger_motion_event(
            motion_score=0.8,
            threshold=0.5,
            last_event_time=last_time,
            cooldown_seconds=10
        ) == True
        
        # Low score
        assert should_trigger_motion_event(
            motion_score=0.3,
            threshold=0.5,
            last_event_time=last_time,
            cooldown_seconds=10
        ) == False
        
        # Too soon after last event
        recent_time = datetime.now() - timedelta(seconds=5)
        assert should_trigger_motion_event(
            motion_score=0.8,
            threshold=0.5,
            last_event_time=recent_time,
            cooldown_seconds=10
        ) == False
    
    def test_create_motion_event(self):
        """Should create immutable motion event."""
        event = create_motion_event(
            timestamp="2024-01-01 12:00:00",
            motion_score=0.75,
            contour_count=3,
            total_motion_area=1500
        )
        
        assert event.timestamp == "2024-01-01 12:00:00"
        assert event.motion_score == 0.75
        assert event.contour_count == 3
        assert event.total_motion_area == 1500
        
        # Test immutability
        with pytest.raises(AttributeError):
            event.motion_score = 0.99
    
    def test_detect_motion_between_frames_integration(self):
        """Should detect motion between two different frames."""
        # Create two frames with a moving object
        frame1 = np.zeros((100, 100, 3), dtype=np.uint8)
        frame2 = np.zeros((100, 100, 3), dtype=np.uint8)
        # Add rectangle in different positions
        frame1[20:40, 20:40] = 255
        frame2[30:50, 30:50] = 255
        
        last_event = datetime.now() - timedelta(minutes=1)
        config = {
            'blur_size': 5,
            'threshold': 30,
            'min_area': 100,
            'weight_area': 0.7,
            'weight_count': 0.3,
            'trigger_threshold': 0.01,
            'cooldown_seconds': 10
        }
        
        event = detect_motion_between_frames(
            frame1, frame2,
            last_event_time=last_event,
            **config
        )
        
        # Should detect motion
        assert event is not None
        assert event.motion_score > 0
        assert event.contour_count > 0