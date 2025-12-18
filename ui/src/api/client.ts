import type {
  ApiResponse,
  HealthResponse,
  PresetResponse,
  MotionStatus,
  MotionConfig,
  MotionEvent,
  PushSubscription,
  AppInfo,
  CameraPreset,
  CameraControl,
  StreamStatus,
  LogResponse,
  BreathingStatus,
  BreathingConfig,
  BreathingZone,
  BreathingWaveformPoint,
} from '../types';

export class CameraAPI {
  private baseUrl: string;

  constructor(baseUrl = '') {
    this.baseUrl = baseUrl;
  }

  private async fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseUrl}${url}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  // Health and Status
  async getHealth(): Promise<HealthResponse> {
    return this.fetchJSON<HealthResponse>('/health');
  }

  async getAppInfo(): Promise<AppInfo> {
    return this.fetchJSON<AppInfo>('/api/app-info');
  }

  // Stream Status
  async getStreamStatus(): Promise<StreamStatus> {
    return this.fetchJSON<StreamStatus>('/api/stream/timestamp');
  }

  // Camera Presets
  async getPresets(): Promise<PresetResponse> {
    return this.fetchJSON<PresetResponse>('/presets');
  }

  async applyPreset(preset: CameraPreset): Promise<ApiResponse> {
    return this.fetchJSON<ApiResponse>('/apply_preset', {
      method: 'POST',
      body: JSON.stringify({ preset }),
    });
  }

  // Camera Controls
  async getControls(): Promise<Record<string, CameraControl[]>> {
    return this.fetchJSON<Record<string, CameraControl[]>>('/controls');
  }

  async updateControl(controlName: string, value: number | boolean | string): Promise<ApiResponse> {
    return this.fetchJSON<ApiResponse>(`/control/${controlName}`, {
      method: 'POST',
      body: JSON.stringify({ value }),
    });
  }

  // Motion Detection
  async getMotionStatus(): Promise<MotionStatus> {
    return this.fetchJSON<MotionStatus>('/api/motion/status');
  }

  async getMotionConfig(): Promise<MotionConfig> {
    return this.fetchJSON<MotionConfig>('/api/motion/config');
  }

  async updateMotionConfig(config: Partial<MotionConfig>): Promise<ApiResponse> {
    return this.fetchJSON<ApiResponse>('/api/motion/config', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async getMotionEvents(): Promise<MotionEvent[]> {
    return this.fetchJSON<MotionEvent[]>('/api/motion/events');
  }

  // Push Notifications
  async getVapidKey(): Promise<Uint8Array> {
    const response = await fetch(`${this.baseUrl}/api/push/vapid-key`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    // Convert base64 string to Uint8Array for applicationServerKey
    return this.base64ToUint8Array(data.publicKey);
  }

  private base64ToUint8Array(base64String: string): Uint8Array {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
      .replace(/\-/g, '+')
      .replace(/_/g, '/');
    
    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    
    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
  }

  async subscribeToPush(subscription: PushSubscription): Promise<ApiResponse> {
    return this.fetchJSON<ApiResponse>('/api/push/subscribe', {
      method: 'POST',
      body: JSON.stringify(subscription),
    });
  }

  async unsubscribeFromPush(endpoint: string): Promise<ApiResponse> {
    return this.fetchJSON<ApiResponse>('/api/push/unsubscribe', {
      method: 'POST',
      body: JSON.stringify({ endpoint }),
    });
  }

  async testPushNotification(endpoint: string): Promise<ApiResponse> {
    return this.fetchJSON<ApiResponse>('/api/push/test', {
      method: 'POST',
      body: JSON.stringify({ endpoint }),
    });
  }

  // Stream URL helper
  getStreamUrl(): string {
    return `${this.baseUrl}/video_feed`;
  }

  // Server Logs
  async getLogs(limit = 100, source: 'memory' | 'file' = 'memory'): Promise<LogResponse> {
    return this.fetchJSON<LogResponse>(`/api/logs?limit=${limit}&source=${source}`);
  }

  // Breathing Detection
  async getBreathingStatus(): Promise<BreathingStatus> {
    return this.fetchJSON<BreathingStatus>('/api/breathing/status');
  }

  async getBreathingConfig(): Promise<BreathingConfig> {
    return this.fetchJSON<BreathingConfig>('/api/breathing/config');
  }

  async updateBreathingConfig(config: Partial<BreathingConfig>): Promise<ApiResponse> {
    return this.fetchJSON<ApiResponse>('/api/breathing/config', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async setBreathingZone(zone: Omit<BreathingZone, 'enabled'> & { enabled?: boolean }): Promise<ApiResponse> {
    return this.fetchJSON<ApiResponse>('/api/breathing/zone', {
      method: 'POST',
      body: JSON.stringify({ ...zone, enabled: zone.enabled ?? true }),
    });
  }

  async clearBreathingZone(): Promise<ApiResponse> {
    return this.fetchJSON<ApiResponse>('/api/breathing/zone', {
      method: 'DELETE',
    });
  }

  async getBreathingWaveform(seconds = 10): Promise<{ points: BreathingWaveformPoint[]; duration_seconds: number }> {
    return this.fetchJSON<{ points: BreathingWaveformPoint[]; duration_seconds: number }>(
      `/api/breathing/waveform?seconds=${seconds}`
    );
  }
}

// Singleton instance
export const api = new CameraAPI();