/**
 * Optimized React hooks using SSE for real-time updates.
 * Polling fallback has been disabled - SSE is the only update mechanism.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { api } from './client';
import { useSSE } from './sse';
import type {
  HealthResponse,
  MotionStatus,
  MotionConfig,
  MotionEvent,
  StreamStatus,
  LogEntry
} from '../types';

/**
 * Optimized health check using SSE only (polling fallback disabled).
 */
export function useOptimizedHealthCheck() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [isHealthy, setIsHealthy] = useState(true);

  // SSE only - no polling fallback
  const { connected: sseConnected } = useSSE({
    onHealth: (data) => {
      setHealth(data as HealthResponse);
      setIsHealthy(true);
    },
    onError: () => {
      setIsHealthy(false);
    },
  });

  return { health, isHealthy, mode: sseConnected ? 'sse' : 'disconnected' };
}

/**
 * Optimized stream status using SSE only (polling fallback disabled).
 */
export function useOptimizedStreamStatus() {
  const [streamStatus, setStreamStatus] = useState<StreamStatus | null>(null);
  const [streamConnected, setStreamConnected] = useState(false);

  // SSE only - no polling fallback
  const { connected: sseConnected, hasEverConnected } = useSSE({
    onStreamStatus: (status: StreamStatus) => {
      setStreamStatus(status);
      const connected = status.healthy && status.status === 'streaming';
      setStreamConnected(connected);
    },
  });

  // Three states: connecting (never connected), sse (connected), disconnected (lost connection)
  const mode = sseConnected ? 'sse' : hasEverConnected ? 'disconnected' : 'connecting';

  return {
    streamStatus,
    streamConnected,
    timestamp: streamStatus?.timestamp || '',
    streamHealthy: streamStatus?.healthy || false,
    mode,
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
      const newEnabled = !prev.enabled;
      api.updateMotionConfig({ enabled: newEnabled }).catch((error) => {
        console.error('Failed to toggle motion detection:', error);
        // Revert on failure
        setStatus((current) =>
          current ? { ...current, enabled: !newEnabled } : null
        );
      });
      return { ...prev, enabled: newEnabled };
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
