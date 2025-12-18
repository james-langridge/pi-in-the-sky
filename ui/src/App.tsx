import { useState, useEffect, useCallback } from 'react';
import { Settings, Images } from 'lucide-react';
import { VideoStream } from './components/VideoStream';
import { ControlPanel } from './components/ControlPanel';
import { PhotoGallery } from './components/PhotoGallery';
import { PowerControl } from './components/PowerControl';
import ZoomControl from './components/ZoomControl';
import { BreathingZoneSelector } from './components/BreathingZoneSelector';
import { BreathingStatusBadge } from './components/BreathingStatusBadge';
import { ErrorBoundary } from './components/ErrorBoundary';
import { useAppInfo } from './api/hooks';
import { useOptimizedStreamStatus, useOptimizedBreathingDetection } from './api/optimized-hooks';
import { playMotionAlert, playAudioAlert, isAudioSupported } from './utils/alertSounds';
import { loadZoomLevel, saveZoomLevel } from './utils/zoomCalculations';
import PWABadge from './PWABadge';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import './App.css';

// Pure function to calculate unified stream status
// Frame age is the source of truth - if frames are fresh, system works
function calculateUnifiedStatus(
  mode: 'connecting' | 'sse' | 'disconnected',
  frameAge: number | null,
  timestamp: string | null
): {
  label: string;
  dotColor: string;
  bgColor: string;
  title: string;
  severity: 'ok' | 'warning' | 'danger';
} {
  // Still establishing initial connection
  if (mode === 'connecting') {
    return {
      label: 'Connecting...',
      dotColor: 'bg-yellow-500',
      bgColor: 'bg-yellow-500/20',
      title: 'Establishing connection',
      severity: 'ok',
    };
  }

  // Lost connection after being connected
  if (mode === 'disconnected') {
    return {
      label: 'Offline',
      dotColor: 'bg-red-500',
      bgColor: 'bg-red-500/20',
      title: 'Connection lost',
      severity: 'danger',
    };
  }

  // Connected but no stream data yet
  if (!timestamp) {
    return {
      label: 'Connecting...',
      dotColor: 'bg-yellow-500',
      bgColor: 'bg-yellow-500/20',
      title: 'Waiting for stream',
      severity: 'ok',
    };
  }

  const age = frameAge ?? 0;

  if (age < 2) {
    return {
      label: 'Live',
      dotColor: 'bg-green-500',
      bgColor: 'bg-green-500/20',
      title: `${age.toFixed(1)}s delay`,
      severity: 'ok',
    };
  }

  if (age < 5) {
    return {
      label: `${age.toFixed(1)}s delay`,
      dotColor: 'bg-green-400',
      bgColor: 'bg-green-500/20',
      title: timestamp,
      severity: 'ok',
    };
  }

  if (age < 10) {
    return {
      label: `${age.toFixed(1)}s delay`,
      dotColor: 'bg-orange-500',
      bgColor: 'bg-orange-500/20',
      title: timestamp,
      severity: 'warning',
    };
  }

  return {
    label: `Stale (${age.toFixed(0)}s)`,
    dotColor: 'bg-red-500',
    bgColor: 'bg-red-500/20',
    title: timestamp,
    severity: 'danger',
  };
}

