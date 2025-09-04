"""Service layer for audio capture and streaming operations."""

import io
import time
import logging
import subprocess
import threading
import queue
from typing import Optional, Generator
from models import AudioFrame, AudioConfig, AudioDetectionConfig, AudioEvent
from audio_calculations import (
    create_wav_chunk,
    calculate_rms_level,
    detect_silence,
    apply_volume,
    detect_audio_event,
    should_trigger_notification
)
from result import Result
from collections import deque
from datetime import datetime

logger = logging.getLogger(__name__)


class AudioCaptureService:
    """Encapsulates ALSA audio capture I/O operations."""
    
    def __init__(self, config: AudioConfig = None):
        """
        Initialize audio capture service.
        
        Args:
            config: Audio configuration, defaults to AudioConfig()
        """
        self._config = config or AudioConfig()
        self._capture_process: Optional[subprocess.Popen] = None
        self._initialized = False
        self._capture_thread: Optional[threading.Thread] = None
        self._audio_queue = queue.Queue(maxsize=10)
        self._stop_flag = threading.Event()
        
    def initialize(self) -> Result[bool, str]:
        """Initialize audio capture from USB microphone."""
        if self._initialized:
            return Result.success(True)
            
        try:
            # Test audio device availability
            test_cmd = [
                'arecord',
                '-D', self._config.device,
                '-f', 'S16_LE',
                '-r', str(self._config.sample_rate),
                '-c', str(self._config.channels),
                '-d', '1',  # 1 second test
                '-t', 'raw',
                '/dev/null'
            ]
            
            result = subprocess.run(test_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"Audio device test failed: {result.stderr}")
                return Result.failure(f"Audio device not available: {result.stderr}")
            
            self._initialized = True
            logger.info(f"Audio capture initialized on device {self._config.device}")
            return Result.success(True)
            
        except Exception as e:
            logger.error(f"Failed to initialize audio capture: {e}")
            return Result.failure(f"Audio initialization failed: {str(e)}")
    
    def start_capture(self) -> Result[bool, str]:
        """Start continuous audio capture in background thread."""
        if not self._initialized:
            return Result.failure("Audio capture not initialized")
        
        if self._capture_thread and self._capture_thread.is_alive():
            return Result.success(True)
        
        try:
            # Start arecord process for continuous capture
            cmd = [
                'arecord',
                '-D', self._config.device,
                '-f', 'S16_LE',
                '-r', str(self._config.sample_rate),
                '-c', str(self._config.channels),
                '-t', 'raw',
                '-B', str(self._config.buffer_size),  # Buffer size for low latency
                '-'  # Output to stdout
            ]
            
            self._capture_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0  # Unbuffered for real-time
            )
            
            # Start background thread to read audio data
            self._stop_flag.clear()
            self._capture_thread = threading.Thread(
                target=self._capture_worker,
                daemon=True
            )
            self._capture_thread.start()
            
            logger.info("Audio capture started")
            return Result.success(True)
            
        except Exception as e:
            logger.error(f"Failed to start audio capture: {e}")
            return Result.failure(f"Failed to start capture: {str(e)}")
    
    def _capture_worker(self):
        """Background worker to read audio from arecord process."""
        bytes_per_sample = 2  # S16LE
        chunk_bytes = self._config.chunk_size * self._config.channels * bytes_per_sample
        
        try:
            while not self._stop_flag.is_set():
                if self._capture_process and self._capture_process.poll() is None:
                    # Read chunk from arecord stdout
                    audio_data = self._capture_process.stdout.read(chunk_bytes)
                    
                    if audio_data:
                        # Create audio frame
                        frame = AudioFrame(
                            samples=audio_data,
                            timestamp=time.time(),
                            sample_rate=self._config.sample_rate,
                            channels=self._config.channels,
                            format=self._config.format
                        )
                        
                        # Put in queue (drop old frames if full)
                        try:
                            self._audio_queue.put_nowait(frame)
                        except queue.Full:
                            # Drop oldest frame and add new one
                            try:
                                self._audio_queue.get_nowait()
                                self._audio_queue.put_nowait(frame)
                            except queue.Empty:
                                pass
                else:
                    # Process died, restart
                    logger.warning("Audio capture process died, restarting...")
                    time.sleep(0.1)
                    self.start_capture()
                    break
                    
        except Exception as e:
            logger.error(f"Audio capture worker error: {e}")
    
    def capture_frame(self) -> Optional[AudioFrame]:
        """
        Capture a single audio frame (non-blocking).
        
        Returns:
            AudioFrame if available, None otherwise
        """
        if not self._initialized:
            return None
        
        try:
            return self._audio_queue.get_nowait()
        except queue.Empty:
            return None
    
    def stop_capture(self):
        """Stop audio capture."""
        self._stop_flag.set()
        
        if self._capture_process:
            try:
                self._capture_process.terminate()
                self._capture_process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self._capture_process.kill()
            self._capture_process = None
        
        # Clear queue
        while not self._audio_queue.empty():
            try:
                self._audio_queue.get_nowait()
            except queue.Empty:
                break
        
        logger.info("Audio capture stopped")
    
    def cleanup(self):
        """Clean up audio resources."""
        self.stop_capture()
        self._initialized = False


