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

// State management
const AppState = {
    controlsOpen: false,
    streamConnected: false,
    lastConnectedTime: null,
    reconnectTimer: null,
    reconnectAttempts: 0,
    healthCheckInterval: null,
    visibilityState: 'visible',
    wasBackgrounded: false,
    backgroundTime: null
};

// Constants
const MAX_RECONNECT_ATTEMPTS = 10;
const RECONNECT_DELAY_BASE = 1000;
const HEALTH_CHECK_INTERVAL = 3000;
const BACKGROUND_TIMEOUT = 30000; // 30 seconds

// Save state to session storage
function saveState() {
    try {
        const stateToSave = {
            controlsOpen: AppState.controlsOpen,
            lastConnectedTime: AppState.lastConnectedTime,
            streamConnected: AppState.streamConnected
        };
        sessionStorage.setItem('appState', JSON.stringify(stateToSave));
    } catch (e) {
        console.warn('Could not save state:', e);
    }
}

// Restore state from session storage
function restoreState() {
    try {
        const savedState = sessionStorage.getItem('appState');
        if (savedState) {
            const state = JSON.parse(savedState);
            AppState.controlsOpen = state.controlsOpen || false;
            AppState.lastConnectedTime = state.lastConnectedTime;

            // Restore UI state
            if (AppState.controlsOpen) {
                const controls = document.getElementById('controls');
                const chevron = document.getElementById('chevron');
                if (controls && chevron) {
                    controls.classList.add('open');
                    chevron.innerHTML = '<path d="M6 9l6 6 6-6"/>';
                }
            }
        }
    } catch (e) {
        console.warn('Could not restore state:', e);
    }
}

function initStream(forceReconnect = false) {
    const stream = document.getElementById('stream');
    const loading = document.getElementById('loading');

    if (!stream || !loading) {
        console.error('Required DOM elements not found');
        return;
    }

    // Clear any existing timers
    if (AppState.reconnectTimer) {
        clearTimeout(AppState.reconnectTimer);
        AppState.reconnectTimer = null;
    }

    // If we were backgrounded for too long, force reconnect
    if (!forceReconnect && AppState.wasBackgrounded && AppState.backgroundTime) {
        const backgroundDuration = Date.now() - AppState.backgroundTime;
        if (backgroundDuration > BACKGROUND_TIMEOUT) {
            console.log(`Was backgrounded for ${backgroundDuration}ms, forcing reconnect`);
            forceReconnect = true;
        }
    }

    // Create new stream URL with cache buster
    const timestamp = new Date().getTime();
    const newSrc = api.getStreamUrl() + '?t=' + timestamp;

    // Only update src if it's different or forced
    if (stream.src !== newSrc || forceReconnect) {
        console.log('Initializing stream connection');

        // Remove old event listeners to prevent memory leaks
        stream.onload = null;
        stream.onerror = null;

        // Set up new event listeners
        stream.onload = handleStreamLoad;
        stream.onerror = handleStreamError;

        // Set the new source
        stream.src = newSrc;
    } else if (stream.complete && stream.naturalHeight > 0) {
        // Stream appears to be working
        handleStreamLoad();
    } else {
        // Stream source is same but not working, force refresh
        stream.src = newSrc;
    }

    // Reset background flags
    AppState.wasBackgrounded = false;
    AppState.backgroundTime = null;
}

// Handle successful stream load
function handleStreamLoad() {
    const stream = document.getElementById('stream');
    const loading = document.getElementById('loading');
    const loadingText = document.getElementById('loading-text');
    const manualReconnectBtn = document.getElementById('manual-reconnect');

    console.log('Stream connected successfully');

    loading.style.display = 'none';
    stream.style.display = 'block';

    // Update state
    AppState.streamConnected = true;
    AppState.reconnectAttempts = 0;
    AppState.lastConnectedTime = Date.now();

    // Reset UI
    if (loadingText) loadingText.textContent = 'Connecting to camera...';
    if (manualReconnectBtn) manualReconnectBtn.style.display = 'none';

    // Save state
    saveState();

    // Start health monitoring
    startHealthCheck();
}

