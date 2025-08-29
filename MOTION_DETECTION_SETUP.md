# Motion Detection Setup Guide

This guide explains how to set up and use the motion detection feature with push notifications.

## Prerequisites

1. Install the required dependencies:
```bash
cd server
pip3 install -r requirements.txt
```

## Setup Steps

### 1. Generate VAPID Keys

VAPID keys are required for push notifications to work. Generate them using the provided utility:

```bash
cd server
python3 generate_vapid_keys.py
```

Follow the prompts to:
- Enter your contact email
- Save the keys to a `.env` file (recommended)

**Important:** Never commit the private key to version control!

### 2. Configure Environment Variables

If you didn't save to `.env` file, export the keys as environment variables:

```bash
export VAPID_PRIVATE_KEY='your-private-key-here'
export VAPID_PUBLIC_KEY='your-public-key-here'
export VAPID_EMAIL='admin@example.com'
```

### 3. Start the Server

```bash
cd server
python3 server.py
```

The server will initialize with motion detection capabilities.

## Using Motion Detection

### In the Web Interface

1. **Open the camera stream** in your browser
2. **Click the control panel toggle** at the bottom of the video
3. **Navigate to Motion Detection section**

### Enable Motion Detection

1. Click the **"Enable"** button to activate motion detection
2. The indicator will turn green and pulse when active

### Configure Settings

Adjust these parameters for optimal detection:

- **Sensitivity** (0-1): Lower values = more sensitive
  - Default: 0.02
  - Increase if getting too many false positives
  
- **Minimum Area** (pixels): Minimum size of motion to detect
  - Default: 500 pixels
  - Increase to ignore small movements
  
- **Cooldown** (seconds): Time between notifications
  - Default: 30 seconds
  - Prevents notification spam
  
- **Detection Threshold**: Binary threshold for motion
  - Default: 25
  - Higher values require more significant changes

### Enable Push Notifications

1. Click **"Enable Notifications"** when prompted
2. Allow notification permissions in your browser
3. Notifications work even when:
   - Browser tab is in background
   - Browser is minimized
   - Phone screen is locked (on mobile)

### Test the System

1. Click **"Test Notification"** to verify push notifications work
2. You should receive a test notification immediately

## How It Works

### Motion Detection Algorithm

The system uses frame differencing:
1. Compares consecutive frames from the camera
2. Calculates pixel differences after Gaussian blur
3. Identifies contours of changed regions
4. Triggers events when motion exceeds thresholds

### Push Notification Flow

1. Motion detected → Event created
2. Check cooldown period
3. Send notification to all subscribed devices
4. Notification appears with action buttons

### Data Storage

- Push subscriptions stored in SQLite database (`subscriptions.db`)
- Database created automatically on first run
- Old subscriptions cleaned up periodically

## Troubleshooting

### Notifications not working?

1. **Check browser support**: Modern Chrome, Firefox, Edge required
2. **HTTPS required**: Push notifications need HTTPS (except localhost)
3. **Check permissions**: Browser must have notification permission
4. **Verify VAPID keys**: Ensure environment variables are set

### Too many false positives?

1. Increase **sensitivity** value (make less sensitive)
2. Increase **minimum area** to ignore small movements
3. Adjust **threshold** for your lighting conditions

### Motion not detected?

1. Decrease **sensitivity** value (make more sensitive)
2. Decrease **minimum area** to catch smaller movements
3. Check if motion detection is enabled (green indicator)

## Security Notes

- VAPID private key must remain secret
- Push subscriptions are device-specific
- Notifications use end-to-end encryption
- No motion data is stored long-term

## Mobile PWA Support

The app works as a Progressive Web App:
1. Open the camera URL on mobile
2. Add to home screen
3. Receive notifications even when app is closed

## API Endpoints

For programmatic access:

- `GET /api/motion/status` - Current motion detection status
- `GET /api/motion/config` - Get configuration
- `POST /api/motion/config` - Update configuration
- `GET /api/motion/events` - Recent motion events
- `POST /api/push/subscribe` - Subscribe to notifications
- `GET /api/push/vapid-key` - Get public key for subscription