class MockAudioService:
    """Mock audio service for development/testing without hardware."""
    
    def __init__(self, config: AudioConfig = None):
        """Initialize mock audio service."""
        self._config = config or AudioConfig()
        self._initialized = False
        self._start_time = None
        
    def initialize(self) -> Result[bool, str]:
        """Initialize mock audio."""
        self._initialized = True
        self._start_time = time.time()
        logger.info("Mock audio service initialized")
        return Result.success(True)
    
    def start_capture(self) -> Result[bool, str]:
        """Start mock capture."""
        if not self._initialized:
            return Result.failure("Mock audio not initialized")
        return Result.success(True)
    
    def capture_frame(self) -> Optional[AudioFrame]:
        """Generate mock audio frame (sine wave)."""
        if not self._initialized:
            return None
        
        import math
        import struct
        
        # Generate sine wave
        duration = self._config.chunk_size / self._config.sample_rate
        samples = []
        
        current_time = time.time() - self._start_time
        frequency = 440  # A4 note
        
        for i in range(self._config.chunk_size):
            t = current_time + (i / self._config.sample_rate)
            # Generate sine wave with some variation
            sample = int(16000 * math.sin(2 * math.pi * frequency * t))
            # Add some harmonics for more interesting sound
            sample += int(4000 * math.sin(4 * math.pi * frequency * t))
            samples.append(max(-32768, min(32767, sample)))
        
        # Pack samples
        audio_data = struct.pack(f'<{len(samples)}h', *samples)
        
        return AudioFrame(
            samples=audio_data,
            timestamp=time.time(),
            sample_rate=self._config.sample_rate,
            channels=self._config.channels,
            format=self._config.format
        )
    
    def stop_capture(self):
        """Stop mock capture."""
        pass
    
    def cleanup(self):
        """Clean up mock resources."""
        self._initialized = False


class AudioStreamingService:
    """Orchestrates audio streaming operations."""
    
    def __init__(self, 
                 capture_service: AudioCaptureService, 
                 detection_service: Optional['AudioDetectionService'] = None,
                 notification_service=None,
                 volume: float = 1.0):
        """
        Initialize audio streaming service.
        
        Args:
            capture_service: Audio capture service instance
            detection_service: Optional audio detection service
            notification_service: Optional notification service for alerts
            volume: Volume multiplier (1.0 = normal)
        """
        self._capture_service = capture_service
        self._detection_service = detection_service
        self._notification_service = notification_service
        self._volume = volume
        self._stream_active = False
        
    def generate_wav_stream(self) -> Generator[bytes, None, None]:
        """
        Generate continuous WAV audio stream.
        
        Yields:
            WAV-formatted audio chunks
        """
        # Initialize and start capture
        init_result = self._capture_service.initialize()
        if not init_result.is_success:
            logger.error(f"Audio init failed: {init_result.error}")
            # Return silent stream as fallback
            yield self._generate_silence_header()
            while True:
                yield self._generate_silence_chunk()
                time.sleep(0.1)
            return
        
        start_result = self._capture_service.start_capture()
        if not start_result.is_success:
            logger.error(f"Audio capture start failed: {start_result.error}")
            # Return silent stream as fallback
            yield self._generate_silence_header()
            while True:
                yield self._generate_silence_chunk()
                time.sleep(0.1)
            return
        
        self._stream_active = True
        first_chunk = True
        
        try:
            while self._stream_active:
                # Capture audio frame
                frame = self._capture_service.capture_frame()
                
                if frame:
                    # Process for audio detection if enabled
                    if self._detection_service and self._detection_service.is_enabled():
                        audio_event = self._detection_service.process_audio_frame(frame)
                        
                        # Send notification if triggered
                        if audio_event and audio_event.triggered and self._notification_service:
                            try:
                                self._notification_service.send_audio_notification(audio_event)
                            except Exception as e:
                                logger.error(f"Failed to send audio notification: {e}")
                    
                    # Apply volume if needed
                    if self._volume != 1.0:
                        frame = apply_volume(frame, self._volume)
                    
                    # Create WAV chunk
                    chunk = create_wav_chunk(frame, include_header=first_chunk)
                    first_chunk = False
                    
                    yield chunk
                else:
                    # No audio available, yield small silence
                    time.sleep(0.01)
                    
        except GeneratorExit:
            # Client disconnected
            self._stream_active = False
            logger.info("Audio stream client disconnected")
        except Exception as e:
            logger.error(f"Audio streaming error: {e}")
            self._stream_active = False
        finally:
            # Don't stop capture here - let other clients continue
            pass
    
    def _generate_silence_header(self) -> bytes:
        """Generate WAV header for silence stream."""
        from audio_calculations import pcm_to_wav_header
        return pcm_to_wav_header(44100, 1, 16)
    
    def _generate_silence_chunk(self) -> bytes:
        """Generate silent audio chunk."""
        # 100ms of silence
        samples = 4410  # 44100 Hz * 0.1 seconds
        return b'\x00\x00' * samples
    
    def stop_stream(self):
        """Stop the audio stream."""
        self._stream_active = False
    
    def get_audio_level(self) -> float:
        """
        Get current audio level for visualization.
        
        Returns:
            RMS level between 0.0 and 1.0
        """
        frame = self._capture_service.capture_frame()
        if frame:
            return calculate_rms_level(frame)
        return 0.0


