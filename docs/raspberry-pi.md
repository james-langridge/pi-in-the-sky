# Raspberry Pi Setup

Detailed setup guide for running Pi in the Sky on a Raspberry Pi.

## Automatic Startup with systemd

### 1. Create the service file

```bash
sudo nano /etc/systemd/system/pi-camera-stream.service
```

### 2. Add this configuration

Adjust paths and username as needed:

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
ExecStart=/home/YOUR_USERNAME/pi-in-the-sky/server/venv/bin/python /home/YOUR_USERNAME/pi-in-the-sky/server/server.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### 3. Enable and start

```bash
sudo systemctl daemon-reload
sudo systemctl enable pi-camera-stream
sudo systemctl start pi-camera-stream
sudo systemctl status pi-camera-stream
```

### 4. View logs

```bash
sudo journalctl -u pi-camera-stream -f
```

## Managing the Service

```bash
sudo systemctl stop pi-camera-stream      # Stop
sudo systemctl restart pi-camera-stream   # Restart
sudo systemctl disable pi-camera-stream   # Disable auto-start
sudo journalctl -u pi-camera-stream -n 50 # View recent logs
```

## Headless Setup (New Location)

When moving to a new location without a monitor.

### If Pi already knows the WiFi network

Just power on - it will auto-connect. Find its IP and SSH in.

### If Pi doesn't know the WiFi network

1. Connect Pi to router via Ethernet
2. Find its IP (see below)
3. SSH in and configure WiFi
4. Disconnect Ethernet

### Finding the Pi's IP Address

**Find your network subnet first:**
```bash
ip route | grep default
# Example: default via 192.168.4.1 dev wlan0
# Your subnet is 192.168.4.0/24
```

**Option A: Before/after scan (most reliable)**
```bash
# Before powering on Pi:
nmap -sn 192.168.4.0/24 | grep "Nmap scan report" | awk '{print $NF}' | sort > /tmp/before.txt

# Power on Pi, wait 60 seconds, then:
nmap -sn 192.168.4.0/24 | grep "Nmap scan report" | awk '{print $NF}' | sort > /tmp/after.txt

# Compare:
diff /tmp/before.txt /tmp/after.txt
```

**Option B: Using nmap with MAC detection**
```bash
sudo nmap -sn 192.168.4.0/24
# Look for Raspberry Pi MAC prefixes:
# b8:27:eb, dc:a6:32, e4:5f:01, d8:3a:dd, 2c:cf:67
```

**Option C: Check router's DHCP client list**

Access your router's admin page and look for "raspberrypi" or Pi MAC addresses.

### Configure WiFi via SSH

```bash
# Method 1: nmcli (if NetworkManager installed)
sudo nmcli dev wifi connect "WiFi-Name" password "WiFi-Password"

# Method 2: wpa_supplicant
sudo nano /etc/wpa_supplicant/wpa_supplicant.conf
```

Add to wpa_supplicant.conf:
```
country=US
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={
    ssid="Your-WiFi-Name"
    psk="Your-Password"
    key_mgmt=WPA-PSK
}
```

Then restart:
```bash
sudo systemctl restart networking
```

### Make Pi Easier to Find

**Enable mDNS:**
```bash
sudo apt install avahi-daemon
# Access as: raspberrypi.local
```

**Set static IP (optional):**
```bash
sudo nano /etc/dhcpcd.conf
```

Add:
```
interface wlan0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=192.168.1.1 8.8.8.8
```

## Camera Presets

### Default
Standard settings with automatic white balance and exposure.

### Low Light
Optimized for dark conditions:
- Extended exposure time (100ms)
- Increased analog gain (4.0)
- Tungsten white balance
- Night HDR mode (Pi 5 only)

## SSL/HTTPS Setup

Push notifications require HTTPS:

```bash
cd server
python3 generate_ssl_cert.py
```

This creates a self-signed certificate. Browsers will show a security warning - this is normal for development.

## Push Notifications Setup

### 1. Generate VAPID keys

```bash
cd server
source venv/bin/activate
python generate_vapid_keys.py
```

### 2. Restart server

```bash
sudo systemctl restart pi-camera-stream.service
```

### 3. Enable in the UI

Open the camera interface, go to Motion Detection, and click "Enable".

### iOS Push Notifications

Push notifications on iOS only work when installed as a PWA:
1. In Safari, navigate to `https://[PI-IP]:8080`
2. Tap Share > "Add to Home Screen"
3. Open from home screen icon (not Safari)
4. Then enable motion detection
