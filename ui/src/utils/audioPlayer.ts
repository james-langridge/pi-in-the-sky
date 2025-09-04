/**
 * Web Audio API based audio player for streaming audio
 */
export class StreamingAudioPlayer {
  private audioContext: AudioContext | null = null;
  private sourceBuffer: AudioBufferSourceNode | null = null;
  private gainNode: GainNode | null = null;
  private isPlaying = false;
  private nextStartTime = 0;
  private fetchController: AbortController | null = null;

  async initialize(): Promise<void> {
    if (this.audioContext) return;
    
    this.audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
    this.gainNode = this.audioContext.createGain();
    this.gainNode.connect(this.audioContext.destination);
  }

  async start(audioUrl: string): Promise<void> {
    await this.initialize();
    if (!this.audioContext) return;

    this.isPlaying = true;
    this.fetchController = new AbortController();
    
    // Start fetching and playing audio chunks
    this.fetchAndPlayChunks(audioUrl);
  }

  private async fetchAndPlayChunks(audioUrl: string): Promise<void> {
    if (!this.audioContext || !this.fetchController) return;

    try {
      const response = await fetch(audioUrl, {
        signal: this.fetchController.signal
      });

      if (!response.body) {
        console.error('No response body for audio stream');
        return;
      }

      const reader = response.body.getReader();
      let buffer = new Uint8Array(0);
      const chunkSize = 44100 * 2; // 1 second of audio at 44.1kHz, 16-bit mono
      
      // Skip WAV header (44 bytes)
      let headerSkipped = false;
      
      while (this.isPlaying) {
        const { done, value } = await reader.read();
        
        if (done) break;
        
        // Concatenate chunks
        const newBuffer = new Uint8Array(buffer.length + value.length);
        newBuffer.set(buffer);
        newBuffer.set(value, buffer.length);
        buffer = newBuffer;
        
        // Skip WAV header on first chunk
        if (!headerSkipped && buffer.length >= 44) {
          buffer = buffer.slice(44);
          headerSkipped = true;
        }
        
        // Process complete chunks
        while (buffer.length >= chunkSize) {
          const chunk = buffer.slice(0, chunkSize);
          buffer = buffer.slice(chunkSize);
          
          // Convert PCM to audio buffer
          await this.playPCMChunk(chunk);
        }
      }
    } catch (error: any) {
      if (error.name !== 'AbortError') {
        console.error('Audio streaming error:', error);
      }
    }
  }

  private async playPCMChunk(pcmData: Uint8Array): Promise<void> {
    if (!this.audioContext || !this.gainNode) return;
    
    // Convert PCM S16LE to Float32
    const float32Array = new Float32Array(pcmData.length / 2);
    const dataView = new DataView(pcmData.buffer, pcmData.byteOffset, pcmData.byteLength);
    
    for (let i = 0; i < float32Array.length; i++) {
      const sample = dataView.getInt16(i * 2, true); // little-endian
      float32Array[i] = sample / 32768.0; // normalize to -1 to 1
    }
    
    // Create audio buffer
    const audioBuffer = this.audioContext.createBuffer(1, float32Array.length, 44100);
    audioBuffer.getChannelData(0).set(float32Array);
    
    // Schedule playback
    const source = this.audioContext.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(this.gainNode);
    
    const currentTime = this.audioContext.currentTime;
    const startTime = Math.max(currentTime, this.nextStartTime);
    source.start(startTime);
    
    // Update next start time to maintain continuous playback
    this.nextStartTime = startTime + audioBuffer.duration;
  }

  stop(): void {
    this.isPlaying = false;
    
    if (this.fetchController) {
      this.fetchController.abort();
      this.fetchController = null;
    }
    
    if (this.sourceBuffer) {
      try {
        this.sourceBuffer.stop();
      } catch (e) {
        // Ignore if already stopped
      }
      this.sourceBuffer = null;
    }
    
    this.nextStartTime = 0;
  }

  setVolume(volume: number): void {
    if (this.gainNode) {
      this.gainNode.gain.value = Math.max(0, Math.min(1, volume));
    }
  }

  async cleanup(): Promise<void> {
    this.stop();
    
    if (this.audioContext && this.audioContext.state !== 'closed') {
      await this.audioContext.close();
      this.audioContext = null;
    }
    
    this.gainNode = null;
  }
}