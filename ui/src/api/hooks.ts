import { useState, useEffect, useCallback } from 'react';
import { api } from './client';
import type {
  HealthResponse,
  CameraControl,
  MotionStatus,
  MotionConfig,
  MotionEvent,
  AppInfo,
  CameraPreset
} from '../types';

// Generic hook for API calls with loading and error states
export function useApiCall<T>(
  apiCall: () => Promise<T>,
  dependencies: any[] = []
) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let cancelled = false;

    const fetchData = async () => {
      try {
        setLoading(true);
        const result = await apiCall();
        if (!cancelled) {
          setData(result);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err : new Error('Unknown error'));
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    fetchData();

    return () => {
      cancelled = true;
    };
  }, dependencies);

  return { data, loading, error, refetch: () => useApiCall(apiCall, [...dependencies, Date.now()]) };
}

// Health check hook with auto-refresh
export function useHealthCheck(interval = 5000) {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [isHealthy, setIsHealthy] = useState(true);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await api.getHealth();
        setHealth(response);
        setIsHealthy(true);
      } catch {
        setIsHealthy(false);
      }
    };

    checkHealth();
    const timer = setInterval(checkHealth, interval);

    return () => clearInterval(timer);
  }, [interval]);

  return { health, isHealthy };
}

// Camera presets hook
export function useCameraPresets() {
  const { data: presets, loading, error } = useApiCall(() => api.getPresets());

  const applyPreset = useCallback(async (preset: CameraPreset) => {
    try {
      await api.applyPreset(preset);
      return true;
    } catch (error) {
      console.error('Failed to apply preset:', error);
      return false;
    }
  }, []);

  return { presets, loading, error, applyPreset };
}

// Camera controls hook
export function useCameraControls() {
  const [controls, setControls] = useState<CameraControl[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchControls = async () => {
      try {
        const data = await api.getControls();
        setControls(data);
      } catch (error) {
        console.error('Failed to fetch controls:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchControls();
  }, []);

  const updateControl = useCallback(async (controlId: string, value: number | boolean | string) => {
    try {
      await api.updateControl(controlId, value);
      // Update local state optimistically
      setControls(prev =>
        prev.map(control =>
          control.id === controlId ? { ...control, value } : control
        )
      );
      return true;
    } catch (error) {
      console.error('Failed to update control:', error);
      return false;
    }
  }, []);

  return { controls, loading, updateControl };
}

// Motion detection hook
export function useMotionDetection() {
  const [status, setStatus] = useState<MotionStatus | null>(null);
  const [events, setEvents] = useState<MotionEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const [statusData, eventsData] = await Promise.all([
          api.getMotionStatus(),
          api.getMotionEvents()
        ]);
        setStatus(statusData);
        setEvents(eventsData);
      } catch (error) {
        console.error('Failed to fetch motion data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchStatus();
    // Poll for updates every 3 seconds
    const interval = setInterval(fetchStatus, 3000);

    return () => clearInterval(interval);
  }, []);

  const updateConfig = useCallback(async (config: Partial<MotionConfig>) => {
    try {
      await api.updateMotionConfig(config);
      // Update local state optimistically
      if (status) {
        setStatus({
          ...status,
          config: { ...status.config, ...config }
        });
      }
      return true;
    } catch (error) {
      console.error('Failed to update motion config:', error);
      return false;
    }
  }, [status]);

  const toggleMotion = useCallback(async () => {
    if (!status) return false;
    return updateConfig({ enabled: !status.enabled });
  }, [status, updateConfig]);

  return {
    status,
    events,
    loading,
    updateConfig,
    toggleMotion
  };
}

// Push notifications hook
export function usePushNotifications() {
  const [subscribed, setSubscribed] = useState(false);
  const [subscription, setSubscription] = useState<PushSubscriptionJSON | null>(null);

  useEffect(() => {
    // Check if already subscribed
    if ('serviceWorker' in navigator && 'PushManager' in window) {
      navigator.serviceWorker.ready.then(async (registration) => {
        const sub = await registration.pushManager.getSubscription();
        if (sub) {
          setSubscription(sub.toJSON());
          setSubscribed(true);
        }
      });
    }
  }, []);

  const subscribe = useCallback(async () => {
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
      throw new Error('Push notifications not supported');
    }

    const registration = await navigator.serviceWorker.ready;
    const vapidKey = await api.getVapidKey();

    const subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: vapidKey
    });

    const subJson = subscription.toJSON();
    await api.subscribeToPush({
      endpoint: subJson.endpoint!,
      keys: {
        p256dh: subJson.keys!.p256dh!,
        auth: subJson.keys!.auth!
      }
    });

    setSubscription(subJson);
    setSubscribed(true);
    return true;
  }, []);

  const unsubscribe = useCallback(async () => {
    if (!subscription) return false;

    try {
      await api.unsubscribeFromPush(subscription.endpoint!);
      
      const registration = await navigator.serviceWorker.ready;
      const sub = await registration.pushManager.getSubscription();
      if (sub) {
        await sub.unsubscribe();
      }

      setSubscription(null);
      setSubscribed(false);
      return true;
    } catch (error) {
      console.error('Failed to unsubscribe:', error);
      return false;
    }
  }, [subscription]);

  const testNotification = useCallback(async () => {
    if (!subscription) return false;

    try {
      await api.testPushNotification(subscription.endpoint!);
      return true;
    } catch (error) {
      console.error('Failed to send test notification:', error);
      return false;
    }
  }, [subscription]);

  return {
    subscribed,
    subscription,
    subscribe,
    unsubscribe,
    testNotification
  };
}

// App info hook with version checking
export function useAppInfo() {
  const [appInfo, setAppInfo] = useState<AppInfo | null>(null);
  const [updateAvailable, setUpdateAvailable] = useState(false);

  useEffect(() => {
    const checkVersion = async () => {
      try {
        const info = await api.getAppInfo();
        setAppInfo(info);
        
        // Check if version changed (simplified check)
        const savedVersion = localStorage.getItem('app_version');
        if (savedVersion && savedVersion !== info.version) {
          setUpdateAvailable(true);
        }
        localStorage.setItem('app_version', info.version);
      } catch (error) {
        console.error('Failed to fetch app info:', error);
      }
    };

    checkVersion();
    // Check for updates every minute
    const interval = setInterval(checkVersion, 60000);

    return () => clearInterval(interval);
  }, []);

  return { appInfo, updateAvailable };
}