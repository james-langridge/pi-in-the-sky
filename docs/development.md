# Development Guide

How to develop and test Pi in the Sky without Raspberry Pi hardware.

## Mock Camera Mode

The server automatically falls back to mock mode when PiCamera2 is unavailable:

```bash
cd server
python3 -m venv venv
source venv/bin/activate
pip install flask flask-cors opencv-python numpy pywebpush cryptography
python server.py
```

The mock camera generates test frames with:
- Gradient backgrounds
- Moving circular element (for motion detection testing)
- Timestamp overlays
- Frame counter

## Frontend Development

```bash
cd ui
npm install
npm run dev      # Development server (proxies to backend on :8080)
npm run build    # Production build
npm run preview  # Preview production build
```

### Key Components

- `VideoStream.tsx` - MJPEG streaming with auto-reconnection
- `ControlPanel.tsx` - Tabbed interface for controls
- `CameraControls.tsx` - Dynamic control generation from API
- `MotionDetection.tsx` - Push notification management
- `AudioDetection.tsx` - Audio level monitoring

### Keyboard Shortcuts

- **Space** - Toggle control panel
- **Escape** - Close control panel

## Testing

```bash
cd server
python run_tests.py        # Core functionality tests
python test_architecture.py # Architecture verification
```

### Test Philosophy

Tests follow the "grug" philosophy:
- Test what matters, not every edge case
- Focus on pure functions (calculations)
- Verify immutability of data models
- Keep tests simple enough to debug at 3 AM

### CI/CD

GitHub Actions runs tests on all PRs:
- Python 3.9, 3.10, 3.11, 3.12
- No Raspberry Pi hardware required

## Project Structure

```
pi-in-the-sky/
├── server/
│   ├── server.py          # Flask entry point
│   ├── app_factory.py     # Application factory with DI
│   ├── services.py        # Camera and streaming services
│   ├── motion_services.py # Motion detection
│   ├── calculations.py    # Pure image processing functions
│   ├── models.py          # Immutable data models
│   ├── result.py          # Result monad for error handling
│   ├── config.py          # Configuration management
│   ├── routes/            # Flask blueprints
│   └── requirements.txt
└── ui/
    ├── src/
    │   ├── api/           # API client hooks
    │   ├── components/    # React components
    │   ├── types/         # TypeScript definitions
    │   └── App.tsx
    ├── public/sw.js       # Service worker
    └── package.json
```

## Architecture

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

### Design Principles

- **Immutability**: All data models are frozen dataclasses
- **Pure Functions**: Image processing via pure functions
- **Dependency Injection**: Services injected via factory
- **Result Monad**: Functional error handling

## Browser Compatibility

- Chrome/Edge 90+
- Safari 14+ (iOS 14+)
- Firefox 88+
- Full iOS PWA support
