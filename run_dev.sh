#!/bin/bash

# RAII-style virtual environment manager for Python development
# Creates/activates venv, runs command, and cleans up on exit

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Virtual environment directory
VENV_DIR="venv"

# Function to print colored messages
print_msg() {
    echo -e "${GREEN}[run_dev]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Cleanup function (RAII-style destructor)
cleanup() {
    if [ -n "$VIRTUAL_ENV" ]; then
        print_msg "Deactivating virtual environment..."
        deactivate 2>/dev/null || true
    fi
    print_msg "Cleanup complete."
}

# Set up trap to ensure cleanup on exit
trap cleanup EXIT INT TERM

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    print_msg "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"

    if [ $? -ne 0 ]; then
        print_error "Failed to create virtual environment"
        exit 1
    fi
    print_msg "Virtual environment created successfully."
fi

# Activate virtual environment
print_msg "Activating virtual environment..."
# Use . instead of source for better compatibility
. "$VENV_DIR/bin/activate" 2>/dev/null || {
    print_error "Virtual environment activation script not found"
    exit 1
}

if [ -z "$VIRTUAL_ENV" ]; then
    print_error "Failed to activate virtual environment"
    exit 1
fi

print_msg "Virtual environment activated: $VIRTUAL_ENV"

# Install/upgrade pip
print_msg "Ensuring pip is up to date..."
pip install --upgrade pip --quiet

# Install requirements if requirements.txt exists
if [ -f "requirements.txt" ]; then
    print_msg "Installing requirements..."
    pip install -r requirements.txt --quiet
    if [ $? -eq 0 ]; then
        print_msg "Requirements installed successfully."
    else
        print_warning "Some requirements failed to install."
    fi
else
    print_warning "No requirements.txt found. Skipping dependency installation."
fi

# Special handling for tox command
if [ "$1" = "tox" ]; then
    # Install dev requirements if running tox
    if [ -f "requirements-dev.txt" ]; then
        print_msg "Installing development dependencies for tox..."
        pip install -r requirements-dev.txt --quiet
        if [ $? -eq 0 ]; then
            print_msg "Development dependencies installed successfully."
        else
            print_warning "Some development dependencies failed to install."
        fi
    fi
fi

# Execute command or launch the app
if [ $# -eq 0 ]; then
    # No arguments - launch the web application
    print_msg "Launching Multi-Robot D* Lite Web Application..."
    print_msg "Backend will run on http://localhost:8000"
    print_msg "Frontend will run on http://localhost:5173"
    echo ""

    # Start backend in background
    print_msg "Starting backend server..."
    python3 -m uvicorn multi_robot_d_star_lite.web.main:app --reload --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!

    # Give backend time to start
    sleep 2

    # Start frontend
    print_msg "Starting frontend server..."
    cd frontend
    npm install
    npm run dev

    # Kill backend when frontend exits
    kill $BACKEND_PID 2>/dev/null || true
else
    print_msg "Executing: $@"
    echo ""
    "$@"
    EXIT_CODE=$?

    if [ $EXIT_CODE -eq 0 ]; then
        print_msg "Command executed successfully."
    else
        print_error "Command failed with exit code: $EXIT_CODE"
    fi

    exit $EXIT_CODE
fi