/**
 * Server-Sent Events client for real-time updates.
 * Uses a singleton pattern to share a single SSE connection across all hooks.
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import type { StreamStatus } from '../types';

interface SSEMessage {
  type: string;
  timestamp: string;
  data: unknown;
}

type SSEEventType =
  | 'stream_status'
  | 'health'
  | 'motion_detected'
  | 'motion_status'
  | 'log_entry';

type SSEHandler = (data: unknown) => void;

/**
 * Singleton SSE connection manager.
 * Maintains a single EventSource and distributes events to all subscribers.
 */
class SSEConnectionManager {
  private eventSource: EventSource | null = null;
  private listeners: Map<SSEEventType, Set<SSEHandler>> = new Map();
  private connectionListeners: Set<(connected: boolean) => void> = new Set();
  private reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
  private reconnectAttempts = 0;
  private _connected = false;

  get connected(): boolean {
    return this._connected;
  }

  subscribe(eventType: SSEEventType, handler: SSEHandler): () => void {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set());
    }
    this.listeners.get(eventType)!.add(handler);

    // Start connection if not already connected
    if (!this.eventSource) {
      this.connect();
    }

    // Return unsubscribe function
    return () => {
      this.listeners.get(eventType)?.delete(handler);
      // Disconnect if no more listeners
      if (this.getTotalListeners() === 0) {
        this.disconnect();
      }
    };
  }

  onConnectionChange(handler: (connected: boolean) => void): () => void {
    this.connectionListeners.add(handler);
    // Immediately notify of current state
    handler(this._connected);
    return () => {
      this.connectionListeners.delete(handler);
    };
  }

  private getTotalListeners(): number {
    let total = this.connectionListeners.size;
    for (const listeners of this.listeners.values()) {
      total += listeners.size;
    }
    return total;
  }

  private setConnected(connected: boolean): void {
    this._connected = connected;
    for (const handler of this.connectionListeners) {
      handler(connected);
    }
  }

  private connect(): void {
    if (this.eventSource) {
      return;
    }

    try {
      this.eventSource = new EventSource('/api/sse/events');

      this.eventSource.onopen = () => {
        console.log('SSE connection established');
        this.setConnected(true);
        this.reconnectAttempts = 0;
      };

      this.eventSource.onerror = () => {
        console.error('SSE connection error');
        this.setConnected(false);
        this.scheduleReconnect();
      };

      // Register event listeners for all event types
      const eventTypes: SSEEventType[] = [
        'stream_status',
        'health',
        'motion_detected',
        'motion_status',
        'log_entry',
      ];

      for (const eventType of eventTypes) {
        this.eventSource.addEventListener(eventType, (event) => {
          try {
            const message: SSEMessage = JSON.parse(event.data);
            this.notifyListeners(eventType, message.data);
          } catch (e) {
            console.error(`Failed to parse ${eventType}:`, e);
          }
        });
      }

      // Handle generic messages
      this.eventSource.onmessage = (event) => {
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
      this.scheduleReconnect();
    }
  }

  private disconnect(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
    this.setConnected(false);
    this.reconnectAttempts = 0;
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimeout) {
      return;
    }

    // Clean up existing connection
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }

    // Only reconnect if there are listeners
    if (this.getTotalListeners() === 0) {
      return;
    }

    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
    this.reconnectAttempts++;

    if (delay === 30000 && this.reconnectAttempts > 5) {
      console.warn(
        'SSE reconnection at maximum delay (30s). Server may be unavailable.'
      );
    }

    this.reconnectTimeout = setTimeout(() => {
      this.reconnectTimeout = null;
      console.log(
        `Attempting SSE reconnection (attempt ${this.reconnectAttempts})...`
      );
      this.connect();
    }, delay);
  }

  private notifyListeners(eventType: SSEEventType, data: unknown): void {
    const handlers = this.listeners.get(eventType);
    if (handlers) {
      for (const handler of handlers) {
        try {
          handler(data);
        } catch (e) {
          console.error(`Error in SSE handler for ${eventType}:`, e);
        }
      }
    }
  }

  forceReconnect(): void {
    this.disconnect();
    if (this.getTotalListeners() > 0) {
      this.connect();
    }
  }
}

// Singleton instance
const sseManager = new SSEConnectionManager();

