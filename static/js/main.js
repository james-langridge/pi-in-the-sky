function updateCameraSettings() {
    const settings = {
        exposureTime: document.getElementById('exposureTime').value,
        iso: document.getElementById('iso').value,
        awbMode: document.getElementById('awbMode').value,
        frameRate: document.getElementById('frameRate').value,
        brightness: document.getElementById('brightness').value,
        contrast: document.getElementById('contrast').value,
        saturation: document.getElementById('saturation').value,
        sharpness: document.getElementById('sharpness').value,
        hdrMode: document.getElementById('hdrMode').value,
        exposureMode: document.getElementById('exposureMode').value,
        meteringMode: document.getElementById('meteringMode').value
    };

    fetch('/update_camera', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(settings),
    })
        .then(response => response.json())
        .then(data => {
            displayStatusMessage(data);
        })
        .catch(error => {
            console.error('Error:', error);
            displayStatusMessage({status: 'error', message: 'An error occurred while updating settings. Please try again.'});
        });
}

function getCameraSettingsFromUI() {
    return {
        exposureTime: document.getElementById('exposure-time').value,
        iso: document.getElementById('iso').value,
        awbMode: document.getElementById('awb-mode').value,
        frameRate: document.getElementById('frame-rate').value,
        noiseReduction: document.getElementById('noise-reduction').value,
        contrast: document.getElementById('contrast').value,
        brightness: document.getElementById('brightness').value,
        sharpness: document.getElementById('sharpness').value,
        hdrMode: document.getElementById('hdr-mode').value,
        temporalNoiseReduction: document.getElementById('temporal-noise-reduction').value,
        highQualityDenoise: document.getElementById('high-quality-denoise').value,
        localToneMapping: document.getElementById('local-tone-mapping').checked,
        lensShading: document.getElementById('lens-shading').value,
        defectivePixelCorrection: document.getElementById('defective-pixel-correction').checked,
        blackLevel: document.getElementById('black-level').value
    };
}

function applyPreset(presetName) {
    fetch('/apply_preset', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ preset: presetName }),
    })
        .then(response => response.json())
        .then(data => {
            displayStatusMessage(data);
            if (data.status === 'success') {
                fetchAndUpdateCameraSettings();
            }
        })
        .catch(error => {
            console.error('Error:', error);
            displayStatusMessage({status: 'error', message: 'An error occurred while applying the preset. Please try again.'});
        });
}

function resetToDefaults() {
    fetch('/reset_camera', {
        method: 'POST',
    })
        .then(response => response.json())
        .then(data => {
            displayStatusMessage(data);
            if (data.status === 'success') {
                fetchAndUpdateCameraSettings();
            }
        })
        .catch(error => {
            console.error('Error:', error);
            displayStatusMessage({status: 'error', message: 'An error occurred while resetting camera settings. Please try again.'});
        });
}

function displayStatusMessage(data) {
    const statusMessage = document.getElementById('status-message');
    statusMessage.textContent = data.message;
    statusMessage.className = data.status === 'success' ? 'success' : 'error';
    statusMessage.style.display = 'block';
    setTimeout(() => {
        statusMessage.style.display = 'none';
    }, 5000);
}

function fetchAndUpdateCameraSettings() {
    fetch('/get_camera_settings')
        .then(response => response.json())
        .then(settings => {
            document.getElementById('exposureTime').value = settings.exposureTime;
            document.getElementById('iso').value = settings.iso;
            document.getElementById('awbMode').value = settings.awbMode;
            document.getElementById('frameRate').value = settings.frameRate;
            document.getElementById('brightness').value = settings.brightness;
            document.getElementById('contrast').value = settings.contrast;
            document.getElementById('saturation').value = settings.saturation;
            document.getElementById('sharpness').value = settings.sharpness;
            document.getElementById('hdrMode').value = settings.hdrMode;
            document.getElementById('exposureMode').value = settings.exposureMode;
            document.getElementById('meteringMode').value = settings.meteringMode;
        })
        .catch(error => {
            console.error('Error fetching camera settings:', error);
            displayStatusMessage({status: 'error', message: 'Failed to fetch current camera settings.'});
        });
}

const settingsMap = {
    'exposureTime': 'exposure-time',
    'iso': 'iso',
    'awbMode': 'awb-mode',
    'frameRate': 'frame-rate',
    'noiseReduction': 'noise-reduction',
    'contrast': 'contrast',
    'brightness': 'brightness',
    'sharpness': 'sharpness',
    'hdrMode': 'hdr-mode',
    'temporalNoiseReduction': 'temporal-noise-reduction',
    'highQualityDenoise': 'high-quality-denoise',
    'localToneMapping': 'local-tone-mapping',
    'lensShading': 'lens-shading',
    'defectivePixelCorrection': 'defective-pixel-correction',
    'blackLevel': 'black-level'
};

function updateUIWithSettings(settings) {
    console.log('Updating UI with settings:', settings);
    for (const [key, value] of Object.entries(settings)) {
        const elementId = settingsMap[key];
        const element = document.getElementById(elementId);
        if (element) {
            if (element.type === 'checkbox') {
                element.checked = value;
            } else {
                element.value = value;
            }
            element.disabled = false;
            console.log(`Updated ${elementId} to ${element.value}`);
        } else {
            console.warn(`Element not found for setting: ${key} (ID: ${elementId})`);
        }
    }

    // Disable controls that are not in the settings
    for (const [key, elementId] of Object.entries(settingsMap)) {
        if (!(key in settings)) {
            const element = document.getElementById(elementId);
            if (element) {
                element.disabled = true;
                console.log(`Disabled unsupported control: ${elementId}`);
            }
        }
    }
}

function checkStreamStatus() {
    fetch('/stream_status')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'stopped') {
                document.getElementById('stream-status').style.display = 'block';
            } else {
                document.getElementById('stream-status').style.display = 'none';
            }
        })
        .catch(error => {
            console.error('Error checking stream status:', error);
            document.getElementById('stream-status').style.display = 'block';
        });
}

function addRealTimeListeners() {
    const controls = [
        'exposure-time', 'iso', 'awb-mode', 'frame-rate', 'noise-reduction',
        'contrast', 'brightness', 'sharpness', 'hdr-mode', 'temporal-noise-reduction',
        'high-quality-denoise', 'local-tone-mapping', 'lens-shading',
        'defective-pixel-correction', 'black-level'
    ];

    controls.forEach(controlId => {
        const element = document.getElementById(controlId);
        if (element) {
            element.addEventListener('change', updateCameraSettings);
        }
    });
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    fetchAndUpdateCameraSettings();
});