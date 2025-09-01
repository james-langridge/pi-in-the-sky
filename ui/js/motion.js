/**
 * Motion detection and push notification management module
 */

import { CameraAPI } from './api.js';

// Create API instance for motion detection
const API = new CameraAPI(window.location.origin);

// Add convenience methods if they don't exist
if (!API.get) {
    API.get = async function(endpoint) {
        const response = await fetch(this.baseUrl + endpoint);
        return response.json();
    };
}

if (!API.post) {
    API.post = async function(endpoint, data) {
        try {
            const response = await fetch(this.baseUrl + endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            const result = await response.json();
            console.log(`POST ${endpoint} response:`, result);
            return result;
        } catch (error) {
            console.error(`Failed to POST ${endpoint}:`, error);
            throw error;
        }
    };
}

export class MotionDetection {
    constructor() {
        this.enabled = false;
        this.config = null;
        this.subscription = null;
        this.vapidPublicKey = null;
    }

    /**
     * Reset push notifications (clears subscription state)
     */
    async resetNotifications() {
        try {
            if ('serviceWorker' in navigator) {
                const registration = await navigator.serviceWorker.ready;
                const subscription = await registration.pushManager.getSubscription();
                if (subscription) {
                    await subscription.unsubscribe();
                }
            }
            this.subscription = null;
            console.log('Push notifications reset');
            return true;
        } catch (error) {
            console.error('Failed to reset notifications:', error);
            return false;
        }
    }

    /**
     * Initialize motion detection module
     */
    async initialize() {
        try {
            // Get current motion detection config
            const configResponse = await API.get('/api/motion/config');
            this.config = configResponse;
            this.enabled = configResponse.enabled;

            // Get VAPID public key
            const vapidResponse = await API.get('/api/push/vapid-key');
            if (vapidResponse.publicKey) {
                this.vapidPublicKey = vapidResponse.publicKey;
                
                // Check if already subscribed
                await this.checkSubscription();
            }
        } catch (error) {
            console.error('Failed to initialize motion detection:', error);
        }
    }

    /**
     * Check if push notifications are supported
     */
    isPushSupported() {
        return 'serviceWorker' in navigator && 'PushManager' in window;
    }

    /**
     * Check current push subscription status
     */
    async checkSubscription() {
        if (!this.isPushSupported()) {
            return false;
        }

        try {
            const registration = await navigator.serviceWorker.ready;
            const subscription = await registration.pushManager.getSubscription();
            this.subscription = subscription;
            return subscription !== null;
        } catch (error) {
            console.error('Failed to check subscription:', error);
            return false;
        }
    }

    /**
     * Request notification permission and subscribe
     */
    async requestNotificationPermission() {
        if (!this.isPushSupported()) {
            throw new Error('Push notifications not supported');
        }

        // Request permission
        const permission = await Notification.requestPermission();
        if (permission !== 'granted') {
            throw new Error('Notification permission denied');
        }

        // Subscribe to push notifications
        await this.subscribeToPush();
    }

    /**
     * Subscribe to push notifications
     */
    async subscribeToPush() {
        if (!this.vapidPublicKey) {
            throw new Error('VAPID public key not available');
        }

        const registration = await navigator.serviceWorker.ready;

        // Convert VAPID key from base64 to Uint8Array
        const vapidKey = this.urlBase64ToUint8Array(this.vapidPublicKey);

        // Subscribe
        const subscription = await registration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: vapidKey
        });

        // Send subscription to server
        const response = await API.post('/api/push/subscribe', subscription.toJSON());
        
        if (response.status === 'success') {
            this.subscription = subscription;
            return true;
        } else {
            throw new Error(response.message || 'Failed to save subscription');
        }
    }

    /**
     * Unsubscribe from push notifications
     */
    async unsubscribeFromPush() {
        if (!this.subscription) {
            return false;
        }

        try {
            // Unsubscribe from browser
            await this.subscription.unsubscribe();

            // Notify server
            await API.post('/api/push/unsubscribe', {
                endpoint: this.subscription.endpoint
            });

            this.subscription = null;
            return true;
        } catch (error) {
            console.error('Failed to unsubscribe:', error);
            throw error;
        }
    }

    /**
     * Send test notification
     */
    async sendTestNotification() {
        if (!this.subscription) {
            throw new Error('Not subscribed to push notifications');
        }

        const response = await API.post('/api/push/test', {
            endpoint: this.subscription.endpoint
        });

        if (response.status !== 'success') {
            throw new Error(response.message || 'Failed to send test notification');
        }
    }

    /**
     * Update motion detection configuration
     */
    async updateConfig(config) {
        console.log('Updating motion config:', config);
        const response = await API.post('/api/motion/config', config);
        console.log('Motion config response:', response);
        
        if (response && response.status === 'success') {
            this.config = { ...this.config, ...config };
            this.enabled = config.enabled !== undefined ? config.enabled : this.enabled;
            return true;
        } else {
            console.error('Motion config update failed:', response);
            throw new Error(response?.message || 'Failed to update config');
        }
    }

    /**
     * Toggle motion detection and handle push notifications automatically
     */
    async toggle() {
        const newEnabled = !this.enabled;
        
        if (newEnabled) {
            // Enabling motion detection - try to subscribe to push notifications
            if (this.isPushSupported() && !this.subscription) {
                try {
                    // Request permission and subscribe
                    await this.requestNotificationPermission();
                    console.log('Push notifications enabled with motion detection');
                } catch (error) {
                    console.warn('Failed to enable push notifications, continuing with motion detection only:', error);
                    // Continue even if push notifications fail
                }
            }
        } else {
            // Disabling motion detection - unsubscribe from push notifications
            if (this.subscription) {
                try {
                    await this.resetNotifications();
                    console.log('Push notifications disabled with motion detection');
                } catch (error) {
                    console.warn('Failed to clean up push notifications:', error);
                    // Continue even if cleanup fails
                }
            }
        }
        
        return this.updateConfig({ enabled: newEnabled });
    }

    /**
     * Get motion detection status
     */
    async getStatus() {
        const response = await API.get('/api/motion/status');
        return response;
    }

    /**
     * Get recent motion events
     */
    async getRecentEvents(limit = 10) {
        const response = await API.get(`/api/motion/events?limit=${limit}`);
        return response.events || [];
    }

    /**
     * Convert base64 string to Uint8Array for VAPID key
     */
    urlBase64ToUint8Array(base64String) {
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
}

// Create singleton instance
export const motionDetection = new MotionDetection();