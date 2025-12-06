"""Services for motion detection and push notifications."""

import time
import logging
import json
from typing import Optional, Dict, Any, List
from collections import deque
from pywebpush import webpush, WebPushException

from models import MotionDetectionConfig, MotionEvent, AudioEvent
from calculations import (
    detect_motion_between_frames,
    should_trigger_motion_event,
    create_motion_event,
    create_timestamp,
    decode_jpeg_to_frame
)
from storage import SubscriptionStorage
from result import Result, StringResult

logger = logging.getLogger(__name__)


class MotionDetectionService:
    """Orchestrates motion detection using frame comparison."""
    
    def __init__(self, config: Optional[MotionDetectionConfig] = None):
        """
        Initialize motion detection service.
        
        Args:
            config: Motion detection configuration
        """
        self._config = config or MotionDetectionConfig()
        self._frame_buffer = deque(maxlen=2)  # Keep last 2 frames
        self._last_trigger_time = 0.0
        self._motion_events = deque(maxlen=100)  # Keep last 100 events
        self._enabled = False
    
    def update_config(self, config: MotionDetectionConfig) -> None:
        """Update motion detection configuration."""
        self._config = config
        self._enabled = config.enabled
        logger.info(f"Motion detection {'enabled' if config.enabled else 'disabled'}")
    
    def get_config(self) -> MotionDetectionConfig:
        """Get current motion detection configuration."""
        return self._config
    
    def is_enabled(self) -> bool:
        """Check if motion detection is enabled."""
        return self._enabled
    
    def process_frame(self, jpeg_frame: bytes) -> Optional[MotionEvent]:
        """
        Process a new frame for motion detection.
        
        Args:
            jpeg_frame: JPEG encoded frame bytes
            
        Returns:
            MotionEvent if motion detected, None otherwise
        """
        if not self._enabled:
            return None
        
        try:
            # Decode JPEG to numpy array
            current_frame = decode_jpeg_to_frame(jpeg_frame)
            
            # Add to buffer
            self._frame_buffer.append(current_frame)
            
            # Need at least 2 frames for comparison
            if len(self._frame_buffer) < 2:
                return None
            
            # Get previous and current frames
            previous_frame = self._frame_buffer[0]
            
            # Detect motion between frames
            motion_score, total_area, frame_diff_percentage = detect_motion_between_frames(
                current_frame, previous_frame, self._config
            )
            
            # Check if should trigger event
            time_since_last = time.time() - self._last_trigger_time
            should_trigger = should_trigger_motion_event(
                motion_score, self._config, time_since_last
            )
            
            # Create motion event
            timestamp = create_timestamp()
            motion_event = create_motion_event(
                timestamp, motion_score, total_area, 
                frame_diff_percentage, should_trigger
            )
            
            # Store event
            self._motion_events.append(motion_event)
            
            # Update trigger time if triggered
            if should_trigger:
                self._last_trigger_time = time.time()
                logger.info(f"Motion triggered: score={motion_score:.3f}, area={total_area}")
            
            return motion_event if motion_score > 0 else None
            
        except Exception as e:
            logger.error(f"Error processing frame for motion detection: {e}")
            return None
    
    def get_recent_events(self, limit: int = 10) -> List[MotionEvent]:
        """
        Get recent motion events.
        
        Args:
            limit: Maximum number of events to return
            
        Returns:
            List of recent motion events
        """
        events = list(self._motion_events)
        events.reverse()  # Most recent first
        return events[:limit]
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get motion detection status.
        
        Returns:
            Dictionary with status information
        """
        recent_events = self.get_recent_events(5)
        triggered_events = [e for e in recent_events if e.triggered]
        
        return {
            "enabled": self._enabled,
            "config": {
                "sensitivity": self._config.sensitivity,
                "min_area": self._config.min_area,
                "cooldown_seconds": self._config.cooldown_seconds,
                "threshold": self._config.threshold
            },
            "last_trigger_time": self._last_trigger_time,
            "recent_events": len(recent_events),
            "triggered_events": len(triggered_events),
            "buffer_size": len(self._frame_buffer)
        }
    
    def reset(self) -> None:
        """Reset motion detection state."""
        self._frame_buffer.clear()
        self._motion_events.clear()
        self._last_trigger_time = 0.0
        logger.info("Motion detection state reset")


class NotificationService:
    """Handles push notification sending."""
    
    def __init__(self, storage: SubscriptionStorage, vapid_obj, 
                 vapid_public_key: str, vapid_email: str):
        """
        Initialize notification service.
        
        Args:
            storage: Subscription storage instance
            vapid_obj: VAPID object for authentication
            vapid_public_key: VAPID public key
            vapid_email: Contact email for VAPID
        """
        self._storage = storage
        self._vapid_obj = vapid_obj
        self._vapid_public_key = vapid_public_key
        self._vapid_claims = {"sub": f"mailto:{vapid_email}"}
        self._failed_endpoints = set()
    
    @property
    def vapid_public_key(self) -> str:
        """Get VAPID public key for client subscriptions."""
        return self._vapid_public_key
    
    @property
    def vapid_private_key(self):
        """Get VAPID private key object for authentication."""
        return self._vapid_obj
    
    @property
    def vapid_email(self) -> str:
        """Get VAPID email for claims."""
        return self._vapid_claims["sub"].replace("mailto:", "")
    
    def send_motion_notification(self, motion_event: MotionEvent) -> Result[Dict[str, Any], str]:
        """
        Send motion detection notification to all subscribers.
        
        Args:
            motion_event: Motion event to notify about
            
        Returns:
            Result containing send statistics or error message
        """
        subscriptions = self._storage.get_all_subscriptions()
        
        if not subscriptions:
            logger.info("No subscriptions to notify")
            return Result.success({
                "sent": 0,
                "failed": 0,
                "total": 0
            })
        
        # Prepare notification payload
        payload = json.dumps({
            "title": "Motion Detected",
            "body": f"Motion detected at {motion_event.timestamp}",
            "icon": "/icon-192.png",
            "badge": "/badge-72.png",
            "timestamp": motion_event.timestamp,
            "data": {
                "motion_score": motion_event.motion_score,
                "area": motion_event.area,
                "percentage": motion_event.frame_diff_percentage
            }
        })
        
        sent_count = 0
        failed_count = 0
        
        for subscription in subscriptions:
            # Skip known failed endpoints
            if subscription.endpoint in self._failed_endpoints:
                continue
            
            try:
                webpush(
                    subscription_info={
                        "endpoint": subscription.endpoint,
                        "keys": {
                            "p256dh": subscription.p256dh,
                            "auth": subscription.auth
                        }
                    },
                    data=payload,
                    vapid_private_key=self._vapid_obj,
                    vapid_claims=self._vapid_claims,
                    ttl=86400  # 24 hours TTL required by Apple
                )
                sent_count += 1
                logger.debug(f"Notification sent to {subscription.id}")
                
            except WebPushException as e:
                failed_count += 1
                logger.error(f"Failed to send notification to {subscription.id}: {e}")
                logger.error(f"WebPushException details - Response status: {e.response.status_code if e.response else 'No response'}")
                logger.error(f"WebPushException details - Response text: {e.response.text if e.response else 'No response text'}")
                
                # Handle expired subscriptions
                if e.response and e.response.status_code == 410:
                    logger.info(f"Removing expired subscription {subscription.id}")
                    self._storage.remove_subscription(subscription.endpoint)
                    self._failed_endpoints.add(subscription.endpoint)
            except Exception as e:
                failed_count += 1
                logger.error(f"Unexpected error sending notification to {subscription.id}: {type(e).__name__}: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
        
        result = {
            "sent": sent_count,
            "failed": failed_count,
            "total": len(subscriptions)
        }
        
        logger.info(f"Notifications sent: {sent_count}/{len(subscriptions)}")
        return Result.success(result)
    
    def send_audio_notification(self, audio_event: AudioEvent) -> Result[Dict[str, Any], str]:
        """
        Send audio detection notification to all subscribers.
        
        Args:
            audio_event: Audio event to notify about
            
        Returns:
            Result containing send statistics or error message
        """
        subscriptions = self._storage.get_all_subscriptions()
        
        if not subscriptions:
            logger.info("No subscriptions to notify for audio event")
            return Result.success({
                "sent": 0,
                "failed": 0,
                "total": 0
            })
        
        # Prepare notification payload
        payload = json.dumps({
            "title": "Audio Detected",
            "body": f"Audio detected at {audio_event.timestamp}",
            "icon": "/icon-192.png",
            "badge": "/badge-72.png",
            "timestamp": audio_event.timestamp,
            "data": {
                "rms_level": audio_event.rms_level,
                "peak_level": audio_event.peak_level,
                "duration": audio_event.duration
            }
        })
        
        sent_count = 0
        failed_count = 0
        
        for subscription in subscriptions:
            # Skip known failed endpoints
            if subscription.endpoint in self._failed_endpoints:
                continue
            
            try:
                webpush(
                    subscription_info={
                        "endpoint": subscription.endpoint,
                        "keys": {
                            "p256dh": subscription.p256dh,
                            "auth": subscription.auth
                        }
                    },
                    data=payload,
                    vapid_private_key=self._vapid_obj,
                    vapid_claims=self._vapid_claims,
                    ttl=86400  # 24 hours TTL required by Apple
                )
                sent_count += 1
                logger.debug(f"Audio notification sent to {subscription.id}")
                
            except WebPushException as e:
                logger.warning(f"Failed to send audio notification to {subscription.id}: {e}")
                
                # Mark endpoint as failed if gone or expired
                if e.response and e.response.status_code == 410:
                    self._failed_endpoints.add(subscription.endpoint)
                    self._storage.remove_subscription(subscription.endpoint)
                    logger.info(f"Removed expired subscription {subscription.id}")
                
                failed_count += 1
            except Exception as e:
                failed_count += 1
                logger.error(f"Unexpected error sending audio notification to {subscription.id}: {type(e).__name__}: {e}")
        
        result = {
            "sent": sent_count,
            "failed": failed_count,
            "total": len(subscriptions)
        }
        
        logger.info(f"Audio notifications sent: {sent_count}/{len(subscriptions)}")
        return Result.success(result)
    
    def test_notification(self, endpoint: str) -> Result[bool, str]:
        """
        Send a test notification to a specific endpoint.
        
        Args:
            endpoint: Push service endpoint URL
            
        Returns:
            True if notification sent successfully
        """
        subscription = self._storage.get_subscription_by_endpoint(endpoint)
        
        if not subscription:
            logger.error(f"No subscription found for endpoint: {endpoint}")
            return Result.failure(f"No subscription found for endpoint: {endpoint}")
        
        payload = json.dumps({
            "title": "Test Notification",
            "body": "This is a test notification from Pi Camera",
            "icon": "/icon-192.png",
            "timestamp": create_timestamp()
        })
        
        try:
            webpush(
                subscription_info={
                    "endpoint": subscription.endpoint,
                    "keys": {
                        "p256dh": subscription.p256dh,
                        "auth": subscription.auth
                    }
                },
                data=payload,
                vapid_private_key=self._vapid_obj,
                vapid_claims=self._vapid_claims,
                ttl=86400  # 24 hours TTL required by Apple
            )
            logger.info(f"Test notification sent to {subscription.id}")
            return Result.success(True)
            
        except WebPushException as e:
            logger.error(f"Failed to send test notification: {e}")
            logger.error(f"WebPushException details - Response: {e.response}")
            logger.error(f"WebPushException details - Response status: {e.response.status_code if e.response else 'No response'}")
            logger.error(f"WebPushException details - Response text: {e.response.text if e.response else 'No response text'}")
            if hasattr(e, 'message'):
                logger.error(f"WebPushException message: {e.message}")
            return Result.failure(f"Failed to send notification: {e}")
        except Exception as e:
            logger.error(f"Unexpected error sending test notification: {type(e).__name__}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return Result.failure(f"Unexpected error: {type(e).__name__}")
    
    def get_vapid_public_key(self) -> str:
        """Get VAPID public key for client subscription."""
        return self._vapid_public_key