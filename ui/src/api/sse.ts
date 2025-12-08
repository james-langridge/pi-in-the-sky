/**
 * Server-Sent Events client for real-time updates.
 * Replaces aggressive polling with efficient server push.
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import type { StreamStatus } from '../types';

interface SSEMessage {
  type: string;
  timestamp: string;
  data: any;
}

interface SSEOptions {
  onStreamStatus?: (status: StreamStatus) => void;
  onHealth?: (status: any) => void;
  onMotionDetected?: (event: any) => void;
  onLogEntry?: (entry: any) => void;
  onError?: (error: Error) => void;
}

/**
 * Hook for Server-Sent Events with automatic reconnection and fallback.
 */
export function useSSE(options: SSEOptions) {
  const [connected, setConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectAttemptsRef = useRef(0);

  const connect = useCallback(() => {
    // Clean up existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    try {
      const eventSource = new EventSource('/api/sse/events');
      eventSourceRef.current = eventSource;

      eventSource.onopen = () => {
        console.log('SSE connection established');
        setConnected(true);
        reconnectAttemptsRef.current = 0;
      };

      eventSource.onerror = (error) => {
        console.error('SSE connection error:', error);
        setConnected(false);
        options.onError?.(new Error('SSE connection lost'));

        // Reconnect with exponential backoff
        const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);
        reconnectAttemptsRef.current++;

        reconnectTimeoutRef.current = setTimeout(() => {
          console.log(`Attempting SSE reconnection (attempt ${reconnectAttemptsRef.current})...`);
          connect();
        }, delay);
      };

      // Handle specific event types
      eventSource.addEventListener('stream_status', (event) => {
        try {
          const message: SSEMessage = JSON.parse(event.data);
          setLastUpdate(new Date(message.timestamp));
          options.onStreamStatus?.(message.data);
        } catch (e) {
          console.error('Failed to parse stream_status:', e);
        }
      });

      eventSource.addEventListener('health', (event) => {
        try {
          const message: SSEMessage = JSON.parse(event.data);
          setLastUpdate(new Date(message.timestamp));
          options.onHealth?.(message.data);
        } catch (e) {
          console.error('Failed to parse health:', e);
        }
      });

      eventSource.addEventListener('motion_detected', (event) => {
        try {
          const message: SSEMessage = JSON.parse(event.data);
          options.onMotionDetected?.(message.data);
        } catch (e) {
          console.error('Failed to parse motion_detected:', e);
        }
      });

      eventSource.addEventListener('log_entry', (event) => {
        try {
          const message: SSEMessage = JSON.parse(event.data);
          options.onLogEntry?.(message.data);
        } catch (e) {
          console.error('Failed to parse log_entry:', e);
        }
      });

      // Handle generic messages
      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'connected') {
            console.log('SSE connected:', data);
          }
        } catch (e) {
          console.error('Failed to parse SSE message:', e);
        }
      };

    } catch (error) {
      console.error('Failed to create SSE connection:', error);
      options.onError?.(error instanceof Error ? error : new Error('SSE connection failed'));
    }
  }, [options]);

  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    setConnected(false);
  }, []);

  useEffect(() => {
    connect();
    return () => disconnect();
  }, []);

  return {
    connected,
    lastUpdate,
    reconnect: connect,
    disconnect
  };
}

/**
 * Smart polling hook that adjusts interval based on success/failure.
 * Used as fallback when SSE is not available.
 */
export function useSmartPolling<T>(
  fetchFn: () => Promise<T>,
  options: {
    initialInterval?: number;
    maxInterval?: number;
    minInterval?: number;
    onSuccess?: (data: T) => void;
    onError?: (error: Error) => void;
    enabled?: boolean;
  } = {}
) {
  const {
    initialInterval = 5000,
    maxInterval = 30000,
    minInterval = 1000,
    onSuccess,
    onError,
    enabled = true
  } = options;

  const [interval, setInterval] = useState(initialInterval);
  const [isPolling, setIsPolling] = useState(false);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const successCountRef = useRef(0);
  const errorCountRef = useRef(0);

  const adjustInterval = useCallback((success: boolean) => {
    if (success) {
      successCountRef.current++;
      errorCountRef.current = 0;

      // After 3 successful polls, increase interval (reduce frequency)
      if (successCountRef.current >= 3) {
        setInterval(prev => Math.min(prev * 1.5, maxInterval));
        successCountRef.current = 0;
      }
    } else {
      errorCountRef.current++;
      successCountRef.current = 0;

      // After error, decrease interval (increase frequency) to recover faster
      if (errorCountRef.current >= 2) {
        setInterval(prev => Math.max(prev * 0.75, minInterval));
        errorCountRef.current = 0;
      }
    }
  }, [maxInterval, minInterval]);

  const poll = useCallback(async () => {
    if (!enabled || isPolling) return;

    setIsPolling(true);
    try {
      const data = await fetchFn();
      onSuccess?.(data);
      adjustInterval(true);
    } catch (error) {
      onError?.(error instanceof Error ? error : new Error('Polling failed'));
      adjustInterval(false);
    } finally {
      setIsPolling(false);
    }
  }, [fetchFn, onSuccess, onError, adjustInterval, enabled, isPolling]);

  useEffect(() => {
    if (!enabled) {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }
      return;
    }

    const scheduleNextPoll = () => {
      timeoutRef.current = setTimeout(() => {
        poll();
        scheduleNextPoll();
      }, interval);
    };

    // Initial poll
    poll();
    scheduleNextPoll();

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }
    };
  }, [poll, interval, enabled]);

  return {
    isPolling,
    currentInterval: interval,
    resetInterval: () => setInterval(initialInterval)
  };
}