// Enhanced error handling with exponential backoff
function handleStreamError() {
    const loading = document.getElementById('loading');
    const loadingText = document.getElementById('loading-text');
    const manualReconnectBtn = document.getElementById('manual-reconnect');
    const stream = document.getElementById('stream');

    console.log('Stream error detected');

    stream.style.display = 'none';
    loading.style.display = 'block';

    AppState.streamConnected = false;

    if (AppState.reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
        AppState.reconnectAttempts++;
        const delay = Math.min(
            RECONNECT_DELAY_BASE * Math.pow(1.5, AppState.reconnectAttempts - 1),
            30000
        );

        if (loadingText) {
            loadingText.textContent = `Connection lost. Reconnecting (${AppState.reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})...`;
        }
        if (manualReconnectBtn) manualReconnectBtn.style.display = 'none';

        console.log(`Scheduling reconnect attempt ${AppState.reconnectAttempts} in ${delay}ms`);

        AppState.reconnectTimer = setTimeout(() => {
            initStream(true);
        }, delay);
    } else {
        if (loadingText) loadingText.textContent = 'Failed to connect to camera stream.';
        if (manualReconnectBtn) manualReconnectBtn.style.display = 'inline-block';
        stopHealthCheck();
    }
}

// Health check for stream
function checkStreamHealth() {
    const stream = document.getElementById('stream');

    if (!stream || stream.style.display === 'none') {
        return;
    }

    // Check if stream is actually updating
    if (stream.complete && stream.naturalHeight === 0) {
        console.log('Stream appears frozen (no height), reconnecting');
        AppState.streamConnected = false;
        handleStreamError();
    } else if (!stream.complete && AppState.streamConnected) {
        // Give it more time if still loading
        const timeSinceConnect = Date.now() - AppState.lastConnectedTime;
        if (timeSinceConnect > 10000) {
            console.log('Stream stuck loading, reconnecting');
            handleStreamError();
        }
    }
}

// Start health monitoring
function startHealthCheck() {
    stopHealthCheck(); // Clear any existing interval
    AppState.healthCheckInterval = setInterval(checkStreamHealth, HEALTH_CHECK_INTERVAL);
}

// Stop health monitoring
function stopHealthCheck() {
    if (AppState.healthCheckInterval) {
        clearInterval(AppState.healthCheckInterval);
        AppState.healthCheckInterval = null;
    }
}

function handleVisibilityChange() {
    const isVisible = !document.hidden;
    const wasHidden = AppState.visibilityState === 'hidden';

    AppState.visibilityState = isVisible ? 'visible' : 'hidden';

    if (!isVisible) {
        // Going to background
        console.log('App going to background');
        AppState.backgroundTime = Date.now();
        AppState.wasBackgrounded = true;
        stopHealthCheck();
        saveState();
    } else if (wasHidden) {
        // Coming from background
        console.log('App returning from background');

        const backgroundDuration = AppState.backgroundTime ?
            Date.now() - AppState.backgroundTime : 0;

        console.log(`Was backgrounded for ${backgroundDuration}ms`);

        // Always check stream health when coming back
        const stream = document.getElementById('stream');

        if (!stream) {
            console.error('Stream element not found on resume');
            window.location.reload(); // Last resort
            return;
        }

        // Check if we need to reconnect
        const needsReconnect =
            !AppState.streamConnected ||
            stream.naturalHeight === 0 ||
            stream.style.display === 'none' ||
            backgroundDuration > BACKGROUND_TIMEOUT ||
            !stream.complete;

        if (needsReconnect) {
            console.log('Stream needs reconnection after background');
            AppState.reconnectAttempts = 0;
            initStream(true);
        } else {
            console.log('Stream appears healthy after background');
            startHealthCheck();
        }

        // Restore any saved state
        restoreState();
    }
}

// Network status monitoring
function handleOnline() {
    console.log('Network connection restored');
    if (!AppState.streamConnected) {
        AppState.reconnectAttempts = 0;
        initStream(true);
    }
}

function handleOffline() {
    console.log('Network connection lost');
    AppState.streamConnected = false;
    stopHealthCheck();
}

