# Pi in the Sky

Raspberry Pi camera streaming application with web interface.

## Components

- **Server**: Flask-based Python server that interfaces with PiCamera2
- **UI**: React + TypeScript + Tailwind CSS Progressive Web App for camera control

## Requirements

### Hardware
- Raspberry Pi with camera module
- PiCamera2 library support

### Software
- Python 3.8+
- Flask 2.3.3
- PiCamera2 0.3.12
- OpenCV 4.8.0
- NumPy 1.24.3
- PyWebPush 2.0.3 (for push notifications)
- py-vapid 1.9.2 (for VAPID key generation)
- Cryptography 41.0.4 (for VAPID keys)

## Installation

### Quick Setup on Raspberry Pi

The easiest way to install is using the automated setup script:

```bash
# SSH into your Raspberry Pi, then run:
curl -fsSL https://raw.githubusercontent.com/james-langridge/pi-in-the-sky/main/setup.sh | bash

# Or if you want to customize the installation:
curl -O https://raw.githubusercontent.com/james-langridge/pi-in-the-sky/main/setup.sh
chmod +x setup.sh
./setup.sh --help  # See available options
./setup.sh --dir ~/my-camera --port 9000
```

The setup script will:
- Install all system dependencies including Node.js
- Clone the repository
- Set up Python virtual environment
- Install Python packages
- Build the React frontend
- Configure systemd service (optional)
- Provide access URLs

### Manual Installation

```bash
# Clone repository
git clone https://github.com/jamesrobertsjr/pi-in-the-sky.git
cd pi-in-the-sky

# Build the React frontend
cd ui
npm install
npm run build
cd ..

# Set up Python environment
cd server
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Note: If venv doesn't exist, create it with:
# python3 -m venv venv --system-site-packages

# Ensure your user is in required groups for camera access
sudo usermod -a -G video $USER
sudo usermod -a -G i2c $USER
sudo usermod -a -G gpio $USER
# Log out and back in for group changes to take effect
```

### Development Setup (Without Raspberry Pi)

The server includes a mock camera mode for development on non-Pi systems:

```bash
# Clone repository
git clone https://github.com/james-langridge/pi-in-the-sky.git
cd pi-in-the-sky

# Build the React frontend
cd ui
npm install
npm run build
cd ..

# Set up Python environment
cd server
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (excluding picamera2)
pip install flask flask-cors opencv-python numpy pywebpush cryptography

# Run server (will auto-detect missing PiCamera2 and use mock)
python server.py
```

The mock camera generates test frames with:
- Gradient backgrounds
- Moving circular element (simulates motion for testing)
- Timestamp overlays
- Frame counter

### Dealing with "externally-managed-environment" Error

On newer Raspberry Pi OS (Bookworm+), you may encounter this error. Solutions:

1. **Use virtual environment (recommended):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Install system packages where available:**
   ```bash
   sudo apt install python3-flask python3-flask-cors python3-opencv python3-numpy
   # Then use venv for remaining packages
   ```

### Updating Dependencies

When updating the project or adding new dependencies:

```bash
cd server
source venv/bin/activate
pip install -r requirements.txt

# If running as a systemd service, restart it:
sudo systemctl restart pi-camera-stream.service
```

## Deployment

### Production Deployment (After Updates)

When deploying updates to the Raspberry Pi:

```bash
# On the Pi, pull latest code
cd ~/pi-in-the-sky
git pull

# Run the deployment script
./deploy.sh

# Or manually:
cd ui
npm ci
npm run build
cd ..
sudo systemctl restart pi-camera-stream.service
```

The deployment script will:
1. Install/update npm dependencies
2. Build the React frontend with Vite
3. Restart the systemd service

### First-Time Production Setup

1. **Install Node.js on Raspberry Pi:**
```bash
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs
```

2. **Build the frontend:**
```bash
cd ui
npm install
npm run build
cd ..
```

3. **Configure systemd service** as described in the Raspberry Pi Setup section

## Configuration

### SSL/HTTPS Setup

Push notifications require HTTPS. To enable HTTPS:

```bash
cd server
python3 generate_ssl_cert.py
```

This creates a self-signed certificate for development. The server will automatically use it when present.

**Note:** Browsers will show a security warning for self-signed certificates - this is normal for development.

### Environment Variables

