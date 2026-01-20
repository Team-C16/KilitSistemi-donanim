# Kiosk Go Application

A fullscreen kiosk application for room reservation display, ported from Python/Tkinter to Go/Fyne.

## Features

- **Three Display Modes:**
  - `STANDARD`: QR code card + 5-day rolling schedule grid
  - `OFFICE`: Full-width Monday-Friday weekly grid (no QR)
  - `BUILDING`: Multi-room sliding display with announcements

- **Optional MQTT Services:**
  - Door lock control
  - Device status reporting
  - OTA updates
  - Fingerprint registration

## Requirements

- Go 1.23+
- Fyne v2 dependencies (see [Fyne Getting Started](https://developer.fyne.io/started/))

## Quick Start

```bash
# Clone and enter directory
cd kiosk-go

# Copy and configure environment
cp .env.example .env
# Edit .env with your settings

# Run in development
make run

# Run specific mode
make run-office
make run-building
```

## Building

```bash
# Build for current platform
make build

# Build for Raspberry Pi (requires fyne-cross)
make build-pi-docker

# Deploy to Pi
make deploy
```

## Configuration

Set these environment variables in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `QR_MODE` | Display mode: STANDARD, OFFICE, BUILDING | STANDARD |
| `JWT_SECRET` | JWT signing secret | (required) |
| `ROOM_ID` | Room identifier | 1 |
| `API_BASE_URL` | Backend API URL | https://pve.izu.edu.tr/randevu/device |
| `ENABLE_LOCK_MQTT` | Enable door lock MQTT | false |
| `ENABLE_DEVICE_MANAGER` | Enable status reporting | false |
| `EDGE_OFFSET` | CSS-like edge padding (see below) | 0 |

### Edge Offset (EDGE_OFFSET)

CSS-like syntax for padding around the entire application. Useful for TVs with overscan:

```bash
# All sides same
EDGE_OFFSET=20

# Top/bottom, left/right
EDGE_OFFSET=10 20

# Top, right, bottom, left
EDGE_OFFSET=10 20 30 40
```

## Project Structure

```
kiosk-go/
├── cmd/kiosk/main.go      # Entry point
├── internal/
│   ├── api/               # HTTP API client
│   ├── config/            # Configuration
│   ├── gpio/              # GPIO lock control
│   ├── mqtt/              # MQTT handlers
│   ├── qr/                # QR generation
│   └── ui/                # Fyne UI
├── .env.example           # Environment template
├── Makefile              # Build targets
└── go.mod                # Go module
```

## Systemd Service

```bash
# Generate service file
make service-file

# Install on Pi
sudo cp kiosk.service /etc/systemd/system/
sudo systemctl enable kiosk
sudo systemctl start kiosk
```

## Current Benchmarks

```

  140MB~ Go Build
  
  Pythons:
  qrGenerator 61MB

  lock 38MB

  deviceManager 24MB

  updateListener 24MB

```
