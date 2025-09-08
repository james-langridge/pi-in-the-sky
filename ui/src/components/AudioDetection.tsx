import { useState, useEffect } from 'react';
import { Mic, MicOff, AlertCircle } from 'lucide-react';
import { toast } from 'react-toastify';

interface AudioDetectionConfig {
  enabled: boolean;
  threshold: number;
  duration_threshold: number;
  cooldown_seconds: number;
}

interface AudioDetectionProps {
  onAudioDetected?: () => void;
  visualAlertsEnabled: boolean;
  onVisualAlertsToggle: (enabled: boolean) => void;
  soundAlertsEnabled: boolean;
  onSoundAlertsToggle: (enabled: boolean) => void;
}

export function AudioDetection({ 
  onAudioDetected, 
  visualAlertsEnabled, 
  onVisualAlertsToggle,
  soundAlertsEnabled,
  onSoundAlertsToggle
}: AudioDetectionProps) {
  const [isEnabled, setIsEnabled] = useState(false);
  const [config, setConfig] = useState<AudioDetectionConfig>({
    enabled: false,
    threshold: 0.05,
    duration_threshold: 0.5,
    cooldown_seconds: 30
  });
  const [isLoading, setIsLoading] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [lastDetectionTime, setLastDetectionTime] = useState<number>(0);

  // Load current status on mount
  useEffect(() => {
    fetchStatus();
  }, []);

  // Poll for audio detection events when enabled
  useEffect(() => {
    if (!isEnabled || !visualAlertsEnabled) return;

    const checkAudioDetection = async () => {
      try {
        const response = await fetch('/api/audio/detection/status');
        const data = await response.json();
        if (data.detected && data.timestamp) {
          const detectionTime = new Date(data.timestamp).getTime();
          if (detectionTime > lastDetectionTime) {
            setLastDetectionTime(detectionTime);
            onAudioDetected?.();
          }
        }
      } catch (error) {
        console.error('Failed to check audio detection:', error);
      }
    };

    // Check immediately and then every 2 seconds
    checkAudioDetection();
    const interval = setInterval(checkAudioDetection, 2000);

    return () => clearInterval(interval);
  }, [isEnabled, visualAlertsEnabled, lastDetectionTime, onAudioDetected]);

  const fetchStatus = async () => {
    try {
      const response = await fetch('/api/audio/detection/config');
      const data = await response.json();
      if (data.status === 'success') {
        setConfig({
          enabled: data.enabled,
          threshold: data.threshold,
          duration_threshold: data.duration_threshold,
          cooldown_seconds: data.cooldown_seconds
        });
        setIsEnabled(data.enabled);
      }
    } catch (error) {
      console.error('Failed to fetch audio detection status:', error);
    }
  };

  const handleToggle = async () => {
    setIsLoading(true);
    const newEnabled = !isEnabled;

    try {
      // Handle notifications permission if enabling
      if (newEnabled && 'Notification' in window) {
        if (Notification.permission === 'default') {
          const permission = await Notification.requestPermission();
          if (permission !== 'granted') {
            toast.error('Notifications permission required for audio detection');
            setIsLoading(false);
            return;
          }
        } else if (Notification.permission === 'denied') {
          toast.error('Please enable notifications in your browser settings');
          setIsLoading(false);
          return;
        }

        // Subscribe to push notifications if not already subscribed
        if ('serviceWorker' in navigator && 'PushManager' in window) {
          try {
            const registration = await navigator.serviceWorker.ready;
            const subscription = await registration.pushManager.getSubscription();
            
            if (!subscription) {
              // Get VAPID key from server
              const vapidResponse = await fetch('/api/push/vapid-key');
              const vapidData = await vapidResponse.json();
              
              if (vapidData.publicKey) {
                // Subscribe to push
                const newSubscription = await registration.pushManager.subscribe({
                  userVisibleOnly: true,
                  applicationServerKey: vapidData.publicKey
                });

                // Send subscription to server
                await fetch('/api/push/subscribe', {
                  method: 'POST',
                  headers: {
                    'Content-Type': 'application/json',
                  },
                  body: JSON.stringify(newSubscription)
                });
              }
            }
          } catch (error) {
            console.error('Failed to setup push notifications:', error);
            toast.warning('Audio detection enabled but notifications may not work');
          }
        }
      }

      // Update audio detection config
      const response = await fetch('/api/audio/detection/config', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...config,
          enabled: newEnabled
        })
      });

      const data = await response.json();
      
      if (data.status === 'success') {
        setIsEnabled(newEnabled);
        setConfig(prev => ({ ...prev, enabled: newEnabled }));
        toast.success(newEnabled ? 'Audio detection enabled' : 'Audio detection disabled');
      } else {
        toast.error(data.message || 'Failed to update audio detection');
      }
    } catch (error) {
      console.error('Failed to toggle audio detection:', error);
      toast.error('Failed to toggle audio detection');
    } finally {
      setIsLoading(false);
    }
  };

  const handleConfigUpdate = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/audio/detection/config', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config)
      });

      const data = await response.json();
      
      if (data.status === 'success') {
        toast.success('Audio detection settings updated');
        setShowSettings(false);
      } else {
        toast.error(data.message || 'Failed to update settings');
      }
    } catch (error) {
      console.error('Failed to update audio detection config:', error);
      toast.error('Failed to update settings');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Alert Settings */}
      <div className="space-y-3">
        {/* Visual Alert Toggle */}
        <div className="p-4 bg-gray-700 rounded-lg">
          <div className="flex items-center justify-between">
            <span className="text-gray-200 font-medium">Visual Screen Alerts</span>
            <button
              onClick={() => onVisualAlertsToggle(!visualAlertsEnabled)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                visualAlertsEnabled ? 'bg-blue-500' : 'bg-gray-600'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  visualAlertsEnabled ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
          <p className="text-xs text-gray-400 mt-1">
            Flash yellow screen when audio is detected
          </p>
        </div>

        {/* Sound Alert Toggle */}
        <div className="p-4 bg-gray-700 rounded-lg">
          <div className="flex items-center justify-between">
            <span className="text-gray-200 font-medium">Sound Alerts</span>
            <button
              onClick={() => onSoundAlertsToggle(!soundAlertsEnabled)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                soundAlertsEnabled ? 'bg-blue-500' : 'bg-gray-600'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  soundAlertsEnabled ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
          <p className="text-xs text-gray-400 mt-1">
            Play beep when audio is detected
          </p>
        </div>
      </div>

      {/* Audio Detection Control */}
      <div className="relative">
      <button
        onClick={handleToggle}
        disabled={isLoading}
        className={`p-3 rounded-lg transition-all flex items-center space-x-2 ${
          isEnabled
            ? 'bg-green-600 hover:bg-green-700 text-white'
            : 'bg-gray-600 hover:bg-gray-700 text-white'
        } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
        title={isEnabled ? 'Disable audio detection' : 'Enable audio detection'}
      >
        {isEnabled ? (
          <Mic className="w-5 h-5" />
        ) : (
          <MicOff className="w-5 h-5" />
        )}
        <span className="text-sm font-medium">
          {isEnabled ? 'Audio Detection On' : 'Audio Detection Off'}
        </span>
      </button>

      {isEnabled && (
        <button
          onClick={() => setShowSettings(!showSettings)}
          className="absolute top-0 right-0 -mr-2 -mt-2 p-1 bg-gray-700 rounded-full hover:bg-gray-600 transition-colors"
        >
          <AlertCircle className="w-4 h-4 text-gray-300" />
        </button>
      )}

        {/* Settings Dropdown */}
        {showSettings && (
          <div className="absolute top-full left-0 mt-2 w-72 bg-gray-800 rounded-lg shadow-lg p-4 z-50">
            <h3 className="text-white font-medium mb-3">Audio Detection Settings</h3>
            
            <div className="space-y-3">
              <div>
                <label className="text-gray-300 text-sm">
                  Sensitivity (RMS Threshold)
                </label>
                <input
                  type="range"
                  min="0.01"
                  max="0.2"
                  step="0.01"
                  value={config.threshold}
                  onChange={(e) => setConfig(prev => ({ ...prev, threshold: parseFloat(e.target.value) }))}
                  className="w-full mt-1"
                />
                <span className="text-gray-400 text-xs">{(config.threshold * 100).toFixed(0)}%</span>
              </div>

              <div>
                <label className="text-gray-300 text-sm">
                  Minimum Duration (seconds)
                </label>
                <input
                  type="number"
                  min="0.1"
                  max="5"
                  step="0.1"
                  value={config.duration_threshold}
                  onChange={(e) => setConfig(prev => ({ ...prev, duration_threshold: parseFloat(e.target.value) }))}
                  className="w-full mt-1 px-2 py-1 bg-gray-700 text-white rounded"
                />
              </div>

              <div>
                <label className="text-gray-300 text-sm">
                  Cooldown Period (seconds)
                </label>
                <input
                  type="number"
                  min="10"
                  max="300"
                  step="10"
                  value={config.cooldown_seconds}
                  onChange={(e) => setConfig(prev => ({ ...prev, cooldown_seconds: parseInt(e.target.value) }))}
                  className="w-full mt-1 px-2 py-1 bg-gray-700 text-white rounded"
                />
              </div>
            </div>

            <div className="flex space-x-2 mt-4">
              <button
                onClick={handleConfigUpdate}
                disabled={isLoading}
                className="flex-1 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors disabled:opacity-50"
              >
                Save
              </button>
              <button
                onClick={() => setShowSettings(false)}
                className="flex-1 px-3 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}