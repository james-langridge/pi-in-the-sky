"""Server-Sent Events for real-time updates."""

import json
import time
import logging
from typing import Generator
from flask import Blueprint, Response, current_app, request
from threading import Thread, Event, Lock
from queue import Queue, Empty, Full
from datetime import datetime

logger = logging.getLogger(__name__)

sse_bp = Blueprint('sse', __name__)


class SSEManager:
    """Manages Server-Sent Events for broadcasting real-time updates."""

    def __init__(self):
        self.clients = []
        self._clients_lock = Lock()
        self.update_thread = None
        self.stop_event = Event()
        self._last_motion_status = None
        self._last_motion_broadcast = 0
        self._last_breathing_status = None
        self._last_breathing_broadcast = 0
        self._last_breathing_waveform = 0
        self._app = None

    def init_app(self, app):
        """Initialize with Flask app reference for background thread context."""
        self._app = app
        
    def add_client(self, client_queue: Queue):
        """Add a new SSE client."""
        with self._clients_lock:
            self.clients.append(client_queue)
            logger.info(f"SSE client connected. Total clients: {len(self.clients)}")

    def remove_client(self, client_queue: Queue):
        """Remove a disconnected SSE client."""
        with self._clients_lock:
            if client_queue in self.clients:
                self.clients.remove(client_queue)
                logger.info(f"SSE client disconnected. Total clients: {len(self.clients)}")
    
    def broadcast_update(self, event_type: str, data: dict):
        """Broadcast an update to all connected clients."""
        message = {
            'type': event_type,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }

        disconnected = []
        with self._clients_lock:
            clients_snapshot = list(self.clients)

        for client_queue in clients_snapshot:
            try:
                client_queue.put_nowait(message)
            except Full:
                disconnected.append(client_queue)
            except Exception as e:
                logger.warning(f"Error sending to SSE client: {e}")
                disconnected.append(client_queue)

        for client in disconnected:
            self.remove_client(client)
    
    def start_update_loop(self):
        """Start background thread for periodic updates."""
        if self.update_thread and self.update_thread.is_alive():
            return
            
        self.stop_event.clear()
        self.update_thread = Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()
        logger.info("SSE update loop started")
    
    def stop_update_loop(self):
        """Stop the background update thread."""
        self.stop_event.set()
        if self.update_thread:
            self.update_thread.join(timeout=2)
            logger.info("SSE update loop stopped")
    
    def _update_loop(self):
        """Background loop to send periodic updates."""
        if not self._app:
            logger.error("SSE update loop started without app context")
            return

        last_stream_update = 0
        last_health_update = 0

        while not self.stop_event.is_set():
            try:
                with self._app.app_context():
                    now = time.time()

                    # Stream status update every 2 seconds
                    if now - last_stream_update >= 2:
                        services = self._app.config.get('services', {})
                        if 'streaming_service' in services:
                            stream_status = services['streaming_service'].get_stream_status()
                            # Add status field to match client expectations
                            if stream_status["healthy"]:
                                stream_status["status"] = "streaming"
                            elif stream_status["timestamp"] and stream_status["frame_age_seconds"] is not None:
                                if stream_status["frame_age_seconds"] > 10:
                                    stream_status["status"] = "stale"
                                else:
                                    stream_status["status"] = "degraded"
                            else:
                                stream_status["status"] = "waiting"
                            self.broadcast_update('stream_status', stream_status)
                        last_stream_update = now

                    # Health update every 10 seconds
                    if now - last_health_update >= 10:
                        self.broadcast_update('health', {
                            'status': 'healthy',
                            'timestamp': datetime.now().isoformat()
                        })
                        last_health_update = now

                    # Check for motion events (throttled to 5s unless changed)
                    services = self._app.config.get('services', {})
                    if 'motion_service' in services:
                        motion_service = services['motion_service']
                        motion_status = motion_service.get_status()
                        status = {
                            'enabled': motion_status['enabled'],
                            'last_trigger': motion_status['last_trigger_time'],
                            'events_count': motion_status['recent_events']
                        }
                        status_changed = status != self._last_motion_status
                        time_since_broadcast = now - self._last_motion_broadcast

                        if status_changed or time_since_broadcast >= 5:
                            self.broadcast_update('motion_status', status)
                            self._last_motion_status = status
                            self._last_motion_broadcast = now

                    # Check for breathing detection updates
                    if 'breathing_service' in services:
                        breathing_service = services['breathing_service']
                        if breathing_service.is_enabled():
                            # Breathing status update every 1 second
                            if now - self._last_breathing_broadcast >= 1:
                                breathing_status = breathing_service.get_status_dict()
                                self.broadcast_update('breathing_status', breathing_status)
                                self._last_breathing_broadcast = now

                            # Waveform data update every 200ms for smooth visualization
                            if now - self._last_breathing_waveform >= 0.2:
                                waveform_points = breathing_service.get_waveform_data(seconds=2.0)
                                if waveform_points:
                                    # Send only the latest point for efficiency
                                    latest = waveform_points[-1]
                                    self.broadcast_update('breathing_waveform', {
                                        'timestamp': latest.timestamp,
                                        'intensity': latest.intensity
                                    })
                                self._last_breathing_waveform = now

                time.sleep(0.5)  # Check every 500ms for responsiveness

            except Exception as e:
                logger.error(f"Error in SSE update loop: {e}")
                time.sleep(1)