// Toggle controls panel
function toggleControls() {
    AppState.controlsOpen = !AppState.controlsOpen;
    const controls = document.getElementById('controls');
    const chevron = document.getElementById('chevron');

    if (AppState.controlsOpen) {
        controls.classList.add('open');
        chevron.innerHTML = '<path d="M6 9l6 6 6-6"/>';
    } else {
        controls.classList.remove('open');
        chevron.innerHTML = '<path d="M18 15l-6-6-6 6"/>';
    }

    saveState();
}

// Show status message
function showStatus(message, isError = false) {
    const status = document.getElementById('status');
    if (!status) return;

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

// Reset controls
async function resetControls() {
    if (cameraControls) {
        await cameraControls.resetControls();
    }
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

    if (!indicator || !statusText || !toggleBtn) return;

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
}

async function toggleMotion() {
    try {
        await motionDetection.toggle();
        updateMotionUI();

        if (motionDetection.enabled) {
            const hasNotifications = motionDetection.subscription ?
                ' (with notifications)' : ' (notifications unavailable)';
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
            await motionDetection.initialize(); // Refresh config
            updateMotionUI();
        } else {
            const error = await response.json();
            showStatus(error.message || 'Failed to apply preset', true);
        }
    } catch (error) {
        showStatus('Failed to apply motion preset', true);
        console.error('Error:', error);
    }
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

// Service Worker registration with update handling
async function registerServiceWorker() {
    if (!('serviceWorker' in navigator)) {
        console.log('Service Workers not supported');
        return;
    }

    try {
        const registration = await navigator.serviceWorker.register('/service-worker.js');
        console.log('ServiceWorker registered:', registration.scope);
        
        // Immediately check for updates
        registration.update();

        // Check for updates
        registration.addEventListener('updatefound', () => {
            const newWorker = registration.installing;
            newWorker.addEventListener('statechange', () => {
                if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                    // New service worker available
                    console.log('New service worker available, refresh to update');
                    showStatus('App update available - refresh to update');
                }
            });
        });

        // Check for updates periodically
        setInterval(() => {
            registration.update();
        }, 60000); // Check every minute

    } catch (error) {
        console.error('ServiceWorker registration failed:', error);
    }
}

// Initialize app
async function initializeApp() {
    console.log('Initializing app');

    // Restore any saved state
    restoreState();

    // Initialize stream
    initStream();

    // Initialize camera controls
    cameraControls = new CameraControls(api, showStatus);
    await cameraControls.init();

    // Initialize motion detection
    await initMotionDetection();

    // Set up event listeners
    setupEventListeners();

    // Register service worker
    await registerServiceWorker();
}

// Set up all event listeners
function setupEventListeners() {
    // Page visibility
    document.addEventListener('visibilitychange', handleVisibilityChange);

    // Network status
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Before unload - save state
    window.addEventListener('beforeunload', saveState);

    // Page focus/blur for additional detection
    window.addEventListener('focus', () => {
        if (!AppState.streamConnected) {
            console.log('Window focused, checking stream');
            initStream();
        }
    });

    window.addEventListener('blur', () => {
        console.log('Window blurred');
        saveState();
    });

    // Control buttons
    document.getElementById('toggleBtn')?.addEventListener('click', toggleControls);
    document.getElementById('preset-default')?.addEventListener('click', () => applyPreset('default'));
    document.getElementById('preset-low-light')?.addEventListener('click', () => applyPreset('low_light'));
    document.getElementById('preset-bright')?.addEventListener('click', () => applyPreset('bright'));
    document.getElementById('reset-all')?.addEventListener('click', resetControls);

    // Manual reconnect
    document.getElementById('manual-reconnect')?.addEventListener('click', () => {
        AppState.reconnectAttempts = 0;
        initStream(true);
    });

    // Motion detection
    document.getElementById('toggle-motion')?.addEventListener('click', toggleMotion);
    document.getElementById('apply-motion-preset')?.addEventListener('click', applyMotionPreset);
    document.getElementById('test-notification')?.addEventListener('click', testNotification);

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && AppState.controlsOpen) {
            toggleControls();
        }
        if (e.key === ' ') {
            e.preventDefault();
            toggleControls();
        }
    });
}

// Wait for DOM to be ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeApp);
} else {
    // DOM already loaded
    initializeApp();
}
