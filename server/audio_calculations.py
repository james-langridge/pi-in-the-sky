"""Pure functions for audio processing and encoding."""

import struct
import math
from typing import List, Tuple, Optional
from models import AudioFrame, AudioDetectionConfig, AudioEvent
from calculations import create_timestamp


def calculate_rms_level(audio_frame: AudioFrame) -> float:
    """
    Calculate RMS (Root Mean Square) audio level for visualization.
    
    Args:
        audio_frame: Audio frame with PCM samples
        
    Returns:
        RMS level between 0.0 (silent) and 1.0 (max volume)
    """
    if not audio_frame.samples or len(audio_frame.samples) < 2:
        return 0.0
    
    # Unpack PCM S16LE samples
    sample_count = len(audio_frame.samples) // 2
    samples = struct.unpack(f'<{sample_count}h', audio_frame.samples)
    
    # Calculate RMS
    sum_squares = sum(s * s for s in samples)
    rms = math.sqrt(sum_squares / sample_count)
    
    # Normalize to 0-1 range (S16 max is 32767)
    normalized = rms / 32767.0
    
    return min(1.0, normalized)


def calculate_peak_level(audio_frame: AudioFrame) -> float:
    """
    Calculate peak audio level for clipping detection.
    
    Args:
        audio_frame: Audio frame with PCM samples
        
    Returns:
        Peak level between 0.0 and 1.0
    """
    if not audio_frame.samples or len(audio_frame.samples) < 2:
        return 0.0
    
    # Unpack PCM S16LE samples
    sample_count = len(audio_frame.samples) // 2
    samples = struct.unpack(f'<{sample_count}h', audio_frame.samples)
    
    # Find peak
    peak = max(abs(s) for s in samples)
    
    # Normalize to 0-1 range
    return peak / 32767.0


def pcm_to_wav_header(sample_rate: int, channels: int, bits_per_sample: int = 16) -> bytes:
    """
    Create WAV file header for PCM data.
    
    Args:
        sample_rate: Sample rate in Hz
        channels: Number of channels
        bits_per_sample: Bits per sample (16 for S16LE)
        
    Returns:
        44-byte WAV header
    """
    byte_rate = sample_rate * channels * bits_per_sample // 8
    block_align = channels * bits_per_sample // 8
    
    # Create WAV header with placeholder for data size (will stream)
    header = b'RIFF'
    header += struct.pack('<I', 0xFFFFFFFF)  # File size placeholder for streaming
    header += b'WAVE'
    header += b'fmt '
    header += struct.pack('<I', 16)  # Format chunk size
    header += struct.pack('<H', 1)   # PCM format
    header += struct.pack('<H', channels)
    header += struct.pack('<I', sample_rate)
    header += struct.pack('<I', byte_rate)
    header += struct.pack('<H', block_align)
    header += struct.pack('<H', bits_per_sample)
    header += b'data'
    header += struct.pack('<I', 0xFFFFFFFF)  # Data size placeholder for streaming
    
    return header


def create_wav_chunk(audio_frame: AudioFrame, include_header: bool = False) -> bytes:
    """
    Create WAV-formatted audio chunk for streaming.
    
    Args:
        audio_frame: Audio frame with PCM samples
        include_header: Include WAV header (for first chunk)
        
    Returns:
        WAV-formatted audio data
    """
    if include_header:
        header = pcm_to_wav_header(
            audio_frame.sample_rate, 
            audio_frame.channels
        )
        return header + audio_frame.samples
    return audio_frame.samples


def resample_audio(
    samples: bytes, 
    from_rate: int, 
    to_rate: int, 
    channels: int = 1
) -> bytes:
    """
    Simple linear interpolation resampling (for non-critical quality).
    
    Args:
        samples: PCM S16LE samples
        from_rate: Source sample rate
        to_rate: Target sample rate
        channels: Number of channels
        
    Returns:
        Resampled PCM S16LE samples
    """
    if from_rate == to_rate:
        return samples
    
    # Unpack samples
    sample_count = len(samples) // 2
    input_samples = struct.unpack(f'<{sample_count}h', samples)
    
    # Calculate output size
    ratio = to_rate / from_rate
    output_count = int(sample_count * ratio)
    output_samples = []
    
    # Linear interpolation
    for i in range(output_count):
        # Find position in input
        pos = i / ratio
        idx = int(pos)
        frac = pos - idx
        
        if idx >= sample_count - 1:
            # Use last sample
            output_samples.append(input_samples[-1])
        else:
            # Interpolate between samples
            sample = int(
                input_samples[idx] * (1 - frac) + 
                input_samples[idx + 1] * frac
            )
            output_samples.append(max(-32768, min(32767, sample)))
    
    # Pack back to bytes
    return struct.pack(f'<{output_count}h', *output_samples)