# Global SSE manager instance
sse_manager = SSEManager()


@sse_bp.route('/api/sse/events')
def sse_events():
    """
    Server-Sent Events endpoint for real-time updates.

    Sends:
        - Stream status and timestamps
        - Server health status
        - Motion detection events
        - Log entries (when requested)
    """
    # Create queue for this client (maxsize prevents memory issues)
    client_queue = Queue(maxsize=100)

    def generate():
        # Register client
        sse_manager.add_client(client_queue)

        # Start update loop if not running
        sse_manager.start_update_loop()

        try:
            # Send initial connection message
            yield f"data: {json.dumps({'type': 'connected', 'timestamp': datetime.now().isoformat()})}\n\n"
            
            while True:
                try:
                    # Wait for updates (with timeout to send keepalive)
                    message = client_queue.get(timeout=30)
                    
                    # Format as SSE
                    event_data = json.dumps(message)
                    yield f"event: {message['type']}\ndata: {event_data}\n\n"
                    
                except Empty:
                    # Send keepalive ping
                    yield f": keepalive {time.time()}\n\n"
                    
                except GeneratorExit:
                    # Client disconnected
                    break
                    
                except Exception as e:
                    logger.error(f"Error sending SSE: {e}")
                    yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
                    
        finally:
            # Clean up on disconnect
            sse_manager.remove_client(client_queue)
    
    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',  # Disable Nginx buffering
            'Connection': 'keep-alive'
        }
    )


@sse_bp.route('/api/sse/broadcast', methods=['POST'])
def broadcast_event():
    """
    Internal endpoint to broadcast events to SSE clients.
    Restricted to localhost for security.

    Note: When behind a reverse proxy, ensure the proxy doesn't forward
    external requests to this endpoint, as remote_addr will show the
    proxy's address (typically localhost).
    """
    from flask import jsonify

    remote_addr = request.remote_addr
    if remote_addr not in ('127.0.0.1', '::1', 'localhost'):
        logger.warning(f"Broadcast attempt from non-localhost: {remote_addr}")
        return jsonify({'error': 'Forbidden'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    event_type = data.get('type', 'update')
    event_data = data.get('data', {})

    sse_manager.broadcast_update(event_type, event_data)

    return jsonify({'status': 'broadcasted', 'clients': len(sse_manager.clients)})


def notify_motion_detected(motion_event: dict):
    """Helper function to notify clients of motion detection."""
    sse_manager.broadcast_update('motion_detected', motion_event)


def notify_log_entry(log_entry: dict):
    """Helper function to notify clients of new log entries."""
    sse_manager.broadcast_update('log_entry', log_entry)
