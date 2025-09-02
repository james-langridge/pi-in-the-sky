import type {
  ApiResponse,
  HealthResponse,
  PresetResponse,
  MotionStatus,
  MotionConfig,
  MotionEvent,
  PushSubscription,
  AppInfo,
  CameraPreset
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
  async getControls(): Promise<Record<string, any[]>> {
    return this.fetchJSON<Record<string, any[]>>('/controls');
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
  async getVapidKey(): Promise<string> {
    const response = await fetch(`${this.baseUrl}/api/push/vapid-key`);
    return response.text();
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
}

// Singleton instance
export const api = new CameraAPI();