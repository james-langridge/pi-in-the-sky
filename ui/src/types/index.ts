// API Response Types

export interface ApiResponse<T = any> {
  status: 'success' | 'error';
  message?: string;
  data?: T;
  error?: string;
}

export interface HealthResponse {
  status: string;
  timestamp: string;
  config: {
    host: string;
    port: number;
    debug: boolean;
    cors_origins: string[];
  };
}

export interface PresetResponse {
  presets: string[];
  current: string | null;
}

export interface CameraControl {
  name: string;
  display_name: string;
  type: 'slider' | 'toggle' | 'select';
  default: number | boolean | string;
  min?: number;
  max?: number;
  step?: number;
  unit?: string;
  options?: Record<string, string>;  // Object mapping values to labels
  category: string;
}

export interface MotionConfig {
  enabled: boolean;
  sensitivity: number;
  min_area: number;
  cooldown_seconds: number;
  blur_size: number;
  threshold: number;
  capture_on_motion: boolean;
}

export interface MotionStatus {
  enabled: boolean;
  config: MotionConfig;
  recent_events: number;
  triggered_events: number;
}

export interface MotionEvent {
  timestamp: string;
  area: number;
  contours: number;
  triggered: boolean;
}

export interface PushSubscription {
  endpoint: string;
  keys: {
    p256dh: string;
    auth: string;
  };
}

export interface AppInfo {
  version: string;
  last_modified: string;
  timestamp: string;
}

export interface LogEntry {
  timestamp: string;
  level: string;
  name: string;
  message: string;
}

export interface LogResponse {
  status: string;
  count: number;
  entries: LogEntry[];
}

export interface StreamStatus {
  timestamp: string | null;
  status: 'streaming' | 'waiting' | 'degraded' | 'stale';
  healthy: boolean;
  active_streams: number;
  frame_age_seconds: number | null;
}

// Motion Detection Presets
export interface MotionPreset {
  name: string;
  description: string;
  config: Partial<MotionConfig>;
}

export const MOTION_PRESETS: Record<string, MotionPreset> = {
  sensitive: {
    name: 'Sensitive',
    description: 'Indoor monitoring',
    config: {
      sensitivity: 0.01,
      min_area: 300,
      cooldown_seconds: 15,
      blur_size: 15,
      threshold: 20
    }
  },
  normal: {
    name: 'Normal',
    description: 'General use',
    config: {
      sensitivity: 0.02,
      min_area: 500,
      cooldown_seconds: 30,
      blur_size: 21,
      threshold: 25
    }
  },
  outdoor: {
    name: 'Outdoor',
    description: 'Weather/trees',
    config: {
      sensitivity: 0.05,
      min_area: 1000,
      cooldown_seconds: 60,
      blur_size: 31,
      threshold: 35
    }
  },
  security: {
    name: 'Security',
    description: 'Night vision',
    config: {
      sensitivity: 0.015,
      min_area: 400,
      cooldown_seconds: 10,
      blur_size: 17,
      threshold: 22
    }
  }
};

// Camera Presets
export type CameraPreset = 'default' | 'low_light' | 'bright';

// App State
export interface AppState {
  streamConnected: boolean;
  controlsOpen: boolean;
  motionEnabled: boolean;
  pushSubscribed: boolean;
  version: string;
  updateAvailable: boolean;
}