import { useState, useEffect } from 'react';
import { useMotionDetection, usePushNotifications } from '../api/hooks';
import { MOTION_PRESETS } from '../types';
import { toast } from 'react-toastify';

export function MotionDetection() {
  const { status, events, loading, updateConfig, toggleMotion } = useMotionDetection();
  const { subscribed, subscribe, unsubscribe, testNotification } = usePushNotifications();
  const [selectedPreset, setSelectedPreset] = useState('normal');
  const [isApplyingPreset, setIsApplyingPreset] = useState(false);
  const [isTestingNotification, setIsTestingNotification] = useState(false);

  // Request notification permission when enabling motion detection
  useEffect(() => {
    if (status?.enabled && !subscribed && 'Notification' in window) {
      if (Notification.permission === 'default') {
        Notification.requestPermission();
      }
    }
  }, [status?.enabled, subscribed]);

  const handleToggleMotion = async () => {
    if (!status) return;

    try {
      if (!status.enabled) {
        // Enable motion detection
        await toggleMotion();
        toast.success('Motion detection enabled');
        
        // Subscribe to push notifications if not already
        if (!subscribed && 'Notification' in window) {
          if (Notification.permission === 'granted') {
            await subscribe();
            toast.success('Push notifications enabled');
          } else if (Notification.permission === 'default') {
            const permission = await Notification.requestPermission();
            if (permission === 'granted') {
              await subscribe();
              toast.success('Push notifications enabled');
            }
          }
        }
      } else {
        // Disable motion detection
        await toggleMotion();
        toast.info('Motion detection disabled');
      }
    } catch (error) {
      toast.error('Failed to toggle motion detection');
      console.error('Toggle motion error:', error);
    }
  };

  const handleApplyPreset = async () => {
    const preset = MOTION_PRESETS[selectedPreset];
    if (!preset) return;

    setIsApplyingPreset(true);
    try {
      await updateConfig(preset.config);
      toast.success(`Applied "${preset.name}" preset`);
    } catch (error) {
      toast.error('Failed to apply preset');
      console.error('Apply preset error:', error);
    } finally {
      setIsApplyingPreset(false);
    }
  };

  const handleTestNotification = async () => {
    setIsTestingNotification(true);
    try {
      await testNotification();
      toast.success('Test notification sent');
    } catch (error) {
      toast.error('Failed to send test notification');
      console.error('Test notification error:', error);
    } finally {
      setIsTestingNotification(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  const recentTriggeredEvents = events.filter(e => e.triggered).slice(0, 5);

  return (
    <div className="space-y-6">
      {/* Status Header */}
      <div className="flex items-center justify-between p-4 bg-gray-700 rounded-lg">
        <div className="flex items-center space-x-3">
          <div className={`w-3 h-3 rounded-full ${
            status?.enabled ? 'bg-green-500 animate-pulse' : 'bg-gray-500'
          }`}></div>
          <span className="text-gray-200 font-medium">
            Motion Detection: {status?.enabled ? 'Active' : 'Inactive'}
          </span>
        </div>
        <button
          onClick={handleToggleMotion}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            status?.enabled
              ? 'bg-red-500 hover:bg-red-600 text-white'
              : 'bg-green-500 hover:bg-green-600 text-white'
          }`}
        >
          {status?.enabled ? 'Disable' : 'Enable'}
        </button>
      </div>

      {/* Push Notifications Status */}
      <div className="p-4 bg-gray-700 rounded-lg">
        <div className="flex items-center justify-between mb-3">
          <span className="text-gray-200 font-medium">Push Notifications</span>
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${
              subscribed ? 'bg-green-500' : 'bg-gray-500'
            }`}></div>
            <span className="text-sm text-gray-400">
              {subscribed ? 'Subscribed' : 'Not subscribed'}
            </span>
          </div>
        </div>

        {subscribed ? (
          <div className="flex space-x-2">
            <button
              onClick={handleTestNotification}
              disabled={isTestingNotification}
              className="flex-1 px-3 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded 
                       transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isTestingNotification ? 'Sending...' : 'Test Notification'}
            </button>
            <button
              onClick={async () => {
                try {
                  await unsubscribe();
                  toast.info('Push notifications disabled');
                } catch (error) {
                  toast.error('Failed to unsubscribe');
                  console.error('Unsubscribe error:', error);
                }
              }}
              className="px-3 py-2 bg-gray-600 hover:bg-gray-500 text-white rounded transition-colors"
            >
              Unsubscribe
            </button>
          </div>
        ) : (
          <button
            onClick={async () => {
              try {
                await subscribe();
                toast.success('Push notifications enabled');
              } catch (error) {
                toast.error('Failed to enable push notifications');
                console.error('Subscribe error:', error);
              }
            }}
            className="w-full px-3 py-2 bg-green-500 hover:bg-green-600 text-white rounded transition-colors"
          >
            Enable Push Notifications
          </button>
        )}
      </div>

      {/* Preset Selection */}
      <div className="space-y-3">
        <label className="text-sm font-medium text-gray-300">Detection Preset</label>
        <select
          value={selectedPreset}
          onChange={(e) => setSelectedPreset(e.target.value)}
          className="w-full px-3 py-2 bg-gray-700 text-gray-200 rounded-lg border border-gray-600 
                   focus:border-blue-500 focus:outline-none"
        >
          {Object.entries(MOTION_PRESETS).map(([key, preset]) => (
            <option key={key} value={key}>
              {preset.name} - {preset.description}
            </option>
          ))}
        </select>
        <button
          onClick={handleApplyPreset}
          disabled={isApplyingPreset || !status?.enabled}
          className="w-full px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg 
                   transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isApplyingPreset ? 'Applying...' : 'Apply Preset'}
        </button>
      </div>

      {/* Current Configuration */}
      {status && (
        <div className="p-4 bg-gray-700/50 rounded-lg space-y-2">
          <h4 className="text-sm font-medium text-gray-300 mb-3">Current Settings</h4>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <span className="text-gray-400">Sensitivity:</span>
              <span className="ml-2 text-gray-200">{status.config.sensitivity}</span>
            </div>
            <div>
              <span className="text-gray-400">Min Area:</span>
              <span className="ml-2 text-gray-200">{status.config.min_area}px</span>
            </div>
            <div>
              <span className="text-gray-400">Cooldown:</span>
              <span className="ml-2 text-gray-200">{status.config.cooldown_seconds}s</span>
            </div>
            <div>
              <span className="text-gray-400">Recent Events:</span>
              <span className="ml-2 text-gray-200">{status.recent_events}</span>
            </div>
          </div>
        </div>
      )}

      {/* Recent Events */}
      {recentTriggeredEvents.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-300">Recent Motion Events</h4>
          <div className="space-y-1 max-h-32 overflow-y-auto">
            {recentTriggeredEvents.map((event, index) => (
              <div
                key={index}
                className="flex justify-between items-center p-2 bg-gray-700/50 rounded text-sm"
              >
                <span className="text-gray-300">
                  {new Date(event.timestamp).toLocaleTimeString()}
                </span>
                <div className="flex items-center space-x-3 text-gray-400">
                  <span>Area: {event.area}px</span>
                  <span>Objects: {event.contours}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}