# Pi Camera Server - Refactored Architecture

## Overview

This server has been refactored to follow functional programming principles and clean architecture patterns, separating concerns into distinct layers:

- **Data Layer**: Immutable data structures (models.py)
- **Calculation Layer**: Pure functions for business logic (calculations.py)  
- **Action Layer**: Thin orchestration of I/O operations (services.py)
- **Configuration**: Centralized, immutable configuration (config.py)
- **HTTP Layer**: Flask endpoints as thin adapters (server.py)

## Architecture Benefits

### Improved Design
- **Separation of Concerns**: Clear boundaries between layers
- **Immutable Data**: No hidden state changes or mutations
- **Pure Functions**: Business logic is testable without hardware
- **Deep Modules**: Complex implementation hidden behind simple interfaces
- **Dependency Injection**: Services can be mocked for testing

### Security Improvements
- **Removed dangerous shutdown endpoint** that allowed unauthenticated system shutdown
- **Input validation** on all endpoints
- **Proper error handling** without exposing internals
- **Configurable CORS** instead of hardcoded values

### Maintainability
- **Testable**: Pure functions can be tested in isolation
- **Debuggable**: Clear data flow with intermediate variables
- **Configurable**: Environment-based configuration
- **Extensible**: Easy to add new presets or endpoints

## Installation

```bash
pip install -r requirements.txt
```

Note: `picamera2` requires a Raspberry Pi with camera module.

## Configuration

Configure via environment variables:

```bash
export FLASK_PORT=8080
export FLASK_DEBUG=false
export CORS_ORIGINS=http://localhost:3000,http://192.168.1.100:3000
export FRAME_DELAY=0.1
```

## Running the Server

```bash
python server.py
```

## API Endpoints

### GET /video_feed
Stream MJPEG video feed from camera with timestamp overlay.

### POST /apply_preset
Apply camera preset configuration.

Request:
```json
{
  "preset": "low_light"
}
```

Response:
```json
{
  "status": "success",
  "message": "Applied low_light preset successfully"
}
```

### GET /health
Health check endpoint with configuration info.

Response:
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

### GET /presets
List available camera presets.

Response:
```json
{
  "presets": ["default", "low_light"],
  "current": null
}
```

## Testing

Run architecture tests (no hardware required):

```bash
python test_architecture.py
```

## Architecture Diagram

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

## Files

- `server.py` - Flask HTTP layer
- `services.py` - Service layer for I/O operations
- `calculations.py` - Pure functions for business logic
- `models.py` - Immutable data structures
- `config.py` - Configuration management
- `test_architecture.py` - Architecture verification tests
- `requirements.txt` - Python dependencies