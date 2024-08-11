function updateCameraSettings() {
    const settings = {
        exposureTime: document.getElementById('exposure-time').value,
        iso: document.getElementById('iso').value,
        awbMode: document.getElementById('awb-mode').value,
        frameRate: document.getElementById('frame-rate').value,
        noiseReduction: document.getElementById('noise-reduction').value,
        contrast: document.getElementById('contrast').value,
        brightness: document.getElementById('brightness').value
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
        const statusMessage = document.getElementById('status-message');
        if (data.status === 'success') {
            statusMessage.textContent = data.message;
            statusMessage.className = 'success';
        } else {
            statusMessage.textContent = data.messages ? data.messages.join(' ') : data.message;
            statusMessage.className = 'error';
        }
        statusMessage.style.display = 'block';
        setTimeout(() => {
            statusMessage.style.display = 'none';
        }, 5000);
    })
    .catch(error => {
        console.error('Error:', error);
        const statusMessage = document.getElementById('status-message');
        statusMessage.textContent = 'An error occurred while updating settings. Please try again.';
        statusMessage.className = 'error';
        statusMessage.style.display = 'block';
        setTimeout(() => {
            statusMessage.style.display = 'none';
        }, 5000);
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

// Check stream status every 5 seconds
setInterval(checkStreamStatus, 5000);

// Initial stream status check
checkStreamStatus();