// Camera controls module
export class CameraControls {
    constructor(api, statusCallback) {
        this.api = api;
        this.showStatus = statusCallback;
        this.controlsOpen = false;
    }

    init() {
        this.bindEvents();
        this.setupKeyboardShortcuts();
    }

    bindEvents() {
        // Bind button clicks
        document.querySelectorAll('[data-preset]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.applyPreset(e.target.dataset.preset);
            });
        });

        document.querySelector('[data-action="health"]')?.addEventListener('click', () => {
            this.checkHealth();
        });

        document.querySelector('[data-action="list-presets"]')?.addEventListener('click', () => {
            this.listPresets();
        });
    }

    toggle() {
        this.controlsOpen = !this.controlsOpen;
        const controls = document.getElementById('controls');
        const chevron = document.getElementById('chevron');
        
        if (this.controlsOpen) {
            controls.classList.add('open');
            chevron.innerHTML = '<path d="M6 9l6 6 6-6"/>';
        } else {
            controls.classList.remove('open');
            chevron.innerHTML = '<path d="M18 15l-6-6-6 6"/>';
        }
    }

    async applyPreset(presetName) {
        try {
            const data = await this.api.applyPreset(presetName);
            this.showStatus(`Applied ${presetName} preset`, data.status === 'error');
        } catch (error) {
            this.showStatus('Error applying preset', true);
            console.error('Error:', error);
        }
    }

    async checkHealth() {
        try {
            const data = await this.api.getHealth();
            this.showStatus(`Server healthy at ${data.timestamp}`);
        } catch (error) {
            this.showStatus('Cannot reach server', true);
            console.error('Error:', error);
        }
    }

    async listPresets() {
        try {
            const data = await this.api.getPresets();
            this.showStatus(`Available presets: ${data.presets.join(', ')}`);
        } catch (error) {
            this.showStatus('Error fetching presets', true);
            console.error('Error:', error);
        }
    }

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.controlsOpen) {
                this.toggle();
            }
            if (e.key === ' ') {
                e.preventDefault();
                this.toggle();
            }
        });
    }

    // Add method for future slider controls
    async updateCameraControl(control, value) {
        try {
            const data = await this.api.updateControl(control, value);
            this.showStatus(`${control} set to ${value}`);
        } catch (error) {
            this.showStatus(`Error updating ${control}`, true);
            console.error('Error:', error);
        }
    }
}