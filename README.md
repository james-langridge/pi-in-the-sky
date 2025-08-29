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

## Running

### Start the server

```bash
cd server
python server.py
```

The server will start on `http://0.0.0.0:8080` by default.

### Access the web interface

Open `ui/index.html` in a web browser, or serve it from any web server:

```bash
cd ui
python3 -m http.server 3000
# Navigate to http://localhost:3000
```

## API Endpoints

### `GET /video_feed`
Returns MJPEG video stream with timestamp overlay.

### `POST /apply_preset`
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
│   ├── server.py          # Flask application
│   ├── services.py         # Camera and streaming services
│   ├── calculations.py     # Image processing functions
│   ├── models.py          # Data models
│   ├── config.py          # Configuration management
│   ├── requirements.txt   # Python dependencies
│   └── test_architecture.py # Architecture tests
└── ui/
    └── index.html         # Web interface
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