The server can be configured via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_PORT` | `8080` | Server port |
| `FLASK_DEBUG` | `false` | Debug mode |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated CORS origins |
| `FRAME_DELAY` | `0.1` | Delay between frames (seconds) |
| `VAPID_PRIVATE_KEY_FILE` | `vapid_private.pem` | Path to VAPID private key file |
| `VAPID_EMAIL` | `admin@example.com` | Contact email for push service |
| `CERT_FILE` | `cert.pem` | Path to SSL certificate file |
| `KEY_FILE` | `key.pem` | Path to SSL private key file |

## Running

### Start the server

```bash
cd server
python server.py
```

The server will start on `http://0.0.0.0:8080` by default.

### Enable Motion Detection with Push Notifications

Motion detection automatically handles push notification setup when enabled.

1. **Generate VAPID keys:**
   ```bash
   cd server
   source venv/bin/activate
   python generate_vapid_keys.py
   ```
   The script will generate compatible keys using the py-vapid library and save them to:
   - `vapid_private_key.pem` - Private key file
   - `.env` - Configuration with file reference

2. **Restart server** to load the keys.

3. **Enable motion detection:**
   - Open the camera interface at `https://[PI-IP]:8080`
   - Open control panel (tap chevron button)
   - In Motion Detection section, click **"Enable"**
   - Motion detection and push notifications will be configured automatically

**Important for iOS:** Push notifications only work when the app is installed as a PWA:
1. In Safari, navigate to `https://[PI-IP]:8080`
2. Tap Share → "Add to Home Screen" 
3. Open the app from the home screen icon (not Safari)
4. Only then enable motion detection for notifications to work

### Access the web interface

Navigate to `http://[PI-IP-ADDRESS]:8080` in your web browser. The server serves the UI directly.

#### Install as Mobile App (PWA)

The interface can be installed as a Progressive Web App for fullscreen experience. **Note: On iOS, PWA installation is required for push notifications to work.**

**iOS (Safari) - Required for push notifications:**
1. Navigate to `https://[PI-IP-ADDRESS]:8080`
2. Tap the Share button (square with arrow)
3. Select "Add to Home Screen"
4. Name it "PiCam" and tap "Add"
5. Launch from home screen icon (not Safari) for fullscreen view and notifications

**Android (Chrome):**
1. Navigate to `https://[PI-IP-ADDRESS]:8080`
2. Tap the three-dot menu
3. Select "Add to Home screen" or "Install app"
4. Launch from home screen for fullscreen view

The PWA runs in standalone mode without browser UI, providing an app-like experience. Push notifications work in both regular browser and PWA mode on Android, but only in PWA mode on iOS.

## Features

### Live Camera Streaming
- Real-time MJPEG stream with timestamp overlay
- Adjustable frame rate and quality
- Works on any device with a web browser
- Stream sync status indicator with color-coded timestamps:
  - Green (< 5s delay): Stream is in sync
  - Yellow (5-10s delay): Minor delay warning with yellow screen pulse
  - Red (10+ seconds): Significant delay with red screen pulse

### Motion Detection
- Frame differencing algorithm for motion detection
- Configurable sensitivity and detection zones
- Cooldown periods to prevent notification spam
- Visual indicators in the UI
- Optional visual alerts (yellow screen pulse) when motion detected
- Optional sound alerts (double beep at 440Hz) when motion detected
- Independent toggles for visual and sound alerts

### Audio Detection
- Real-time audio level monitoring from USB microphone
- Configurable sensitivity threshold and duration
- Optional visual alerts (yellow screen pulse) when audio detected
- Optional sound alerts (single beep at 523Hz) when audio detected
- Independent toggles for visual and sound alerts
- Cooldown periods to prevent alert spam
- Push notifications for audio events

### Alert System
- Unified alert system for motion and audio detection
- Visual alerts: Yellow screen pulse effect
- Sound alerts: Web Audio API generated tones (no files needed)
- 5-second cooldown between alerts to prevent spam
- Settings persist in browser localStorage
- All alerts are optional and independently configurable

### Push Notifications
- Browser push notifications for motion and audio events
- Works when browser is closed or phone is locked
- No registration or API keys required
- Uses Web Push Protocol with VAPID authentication

### Camera Controls
- Comprehensive control panel with sliders and toggles
- Grouped by category (Image Quality, Exposure, White Balance)
- Real-time adjustments
- Preset configurations for common scenarios

### System Power Control
- Remote shutdown and restart capabilities
- Confirmation dialogs to prevent accidental power operations
- Mock mode support for development without hardware
- Visual power button in the UI top-left corner

## API Endpoints

### Core Endpoints

