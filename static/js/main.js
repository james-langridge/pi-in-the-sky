function updateCameraSettings() {
    const settings = getCameraSettingsFromUI();

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
    statusMessage.textContent = data.messages ? data.messages.join(' ') : data.message;
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
            document.getElementById('exposure-time').value = settings.exposureTime / 1000; // Convert µs to ms
            document.getElementById('iso').value = settings.iso;
            document.getElementById('awb-mode').value = settings.awbMode;
            document.getElementById('frame-rate').value = settings.frameRate;
            document.getElementById('noise-reduction').value = settings.noiseReduction;
            document.getElementById('contrast').value = settings.contrast;
            document.getElementById('brightness').value = settings.brightness;
            document.getElementById('sharpness').value = settings.sharpness;
            document.getElementById('hdr-mode').value = settings.hdrMode;
            document.getElementById('temporal-noise-reduction').value = settings.temporalNoiseReduction;
            document.getElementById('high-quality-denoise').value = settings.highQualityDenoise;
            document.getElementById('local-tone-mapping').checked = settings.localToneMapping;
            document.getElementById('lens-shading').value = settings.lensShading;
            document.getElementById('defective-pixel-correction').checked = settings.defectivePixelCorrection;
            document.getElementById('black-level').value = settings.blackLevel;
        })
        .catch(error => {
            console.error('Error fetching camera settings:', error);
            displayStatusMessage({status: 'error', message: 'Failed to fetch current camera settings.'});
        });
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
    addRealTimeListeners();
    checkStreamStatus();
    setInterval(checkStreamStatus, 5000);
});