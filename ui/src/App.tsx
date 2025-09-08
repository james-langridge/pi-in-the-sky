import { useState, useEffect } from 'react';
import { Settings, Images } from 'lucide-react';
import { VideoStream } from './components/VideoStream';
import { ControlPanel } from './components/ControlPanel';
import { PhotoGallery } from './components/PhotoGallery';
import { PowerControl } from './components/PowerControl';
import { ErrorBoundary } from './components/ErrorBoundary';
import { useHealthCheck, useAppInfo, useStreamStatus } from './api/hooks';
import PWABadge from './PWABadge';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import './App.css';

// Pure function to calculate timestamp sync status
function calculateTimestampSyncStatus(frameAgeSeconds: number | null): {
  status: 'ok' | 'warning' | 'danger';
  colorClass: string;
  bgColorClass: string;
} {
  if (frameAgeSeconds === null) {
    return {
      status: 'ok',
      colorClass: 'text-gray-300',
      bgColorClass: 'bg-gray-700/50'
    };
  }
  
  if (frameAgeSeconds < 5) {
    return {
      status: 'ok',
      colorClass: 'text-green-400',
      bgColorClass: 'bg-green-500/20'
    };
  } else if (frameAgeSeconds < 10) {
    return {
      status: 'warning',
      colorClass: 'text-yellow-400',
      bgColorClass: 'bg-yellow-500/20'
    };
  } else {
    return {
      status: 'danger',
      colorClass: 'text-red-400',
      bgColorClass: 'bg-red-500/20'
    };
  }
}

function App() {
  const [controlsOpen, setControlsOpen] = useState(false);
  const [galleryOpen, setGalleryOpen] = useState(false);
  const { isHealthy } = useHealthCheck();
  const { appInfo, updateAvailable } = useAppInfo();
  const { streamStatus, streamConnected, timestamp: streamTimestamp, streamHealthy } = useStreamStatus();

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

  // Stream status is now handled by useStreamStatus hook


  const handleRefresh = () => {
    window.location.reload();
  };

  return (
    <div className="relative w-screen h-screen bg-gray-900 overflow-hidden">
      {/* Top controls */}
      <div className="absolute top-4 left-4 z-20 flex items-center space-x-3">
        {/* Power control */}
        <PowerControl />
        
        {/* Version display */}
        <div className="flex items-center space-x-2">
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
          streamHealthy ? 'bg-green-500/20' : 
          streamStatus?.status === 'degraded' ? 'bg-orange-500/20' :
          streamStatus?.status === 'stale' ? 'bg-red-500/20' :
          'bg-yellow-500/20'
        }`}>
          <div className={`w-2 h-2 rounded-full ${
            !isHealthy ? 'bg-red-500' : 
            streamHealthy ? 'bg-green-500' : 
            streamStatus?.status === 'degraded' ? 'bg-orange-500' :
            streamStatus?.status === 'stale' ? 'bg-red-500' :
            'bg-yellow-500'
          } animate-pulse`}></div>
          <span className="text-xs text-white">
            {!isHealthy ? 'Server Offline' : 
             streamHealthy ? 'Streaming' : 
             streamStatus?.status === 'degraded' ? 'Stream Issues' :
             streamStatus?.status === 'stale' ? 'Stream Stale' :
             'Connecting...'}
          </span>
        </div>
        
        {/* Frame timestamp - always show when available */}
        {streamTimestamp && (() => {
          const frameAge = streamStatus?.frame_age_seconds || null;
          const syncStatus = calculateTimestampSyncStatus(frameAge);
          const ageText = frameAge !== null ? `${frameAge.toFixed(1)}s delay` : 'No delay info';
          
          return (
            <div 
              className={`flex items-center space-x-2 px-3 py-1 rounded-full ${syncStatus.bgColorClass}`}
              title={ageText}
            >
              <svg className={`w-3 h-3 ${syncStatus.colorClass}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className={`text-xs font-mono ${syncStatus.colorClass}`}>
                {streamTimestamp}
              </span>
            </div>
          );
        })()}
      </div>

      {/* Main video stream */}
      <ErrorBoundary>
        <VideoStream 
          streamConnected={streamConnected}
          streamHealthy={streamHealthy}
          onRetryNeeded={() => {
            // Force a refresh of stream status when manual retry is requested
            window.location.reload();
          }}
        />
      </ErrorBoundary>

      {/* Gallery button - bottom left */}
      <button
        onClick={() => setGalleryOpen(true)}
        className="absolute bottom-8 left-8 z-20 w-12 h-12 bg-gray-700 hover:bg-gray-600 
                   text-white rounded-full shadow-lg transition-all duration-200 
                   flex items-center justify-center"
        aria-label="Open photo gallery"
      >
        <Images className="w-6 h-6" />
      </button>

      {/* Settings toggle button - only show when panel is closed */}
      {!controlsOpen && (
        <button
          onClick={() => setControlsOpen(true)}
          className="absolute bottom-8 right-8 z-20 w-12 h-12 bg-gray-700 hover:bg-gray-600 
                     text-white rounded-full shadow-lg transition-all duration-200 
                     flex items-center justify-center"
          aria-label="Open settings"
        >
          <Settings className="w-6 h-6" />
        </button>
      )}

      {/* Control panel */}
      <ErrorBoundary>
        <ControlPanel
          isOpen={controlsOpen}
          onToggle={() => setControlsOpen(prev => !prev)}
        />
      </ErrorBoundary>

      {/* Photo gallery */}
      <ErrorBoundary>
        <PhotoGallery
          isOpen={galleryOpen}
          onClose={() => setGalleryOpen(false)}
        />
      </ErrorBoundary>

      {/* PWA install badge */}
      <PWABadge />


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