#### `GET /`
Serves the React application build.

#### `GET /video_feed`
Returns MJPEG video stream with timestamp overlay and optional motion detection.

#### `GET /health`
Server health check.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01 12:00:00",
  "config": {
    "host": "0.0.0.0",
    "port": 8080,
    "debug": false,
    "cors_origins": ["http://localhost:3000"]
  }
}
```

#### `GET /api/app-info`
Application version and update information.

**Response:**
```json
{
  "version": "abc1234",
  "last_modified": "2024-01-01T12:00:00",
  "timestamp": "2024-01-01T12:00:00"
}
```

### Camera Endpoints

#### `GET /presets`
List available camera presets.

**Response:**
```json
{
  "presets": ["default", "low_light"],
  "current": null
}
```

#### `POST /apply_preset`
Apply camera preset configuration.

**Request:**
```json
{
  "preset": "default" | "low_light"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Applied default preset successfully"
}
```

### Motion Detection Endpoints

#### `GET /api/motion/status`
Get current motion detection status.

**Response:**
```json
{
  "enabled": true,
  "config": {
    "sensitivity": 0.02,
    "min_area": 500,
    "cooldown_seconds": 30,
    "blur_size": 21,
    "threshold": 25
  },
  "recent_events": 5,
  "triggered_events": 2
}
```

#### `POST /api/motion/config`
Update motion detection configuration.

**Request:**
```json
{
  "enabled": true,
  "sensitivity": 0.02,
  "min_area": 500,
  "cooldown_seconds": 30,
  "blur_size": 21,
  "threshold": 25
}
```

#### `GET /api/motion/presets`
Get available motion detection presets.

**Response:**
```json
{
  "presets": {
    "sensitive": "High sensitivity for indoor monitoring",
    "normal": "Balanced settings for general use",
    "outdoor": "Reduced sensitivity for outdoor environments",
    "security": "Optimized for security monitoring",
    "disabled": "Motion detection disabled"
  }
}
```

#### `POST /api/motion/preset`
Apply a motion detection preset.

**Request:**
```json
{
  "preset": "outdoor"
}
```

### Push Notification Endpoints

#### `GET /api/push/vapid-key`
Get VAPID public key for push subscriptions.

#### `POST /api/push/subscribe`
Subscribe to push notifications.

**Request:**
```json
{
  "endpoint": "https://fcm.googleapis.com/...",
  "keys": {
    "p256dh": "...",
    "auth": "..."
  }
}
```

### System Endpoints

#### `POST /api/system/shutdown`
Shutdown the Raspberry Pi system.

**Request:**
```json
{
  "confirm": true
}
```

**Response:**
```json
{
  "status": "success",
  "message": "System shutdown initiated",
  "timestamp": "2024-01-01 12:00:00"
}
```

#### `POST /api/system/restart`
Restart the Raspberry Pi system.

**Request:**
```json
{
  "confirm": true
}
```

**Response:**
```json
{
  "status": "success",
  "message": "System restart initiated",
  "timestamp": "2024-01-01 12:00:00"
}
```

#### `GET /api/system/status`
Get current system status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01 12:00:00",
  "mock_mode": false,
  "platform": "raspberry-pi"
}
```

## Camera Presets

### Default
Standard camera settings with automatic white balance and exposure.

### Low Light
Optimized for low-light conditions with:
- Extended exposure time (100ms)
- Increased analog gain (4.0)
- Tungsten white balance
- Night HDR mode (Pi 5 only)

## Project Structure