def create_audio_service(use_mock: bool = False) -> AudioCaptureService:
    """
    Factory function to create appropriate audio service.
    
    Args:
        use_mock: Use mock service instead of real hardware
        
    Returns:
        Audio capture service instance
    """
    if use_mock:
        logger.info("Using mock audio service")
        return MockAudioService()
    
    # Try real audio first
    service = AudioCaptureService()
    result = service.initialize()
    
    if result.is_success:
        return service
    
    # Fall back to mock if real audio unavailable
    logger.warning("Real audio unavailable, using mock service")
    return MockAudioService()


class AudioDetectionService:
    """Service for detecting audio events and managing notifications."""
    
    def __init__(self, config: AudioDetectionConfig = None):
        """
        Initialize audio detection service.
        
        Args:
            config: Detection configuration
        """
        self._config = config or AudioDetectionConfig()
        self._enabled = self._config.enabled
        self._last_notification_time: Optional[float] = None
        self._recent_events: deque = deque(maxlen=100)
        self._level_buffer: deque = deque(maxlen=50)  # Buffer for duration calculation
        
    def is_enabled(self) -> bool:
        """Check if audio detection is enabled."""
        return self._enabled
    
    def enable(self):
        """Enable audio detection."""
        self._enabled = True
        logger.info("Audio detection enabled")
    
    def disable(self):
        """Disable audio detection."""
        self._enabled = False
        self._level_buffer.clear()
        logger.info("Audio detection disabled")
    
    def update_config(self, config: AudioDetectionConfig):
        """Update detection configuration."""
        self._config = config
        self._enabled = config.enabled
        logger.info(f"Audio detection config updated: threshold={config.threshold}")
    
    def process_audio_frame(self, audio_frame: AudioFrame) -> Optional[AudioEvent]:
        """
        Process an audio frame for detection.
        
        Args:
            audio_frame: Audio frame to process
            
        Returns:
            AudioEvent if detected and should trigger notification, None otherwise
        """
        if not self._enabled:
            return None
        
        # Calculate current RMS level
        current_level = calculate_rms_level(audio_frame)
        
        # Add to buffer for duration tracking
        self._level_buffer.append(current_level)
        
        # Detect audio event
        event = detect_audio_event(
            audio_frame,
            self._config,
            list(self._level_buffer)
        )
        
        if event:
            # Check if should trigger notification
            current_time = time.time()
            should_trigger = should_trigger_notification(
                event,
                self._last_notification_time,
                current_time,
                self._config.cooldown_seconds
            )
            
            if should_trigger:
                # Create triggered event
                triggered_event = AudioEvent(
                    timestamp=event.timestamp,
                    rms_level=event.rms_level,
                    peak_level=event.peak_level,
                    duration=event.duration,
                    triggered=True
                )
                
                self._last_notification_time = current_time
                self._recent_events.append(triggered_event)
                
                logger.info(f"Audio event detected: RMS={event.rms_level:.3f}, duration={event.duration:.1f}s")
                return triggered_event
            else:
                # Store non-triggered event
                self._recent_events.append(event)
        
        return None
    
    def get_recent_events(self, limit: int = 10) -> list:
        """Get recent audio events."""
        events = list(self._recent_events)
        events.reverse()  # Most recent first
        return events[:limit]
    
    def get_status(self) -> dict:
        """Get current detection status."""
        return {
            'enabled': self._enabled,
            'config': {
                'threshold': self._config.threshold,
                'duration_threshold': self._config.duration_threshold,
                'cooldown_seconds': self._config.cooldown_seconds
            },
            'last_notification': datetime.fromtimestamp(
                self._last_notification_time
            ).isoformat() if self._last_notification_time else None,
            'recent_events_count': len(self._recent_events),
            'current_buffer_size': len(self._level_buffer)
        }
    
    def reset(self):
        """Reset detection state."""
        self._last_notification_time = None
        self._recent_events.clear()
        self._level_buffer.clear()
        logger.info("Audio detection state reset")