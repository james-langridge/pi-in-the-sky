import { useState, useEffect } from 'react';
import { VideoStream } from './components/VideoStream';
import { ControlPanel } from './components/ControlPanel';
import { ErrorBoundary } from './components/ErrorBoundary';
import { useHealthCheck, useAppInfo } from './api/hooks';
import PWABadge from './PWABadge';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import './App.css';

function App() {
  const [controlsOpen, setControlsOpen] = useState(false);
  const [streamConnected, setStreamConnected] = useState(false);
  const [streamTimestamp, setStreamTimestamp] = useState<string>('');
  const { isHealthy } = useHealthCheck();
  const { appInfo, updateAvailable } = useAppInfo();

  // Keep-alive mechanism for iOS PWA
  useEffect(() => {
    let keepAliveInterval: number;

    const startKeepAlive = () => {
      keepAliveInterval = setInterval(() => {
        if (!document.hidden) {
          fetch('/health', { method: 'HEAD' }).catch(() => {});
        }
      }, 25000); // Ping every 25 seconds (before iOS 30s timeout)
    };

    const stopKeepAlive = () => {
      if (keepAliveInterval) {
        clearInterval(keepAliveInterval);
      }
    };

    // Manage based on visibility
    const handleVisibilityChange = () => {
      if (document.hidden) {
        stopKeepAlive();
      } else {
        startKeepAlive();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    startKeepAlive();

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      stopKeepAlive();
    };
  }, []);

  // Poll for frame timestamp when stream is connected
  useEffect(() => {
    if (!streamConnected) {
      setStreamTimestamp('');
      return;
    }

    const fetchTimestamp = async () => {
      try {
        const response = await fetch('/api/stream/timestamp');
        const data = await response.json();
        if (data.timestamp) {
          setStreamTimestamp(data.timestamp);
        }
      } catch (error) {
        console.error('Failed to fetch timestamp:', error);
      }
    };

    // Fetch immediately
    fetchTimestamp();

    // Then poll every 500ms to get more responsive updates
    const interval = setInterval(fetchTimestamp, 500);

    return () => clearInterval(interval);
  }, [streamConnected]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.code === 'Space' && e.target === document.body) {
        e.preventDefault();
        setControlsOpen(prev => !prev);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleRefresh = () => {
    window.location.reload();
  };

  return (
    <div className="relative w-screen h-screen bg-gray-900 overflow-hidden">
      {/* Version display */}
      <div className="absolute top-4 left-4 z-20 flex items-center space-x-2">
        <span className="text-xs text-gray-400">
          v{appInfo?.version || '0.0.0'}
        </span>
        <button
          onClick={handleRefresh}
          className="p-1 rounded hover:bg-gray-800 transition-colors"
          title="Refresh app"
        >
          <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>
      </div>

      {/* Update notification */}
      {updateAvailable && (
        <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-30">
          <div className="bg-blue-600 text-white px-4 py-2 rounded-lg shadow-lg flex items-center space-x-3">
            <span className="text-sm">A new version is available!</span>
            <button
              onClick={handleRefresh}
              className="px-3 py-1 bg-blue-700 hover:bg-blue-800 rounded transition-colors text-sm font-medium"
            >
              Refresh Now
            </button>
          </div>
        </div>
      )}

      {/* Unified status indicator */}
      <div className="absolute top-4 right-4 z-20 flex flex-col gap-2">
        {/* Connection status */}
        <div className={`flex items-center space-x-2 px-3 py-1 rounded-full ${
          !isHealthy ? 'bg-red-500/20' : 
          streamConnected ? 'bg-green-500/20' : 'bg-yellow-500/20'
        }`}>
          <div className={`w-2 h-2 rounded-full ${
            !isHealthy ? 'bg-red-500' : 
            streamConnected ? 'bg-green-500' : 'bg-yellow-500'
          } animate-pulse`}></div>
          <span className="text-xs text-white">
            {!isHealthy ? 'Server Offline' : 
             streamConnected ? 'Connected' : 'Connecting...'}
          </span>
        </div>
        
        {/* Frame timestamp - always show when available */}
        {streamTimestamp && (
          <div className="flex items-center space-x-2 px-3 py-1 rounded-full bg-gray-700/50">
            <svg className="w-3 h-3 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="text-xs text-white font-mono">
              {streamTimestamp}
            </span>
          </div>
        )}
      </div>

      {/* Main video stream */}
      <ErrorBoundary>
        <VideoStream onStreamStatusChange={setStreamConnected} />
      </ErrorBoundary>

      {/* Control panel */}
      <ErrorBoundary>
        <ControlPanel
          isOpen={controlsOpen}
          onToggle={() => setControlsOpen(prev => !prev)}
        />
      </ErrorBoundary>

      {/* PWA install badge */}
      <PWABadge />

      {/* Keyboard shortcut hint - only show on desktop */}
      {!controlsOpen && (
        <div className="hidden sm:block absolute bottom-20 left-1/2 transform -translate-x-1/2 text-xs text-gray-500">
          Press Space to toggle controls
        </div>
      )}

      {/* Toast notifications */}
      <ToastContainer
        position="bottom-center"
        autoClose={3000}
        hideProgressBar
        newestOnTop
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
        theme="dark"
        toastClassName="!bg-gray-800 !text-white"
      />
    </div>
  );
}

export default App;