```
pi-in-the-sky/
├── server/
│   ├── server.py          # Flask application entry point
│   ├── app_factory.py     # Flask application factory with DI
│   ├── services.py         # Camera and streaming services
│   ├── motion_services.py # Motion detection and notifications
│   ├── storage.py         # SQLite subscription storage
│   ├── calculations.py     # Image processing and motion detection
│   ├── models.py          # Data models including motion events
│   ├── result.py          # Result type for error handling
│   ├── config.py          # Configuration management
│   ├── motion_presets.py  # Motion detection preset configurations
│   ├── mock_camera.py     # Mock camera for development
│   ├── routes/            # Flask route blueprints
│   │   ├── __init__.py    # Blueprint initialization
│   │   ├── camera.py      # Camera control endpoints
│   │   ├── motion.py      # Motion detection endpoints
│   │   ├── photos.py      # Photo gallery endpoints
│   │   ├── push.py        # Push notification endpoints
│   │   ├── static.py      # Static file serving
│   │   └── system.py      # System power control endpoints
│   ├── generate_vapid_keys.py # VAPID key generation utility
│   ├── generate_ssl_cert.py   # SSL certificate generation
│   ├── requirements.txt   # Python dependencies
│   ├── run_tests.py      # Test runner
│   └── test_architecture.py # Architecture tests
└── ui/                    # React PWA frontend
    ├── src/
    │   ├── api/           # API client and hooks
    │   ├── components/    # React components
    │   │   ├── VideoStream.tsx
    │   │   ├── ControlPanel.tsx
    │   │   ├── CameraControls.tsx
    │   │   ├── MotionDetection.tsx
    │   │   └── ErrorBoundary.tsx
    │   ├── types/         # TypeScript definitions
    │   ├── App.tsx        # Main application
    │   ├── main.tsx       # React entry point
    │   └── PWABadge.tsx   # PWA installation prompt
    ├── public/
    │   └── sw.js          # Service worker
    ├── package.json       # Frontend dependencies
    ├── vite.config.ts     # Vite + PWA configuration
    └── pwa-assets.config.ts # PWA asset generation config
```

## Architecture

### Server

The server follows a layered architecture:

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Flask     │────▶│   Services   │────▶│   Camera    │
│  (HTTP)     │     │ (Orchestrate)│     │    (I/O)    │
└─────────────┘     └──────────────┘     └─────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │ Calculations │
                    │    (Pure)    │
                    └──────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │    Models    │
                    │  (Immutable) │
                    └──────────────┘
```

- **HTTP Layer** (`server.py`, `app_factory.py`): Flask endpoints and application factory
- **Route Layer** (`routes/`): Organized blueprints for different API concerns
- **Service Layer** (`services.py`, `motion_services.py`): Camera operations and streaming
- **Calculation Layer** (`calculations.py`): Pure functions for image processing
- **Data Layer** (`models.py`): Immutable data structures
- **Result Type** (`result.py`): Functional error handling with Result monad
- **Configuration** (`config.py`): Environment-based settings
- **Motion Presets** (`motion_presets.py`): Predefined motion detection configurations

### UI

Modern React PWA with:
- **React + TypeScript** for type-safe component architecture
- **Tailwind CSS** for responsive, dark-themed design
- **Vite** for fast builds and hot module replacement
- **PWA Support** with service worker and offline capabilities
- **Real-time streaming** with automatic reconnection
- **Touch-optimized** controls for mobile devices

#### Keyboard Shortcuts
- **Space** - Toggle control panel
- **Escape** - Close control panel

#### Browser Compatibility
Works in all modern browsers:
- Chrome/Edge 90+
- Safari 14+ (iOS 14+)
- Firefox 88+
- Full iOS PWA support (no module loading issues)

## Frontend Development

The UI is a modern React application with TypeScript and Tailwind CSS:

```bash
cd ui

# Install dependencies
npm install

# Start development server (proxies to backend on port 8080)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Key Features
- **VideoStream Component**: MJPEG streaming with auto-reconnection
- **ControlPanel**: Tabbed interface for presets, controls, and motion detection
- **CameraControls**: Dynamic control generation from API
- **MotionDetection**: Push notification management and event display
- **PWA Support**: Installable on iOS/Android with offline capabilities

## Testing

The project includes comprehensive tests that run automatically on all pull requests:

### Run Tests Locally

```bash
cd server

# Run core functionality tests
python run_tests.py

# Run architecture verification tests
python test_architecture.py
```

### Test Coverage

- **Pure calculations**: Image processing, motion detection algorithms
- **Data models**: Immutability and structure validation
- **Service layer**: Initialization and core operations
- **API endpoints**: Health checks and configuration
- **Mock camera**: Development without hardware

### Continuous Integration

GitHub Actions automatically runs tests on:
- All pull requests to main branch
- Python versions 3.9, 3.10, 3.11, and 3.12
- Tests run without requiring Raspberry Pi hardware

## Raspberry Pi Setup

### Automatic Startup with systemd

1. **Create the service file:**

```bash
sudo nano /etc/systemd/system/pi-camera-stream.service
```

2. **Add this configuration (adjust paths and username as needed):**

