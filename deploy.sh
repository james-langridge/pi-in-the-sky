#!/bin/bash

# Pi in the Sky - Deployment Script
# Run this on the Raspberry Pi after pulling the latest code

set -e  # Exit on error

echo "🚀 Starting deployment..."

# Build the frontend
echo "📦 Building frontend with Vite..."
npm ci  # Clean install from package-lock.json
npm run build

echo "✅ Build complete!"

# Restart the service (adjust service name as needed)
echo "🔄 Restarting pi-camera service..."
sudo systemctl restart pi-camera-stream.service || echo "⚠️  Could not restart service - you may need to do this manually"

echo "✨ Deployment complete!"
echo "📝 Note: If the service didn't restart, run: sudo systemctl restart pi-camera"
