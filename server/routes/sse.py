"""Server-Sent Events for real-time updates."""

import json
import time
import logging
from typing import Generator
from flask import Blueprint, Response, current_app
from threading import Thread, Event
from queue import Queue, Empty
from datetime import datetime

logger = logging.getLogger(__name__)

sse_bp = Blueprint('sse', __name__)


class SSEManager:
    """Manages Server-Sent Events for broadcasting real-time updates."""
    
    def __init__(self):
        self.clients = []
        self.update_thread = None
        self.stop_event = Event()
        
    def add_client(self, client_queue: Queue):
        """Add a new SSE client."""
        self.clients.append(client_queue)
        logger.info(f"SSE client connected. Total clients: {len(self.clients)}")
        
    def remove_client(self, client_queue: Queue):
        """Remove a disconnected SSE client."""
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
        
        # Send to all connected clients
        disconnected = []
        for client_queue in self.clients:
            try:
                client_queue.put_nowait(message)
            except:
                disconnected.append(client_queue)
        
        # Clean up disconnected clients
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
        last_stream_update = 0
        last_health_update = 0
        
        while not self.stop_event.is_set():
            try:
                now = time.time()
                
                # Stream status update every 2 seconds (reduced from 1 second)
                if now - last_stream_update >= 2:
                    services = current_app.config.get('services', {})
                    if 'streaming_service' in services:
                        stream_status = services['streaming_service'].get_stream_status()
                        self.broadcast_update('stream_status', stream_status)
                    last_stream_update = now
                
                # Health update every 10 seconds (reduced from 5 seconds)
                if now - last_health_update >= 10:
                    self.broadcast_update('health', {
                        'status': 'healthy',
                        'timestamp': datetime.now().isoformat()
                    })
                    last_health_update = now
                
                # Check for motion events
                services = current_app.config.get('services', {})
                if 'motion_service' in services:
                    motion_service = services['motion_service']
                    if motion_service.is_enabled():
                        # Get latest motion status
                        status = {
                            'enabled': motion_service.is_enabled(),
                            'last_trigger': motion_service.last_motion_time,
                            'events_count': len(motion_service.get_recent_events())
                        }
                        self.broadcast_update('motion_status', status)
                
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
    # Create queue for this client
    client_queue = Queue()
    
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
    Used by other parts of the application to push updates.
    """
    from flask import request, jsonify
    
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