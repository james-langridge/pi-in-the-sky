        import { CameraAPI } from './js/api.js';
        import { CameraControls } from './js/controls.js';
        import { motionDetection } from './js/motion.js';
        
        // Configuration
        const BASE_URL = window.location.protocol === 'file:' 
            ? 'http://localhost:8080'
            : window.location.origin;

        // Initialize API and controls
        const api = new CameraAPI(BASE_URL);
        let cameraControls = null;
        
        // State
        let controlsOpen = false;

        // Initialize stream
        function initStream() {
            const stream = document.getElementById('stream');
            const loading = document.getElementById('loading');
            
            stream.src = api.getStreamUrl();
            
            stream.onload = () => {
                loading.style.display = 'none';
                stream.style.display = 'block';
            };
            
            stream.onerror = () => {
                loading.innerHTML = 'Failed to connect to camera stream';
            };
        }

        // Toggle controls panel
        function toggleControls() {
            controlsOpen = !controlsOpen;
            const controls = document.getElementById('controls');
            const chevron = document.getElementById('chevron');
            
            if (controlsOpen) {
                controls.classList.add('open');
                chevron.innerHTML = '<path d="M6 9l6 6 6-6"/>';
            } else {
                controls.classList.remove('open');
                chevron.innerHTML = '<path d="M18 15l-6-6-6 6"/>';
            }
        }

        // Show status message
        function showStatus(message, isError = false) {
            const status = document.getElementById('status');
            status.textContent = message;
            status.style.background = isError ? 'rgba(239, 68, 68, 0.9)' : 'rgba(16, 185, 129, 0.9)';
            status.classList.add('show');
            
            setTimeout(() => {
                status.classList.remove('show');
            }, 3000);
        }

        // Apply camera preset
        async function applyPreset(presetName) {
            try {
                const data = await api.applyPreset(presetName);
                
                if (data.status === 'success') {
                    showStatus(`Applied ${presetName} preset`);
                    // Reload controls to reflect new values
                    if (cameraControls) {
                        await cameraControls.loadControls();
                    }
                } else {
                    showStatus(data.message || 'Failed to apply preset', true);
                }
            } catch (error) {
                showStatus('Error applying preset', true);
                console.error('Error:', error);
            }
        }

        // Reset all controls to defaults
        async function resetControls() {
            if (cameraControls) {
                await cameraControls.resetControls();
            }
        }

        // Register service worker for PWA
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('/service-worker.js')
                    .then(registration => {
                        console.log('ServiceWorker registered:', registration.scope);
                    })
                    .catch(error => {
                        console.log('ServiceWorker registration failed:', error);
                    });
            });
        }

        // Motion detection functions
        async function initMotionDetection() {
            try {
                await motionDetection.initialize();
                updateMotionUI();
            } catch (error) {
                console.error('Failed to initialize motion detection:', error);
            }
        }
        
        function updateMotionUI() {
            const indicator = document.getElementById('motion-indicator');
            const statusText = document.getElementById('motion-status-text');
            const toggleBtn = document.getElementById('toggle-motion');
            
            if (motionDetection.enabled) {
                indicator.classList.add('active');
                statusText.textContent = 'Motion Detection: Active';
                toggleBtn.textContent = 'Disable';
                toggleBtn.classList.remove('btn-info');
                toggleBtn.classList.add('btn-danger');
            } else {
                indicator.classList.remove('active');
                statusText.textContent = 'Motion Detection: Off';
                toggleBtn.textContent = 'Enable';
                toggleBtn.classList.remove('btn-danger');
                toggleBtn.classList.add('btn-info');
            }
            
            // Update slider values from config
            if (motionDetection.config) {
                document.getElementById('motion-sensitivity').value = motionDetection.config.sensitivity;
                document.getElementById('motion-sensitivity-value').textContent = motionDetection.config.sensitivity.toFixed(2);
                document.getElementById('motion-min-area').value = motionDetection.config.min_area;
                document.getElementById('motion-min-area-value').textContent = motionDetection.config.min_area;
                document.getElementById('motion-cooldown').value = motionDetection.config.cooldown_seconds;
                document.getElementById('motion-cooldown-value').textContent = motionDetection.config.cooldown_seconds;
                document.getElementById('motion-threshold').value = motionDetection.config.threshold;
                document.getElementById('motion-threshold-value').textContent = motionDetection.config.threshold;
            }
        }
        
        async function toggleMotion() {
            try {
                await motionDetection.toggle();
                updateMotionUI();
                
                if (motionDetection.enabled) {
                    const hasNotifications = motionDetection.subscription ? ' (with notifications)' : ' (notifications unavailable)';
                    showStatus('Motion detection enabled' + hasNotifications);
                } else {
                    showStatus('Motion detection disabled');
                }
            } catch (error) {
                showStatus('Failed to toggle motion detection', true);
                console.error('Error:', error);
            }
        }
        
        async function applyMotionPreset() {
            try {
                const preset = document.getElementById('motion-preset').value;
                const response = await fetch(`${BASE_URL}/api/motion/preset/${preset}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                
                if (response.ok) {
                    showStatus('Motion preset applied successfully');
                    await updateMotionStatus();
                } else {
                    const error = await response.json();
                    showStatus(error.message || 'Failed to apply preset', true);
                }
            } catch (error) {
                showStatus('Failed to apply motion preset', true);
                console.error('Error:', error);
            }
        }
        
        // Legacy function for backwards compatibility
        async function saveMotionConfig() {
            // Now just applies the selected preset
            await applyMotionPreset();
        }
        
        
        async function testNotification() {
            try {
                await motionDetection.sendTestNotification();
                showStatus('Test notification sent');
            } catch (error) {
                showStatus('Failed to send test notification', true);
                console.error('Error:', error);
            }
        }
        
        // Initialize on load
        window.addEventListener('DOMContentLoaded', async () => {
            initStream();
            
            // Initialize camera controls
            cameraControls = new CameraControls(api, showStatus);
            await cameraControls.init();
            
            // Initialize motion detection
            await initMotionDetection();
            
            // Bind button events
            document.getElementById('toggleBtn').addEventListener('click', toggleControls);
            document.getElementById('preset-default').addEventListener('click', () => applyPreset('default'));
            document.getElementById('preset-low-light').addEventListener('click', () => applyPreset('low_light'));
            document.getElementById('preset-bright').addEventListener('click', () => applyPreset('bright'));
            document.getElementById('reset-all').addEventListener('click', resetControls);
            
            // Motion detection events
            document.getElementById('toggle-motion').addEventListener('click', toggleMotion);
            document.getElementById('apply-motion-preset')?.addEventListener('click', applyMotionPreset);
            document.getElementById('save-motion-config')?.addEventListener('click', saveMotionConfig); // Legacy
            document.getElementById('test-notification').addEventListener('click', testNotification);
            
            // Motion config slider events (if they exist - for backwards compatibility)
            document.getElementById('motion-sensitivity')?.addEventListener('input', (e) => {
                document.getElementById('motion-sensitivity-value').textContent = parseFloat(e.target.value).toFixed(2);
            });
            document.getElementById('motion-min-area')?.addEventListener('input', (e) => {
                document.getElementById('motion-min-area-value').textContent = e.target.value;
            });
            document.getElementById('motion-cooldown')?.addEventListener('input', (e) => {
                document.getElementById('motion-cooldown-value').textContent = e.target.value;
            });
            document.getElementById('motion-threshold')?.addEventListener('input', (e) => {
                document.getElementById('motion-threshold-value').textContent = e.target.value;
            });
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && controlsOpen) {
                toggleControls();
            }
            if (e.key === ' ') {
                e.preventDefault();
                toggleControls();
            }
        });
