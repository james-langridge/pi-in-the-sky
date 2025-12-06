# Troubleshooting

Common issues and solutions.

## Camera Issues

### Mock camera instead of real camera

**Symptom:** Server says "PiCamera2 not available, using mock camera"

**Cause:** Virtual environment can't access system-installed picamera2.

**Fix:**
```bash
sudo systemctl stop pi-camera-stream.service
cd /home/YOUR_USERNAME/pi-in-the-sky/server
rm -rf venv
python3 -m venv venv --system-site-packages
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl start pi-camera-stream.service
```

**Verify:** Check that `include-system-site-packages = true` in `venv/pyvenv.cfg`

### Camera not detected

1. Enable camera: `sudo raspi-config` > Interface Options > Camera
2. Check connection: camera ribbon cable seated properly
3. Verify user groups: `groups $USER` should include `video`
4. Check conflicts: `sudo lsof /dev/video*`
5. Reboot: `sudo reboot`

## Push Notifications

### Notifications not working

**Symptoms:**
- Motion detection works (events in `/api/motion/status`)
- VAPID key endpoint returns empty or 404
- No notifications despite motion detected

**Fix:**
```bash
cd server
source venv/bin/activate
python generate_vapid_keys.py
sudo systemctl restart pi-camera-stream.service
```

**Verify:**
```bash
curl -k https://localhost:8080/api/push/vapid-key
```

**Requirements:**
- HTTPS required (server auto-generates self-signed cert)
- Browser must have notification permission
- iOS: Must be installed as PWA (Add to Home Screen)

### Too many false positives

1. Increase sensitivity value (less sensitive)
2. Increase minimum area to ignore small movements
3. Adjust threshold for your lighting

### Motion not detected

1. Decrease sensitivity value (more sensitive)
2. Decrease minimum area
3. Verify motion detection is enabled (green indicator)

## Streaming Issues

### Stream not displaying

1. Check server: `curl http://localhost:8080/health`
2. Test video feed: `curl http://localhost:8080/video_feed`
3. Check browser console for errors
4. Verify CORS settings if accessing from different origin

### Poor performance

1. Increase `FRAME_DELAY` environment variable
2. Reduce camera resolution
3. Check CPU usage and temperature: `vcgencmd measure_temp`

## Service Issues

### Service won't start

1. Check port: `sudo lsof -i :8080`
2. Test manually: `cd server && python3 server.py`
3. View logs: `sudo journalctl -u pi-camera-stream -n 50`
4. Change port if 8080 in use (edit systemd service file)

### "externally-managed-environment" error

On Raspberry Pi OS Bookworm+:

```bash
python3 -m venv venv --system-site-packages
source venv/bin/activate
pip install -r requirements.txt
```

Or install system packages:
```bash
sudo apt install python3-flask python3-flask-cors python3-opencv python3-numpy
```

## Network Issues

### Can't find Pi on network

See [Headless Setup](raspberry-pi.md#headless-setup-new-location) for IP discovery methods.

### Can't access from other devices

1. Check firewall: `sudo ufw status`
2. Verify Pi IP: `hostname -I`
3. Test locally first: `curl http://localhost:8080/health`
4. Check if server bound to 0.0.0.0 (not 127.0.0.1)
