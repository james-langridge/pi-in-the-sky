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
4. Switch to WiFi and disconnect Ethernet

### Finding the Pi's IP Address

**Step 1: Find your network subnet**

Run this on your laptop/desktop (not the Pi):
```bash
ip route | grep default
```

Example output:
```
default via 192.168.1.1 dev wlan0
```

The subnet is based on your gateway IP. Replace the last number with `0/24`:
- Gateway `192.168.1.1` → Subnet `192.168.1.0/24`
- Gateway `192.168.4.1` → Subnet `192.168.4.0/24`
- Gateway `10.0.0.1` → Subnet `10.0.0.0/24`

**Step 2: Find the Pi** (choose one method)

**Option A: Before/after scan (most reliable)**

Requires `nmap` installed (`sudo apt install nmap` or `brew install nmap`).

```bash
# 1. BEFORE connecting the Pi, scan your network:
nmap -sn 192.168.1.0/24 | grep "Nmap scan report" | awk '{print $NF}' | sort > /tmp/before.txt

# 2. Connect Pi via ethernet, power it on, wait 60 seconds

# 3. Scan again:
nmap -sn 192.168.1.0/24 | grep "Nmap scan report" | awk '{print $NF}' | sort > /tmp/after.txt

# 4. Compare - the new IP is your Pi:
diff /tmp/before.txt /tmp/after.txt
```

Example output:
```
4a5
> 192.168.1.167
```
The Pi's IP is `192.168.1.167`.

**Option B: Scan for Raspberry Pi MAC addresses**
```bash
sudo nmap -sn 192.168.1.0/24
# Look for Raspberry Pi MAC prefixes:
# b8:27:eb, dc:a6:32, e4:5f:01, d8:3a:dd, 2c:cf:67
```

**Option C: Check router's DHCP client list**

Access your router's admin page (usually http://192.168.1.1) and look for "raspberrypi" or Pi MAC addresses in the connected devices list.

### SSH into the Pi

```bash
ssh pi@192.168.1.167  # Replace with your Pi's IP and username
```

On first connection, you'll see a host key verification prompt:
```
The authenticity of host '192.168.1.167' can't be established.
ED25519 key fingerprint is SHA256:xWoyoJ...
Are you sure you want to continue connecting (yes/no/[fingerprint])?
```

Type `yes` and press Enter. This is normal for first-time connections - SSH is verifying the Pi's identity and will remember it for future connections.

### Terminal compatibility note

Some modern terminals (like Ghostty, Kitty, or Alacritty) may not be recognized by the Pi, causing errors like:
```
Error opening terminal: xterm-ghostty.
```

**Fix:** Set a compatible terminal type before running terminal apps:
```bash
export TERM=xterm-256color
sudo nano /etc/wpa_supplicant/wpa_supplicant.conf
```

Or use `vi` instead of `nano`, which has fewer terminal dependencies.

### Configure WiFi via SSH

**Method 1: nmcli (recommended)**

Most modern Raspberry Pi OS installations use NetworkManager:
```bash
sudo nmcli dev wifi connect "Your-WiFi-Name" password "Your-Password"
```

If successful, you'll see:
```
Device 'wlan0' successfully activated with '...'
```

**Method 2: wpa_supplicant (older systems)**

```bash
export TERM=xterm-256color  # If needed for nano
sudo nano /etc/wpa_supplicant/wpa_supplicant.conf
```

Add:
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

Then restart networking:
```bash
sudo systemctl restart networking
```

### Switch from Ethernet to WiFi

After configuring WiFi, no reboot is needed. Get the WiFi IP **while still connected via ethernet**:

```bash
# Run this on the Pi (via your ethernet SSH session):
ip addr show wlan0
```

Look for the `inet` line:
```
3: wlan0: <BROADCAST,MULTICAST,UP,LOWER_UP> ...
    inet 192.168.1.170/24 brd 192.168.1.255 scope global dynamic wlan0
```

The WiFi IP is `192.168.1.170` (yours will differ). Write it down.

Now you can safely switch:

1. Disconnect the ethernet cable from the Pi
2. Exit your current SSH session (it will hang since ethernet is gone)
3. From your laptop, SSH to the WiFi IP:
   ```bash
   ssh pi@192.168.1.170  # Use your WiFi IP
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

## Remote Access via Tailscale

Access your camera from anywhere (outside your home network) using Tailscale, a zero-config VPN.

### Why Tailscale?

- No port forwarding or exposing your home IP
- End-to-end encrypted (WireGuard)
- Works behind any NAT/firewall
- Free for personal use
- No changes to the camera app required

### Setup

**1. Install Tailscale on the Pi:**

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

Follow the authentication URL to link to your Tailscale account.

**2. Get the Pi's Tailscale IP:**

```bash
tailscale ip -4
# Example output: 100.76.141.42
```

**3. Install Tailscale on your phone/laptop:**

- iOS/Android: Install from App Store / Play Store
- macOS/Windows/Linux: https://tailscale.com/download

**4. Access your camera:**

```
https://100.x.x.x:8080
```

Replace with your Pi's Tailscale IP. Use `https://` (the server runs HTTPS).

Your browser will show a certificate warning (self-signed cert) - click through to proceed.

### Verify Connectivity

From any device with Tailscale:

```bash
tailscale status          # Shows all connected devices
ping 100.x.x.x            # Test connectivity to Pi
curl -k https://100.x.x.x:8080/health  # Test the server
```

### Optional: Friendly Hostname

In the [Tailscale admin console](https://login.tailscale.com/admin/machines), rename your Pi to something memorable. With MagicDNS enabled, access it as:

```
https://pi-camera.your-tailnet.ts.net:8080
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
