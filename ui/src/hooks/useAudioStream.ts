import { useEffect, useRef, useState } from 'react';

export function useAudioStream(enabled: boolean, streamHealthy: boolean) {
  const [audioInitialized, setAudioInitialized] = useState(false);
  const audioContextRef = useRef<AudioContext | null>(null);
  const sourceNodeRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const audioElementRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    if (!enabled || !streamHealthy) {
      // Clean up audio when disabled
      if (audioElementRef.current) {
        audioElementRef.current.pause();
        audioElementRef.current.src = '';
      }
      if (sourceNodeRef.current) {
        sourceNodeRef.current.disconnect();
        sourceNodeRef.current = null;
      }
      if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
        audioContextRef.current.close();
        audioContextRef.current = null;
      }
      setAudioInitialized(false);
      return;
    }

    // Initialize audio playback
    const initAudio = async () => {
      try {
        // Create audio element
        const audio = new Audio();
        audio.src = '/audio_feed';
        audio.autoplay = true;
        audio.controls = false;
        audioElementRef.current = audio;

        // Try to play (may fail due to autoplay policy)
        try {
          await audio.play();
          setAudioInitialized(true);
        } catch (e) {
          console.log('Audio autoplay blocked, will retry on user interaction');
          // Will retry on user interaction
        }
      } catch (error) {
        console.error('Failed to initialize audio:', error);
      }
    };

    initAudio();

    return () => {
      if (audioElementRef.current) {
        audioElementRef.current.pause();
        audioElementRef.current.src = '';
        audioElementRef.current = null;
      }
    };
  }, [enabled, streamHealthy]);

  const toggleAudio = async () => {
    if (!audioElementRef.current) return;

    try {
      if (audioElementRef.current.paused) {
        await audioElementRef.current.play();
      } else {
        audioElementRef.current.pause();
      }
    } catch (error) {
      console.error('Failed to toggle audio:', error);
    }
  };

  return {
    audioInitialized,
    toggleAudio,
    audioElement: audioElementRef.current
  };
}