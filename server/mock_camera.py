"""Mock camera implementation for development without PiCamera2."""

import io
import time
import numpy as np
import cv2
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class MockCamera:
    """Mock PiCamera2 for development/testing."""
    
    def __init__(self):
        self.width = 1920
        self.height = 1080
        self.frame_count = 0
        self.controls = {}
        
    def create_preview_configuration(self, main=None):
        """Mock configuration creation."""
        if main and "size" in main:
            self.width, self.height = main["size"]
        return {"main": {"size": (self.width, self.height)}}
    
    def configure(self, config):
        """Mock configure."""
        pass
    
    def start(self):
        """Mock start."""
        logger.info("Mock camera started")
    
    def stop(self):
        """Mock stop."""
        logger.info("Mock camera stopped")
    
    def close(self):
        """Mock close."""
        logger.info("Mock camera closed")
    
    def capture_file(self, stream, format='jpeg'):
        """Generate a mock frame with some visual variation."""
        # Create a frame with gradient and noise
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        # Add gradient background
        for i in range(self.height):
            frame[i, :] = [
                int(255 * i / self.height),  # Red gradient
                100,  # Green constant
                int(255 * (1 - i / self.height))  # Blue inverse gradient
            ]
        
        # Add some moving elements to simulate motion
        self.frame_count += 1
        
        # Moving circle
        circle_x = int(self.width / 2 + 300 * np.sin(self.frame_count * 0.05))
        circle_y = int(self.height / 2 + 200 * np.cos(self.frame_count * 0.05))
        cv2.circle(frame, (circle_x, circle_y), 50, (255, 255, 0), -1)
        
        # Add timestamp text
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, f"MOCK CAMERA - {timestamp}", 
                   (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 
                   2, (255, 255, 255), 3)
        
        # Add frame counter
        cv2.putText(frame, f"Frame: {self.frame_count}", 
                   (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 
                   1, (255, 255, 255), 2)
        
        # Add random noise for variety
        noise = np.random.randint(0, 50, (self.height, self.width, 3), dtype=np.uint8)
        frame = cv2.add(frame, noise)
        
        # Encode to JPEG
        success, buffer = cv2.imencode('.jpg', frame)
        if success:
            stream.write(buffer.tobytes())
        else:
            raise ValueError("Failed to encode mock frame")
    
    def set_controls(self, controls):
        """Mock set_controls."""
        self.controls.update(controls)
        logger.info(f"Mock camera controls updated: {controls}")
    
    def capture_metadata(self):
        """Mock capture_metadata."""
        return self.controls.copy()


def MockPicamera2():
    """Factory function to create MockCamera."""
    return MockCamera()