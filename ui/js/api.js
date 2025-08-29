// API communication module
export class CameraAPI {
    constructor(baseUrl) {
        this.baseUrl = baseUrl || window.location.origin;
    }

    async applyPreset(presetName) {
        const response = await fetch(`${this.baseUrl}/apply_preset`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ preset: presetName })
        });
        return response.json();
    }

    async getHealth() {
        const response = await fetch(`${this.baseUrl}/health`);
        return response.json();
    }

    async getPresets() {
        const response = await fetch(`${this.baseUrl}/presets`);
        return response.json();
    }

    async updateControl(control, value) {
        const response = await fetch(`${this.baseUrl}/control`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ control, value })
        });
        return response.json();
    }

    getStreamUrl() {
        return `${this.baseUrl}/video_feed`;
    }
}