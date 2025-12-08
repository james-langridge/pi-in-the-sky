/**
 * Optimized React hooks that use SSE with smart polling fallback.
 * Dramatically reduces server load while maintaining real-time updates.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { api } from './client';
import { useSSE, useSmartPolling } from './sse';
import type {
  HealthResponse,
  MotionStatus,
  MotionConfig,
  MotionEvent,
  StreamStatus,
  LogEntry
} from '../types';

/**
 * Optimized health check using SSE with smart polling fallback.
 */
export function useOptimizedHealthCheck() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [isHealthy, setIsHealthy] = useState(true);
  const [useSSEMode, setUseSSEMode] = useState(true);

  // Try SSE first
  const { connected: sseConnected } = useSSE({
    onHealth: (data) => {
      setHealth(data as HealthResponse);
      setIsHealthy(true);
      setUseSSEMode(true);
    },
    onError: () => {
      // Fall back to polling if SSE fails
      setUseSSEMode(false);
    },
  });

  // Smart polling as fallback (only active when SSE is not connected)
  useSmartPolling(
    () => api.getHealth(),
    {
      initialInterval: 10000, // Start at 10s instead of 5s
      maxInterval: 60000,     // Can go up to 60s when stable
      minInterval: 5000,      // Never faster than 5s
      enabled: !sseConnected && !useSSEMode,
      onSuccess: (data) => {
        setHealth(data);
        setIsHealthy(true);
      },
      onError: () => {
        setIsHealthy(false);
      }
    }
  );

  return { health, isHealthy, mode: sseConnected ? 'sse' : 'polling' };
}

/**
 * Optimized stream status using SSE with smart polling fallback.
 */
export function useOptimizedStreamStatus() {
  const [streamStatus, setStreamStatus] = useState<StreamStatus | null>(null);
  const [streamConnected, setStreamConnected] = useState(false);
  const [useSSEMode, setUseSSEMode] = useState(true);

  // SSE for real-time updates
  const { connected: sseConnected } = useSSE({
    onStreamStatus: (status: StreamStatus) => {
      setStreamStatus(status);
      const connected = status.healthy && status.status === 'streaming';
      setStreamConnected(connected);
      setUseSSEMode(true);
    },
    onError: () => {
      setUseSSEMode(false);
    }
  });

  // Smart polling fallback with adaptive intervals
  useSmartPolling(
    () => api.getStreamStatus(),
    {
      initialInterval: 3000,  // Start at 3s for stream status
      maxInterval: 15000,     // Max 15s when stable
      minInterval: 2000,      // Min 2s for responsiveness
      enabled: !sseConnected && !useSSEMode,
      onSuccess: (status) => {
        setStreamStatus(status);
        const connected = status.healthy && status.status === 'streaming';
        setStreamConnected(connected);
      },
      onError: () => {
        setStreamConnected(false);
        setStreamStatus(prev => prev ? { ...prev, healthy: false, status: 'waiting' } : null);
      }
    }
  );

  return {
    streamStatus,
    streamConnected,
    timestamp: streamStatus?.timestamp || '',
    streamHealthy: streamStatus?.healthy || false,
    mode: sseConnected ? 'sse' : 'polling'
  };
}

/**
 * Conditional log fetching - only active when viewer is open.
 */
export function useConditionalLogs(
  enabled: boolean,
  limit = 200,
  source: 'memory' | 'file' = 'memory'
) {
  const [entries, setEntries] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const sseActiveRef = useRef(false);

  // Manual fetch function
  const fetchLogs = useCallback(async () => {
    if (!enabled) return;
    
    try {
      setLoading(true);
      const response = await api.getLogs(limit, source);
      setEntries(response.entries);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch logs'));
    } finally {
      setLoading(false);
    }
  }, [enabled, limit, source]);

  // SSE for streaming new log entries when viewer is open
  useSSE({
    onLogEntry: (entry) => {
      if (enabled && sseActiveRef.current) {
        setEntries((prev) => [...prev.slice(-limit + 1), entry as LogEntry]);
      }
    },
  });

  // Initial fetch when enabled
  useEffect(() => {
    if (enabled) {
      sseActiveRef.current = true;
      fetchLogs();
    } else {
      sseActiveRef.current = false;
      setEntries([]);
    }
  }, [enabled, fetchLogs]);

  return { 
    entries, 
    loading, 
    error, 
    refetch: fetchLogs,
    clear: () => setEntries([])
  };
}

/**
 * Optimized motion detection using SSE.
 */
export function useOptimizedMotionDetection() {
  const [status, setStatus] = useState<MotionStatus | null>(null);
  const [events, setEvents] = useState<MotionEvent[]>([]);
  const [loading, setLoading] = useState(true);

  // Initial load
  useEffect(() => {
    const fetchInitial = async () => {
      try {
        const [statusData, eventsData] = await Promise.all([
          api.getMotionStatus(),
          api.getMotionEvents(),
        ]);
        setStatus(statusData);
        setEvents(eventsData);
      } catch (error) {
        console.error('Failed to fetch motion data:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchInitial();
  }, []);

  // SSE for real-time motion updates
  useSSE({
    onMotionDetected: (event) => {
      setEvents((prev) => [...prev.slice(-99), event as MotionEvent]);
      setStatus((prev) =>
        prev
          ? {
              ...prev,
              last_motion_time: new Date().toISOString(),
            }
          : null
      );
    },
  });

  const updateConfig = useCallback(async (config: Partial<MotionConfig>) => {
    try {
      await api.updateMotionConfig(config);
      setStatus((prev) =>
        prev
          ? {
              ...prev,
              config: { ...prev.config, ...config },
            }
          : null
      );
      return true;
    } catch (error) {
      console.error('Failed to update motion config:', error);
      return false;
    }
  }, []);

  const toggleMotion = useCallback(async () => {
    setStatus((prev) => {
      if (!prev) return null;
      api
        .updateMotionConfig({ enabled: !prev.enabled })
        .catch((error) =>
          console.error('Failed to toggle motion detection:', error)
        );
      return { ...prev, enabled: !prev.enabled };
    });
  }, []);

  return {
    status,
    events,
    loading,
    updateConfig,
    toggleMotion,
  };
}

/**
 * Combined hook for all optimized real-time updates.
 */
export function useOptimizedUpdates() {
  const health = useOptimizedHealthCheck();
  const stream = useOptimizedStreamStatus();
  const motion = useOptimizedMotionDetection();

  return {
    health,
    stream,
    motion,
    // Overall connection mode
    connectionMode: stream.mode === 'sse' ? 'optimized' : 'fallback',
  };
}