def apply_volume(audio_frame: AudioFrame, gain: float) -> AudioFrame:
    """
    Apply volume gain to audio frame.
    
    Args:
        audio_frame: Input audio frame
        gain: Volume multiplier (1.0 = no change, 0.5 = half volume, 2.0 = double)
        
    Returns:
        New audio frame with adjusted volume
    """
    if gain == 1.0:
        return audio_frame
    
    # Unpack samples
    sample_count = len(audio_frame.samples) // 2
    samples = struct.unpack(f'<{sample_count}h', audio_frame.samples)
    
    # Apply gain with clipping protection
    adjusted = []
    for s in samples:
        new_val = int(s * gain)
        adjusted.append(max(-32768, min(32767, new_val)))
    
    # Create new frame with adjusted samples
    new_samples = struct.pack(f'<{len(adjusted)}h', *adjusted)
    
    return AudioFrame(
        samples=new_samples,
        timestamp=audio_frame.timestamp,
        sample_rate=audio_frame.sample_rate,
        channels=audio_frame.channels,
        format=audio_frame.format
    )


def mix_audio_frames(frames: List[AudioFrame], weights: List[float] = None) -> AudioFrame:
    """
    Mix multiple audio frames together.
    
    Args:
        frames: List of audio frames to mix
        weights: Optional mixing weights for each frame
        
    Returns:
        Mixed audio frame
    """
    if not frames:
        raise ValueError("No frames to mix")
    
    if len(frames) == 1:
        return frames[0]
    
    if weights is None:
        weights = [1.0 / len(frames)] * len(frames)
    
    # All frames must have same format
    first = frames[0]
    sample_count = len(first.samples) // 2
    
    # Initialize mix buffer
    mixed = [0.0] * sample_count
    
    # Mix all frames
    for frame, weight in zip(frames, weights):
        samples = struct.unpack(f'<{sample_count}h', frame.samples)
        for i, s in enumerate(samples):
            mixed[i] += s * weight
    
    # Convert back to int16 with clipping
    output = []
    for val in mixed:
        output.append(max(-32768, min(32767, int(val))))
    
    # Pack and return
    mixed_samples = struct.pack(f'<{len(output)}h', *output)
    
    return AudioFrame(
        samples=mixed_samples,
        timestamp=first.timestamp,
        sample_rate=first.sample_rate,
        channels=first.channels,
        format=first.format
    )


def detect_silence(audio_frame: AudioFrame, threshold: float = 0.01) -> bool:
    """
    Detect if audio frame is silence.
    
    Args:
        audio_frame: Audio frame to check
        threshold: RMS threshold for silence (0.0-1.0)
        
    Returns:
        True if frame is considered silence
    """
    rms = calculate_rms_level(audio_frame)
    return rms < threshold


def calculate_frame_duration(audio_frame: AudioFrame) -> float:
    """
    Calculate duration of audio frame in seconds.
    
    Args:
        audio_frame: Audio frame
        
    Returns:
        Duration in seconds
    """
    sample_count = len(audio_frame.samples) // 2  # S16LE = 2 bytes per sample
    return sample_count / audio_frame.sample_rate


def split_audio_frame(audio_frame: AudioFrame, chunk_samples: int) -> List[AudioFrame]:
    """
    Split audio frame into smaller chunks.
    
    Args:
        audio_frame: Audio frame to split
        chunk_samples: Number of samples per chunk
        
    Returns:
        List of smaller audio frames
    """
    sample_count = len(audio_frame.samples) // 2
    chunks = []
    
    for i in range(0, sample_count, chunk_samples):
        end = min(i + chunk_samples, sample_count)
        chunk_data = audio_frame.samples[i*2:end*2]
        
        # Calculate timestamp offset for this chunk
        time_offset = i / audio_frame.sample_rate
        
        chunks.append(AudioFrame(
            samples=chunk_data,
            timestamp=audio_frame.timestamp + time_offset,
            sample_rate=audio_frame.sample_rate,
            channels=audio_frame.channels,
            format=audio_frame.format
        ))
    
    return chunks


