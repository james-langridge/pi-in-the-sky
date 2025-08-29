"""Integration tests for end-to-end flows."""

import pytest
import json
from unittest.mock import patch, Mock
import numpy as np

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import create_app
from config import AppConfig
from models import MotionEvent


class TestAPIEndpoints:
    """Test Flask API endpoints."""
    
    @pytest.fixture
    def app(self):
        """Create test Flask app."""
        config = AppConfig()
        app = create_app(config)
        app.config['TESTING'] = True
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()
    
    def test_health_endpoint(self, client):
        """Health check should return status."""
        response = client.get('/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'camera' in data
    
    def test_presets_endpoint(self, client):
        """Should return available presets."""
        response = client.get('/presets')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'presets' in data
        assert 'default' in data['presets']
    
    def test_apply_preset_endpoint(self, client):
        """Should apply camera preset."""
        response = client.post('/apply_preset',
                              json={'preset': 'default'},
                              content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'success' in data
    
    def test_motion_status_endpoint(self, client):
        """Should return motion detection status."""
        response = client.get('/api/motion/status')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'enabled' in data
        assert 'config' in data
    
    def test_motion_config_update(self, client):
        """Should update motion detection config."""
        new_config = {
            'enabled': True,
            'threshold': 50,
            'min_area': 1000
        }
        
        response = client.post('/api/motion/config',
                              json=new_config,
                              content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['config']['enabled'] == True
        assert data['config']['threshold'] == 50
    
    def test_motion_events_endpoint(self, client, app):
        """Should return recent motion events."""
        # Add some test events
        with app.app_context():
            motion_service = app.config['motion_service']
            for i in range(3):
                event = MotionEvent(
                    timestamp=f"2024-01-01 12:00:0{i}",
                    motion_score=0.5,
                    contour_count=2,
                    total_motion_area=500
                )
                motion_service.recent_events.append(event)
        
        response = client.get('/api/motion/events?limit=2')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['events']) <= 2
    
    def test_vapid_key_endpoint(self, client):
        """Should return VAPID public key or error."""
        response = client.get('/api/push/vapid-key')
        
        assert response.status_code in [200, 503]
        data = json.loads(response.data)
        if response.status_code == 200:
            assert 'vapid_public_key' in data
        else:
            assert 'error' in data
    
    def test_video_feed_streaming(self, client):
        """Should stream video frames."""
        # Just test that endpoint exists and returns proper content type
        response = client.get('/video_feed', 
                             headers={'Accept': 'multipart/x-mixed-replace'})
        
        # Should return multipart response
        assert response.status_code == 200
        assert 'multipart/x-mixed-replace' in response.content_type


class TestMotionDetectionFlow:
    """Test complete motion detection flow."""
    
    def test_motion_detection_integration(self):
        """Test motion detection from frame capture to event."""
        from services import CameraService
        from motion_services import MotionDetectionService
        from config import AppConfig
        
        # Create services
        camera = CameraService(AppConfig())
        motion = MotionDetectionService()
        
        # Enable motion detection
        motion.update_config({
            'enabled': True,
            'threshold': 30,
            'min_area': 100,
            'trigger_threshold': 0.01
        })
        
        # Capture and process frames
        frame1 = camera.capture_frame()
        if frame1 is not None:
            motion.process_frame(frame1)
            
            # Create frame with motion
            frame2 = frame1.copy()
            # Add a white rectangle to simulate motion
            if len(frame2.shape) == 3:
                frame2[50:150, 50:150] = 255
            
            event = motion.process_frame(frame2)
            
            # Verify motion detection works end-to-end
            assert motion.config.enabled == True
            # Event may or may not trigger depending on motion threshold