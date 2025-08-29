# Pi in the Sky

Raspberry Pi camera streaming application with web interface.

## Components

- **Server**: Flask-based Python server that interfaces with PiCamera2
- **UI**: Single-file HTML interface for viewing the stream and controlling camera settings

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
- PyWebPush 2.0.0 (for push notifications)
- Cryptography 41.0.4 (for VAPID keys)

## Installation

### Quick Setup on Raspberry Pi

```bash
# Clone repository
git clone https://github.com/yourusername/pi-in-the-sky.git
cd pi-in-the-sky

# Install server dependencies
cd server
pip3 install -r requirements.txt

# Ensure your user is in required groups for camera access
sudo usermod -a -G video $USER
sudo usermod -a -G i2c $USER
sudo usermod -a -G gpio $USER
# Log out and back in for group changes to take effect
```

## Configuration

The server can be configured via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_PORT` | `8080` | Server port |
| `FLASK_DEBUG` | `false` | Debug mode |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated CORS origins |
| `FRAME_DELAY` | `0.1` | Delay between frames (seconds) |
| `VAPID_PRIVATE_KEY` | - | Private key for push notifications |
| `VAPID_PUBLIC_KEY` | - | Public key for push notifications |
| `VAPID_EMAIL` | `admin@example.com` | Contact email for push service |

## Running

### Start the server

```bash
cd server
python server.py
```

The server will start on `http://0.0.0.0:8080` by default.

### Enable Motion Detection (Optional)

For motion detection with push notifications:

1. **Generate VAPID keys:**
   ```bash
   cd server
   python generate_vapid_keys.py
   ```
   Follow prompts to save keys to `.env` file.

2. **Restart server** to load the keys.

3. **In the web interface:**
   - Open control panel
   - Navigate to Motion Detection section
   - Enable motion detection
   - Allow push notifications when prompted

See [MOTION_DETECTION_SETUP.md](MOTION_DETECTION_SETUP.md) for detailed configuration.

### Access the web interface

Navigate to `http://[PI-IP-ADDRESS]:8080` in your web browser. The server serves the UI directly.

#### Install as Mobile App (PWA)

The interface can be installed as a Progressive Web App for fullscreen experience:

**iOS (Safari):**
1. Navigate to `http://[PI-IP-ADDRESS]:8080`
2. Tap the Share button (square with arrow)
3. Select "Add to Home Screen"
4. Name it and tap "Add"
5. Launch from home screen for fullscreen view

**Android (Chrome):**
1. Navigate to `http://[PI-IP-ADDRESS]:8080`
2. Tap the three-dot menu
3. Select "Add to Home screen" or "Install app"
4. Launch from home screen for fullscreen view

The PWA runs in standalone mode without browser UI, providing an app-like experience.

## Features

### Live Camera Streaming
- Real-time MJPEG stream with timestamp overlay
- Adjustable frame rate and quality
- Works on any device with a web browser

### Motion Detection 🆕
- Frame differencing algorithm for motion detection
- Configurable sensitivity and detection zones
- Cooldown periods to prevent notification spam
- Visual indicators in the UI

### Push Notifications 🆕
- Browser push notifications for motion events
- Works when browser is closed or phone is locked
- No registration or API keys required
- Uses Web Push Protocol with VAPID authentication

### Camera Controls
- Comprehensive control panel with sliders and toggles
- Grouped by category (Image Quality, Exposure, White Balance)
- Real-time adjustments
- Preset configurations for common scenarios

## API Endpoints

### Camera Endpoints

#### `GET /video_feed`
Returns MJPEG video stream with timestamp overlay and optional motion detection.

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

### `GET /health`
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

### `GET /presets`
List available camera presets.

**Response:**
```json
{
  "presets": ["default", "low_light"],
  "current": null
}
```

### Motion Detection Endpoints 🆕

#### `GET /api/motion/status`
Get current motion detection status.

**Response:**
```json
{
  "enabled": true,
  "config": {
    "sensitivity": 0.02,
    "min_area": 500,
    "cooldown_seconds": 30
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
  "cooldown_seconds": 30
}
```

### Push Notification Endpoints 🆕

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
│   ├── server.py          # Flask application with motion detection
│   ├── services.py         # Camera and streaming services
│   ├── motion_services.py # Motion detection and notifications
│   ├── storage.py         # SQLite subscription storage
│   ├── calculations.py     # Image processing and motion detection
│   ├── models.py          # Data models including motion events
│   ├── config.py          # Configuration management
│   ├── generate_vapid_keys.py # VAPID key generation utility
│   ├── requirements.txt   # Python dependencies
│   ├── test_architecture.py # Architecture tests
│   └── ui/                # PWA assets served by Flask
│       ├── manifest.json  # PWA manifest
│       └── service-worker.js # Service worker with push support
└── ui/
    ├── index.html         # Web interface with motion controls
    └── js/
        ├── api.js         # API client module
        ├── controls.js    # UI control logic
        └── motion.js      # Motion detection UI module
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

- **HTTP Layer** (`server.py`): Flask endpoints
- **Service Layer** (`services.py`): Camera operations and streaming
- **Calculation Layer** (`calculations.py`): Pure functions for image processing
- **Data Layer** (`models.py`): Immutable data structures
- **Configuration** (`config.py`): Environment-based settings

### UI

Single HTML file containing:
- Inline CSS styling
- Vanilla JavaScript for API interaction
- MJPEG stream display via img tag
- Responsive control panel

#### Keyboard Shortcuts
- **Space** - Toggle control panel
- **Escape** - Close control panel

#### Browser Compatibility
Works in all modern browsers that support:
- ES6 JavaScript (async/await)
- CSS Flexbox
- MJPEG streams via img tag

## Testing

Run architecture tests (no hardware required):

```bash
cd server
python test_architecture.py
```

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
ExecStart=/usr/bin/python3 /home/YOUR_USERNAME/pi-in-the-sky/server/server.py
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

# Restart the service
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

### Camera not initializing
- Ensure camera is enabled: `sudo raspi-config`
- Check camera connection
- Verify PiCamera2 installation

### Stream not displaying
- Check server is running: `curl http://localhost:8080/health`
- Verify CORS settings if accessing from different origin
- Check browser console for errors

### Poor performance
- Adjust `FRAME_DELAY` environment variable
- Reduce resolution in camera configuration
- Check CPU usage and temperature

## License

MIT