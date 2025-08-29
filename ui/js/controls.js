// Camera controls module
export class CameraControls {
    constructor(api, statusCallback) {
        this.api = api;
        this.showStatus = statusCallback;
        this.controlsOpen = false;
        this.controls = {};
        this.debounceTimers = {};
    }

    async init() {
        await this.loadControls();
        this.bindEvents();
        this.setupKeyboardShortcuts();
    }

    async loadControls() {
        try {
            this.controls = await this.api.getControls();
            this.renderControls();
        } catch (error) {
            console.error('Failed to load controls:', error);
            // Don't show error status for local testing, just log it
            console.log('Note: Controls will not work without server connection');
        }
    }

    renderControls() {
        const container = document.getElementById('controls-container');
        if (!container) return;
        
        container.innerHTML = '';
        
        // Render each category
        for (const [category, controls] of Object.entries(this.controls)) {
            const categorySection = this.createCategorySection(category, controls);
            container.appendChild(categorySection);
        }
    }

    createCategorySection(category, controls) {
        const section = document.createElement('div');
        section.className = 'control-category';
        
        const header = document.createElement('h3');
        header.className = 'category-header';
        header.textContent = category;
        section.appendChild(header);
        
        const controlsContainer = document.createElement('div');
        controlsContainer.className = 'category-controls';
        
        for (const control of controls) {
            const controlElement = this.createControlElement(control);
            controlsContainer.appendChild(controlElement);
        }
        
        section.appendChild(controlsContainer);
        return section;
    }

    createControlElement(control) {
        const container = document.createElement('div');
        container.className = 'control-item';
        
        const label = document.createElement('label');
        label.className = 'control-label';
        label.textContent = control.display_name;
        if (control.unit) {
            label.textContent += ` (${control.unit})`;
        }
        container.appendChild(label);
        
        switch (control.type) {
            case 'slider':
                this.createSliderControl(container, control);
                break;
            case 'toggle':
                this.createToggleControl(container, control);
                break;
            case 'select':
                this.createSelectControl(container, control);
                break;
        }
        
        return container;
    }

    createSliderControl(container, control) {
        const wrapper = document.createElement('div');
        wrapper.className = 'slider-wrapper';
        
        const slider = document.createElement('input');
        slider.type = 'range';
        slider.className = 'control-slider';
        slider.id = `control-${control.name}`;
        slider.min = control.min;
        slider.max = control.max;
        slider.step = control.step || 1;
        slider.value = control.default;
        
        const valueDisplay = document.createElement('span');
        valueDisplay.className = 'slider-value';
        valueDisplay.textContent = control.default;
        
        slider.addEventListener('input', (e) => {
            valueDisplay.textContent = e.target.value;
            this.debouncedUpdateControl(control.name, parseFloat(e.target.value));
        });
        
        wrapper.appendChild(slider);
        wrapper.appendChild(valueDisplay);
        container.appendChild(wrapper);
    }

    createToggleControl(container, control) {
        const toggle = document.createElement('input');
        toggle.type = 'checkbox';
        toggle.className = 'control-toggle';
        toggle.id = `control-${control.name}`;
        toggle.checked = control.default;
        
        toggle.addEventListener('change', (e) => {
            this.updateControlValue(control.name, e.target.checked);
        });
        
        container.appendChild(toggle);
    }

    createSelectControl(container, control) {
        const select = document.createElement('select');
        select.className = 'control-select';
        select.id = `control-${control.name}`;
        
        for (const [value, label] of Object.entries(control.options)) {
            const option = document.createElement('option');
            option.value = value;
            option.textContent = label;
            if (parseInt(value) === control.default) {
                option.selected = true;
            }
            select.appendChild(option);
        }
        
        select.addEventListener('change', (e) => {
            this.updateControlValue(control.name, parseInt(e.target.value));
        });
        
        container.appendChild(select);
    }

    debouncedUpdateControl(controlName, value) {
        // Clear existing timer
        if (this.debounceTimers[controlName]) {
            clearTimeout(this.debounceTimers[controlName]);
        }
        
        // Set new timer
        this.debounceTimers[controlName] = setTimeout(() => {
            this.updateControlValue(controlName, value);
        }, 200);
    }

    async updateControlValue(controlName, value) {
        try {
            const result = await this.api.updateControl(controlName, value);
            if (result.status === 'success') {
                this.showStatus(`${controlName} updated`);
            } else {
                this.showStatus(`Failed to update ${controlName}`, true);
            }
        } catch (error) {
            this.showStatus(`Error updating ${controlName}`, true);
            console.error('Update control error:', error);
        }
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

    async resetControls() {
        try {
            await this.applyPreset('default');
            await this.loadControls();
            this.showStatus('Controls reset to defaults');
        } catch (error) {
            this.showStatus('Error resetting controls', true);
            console.error('Reset error:', error);
        }
    }
}