interface SSEOptions {
  onStreamStatus?: (status: StreamStatus) => void;
  onHealth?: (status: unknown) => void;
  onMotionDetected?: (event: unknown) => void;
  onMotionStatus?: (status: unknown) => void;
  onLogEntry?: (entry: unknown) => void;
  onError?: (error: Error) => void;
}

/**
 * Hook for Server-Sent Events with automatic reconnection.
 * Uses a shared singleton connection for efficiency.
 */
export function useSSE(options: SSEOptions) {
  const [connected, setConnected] = useState(sseManager.connected);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  // Use refs to avoid stale closures in callbacks
  const optionsRef = useRef(options);
  optionsRef.current = options;

  useEffect(() => {
    const unsubscribers: (() => void)[] = [];

    // Subscribe to connection state changes
    unsubscribers.push(
      sseManager.onConnectionChange((isConnected) => {
        setConnected(isConnected);
        if (!isConnected) {
          optionsRef.current.onError?.(new Error('SSE connection lost'));
        }
      })
    );

    // Subscribe to events based on provided handlers
    if (optionsRef.current.onStreamStatus) {
      unsubscribers.push(
        sseManager.subscribe('stream_status', (data) => {
          setLastUpdate(new Date());
          optionsRef.current.onStreamStatus?.(data as StreamStatus);
        })
      );
    }

    if (optionsRef.current.onHealth) {
      unsubscribers.push(
        sseManager.subscribe('health', (data) => {
          setLastUpdate(new Date());
          optionsRef.current.onHealth?.(data);
        })
      );
    }

    if (optionsRef.current.onMotionDetected) {
      unsubscribers.push(
        sseManager.subscribe('motion_detected', (data) => {
          optionsRef.current.onMotionDetected?.(data);
        })
      );
    }

    if (optionsRef.current.onMotionStatus) {
      unsubscribers.push(
        sseManager.subscribe('motion_status', (data) => {
          optionsRef.current.onMotionStatus?.(data);
        })
      );
    }

    if (optionsRef.current.onLogEntry) {
      unsubscribers.push(
        sseManager.subscribe('log_entry', (data) => {
          optionsRef.current.onLogEntry?.(data);
        })
      );
    }

    return () => {
      for (const unsubscribe of unsubscribers) {
        unsubscribe();
      }
    };
  }, []); // Empty deps - we use refs for handler updates

  const reconnect = useCallback(() => {
    sseManager.forceReconnect();
  }, []);

  return {
    connected,
    lastUpdate,
    reconnect,
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
    enabled = true,
  } = options;

  const [interval, setIntervalState] = useState(initialInterval);
  const [isPolling, setIsPolling] = useState(false);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const successCountRef = useRef(0);
  const errorCountRef = useRef(0);

  // Use refs to avoid stale closures
  const fetchFnRef = useRef(fetchFn);
  const onSuccessRef = useRef(onSuccess);
  const onErrorRef = useRef(onError);

  fetchFnRef.current = fetchFn;
  onSuccessRef.current = onSuccess;
  onErrorRef.current = onError;

  const adjustInterval = useCallback(
    (success: boolean) => {
      if (success) {
        successCountRef.current++;
        errorCountRef.current = 0;

        if (successCountRef.current >= 3) {
          setIntervalState((prev) => Math.min(prev * 1.5, maxInterval));
          successCountRef.current = 0;
        }
      } else {
        errorCountRef.current++;
        successCountRef.current = 0;

        if (errorCountRef.current >= 2) {
          setIntervalState((prev) => Math.max(prev * 0.75, minInterval));
          errorCountRef.current = 0;
        }
      }
    },
    [maxInterval, minInterval]
  );

  const poll = useCallback(async () => {
    if (!enabled || isPolling) return;

    setIsPolling(true);
    try {
      const data = await fetchFnRef.current();
      onSuccessRef.current?.(data);
      adjustInterval(true);
    } catch (error) {
      onErrorRef.current?.(
        error instanceof Error ? error : new Error('Polling failed')
      );
      adjustInterval(false);
    } finally {
      setIsPolling(false);
    }
  }, [adjustInterval, enabled, isPolling]);

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
    resetInterval: () => setIntervalState(initialInterval),
  };
}