```ini
[Unit]
Description=Pi Camera Streaming Server
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
Group=video
SupplementaryGroups=video i2c gpio
WorkingDirectory=/home/YOUR_USERNAME/pi-in-the-sky/server
Environment="FLASK_PORT=8080"
Environment="FLASK_DEBUG=false"
Environment="CORS_ORIGINS=http://localhost:8080"
# Add VAPID keys here if using motion detection
# Environment="VAPID_PRIVATE_KEY=your-private-key"
# Environment="VAPID_PUBLIC_KEY=your-public-key"
# Environment="VAPID_EMAIL=admin@example.com"
ExecStart=/home/YOUR_USERNAME/pi-in-the-sky/server/venv/bin/python /home/YOUR_USERNAME/pi-in-the-sky/server/server.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

3. **Enable and start the service:**

```bash
# Reload systemd configuration
sudo systemctl daemon-reload

# Enable service to start at boot
sudo systemctl enable pi-camera-stream

# Start the service now
sudo systemctl start pi-camera-stream

# Check status
sudo systemctl status pi-camera-stream

# View logs if needed
sudo journalctl -u pi-camera-stream -f
```

4. **Access the interface:**
   - From the Pi itself: `http://localhost:8080`
   - From another device on the network: `http://[PI-IP-ADDRESS]:8080`
   - Find your Pi's IP with: `hostname -I`

### Managing the Service

```bash
# Stop the service
sudo systemctl stop pi-camera-stream

# Restart the service (after updating dependencies or configuration)
sudo systemctl restart pi-camera-stream

# Disable automatic startup
sudo systemctl disable pi-camera-stream

# View logs
sudo journalctl -u pi-camera-stream -n 50
```

### Troubleshooting Service Issues

If the service fails to start:

1. **Check port availability:**
```bash
sudo lsof -i :8080
```

2. **Test manual startup:**
```bash
cd /home/YOUR_USERNAME/pi-in-the-sky/server
python3 server.py
```

3. **Common fixes:**
   - If port 8080 is in use, change `FLASK_PORT` in the service file
   - Ensure all Python dependencies are installed
   - Verify camera is enabled: `sudo raspi-config` → Interface Options → Camera
   - Reboot if camera or port issues persist: `sudo reboot`

## Headless Setup in New Location

When moving to a new location with only an Ethernet cable and no monitor:

### 1. Find the Pi's IP Address

After connecting the Pi to Ethernet and powering it on, find its IP from your laptop:

**Option A: Using nmap (most reliable)**
```bash
# Install nmap if needed
# Mac: brew install nmap
# Linux: sudo apt install nmap
# Windows: Download from nmap.org

# Scan your network (adjust IP range to match your network)
nmap -sn 192.168.1.0/24
# or
sudo nmap -sn 192.168.0.0/24

# Look for "Raspberry Pi" in the output
```

**Option B: Using arp**
```bash
# Mac/Linux: Look for Raspberry Pi MAC addresses (start with B8:27:EB or DC:A6:32)
arp -a | grep -i "b8:27:eb\|dc:a6:32"

# Windows
arp -a
# Look for MAC addresses starting with b8-27-eb or dc-a6-32
```

**Option C: Check router's DHCP client list**
- Access your router's admin page (usually 192.168.1.1 or 192.168.0.1)
- Look for DHCP clients/connected devices
- Find device named "raspberrypi" or with Raspberry Pi MAC address

### 2. SSH into the Pi
```bash
ssh YOUR_USERNAME@[PI-IP-ADDRESS]
```

### 3. Configure WiFi from Command Line

Once connected via SSH:

```bash
# Method 1: Using nmcli (if NetworkManager is installed)
sudo nmcli dev wifi connect "WiFi-Network-Name" password "WiFi-Password"

# Method 2: Using wpa_supplicant (standard on Raspberry Pi OS)
sudo nano /etc/wpa_supplicant/wpa_supplicant.conf
```

Add your network to wpa_supplicant.conf:
```
country=US
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={
    ssid="Your-WiFi-Network-Name"
    psk="Your-WiFi-Password"
    key_mgmt=WPA-PSK
}
```

Then restart networking:
```bash
sudo systemctl restart networking
# or
sudo reboot
```

### 4. Find the New WiFi IP Address
```bash
# While still connected via Ethernet
ip addr show wlan0
# or
hostname -I
```

### 5. Make Pi Easier to Find (Optional)

**Enable mDNS (Avahi) for hostname access:**
```bash
# Should be installed by default, but if not:
sudo apt install avahi-daemon

# Access your Pi as:
# raspberrypi.local (or YOUR_HOSTNAME.local)
```

**Set a static IP (optional):**
```bash
sudo nano /etc/dhcpcd.conf
```

