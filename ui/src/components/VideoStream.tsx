import { useState, useRef, useEffect } from 'react';
import { api } from '../api/client';
import { toast } from 'react-toastify';
import { StreamingAudioPlayer } from '../utils/audioPlayer';
import { calculateZoomScale } from '../utils/zoomCalculations';

interface VideoStreamProps {
  streamConnected: boolean;
  streamHealthy: boolean;
  onRetryNeeded?: () => void;
  zoomLevel?: number;
}

export function VideoStream({ streamConnected, streamHealthy, onRetryNeeded, zoomLevel = 0 }: VideoStreamProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [capturing, setCapturing] = useState(false);
  const [imgLoaded, setImgLoaded] = useState(false);
  const [audioEnabled, setAudioEnabled] = useState(false); // Start muted to avoid autoplay issues
  const imgRef = useRef<HTMLImageElement>(null);
  const audioPlayerRef = useRef<StreamingAudioPlayer | null>(null);
  const reconnectTimeoutRef = useRef<number | undefined>(undefined);
  const reconnectAttemptsRef = useRef(0);

  useEffect(() => {
    if (!imgRef.current) return;

    const img = imgRef.current;
    const streamUrl = api.getStreamUrl();

    const handleLoad = () => {
      // MJPEG streams fire onload for every frame
      setImgLoaded(true);
      setLoading(false);
      setError(null);
      reconnectAttemptsRef.current = 0;
    };

    const handleError = () => {
      setImgLoaded(false);
      setLoading(false);
      
      // Don't auto-retry - let the unified stream status handle reconnection logic
      if (!streamHealthy) {
        setError('Stream connection lost');
      }
    };

    img.addEventListener('load', handleLoad);
    img.addEventListener('error', handleError);
    
    // Start loading stream
    img.src = streamUrl + '?t=' + Date.now();

    return () => {
      img.removeEventListener('load', handleLoad);
      img.removeEventListener('error', handleError);
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [streamHealthy]);

  // Initialize audio player
  useEffect(() => {
    if (!audioPlayerRef.current) {
      audioPlayerRef.current = new StreamingAudioPlayer();
    }

    return () => {
      if (audioPlayerRef.current) {
        audioPlayerRef.current.cleanup();
        audioPlayerRef.current = null;
      }
    };
  }, []);

  // Manage audio streaming
  useEffect(() => {
    const manageAudio = async () => {
      if (!audioPlayerRef.current) return;

      if (audioEnabled && streamHealthy) {
        try {
          await audioPlayerRef.current.start('/audio_feed');
        } catch (e) {
          console.error('Failed to start audio:', e);
        }
      } else {
        audioPlayerRef.current.stop();
      }
    };

    manageAudio();
  }, [audioEnabled, streamHealthy]);

  // Handle page visibility changes to refresh stream after phone unlock/app resume
  useEffect(() => {
    const handleVisibilityChange = () => {
      // When page becomes visible again (e.g., after phone unlock)
      if (!document.hidden && streamHealthy) {
        // Refresh video stream
        if (imgRef.current) {
          const streamUrl = api.getStreamUrl();
          imgRef.current.src = streamUrl + '?t=' + Date.now();
          setLoading(true);
          setError(null);
        }
        // Restart audio stream
        if (audioPlayerRef.current && audioEnabled) {
          audioPlayerRef.current.start('/audio_feed').catch(() => {});
        }
      }
    };

    // Also handle pageshow event for iOS PWA
    const handlePageShow = (event: PageTransitionEvent) => {
      // Persisted means the page was restored from bfcache
      if (event.persisted && imgRef.current && streamHealthy) {
        const streamUrl = api.getStreamUrl();
        imgRef.current.src = streamUrl + '?t=' + Date.now();
        setLoading(true);
        setError(null);
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('pageshow', handlePageShow);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('pageshow', handlePageShow);
    };
  }, [streamHealthy]);

  // React to external stream status changes
  useEffect(() => {
    if (!streamConnected || !streamHealthy) {
      setImgLoaded(false);
      if (!streamConnected) {
        setError('Waiting for stream connection...');
      } else if (!streamHealthy) {
        setError('Stream quality issues detected');
      }
    } else if (error && streamConnected && streamHealthy) {
      // Clear error when stream becomes healthy
      setError(null);
      // Refresh the image when stream becomes healthy
      if (imgRef.current) {
        imgRef.current.src = api.getStreamUrl() + '?t=' + Date.now();
      }
    }
  }, [streamConnected, streamHealthy, error]);

  const handleManualReconnect = () => {
    if (imgRef.current) {
      reconnectAttemptsRef.current = 0;
      setLoading(true);
      setError(null);
      imgRef.current.src = api.getStreamUrl() + '?t=' + Date.now();
    }
    // Notify parent that retry was requested
    onRetryNeeded?.();
  };

  const handleCapturePhoto = async () => {
    if (capturing) return;
    
    setCapturing(true);
    try {
      const response = await fetch('/api/capture-photo', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      const data = await response.json();
      
      if (data.status === 'success') {
        toast.success(`Photo saved: ${data.filename}`);
      } else {
        toast.error(data.message || 'Failed to capture photo');
      }
    } catch (error) {
      console.error('Failed to capture photo:', error);
      toast.error('Failed to capture photo');
    } finally {
      setCapturing(false);
    }
  };

  const toggleAudio = async () => {
    const newEnabled = !audioEnabled;
    setAudioEnabled(newEnabled);
    
    if (audioPlayerRef.current && streamHealthy) {
      if (newEnabled) {
        try {
          await audioPlayerRef.current.start('/audio_feed');
        } catch (e) {
          console.error('Failed to start audio:', e);
          toast.error('Failed to enable audio');
        }
      } else {
        audioPlayerRef.current.stop();
      }
    }
  };

  const zoomScale = calculateZoomScale(zoomLevel);
  const isZoomed = zoomLevel > 0;

  return (
    <div className="relative w-full h-full bg-gray-900 rounded-lg overflow-hidden">
      {/* Loading state */}
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-900">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
            <p className="text-gray-300">Connecting to camera...</p>
          </div>
        </div>
      )}

      {/* Error state */}
      {error && !loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-900">
          <div className="text-center">
            <svg className="w-12 h-12 text-red-500 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-gray-300 mb-4">{error}</p>
            <button
              onClick={handleManualReconnect}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
            >
              Retry Connection
            </button>
          </div>
        </div>
      )}

      {/* Scrollable container for zoomed video */}
      <div
        className={`w-full h-full ${isZoomed ? 'overflow-auto' : 'overflow-hidden'}`}
        style={{
          display: imgLoaded && streamConnected ? 'block' : 'none',
        }}
      >
        {/* Video stream */}
        <img
          ref={imgRef}
          alt="Camera stream"
          className="w-full h-full object-contain"
          style={{
            transform: `scale(${zoomScale})`,
            transformOrigin: 'center center',
            transition: 'transform 0.2s ease-out',
          }}
        />
      </div>


      {/* Controls overlay - only show when stream is healthy */}
      {imgLoaded && streamHealthy && (
        <>
          {/* Audio toggle button - left of center */}
          <button
            onClick={toggleAudio}
            className={`absolute bottom-8 left-1/2 -translate-x-1/2 -ml-16 p-3 rounded-full transition-all ${
              audioEnabled
                ? 'bg-green-500 hover:bg-green-600'
                : 'bg-gray-500 hover:bg-gray-600'
            } shadow-lg z-20`}
            title={audioEnabled ? 'Mute audio' : 'Unmute audio'}
          >
            {audioEnabled ? (
              <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
              </svg>
            ) : (
              <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z"
                />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2" />
              </svg>
            )}
          </button>

          {/* Capture button - center */}
          <button
            onClick={handleCapturePhoto}
            disabled={capturing}
            className={`absolute bottom-8 left-1/2 -translate-x-1/2 p-4 rounded-full transition-all ${
              capturing
                ? 'bg-gray-600 cursor-not-allowed'
                : 'bg-blue-500 hover:bg-blue-600 active:scale-95'
            } shadow-lg z-20`}
            title="Capture photo"
          >
            <svg
              className="w-8 h-8 text-white"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"
              />
            </svg>
            {capturing && (
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
              </div>
            )}
          </button>
        </>
      )}

    </div>
  );
}