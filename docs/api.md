# API Reference

Complete API documentation for Pi in the Sky.

## Core Endpoints

### `GET /`
Serves the React application.

### `GET /video_feed`
MJPEG video stream with timestamp overlay.

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

### `GET /api/app-info`
Application version information.

**Response:**
```json
{
  "version": "abc1234",
  "last_modified": "2024-01-01T12:00:00",
  "timestamp": "2024-01-01T12:00:00"
}
```

## Camera Endpoints

### `GET /presets`
List available camera presets.

**Response:**
```json
{
  "presets": ["default", "low_light"],
  "current": null
}
```

### `POST /apply_preset`
Apply a camera preset.

**Request:**
```json
{
  "preset": "default"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Applied default preset successfully"
}
```

## Motion Detection Endpoints

### `GET /api/motion/status`
Get motion detection status.

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

### `GET /api/motion/config`
Get current motion detection configuration.

### `POST /api/motion/config`
Update motion detection settings.

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

### `GET /api/motion/presets`
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

### `POST /api/motion/preset`
Apply a motion detection preset.

**Request:**
```json
{
  "preset": "outdoor"
}
```

### `GET /api/motion/events`
Get recent motion events with metadata.

## Push Notification Endpoints

### `GET /api/push/vapid-key`
Get VAPID public key for client subscription.

### `POST /api/push/subscribe`
Register device for push notifications.

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

### `POST /api/push/unsubscribe`
Remove push subscription.

### `POST /api/push/test`
Send test notification to verify setup.

## System Endpoints

### `GET /api/system/status`
Get system status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01 12:00:00",
  "mock_mode": false,
  "platform": "raspberry-pi"
}
```

### `POST /api/system/shutdown`
Shutdown the Raspberry Pi.

**Request:**
```json
{
  "confirm": true
}
```

### `POST /api/system/restart`
Restart the Raspberry Pi.

**Request:**
```json
{
  "confirm": true
}
```