Add at the end:
```
interface wlan0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=192.168.1.1 8.8.8.8
```

### Pro Tips for Headless Setup

1. **Before moving locations**, while you still have access:
   ```bash
   # Save your current network config
   sudo cat /etc/wpa_supplicant/wpa_supplicant.conf > ~/networks_backup.txt
   
   # Pre-add the new location's WiFi
   sudo nano /etc/wpa_supplicant/wpa_supplicant.conf
   # Add multiple networks - Pi will connect to whichever is available
   ```

2. **Create a setup script** on the Pi:
   ```bash
   nano ~/connect_wifi.sh
   ```
   ```bash
   #!/bin/bash
   echo "Available networks:"
   sudo iwlist wlan0 scan | grep ESSID
   read -p "Enter SSID: " ssid
   read -sp "Enter Password: " password
   echo
   sudo nmcli dev wifi connect "$ssid" password "$password"
   ```
   ```bash
   chmod +x ~/connect_wifi.sh
   ```

3. **Enable SSH over Ethernet** (should be default):
   ```bash
   sudo systemctl enable ssh
   sudo systemctl start ssh
   ```

### Web Interface

The `ui/index.html` file can be:
- Opened directly from the filesystem
- Served by any static web server
- Embedded in other applications

## Troubleshooting

### Camera not initializing (showing mock camera instead of real camera)

This is the most common issue when the server says "PiCamera2 not available, using mock camera".

**Root Cause:** The virtual environment was created without system packages access, so it can't see the system-installed `picamera2`.

**Fix:**
1. Stop the server: `sudo systemctl stop pi-camera-stream.service`
2. Recreate the virtual environment with system packages:
   ```bash
   cd /home/james/pi-in-the-sky/server
   rm -rf venv
   python3 -m venv venv --system-site-packages
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Restart the server: `sudo systemctl start pi-camera-stream.service`

**Verification:** Check that `include-system-site-packages = true` in `venv/pyvenv.cfg`

**Why this happens:** On Raspberry Pi, `picamera2` must be installed as a system package (not via pip) because it needs access to system camera drivers. The virtual environment needs the `--system-site-packages` flag to access these system packages.

### Push Notifications Not Working

If motion detection is enabled but push notifications aren't being sent:

**Symptoms:**
- Motion detection works (you see events in `/api/motion/status`)
- VAPID key endpoint returns empty response or 404
- No push notifications received despite motion being detected
- Error logs show "Could not deserialize key data" or "header too long"

**Root Cause:** VAPID key generation or loading compatibility issue between py-vapid and pywebpush libraries.

**Fix:**
1. **Generate new compatible VAPID keys:**
   ```bash
   cd server
   source venv/bin/activate
   python generate_vapid_keys.py
   ```
   This will create:
   - `vapid_private_key.pem` - Private key file (recommended approach)
   - `.env` - Configuration with `VAPID_PRIVATE_KEY_FILE=vapid_private_key.pem`

2. **Restart the service:**
   ```bash
   sudo systemctl restart pi-camera-stream.service
   ```

3. **Verify the fix:**
   ```bash
   # Should return your public key (requires HTTPS on most browsers)
   curl -k https://localhost:8080/api/push/vapid-key
   ```

**Why this happens:** Earlier versions of the VAPID key generator used manual cryptography that was incompatible with current py-vapid/pywebpush versions. The updated generator uses py-vapid directly and saves keys to files, which avoids environment variable parsing issues.

**Important:** Push notifications require HTTPS. The server automatically generates self-signed certificates for development.

**Legacy Environment Variable Approach:** If you prefer environment variables, ensure you have compatible keys generated with py-vapid and properly escaped in the systemd service file.

### Other Camera Issues
- Ensure camera is enabled: `sudo raspi-config`
- Check camera connection
- Verify user is in video group: `groups $USER`
- Check for camera conflicts: `sudo lsof /dev/video*`

### Stream not displaying
- Check server is running: `curl http://localhost:8080/health`
- Verify CORS settings if accessing from different origin
- Check browser console for errors
- Test video feed directly: `curl http://localhost:8080/video_feed`

### Poor performance
- Adjust `FRAME_DELAY` environment variable
- Reduce resolution in camera configuration
- Check CPU usage and temperature

### Service Management Issues
- View service logs: `sudo journalctl -u pi-camera-stream.service -n 50`
- Check service status: `sudo systemctl status pi-camera-stream.service`
- Manual test: `cd server && python3 server.py`

## License

MIT