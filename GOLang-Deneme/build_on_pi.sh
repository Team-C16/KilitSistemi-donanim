#!/bin/bash
# Build script for Kiosk application on Raspberry Pi
# Run this script on your Raspberry Pi Zero 2 W

set -e

echo "=== Kiosk Build Script for Raspberry Pi ==="

# Check if running on ARM64
ARCH=$(uname -m)
if [[ "$ARCH" != "aarch64" && "$ARCH" != "arm64" ]]; then
    echo "Warning: This script is intended for ARM64 architecture (current: $ARCH)"
fi

# Install Go if not present
if ! command -v go &> /dev/null; then
    echo "Installing Go 1.23.4..."
    wget -q https://go.dev/dl/go1.23.4.linux-arm64.tar.gz -O /tmp/go.tar.gz
    sudo rm -rf /usr/local/go
    sudo tar -C /usr/local -xzf /tmp/go.tar.gz
    rm /tmp/go.tar.gz
    echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
    export PATH=$PATH:/usr/local/go/bin
    echo "Go installed successfully!"
else
    echo "Go is already installed: $(go version)"
fi

# Install build dependencies
echo "Installing build dependencies..."
sudo apt-get update
sudo apt-get install -y \
    build-essential \
    libgl1-mesa-dev \
    xorg-dev \
    libxcursor-dev \
    libxrandr-dev \
    libxinerama-dev \
    libxi-dev \
    libxxf86vm-dev

# Build the application
echo "Building kiosk application..."
cd "$(dirname "$0")"
go mod download
go build -o bin/kiosk ./cmd/kiosk

echo ""
echo "=== Build Complete! ==="
echo "Binary location: $(pwd)/bin/kiosk"
echo ""
echo "To run: ./bin/kiosk"
echo "To install as service: sudo cp kiosk.service /etc/systemd/system/ && sudo systemctl enable kiosk"