def detect_audio_event(
    audio_frame: AudioFrame,
    config: AudioDetectionConfig,
    previous_levels: List[float]
) -> Optional[AudioEvent]:
    """
    Detect if audio frame represents a significant audio event.
    
    Args:
        audio_frame: Audio frame to analyze
        config: Detection configuration
        previous_levels: List of previous RMS levels for duration calculation
        
    Returns:
        AudioEvent if detected, None otherwise
    """
    # Calculate current levels
    rms_level = calculate_rms_level(audio_frame)
    peak_level = calculate_peak_level(audio_frame)
    
    # Check if above threshold
    if rms_level < config.threshold:
        return None
    
    # Calculate duration based on consecutive frames above threshold
    frames_above_threshold = sum(1 for level in previous_levels if level >= config.threshold)
    duration = frames_above_threshold * (len(audio_frame.samples) / 2) / audio_frame.sample_rate
    
    # Check if duration meets threshold
    if duration < config.duration_threshold:
        return None
    
    # Create event
    return AudioEvent(
        timestamp=create_timestamp(),
        rms_level=rms_level,
        peak_level=peak_level,
        duration=duration,
        triggered=False  # Will be set by service based on cooldown
    )


def should_trigger_notification(
    event: AudioEvent,
    last_notification_time: Optional[float],
    current_time: float,
    cooldown_seconds: int
) -> bool:
    """
    Determine if an audio event should trigger a notification.
    
    Args:
        event: Audio event to check
        last_notification_time: Timestamp of last notification
        current_time: Current timestamp
        cooldown_seconds: Cooldown period between notifications
        
    Returns:
        True if notification should be triggered
    """
    if last_notification_time is None:
        return True
    
    time_since_last = current_time - last_notification_time
    return time_since_last >= cooldown_seconds


def calculate_frequency_spectrum(audio_frame: AudioFrame) -> List[Tuple[float, float]]:
    """
    Calculate frequency spectrum using FFT (for future frequency-based detection).
    
    Args:
        audio_frame: Audio frame to analyze
        
    Returns:
        List of (frequency, magnitude) tuples
    """
    # Unpack samples
    sample_count = len(audio_frame.samples) // 2
    samples = struct.unpack(f'<{sample_count}h', audio_frame.samples)
    
    # Apply window function (Hamming)
    windowed = []
    for i, sample in enumerate(samples):
        window = 0.54 - 0.46 * math.cos(2 * math.pi * i / (sample_count - 1))
        windowed.append(sample * window)
    
    # Simple DFT (for demonstration - real implementation would use numpy.fft)
    # This is computationally expensive but keeps it pure Python
    spectrum = []
    for k in range(sample_count // 2):  # Only need half due to symmetry
        freq = k * audio_frame.sample_rate / sample_count
        
        real = 0.0
        imag = 0.0
        for n, sample in enumerate(windowed):
            angle = -2 * math.pi * k * n / sample_count
            real += sample * math.cos(angle)
            imag += sample * math.sin(angle)
        
        magnitude = math.sqrt(real * real + imag * imag) / sample_count
        spectrum.append((freq, magnitude))
    
    return spectrum


def filter_audio_by_frequency(
    audio_frame: AudioFrame,
    freq_min: float,
    freq_max: float
) -> bool:
    """
    Check if audio contains significant energy in specified frequency range.
    
    Args:
        audio_frame: Audio frame to analyze
        freq_min: Minimum frequency in Hz
        freq_max: Maximum frequency in Hz
        
    Returns:
        True if significant energy in frequency range
    """
    # For efficiency, use simple energy calculation instead of full FFT
    # This is a simplified band-pass check
    rms = calculate_rms_level(audio_frame)
    
    # If RMS is very low, no significant audio
    if rms < 0.01:
        return False
    
    # For now, return True if any significant audio
    # Full frequency filtering would require FFT
    return True


def calculate_audio_statistics(frames: List[AudioFrame]) -> dict:
    """
    Calculate statistics over multiple audio frames.
    
    Args:
        frames: List of audio frames
        
    Returns:
        Dictionary with statistics
    """
    if not frames:
        return {
            'avg_rms': 0.0,
            'max_rms': 0.0,
            'min_rms': 0.0,
            'avg_peak': 0.0,
            'max_peak': 0.0
        }
    
    rms_levels = [calculate_rms_level(frame) for frame in frames]
    peak_levels = [calculate_peak_level(frame) for frame in frames]
    
    return {
        'avg_rms': sum(rms_levels) / len(rms_levels),
        'max_rms': max(rms_levels),
        'min_rms': min(rms_levels),
        'avg_peak': sum(peak_levels) / len(peak_levels),
        'max_peak': max(peak_levels)
    }