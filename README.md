# Pi in the Sky

Raspberry Pi camera streaming with motion detection, push notifications, and a Progressive Web App interface.

## Quick Start

### Automated Setup (Raspberry Pi)

```bash
curl -fsSL https://raw.githubusercontent.com/james-langridge/pi-in-the-sky/main/setup.sh | bash
```

The script installs dependencies, builds the frontend, and optionally configures systemd for auto-start.

### Manual Setup

```bash
# Clone and build frontend
git clone https://github.com/james-langridge/pi-in-the-sky.git
cd pi-in-the-sky/ui
npm install && npm run build

# Setup Python environment
cd ../server
python3 -m venv venv --system-site-packages
source venv/bin/activate
pip install -r requirements.txt

# Ensure camera access
sudo usermod -a -G video,i2c,gpio $USER
# Log out and back in for group changes

# Run
python server.py
```

Access at `http://[PI-IP]:8080`

## Features

- **Live Streaming** - MJPEG stream with timestamp overlay and sync status indicator
- **Motion Detection** - Frame differencing with configurable sensitivity and presets
- **Audio Detection** - Real-time audio monitoring from USB microphone
- **Push Notifications** - Browser notifications when motion/audio detected (works when phone locked)
- **PWA Support** - Install on mobile for fullscreen app-like experience
- **Camera Controls** - Exposure, white balance, presets via web interface
- **Remote Power** - Shutdown/restart Pi from the UI

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_PORT` | `8080` | Server port |
| `FLASK_DEBUG` | `false` | Debug mode |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated CORS origins |
| `FRAME_DELAY` | `0.1` | Delay between frames (seconds) |

For push notifications, generate VAPID keys:
```bash
cd server && python generate_vapid_keys.py
```

## Development (Without Pi)

The server auto-detects missing PiCamera2 and uses a mock camera:

```bash
cd server
python3 -m venv venv
source venv/bin/activate
pip install flask flask-cors opencv-python numpy pywebpush cryptography
python server.py
```

Frontend development:
```bash
cd ui
npm install
npm run dev  # Proxies to backend on :8080
```

## Common Issues

### Mock camera instead of real camera

Virtual environment needs system packages access:
```bash
rm -rf venv
python3 -m venv venv --system-site-packages
source venv/bin/activate
pip install -r requirements.txt
```

### Push notifications not working

1. HTTPS required - server auto-generates self-signed cert
2. Run `python generate_vapid_keys.py` and restart server
3. iOS: Must install as PWA (Safari > Share > Add to Home Screen)

### Can't access from other devices

Check Pi IP with `hostname -I` and ensure firewall allows port 8080.

## Documentation

- [API Reference](docs/api.md) - Complete endpoint documentation
- [Raspberry Pi Setup](docs/raspberry-pi.md) - systemd, headless setup, SSL
- [Development Guide](docs/development.md) - Architecture, testing, project structure
- [Troubleshooting](docs/troubleshooting.md) - Detailed problem solutions

## License

MIT
