#!/bin/bash

set -e

FLASK_DIR="./server"
NEXT_DIR="./ui"
NEXT_ENV_FILE="$NEXT_DIR/.env"
LOG_DIR="./logs"
FLASK_LOG="$LOG_DIR/flask.log"
NEXT_LOG="$LOG_DIR/nextjs.log"
NEXT_PORT=3000
VENV_DIR="$FLASK_DIR/venv"

mkdir -p $LOG_DIR
touch $FLASK_LOG
touch $NEXT_LOG

setup_venv() {
    echo "Creating virtual environment..."
    python3 -m venv $VENV_DIR
    echo "Activating virtual environment..."
    source $VENV_DIR/bin/activate
}

install_dependencies() {
    echo "Installing Flask-CORS..."
    pip install flask-cors
    echo "Dependencies installed successfully."
}

get_ip_address() {
    if command -v ip > /dev/null; then
        IP=$(ip -4 addr show scope global | grep inet | awk '{print $2}' | cut -d / -f 1 | head -n 1)
    elif command -v ifconfig > /dev/null; then
        IP=$(ifconfig | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1' | head -n 1)
    else
        IP="<Your IP Address>"
    fi
    echo $IP
}

start_flask() {
    echo "Starting Flask server..."
    cd $FLASK_DIR
#    setup_venv
#    install_dependencies
    python3 server.py > $FLASK_LOG 2>&1 &
    FLASK_PID=$!
    cd ..
    echo "Flask server started with PID: $FLASK_PID"
#    deactivate
}

start_nextjs() {
    echo "Building Next.js application..."
    cd $NEXT_DIR
    npm run build
    echo "Starting Next.js server..."
    npm run start -- -H 0.0.0.0 > $NEXT_LOG 2>&1 &
    NEXT_PID=$!
    cd ..
    echo "Next.js server started with PID: $NEXT_PID"
}

show_logs() {
    tail -f $FLASK_LOG $NEXT_LOG
}

#if [ -f "$FLASK_ENV_FILE" ]; then
#    export $(cat "$FLASK_ENV_FILE" | xargs)
#fi
#
#if [ -f "$NEXT_ENV_FILE" ]; then
#    export $(cat "$NEXT_ENV_FILE" | xargs)
#fi

cleanup() {
    echo "Stopping servers..."
    kill $FLASK_PID 2>/dev/null || echo "Flask server already stopped"
    kill $NEXT_PID 2>/dev/null || echo "Next.js server already stopped"
    exit 0
}

trap cleanup EXIT

echo "Starting servers..."
start_flask
start_nextjs

IP=$(get_ip_address)
echo "----------------------------------------"
echo "Access your Next.js app:"
echo "  - From this machine: http://localhost:$NEXT_PORT"
echo "  - From other devices on the network: http://$IP:$NEXT_PORT"
echo "----------------------------------------"

# Display logs
echo "Servers are running. Displaying logs... Press Ctrl+C to stop."
show_logs

wait $FLASK_PID $NEXT_PID
