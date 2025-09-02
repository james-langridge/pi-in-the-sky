import { useState, useRef, useEffect } from 'react';
import { api } from '../api/client';

interface VideoStreamProps {
  onStreamStatusChange?: (connected: boolean) => void;
}

export function VideoStream({ onStreamStatusChange }: VideoStreamProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [connected, setConnected] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const reconnectAttemptsRef = useRef(0);

  useEffect(() => {
    if (!imgRef.current) return;

    const img = imgRef.current;
    const streamUrl = api.getStreamUrl();

    const handleLoad = () => {
      // MJPEG streams fire onload for every frame, only handle first connection
      if (!connected) {
        setConnected(true);
        setLoading(false);
        setError(null);
        reconnectAttemptsRef.current = 0;
        onStreamStatusChange?.(true);
      }
    };

    const handleError = () => {
      setConnected(false);
      setLoading(false);
      onStreamStatusChange?.(false);

      // Implement exponential backoff for reconnection
      const attempts = reconnectAttemptsRef.current;
      if (attempts < 10) {
        const delay = Math.min(1000 * Math.pow(2, attempts), 30000);
        setError(`Connection lost. Retrying in ${delay / 1000}s...`);
        
        reconnectTimeoutRef.current = setTimeout(() => {
          reconnectAttemptsRef.current++;
          img.src = streamUrl + '?t=' + Date.now(); // Add timestamp to force reload
        }, delay);
      } else {
        setError('Unable to connect to camera stream');
      }
    };

    img.addEventListener('load', handleLoad);
    img.addEventListener('error', handleError);
    
    // Start loading stream
    img.src = streamUrl;

    return () => {
      img.removeEventListener('load', handleLoad);
      img.removeEventListener('error', handleError);
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [connected, onStreamStatusChange]);

  const handleManualReconnect = () => {
    if (imgRef.current) {
      reconnectAttemptsRef.current = 0;
      setLoading(true);
      setError(null);
      imgRef.current.src = api.getStreamUrl() + '?t=' + Date.now();
    }
  };

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

      {/* Video stream */}
      <img
        ref={imgRef}
        alt="Camera stream"
        className="w-full h-full object-contain"
        style={{ display: connected ? 'block' : 'none' }}
      />

      {/* Connection indicator */}
      <div className="absolute top-4 right-4">
        <div className={`flex items-center space-x-2 px-3 py-1 rounded-full ${
          connected ? 'bg-green-500/20' : 'bg-red-500/20'
        }`}>
          <div className={`w-2 h-2 rounded-full ${
            connected ? 'bg-green-500' : 'bg-red-500'
          } animate-pulse`}></div>
          <span className="text-xs text-white">
            {connected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>
    </div>
  );
}