function App() {
  const [controlsOpen, setControlsOpen] = useState(false);
  const [galleryOpen, setGalleryOpen] = useState(false);
  const [zoomPanelOpen, setZoomPanelOpen] = useState(false);
  const [showDetectionPulse, setShowDetectionPulse] = useState(false);
  const [lastPulseTime, setLastPulseTime] = useState(0);
  const [zoomLevel, setZoomLevel] = useState(() => loadZoomLevel(0));
  const [zoneSelectorActive, setZoneSelectorActive] = useState(false);
  const [motionVisualAlertsEnabled, setMotionVisualAlertsEnabled] = useState(() => {
    return localStorage.getItem('motionVisualAlerts') !== 'false';
  });
  const [audioVisualAlertsEnabled, setAudioVisualAlertsEnabled] = useState(() => {
    return localStorage.getItem('audioVisualAlerts') !== 'false';
  });
  const [motionSoundAlertsEnabled, setMotionSoundAlertsEnabled] = useState(() => {
    return localStorage.getItem('motionSoundAlerts') === 'true';
  });
  const [audioSoundAlertsEnabled, setAudioSoundAlertsEnabled] = useState(() => {
    return localStorage.getItem('audioSoundAlerts') === 'true';
  });

  const { appInfo, updateAvailable } = useAppInfo();
  const { streamStatus, streamConnected, timestamp: streamTimestamp, streamHealthy, mode } = useOptimizedStreamStatus();
  const { status: breathingStatus, setZone: setBreathingZone } = useOptimizedBreathingDetection();

  const status = calculateUnifiedStatus(
    mode as 'connecting' | 'sse' | 'disconnected',
    streamStatus?.frame_age_seconds ?? null,
    streamTimestamp || null
  );

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

  // Handle detection pulses with 5-second cooldown
  const triggerDetectionPulse = () => {
    const now = Date.now();
    const timeSinceLastPulse = now - lastPulseTime;
    
    // Only pulse if 5 seconds have passed since last pulse
    if (timeSinceLastPulse >= 5000) {
      setShowDetectionPulse(true);
      setLastPulseTime(now);
      
      // Remove pulse after animation completes
      setTimeout(() => {
        setShowDetectionPulse(false);
      }, 1000);
    }
  };

  const handleMotionDetected = () => {
    if (motionVisualAlertsEnabled) {
      triggerDetectionPulse();
    }
    if (motionSoundAlertsEnabled && isAudioSupported()) {
      const now = Date.now();
      const timeSinceLastPulse = now - lastPulseTime;
      // Use same cooldown for sound as visual pulse
      if (timeSinceLastPulse >= 5000) {
        playMotionAlert();
      }
    }
  };

  const handleAudioDetected = () => {
    if (audioVisualAlertsEnabled) {
      triggerDetectionPulse();
    }
    if (audioSoundAlertsEnabled && isAudioSupported()) {
      const now = Date.now();
      const timeSinceLastPulse = now - lastPulseTime;
      // Use same cooldown for sound as visual pulse
      if (timeSinceLastPulse >= 5000) {
        playAudioAlert();
      }
    }
  };

  const handleMotionVisualAlertsToggle = (enabled: boolean) => {
    setMotionVisualAlertsEnabled(enabled);
    localStorage.setItem('motionVisualAlerts', enabled.toString());
  };

  const handleAudioVisualAlertsToggle = (enabled: boolean) => {
    setAudioVisualAlertsEnabled(enabled);
    localStorage.setItem('audioVisualAlerts', enabled.toString());
  };

  const handleMotionSoundAlertsToggle = (enabled: boolean) => {
    setMotionSoundAlertsEnabled(enabled);
    localStorage.setItem('motionSoundAlerts', enabled.toString());
  };

  const handleAudioSoundAlertsToggle = (enabled: boolean) => {
    setAudioSoundAlertsEnabled(enabled);
    localStorage.setItem('audioSoundAlerts', enabled.toString());
  };

  const handleZoomChange = (newZoom: number) => {
    setZoomLevel(newZoom);
    saveZoomLevel(newZoom);
  };

  const handleStartZoneSelection = useCallback(() => {
    setZoneSelectorActive(true);
  }, []);

  const handleZoneSave = useCallback(async (zone: { x: number; y: number; width: number; height: number }) => {
    const success = await setBreathingZone(zone);
    if (success) {
      setZoneSelectorActive(false);
    }
  }, [setBreathingZone]);

  const handleZoneCancel = useCallback(() => {
    setZoneSelectorActive(false);
  }, []);

  // Assume standard video dimensions (can be made dynamic)
  const VIDEO_WIDTH = 1280;
  const VIDEO_HEIGHT = 720;

  return (
    <div className="relative w-screen h-screen bg-gray-900 overflow-hidden">
      {/* Sync warning overlay - pulses when out of sync */}
      {status.severity === 'warning' && (
        <div className="absolute inset-0 bg-yellow-500 pulse-warning-overlay pointer-events-none z-10"></div>
      )}
      {status.severity === 'danger' && (
        <div className="absolute inset-0 bg-red-500 pulse-danger-overlay pointer-events-none z-10"></div>
      )}
      
      {/* Detection pulse overlay - single pulse for motion/audio detection */}
      {showDetectionPulse && (
        <div className="absolute inset-0 bg-yellow-400 pulse-detection-overlay pointer-events-none z-10"></div>
      )}
      
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

      {/* Stream status indicator - hide when control panel open on desktop */}
      {!controlsOpen && (
        <div className="absolute top-4 right-4 z-20 flex items-center space-x-2">
          {/* Breathing status badge */}
          <BreathingStatusBadge status={breathingStatus} compact />

          {/* Stream status */}
          <div
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-full ${status.bgColor}`}
            title={status.title}
          >
            <div className={`w-2 h-2 rounded-full ${status.dotColor} animate-pulse`} />
            <span className="text-xs text-white">{status.label}</span>
          </div>
        </div>
      )}

      {/* Main video stream */}
      <ErrorBoundary>
        <VideoStream
          streamConnected={streamConnected}
          streamHealthy={streamHealthy}
          onRetryNeeded={() => {
            // Force a refresh of stream status when manual retry is requested
            window.location.reload();
          }}
          zoomLevel={zoomLevel}
          controlsOpen={controlsOpen}
        />
      </ErrorBoundary>

      {/* Gallery button - bottom left (hide when control panel open) */}
      {!controlsOpen && (
        <button
          onClick={() => setGalleryOpen(true)}
          className="absolute bottom-8 left-8 z-20 w-12 h-12 bg-gray-700 hover:bg-gray-600
                     text-white rounded-full shadow-lg transition-all duration-200
                     flex items-center justify-center"
          aria-label="Open photo gallery"
        >
          <Images className="w-6 h-6" />
        </button>
      )}

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

      {/* Zoom control - right of center at bottom (hide when control panel open) */}
      {!controlsOpen && (
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 ml-16 z-20">
          <ErrorBoundary>
            <ZoomControl
              zoomLevel={zoomLevel}
              onZoomChange={handleZoomChange}
              isOpen={zoomPanelOpen}
              onToggle={() => setZoomPanelOpen(prev => !prev)}
            />
          </ErrorBoundary>
        </div>
      )}

      {/* Control panel */}
      <ErrorBoundary>
        <ControlPanel
          isOpen={controlsOpen}
          onToggle={() => setControlsOpen(prev => !prev)}
          onMotionDetected={handleMotionDetected}
          onAudioDetected={handleAudioDetected}
          motionVisualAlertsEnabled={motionVisualAlertsEnabled}
          onMotionVisualAlertsToggle={handleMotionVisualAlertsToggle}
          audioVisualAlertsEnabled={audioVisualAlertsEnabled}
          onAudioVisualAlertsToggle={handleAudioVisualAlertsToggle}
          motionSoundAlertsEnabled={motionSoundAlertsEnabled}
          onMotionSoundAlertsToggle={handleMotionSoundAlertsToggle}
          audioSoundAlertsEnabled={audioSoundAlertsEnabled}
          onAudioSoundAlertsToggle={handleAudioSoundAlertsToggle}
          onStartZoneSelection={handleStartZoneSelection}
        />
      </ErrorBoundary>

      {/* Breathing zone selector overlay */}
      {zoneSelectorActive && (
        <ErrorBoundary>
          <BreathingZoneSelector
            videoWidth={VIDEO_WIDTH}
            videoHeight={VIDEO_HEIGHT}
            onSave={handleZoneSave}
            onCancel={handleZoneCancel}
          />
        </ErrorBoundary>
      )}

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