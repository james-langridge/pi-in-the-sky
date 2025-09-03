#!/bin/bash
set -e

# Pi-in-the-Sky Camera Streaming Server Setup Script
# This script automates the installation and configuration of the camera streaming server

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${YELLOW}→${NC} $1"
}

print_header() {
    echo ""
    echo "========================================="
    echo "$1"
    echo "========================================="
    echo ""
}

# Check if running on Raspberry Pi
check_raspberry_pi() {
    if [ -f /proc/device-tree/model ]; then
        MODEL=$(cat /proc/device-tree/model)
        if [[ $MODEL == *"Raspberry Pi"* ]]; then
            print_success "Detected Raspberry Pi: $MODEL"
            return 0
        fi
    fi
    print_info "Not running on Raspberry Pi - will use mock camera mode"
    return 1
}

# Default values
INSTALL_DIR="$HOME/pi-in-the-sky"
SERVICE_NAME="pi-camera-stream"
REPO_URL="git@github.com:james-langridge/pi-in-the-sky.git"
PORT=8080

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dir)
            INSTALL_DIR="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --service-name)
            SERVICE_NAME="$2"
            shift 2
            ;;
        --help)
            echo "Pi-in-the-Sky Setup Script"
            echo ""
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --dir PATH           Installation directory (default: ~/pi-in-the-sky)"
            echo "  --port PORT          Server port (default: 8080)"
            echo "  --service-name NAME  Systemd service name (default: pi-camera-stream)"
            echo "  --help              Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

print_header "Pi-in-the-Sky Camera Streaming Server Setup"

# Check if we're on a Raspberry Pi
IS_PI=false
if check_raspberry_pi; then
    IS_PI=true
fi

# Step 1: Update system packages
print_header "Step 1: Updating System Packages"
print_info "Updating package lists..."
sudo apt-get update -qq

print_info "Installing required system packages..."
sudo apt-get install -y -qq git python3 python3-venv python3-pip

if [ "$IS_PI" = true ]; then
    print_info "Installing Raspberry Pi camera dependencies..."
    sudo apt-get install -y -qq python3-libcamera python3-kms++ libcap-dev
fi

print_success "System packages updated"

# Step 2: Clone or update repository
print_header "Step 2: Setting Up Repository"

if [ -d "$INSTALL_DIR" ]; then
    print_info "Directory exists, updating repository..."
    cd "$INSTALL_DIR"
    git pull origin main
    print_success "Repository updated"
else
    print_info "Cloning repository..."
    git clone "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
    print_success "Repository cloned"
fi

# Step 3: Set up Python virtual environment
print_header "Step 3: Setting Up Python Environment"

cd "$INSTALL_DIR/server"

if [ -d "venv" ]; then
    print_info "Virtual environment exists, updating..."
else
    print_info "Creating virtual environment..."
    if [ "$IS_PI" = true ]; then
        # On Pi, need system packages for picamera2
        python3 -m venv venv --system-site-packages
    else
        # On development machines, regular venv
        python3 -m venv venv
    fi
fi

print_info "Activating virtual environment..."
source venv/bin/activate

print_info "Upgrading pip..."
pip install --upgrade pip -q

print_info "Installing Python dependencies..."
if [ "$IS_PI" = true ]; then
    pip install -r requirements.txt -q
else
    # Install without picamera2 for non-Pi systems
    grep -v picamera2 requirements.txt | pip install -r /dev/stdin -q
fi

print_success "Python environment configured"

# Step 4: Build React Frontend
print_header "Step 4: Building React Frontend"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    print_info "Node.js not found. Installing Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
    sudo apt-get install -y nodejs
    print_success "Node.js installed"
else
    print_success "Node.js found: $(node --version)"
fi

# Build the frontend
cd "$INSTALL_DIR/ui"
print_info "Installing frontend dependencies..."
npm ci -q  # Clean install from package-lock.json
print_success "Frontend dependencies installed"

print_info "Building React application..."
npm run build -q
print_success "Frontend build complete"

cd "$INSTALL_DIR/server"

# Step 5: Test the server
print_header "Step 5: Testing Server"

print_info "Running quick server test..."
timeout 5 python server.py --test 2>/dev/null || true

if [ $? -eq 124 ]; then
    print_success "Server started successfully (test mode)"
else
    print_info "Server test completed"
fi

# Step 6: Configure systemd service (optional for Pi)
if [ "$IS_PI" = true ]; then
    print_header "Step 6: Configuring Systemd Service"
    
    read -p "Would you like to install as a systemd service? (y/n) " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Creating systemd service file..."
        
        # Create service file
        sudo tee "/etc/systemd/system/${SERVICE_NAME}.service" > /dev/null <<EOF
[Unit]
Description=Pi Camera Streaming Server
After=network.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$INSTALL_DIR/server
Environment="FLASK_PORT=$PORT"
ExecStart=$INSTALL_DIR/server/venv/bin/python $INSTALL_DIR/server/server.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
        
        print_info "Reloading systemd daemon..."
        sudo systemctl daemon-reload
        
        print_info "Enabling service..."
        sudo systemctl enable "${SERVICE_NAME}.service"
        
        print_info "Starting service..."
        sudo systemctl start "${SERVICE_NAME}.service"
        
        sleep 2
        
        if sudo systemctl is-active --quiet "${SERVICE_NAME}.service"; then
            print_success "Service installed and running"
            print_info "Service name: ${SERVICE_NAME}"
            print_info "Check status: sudo systemctl status ${SERVICE_NAME}"
            print_info "View logs: sudo journalctl -u ${SERVICE_NAME} -f"
        else
            print_error "Service failed to start"
            print_info "Check logs: sudo journalctl -u ${SERVICE_NAME} -n 50"
        fi
    fi
fi

# Step 7: Display access information
print_header "Setup Complete!"

# Get IP address
IP_ADDR=$(hostname -I | awk '{print $1}')

echo "Access your camera stream at:"
echo ""
echo "  http://${IP_ADDR}:${PORT}"
echo "  http://$(hostname).local:${PORT}"
echo ""

if [ "$IS_PI" = true ] && sudo systemctl is-active --quiet "${SERVICE_NAME}.service" 2>/dev/null; then
    echo "Service Management:"
    echo "  Start:   sudo systemctl start ${SERVICE_NAME}"
    echo "  Stop:    sudo systemctl stop ${SERVICE_NAME}"
    echo "  Restart: sudo systemctl restart ${SERVICE_NAME}"
    echo "  Status:  sudo systemctl status ${SERVICE_NAME}"
    echo "  Logs:    sudo journalctl -u ${SERVICE_NAME} -f"
else
    echo "Manual Start:"
    echo "  cd $INSTALL_DIR/server"
    echo "  source venv/bin/activate"
    echo "  python server.py"
fi

echo ""
print_success "Installation complete!"