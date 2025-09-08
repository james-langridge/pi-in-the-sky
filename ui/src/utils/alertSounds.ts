// Pure functions for alert sound generation using Web Audio API

interface AlertSoundConfig {
  frequency: number;
  duration: number;
  volume: number;
  type: OscillatorType;
}

// Predefined alert sound configurations
export const ALERT_SOUNDS = {
  motion: {
    frequency: 440,  // A4 note
    duration: 200,
    volume: 0.3,
    type: 'sine' as OscillatorType
  },
  audio: {
    frequency: 523,  // C5 note
    duration: 150,
    volume: 0.3,
    type: 'sine' as OscillatorType
  },
  warning: {
    frequency: 350,
    duration: 300,
    volume: 0.2,
    type: 'sine' as OscillatorType
  }
};

// Create and play an alert sound
export function playAlertSound(config: AlertSoundConfig): void {
  try {
    const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
    
    // Create oscillator for tone generation
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();
    
    // Configure the sound
    oscillator.type = config.type;
    oscillator.frequency.setValueAtTime(config.frequency, audioContext.currentTime);
    
    // Set volume with fade in/out for smooth sound
    gainNode.gain.setValueAtTime(0, audioContext.currentTime);
    gainNode.gain.linearRampToValueAtTime(config.volume, audioContext.currentTime + 0.01);
    gainNode.gain.linearRampToValueAtTime(0, audioContext.currentTime + config.duration / 1000);
    
    // Connect nodes
    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);
    
    // Play the sound
    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + config.duration / 1000);
    
    // Clean up after sound finishes
    setTimeout(() => {
      oscillator.disconnect();
      gainNode.disconnect();
      if (audioContext.state !== 'closed') {
        audioContext.close();
      }
    }, config.duration + 100);
    
  } catch (error) {
    console.error('Failed to play alert sound:', error);
  }
}

// Play a double beep for motion detection
export function playMotionAlert(): void {
  playAlertSound(ALERT_SOUNDS.motion);
  setTimeout(() => {
    playAlertSound(ALERT_SOUNDS.motion);
  }, 250);
}

// Play a single beep for audio detection  
export function playAudioAlert(): void {
  playAlertSound(ALERT_SOUNDS.audio);
}

// Play a warning sound
export function playWarningAlert(): void {
  playAlertSound(ALERT_SOUNDS.warning);
}

// Check if Web Audio API is supported
export function isAudioSupported(): boolean {
  return !!(window.AudioContext || (window as any).webkitAudioContext);
}