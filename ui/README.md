# Pi Camera Web Interface

A simple, zero-dependency web interface for viewing Raspberry Pi camera streams.

## Features

- **Live MJPEG video streaming**
- **Camera preset controls** (default, low light)
- **Health monitoring**
- **Responsive design**
- **Keyboard shortcuts** (Space to toggle controls, Esc to close)

## Usage

Simply open `index.html` in a web browser. No build process or installation required.

### Configuration

By default, the interface expects the camera server at:
- `http://localhost:8080` when accessed from localhost
- `http://[current-hostname]:8080` when accessed from other machines

### Deployment

Copy the single `index.html` file to any web server or open it directly from the filesystem.

```bash
# Serve locally with Python
python3 -m http.server 3000

# Or with any other static server
npx serve .
```

## Architecture

This is a single-file application with:
- **312 lines total** (HTML + CSS + JavaScript)
- **Zero dependencies**
- **No build process**
- **No framework overhead**
- **Instant load time**

All styling is inline CSS, all functionality is vanilla JavaScript. The entire application is viewable with "View Source".

## API Endpoints Used

- `GET /video_feed` - MJPEG video stream
- `POST /apply_preset` - Apply camera preset
- `GET /health` - Server health check
- `GET /presets` - List available presets

## Keyboard Shortcuts

- **Space** - Toggle control panel
- **Escape** - Close control panel

## Browser Compatibility

Works in all modern browsers that support:
- ES6 JavaScript (async/await)
- CSS Flexbox
- MJPEG streams via img tag

## Comparison with Previous Next.js Version

| Metric | Next.js Version | Vanilla Version |
|--------|----------------|-----------------|
| Files | 15+ | 1 |
| Dependencies | 300+ | 0 |
| Build time | 30+ seconds | 0 seconds |
| Total size | ~100MB (with node_modules) | 9KB |
| Lines of code | 1000+ | 312 |
| Load time | 2-3 seconds | Instant |
| Complexity | High | Low |

## Philosophy

Following the principle: "Complexity is the enemy." This interface does exactly what's needed, nothing more. It's debuggable, maintainable, and understandable by anyone who knows basic web development.
