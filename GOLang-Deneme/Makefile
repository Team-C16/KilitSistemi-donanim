# Kiosk Application Makefile
# Cross-compilation for Raspberry Pi Zero 2 W (ARM64)

.PHONY: all build build-pi run clean deps test fmt lint

# Default target
all: deps build

# Install dependencies
deps:
	go mod download
	go mod tidy

# Build for current platform
build:
	go build -o bin/kiosk ./cmd/kiosk

# Build for Raspberry Pi (ARM64 Linux)
# Note: Cross-compilation with CGO requires appropriate toolchain
# For fyne-cross method, use: make build-pi-docker
build-pi:
	GOOS=linux GOARCH=arm64 CGO_ENABLED=0 go build -o bin/kiosk-pi-nocgo ./cmd/kiosk

# Build for Raspberry Pi (ARMv6 Linux - e.g., Pi Zero)
# Cross-compile for armv6 (GOARM=6). Note: CGO disabled; enable and toolchain needed for CGO.
build-pi-armv6:
	GOOS=linux GOARCH=arm GOARM=6 CGO_ENABLED=0 go build -o bin/kiosk-pi-armv6 ./cmd/kiosk

# Build using fyne-cross (Docker-based, recommended for cross-compilation)
# Install fyne-cross: go install github.com/fyne-io/fyne-cross@latest
build-pi-v6:
	fyne-cross linux -arch arm -env GOARM=6 -app-id com.izu.kiosk -output kiosk-pi-armv6 ./cmd/kiosk

build-pi-arm64:
	fyne-cross linux -arch arm64 -app-id com.izu.kiosk -output kiosk-pi-arm64 ./cmd/kiosk

build-pi-all: build-pi-v6 build-pi-arm64

# Run locally
run:
	QR_MODE=STANDARD go run ./cmd/kiosk

# Run in OFFICE mode
run-office:
	QR_MODE=OFFICE go run ./cmd/kiosk

# Run in BUILDING mode
run-building:
	QR_MODE=BUILDING go run ./cmd/kiosk

# Run tests
test:
	go test -v ./...

# Run tests with coverage
test-coverage:
	go test -coverprofile=coverage.out ./...
	go tool cover -html=coverage.out -o coverage.html

# Format code
fmt:
	go fmt ./...

# Lint code (requires golangci-lint)
lint:
	golangci-lint run

# Clean build artifacts
clean:
	rm -rf bin/
	rm -f coverage.out coverage.html
	rm -rf fyne-cross/

# Copy to Raspberry Pi (adjust IP as needed)
deploy: build-pi
	scp bin/kiosk-pi pi@raspberrypi:/home/pi/kiosk/
	scp .env.example pi@raspberrypi:/home/pi/kiosk/.env

# Create systemd service file
service-file:
	@echo "[Unit]" > kiosk.service
	@echo "Description=Kiosk Display Application" >> kiosk.service
	@echo "After=network.target" >> kiosk.service
	@echo "" >> kiosk.service
	@echo "[Service]" >> kiosk.service
	@echo "Type=simple" >> kiosk.service
	@echo "User=pi" >> kiosk.service
	@echo "WorkingDirectory=/home/pi/kiosk" >> kiosk.service
	@echo "EnvironmentFile=/home/pi/kiosk/.env" >> kiosk.service
	@echo "ExecStart=/home/pi/kiosk/kiosk-pi" >> kiosk.service
	@echo "Restart=always" >> kiosk.service
	@echo "RestartSec=5" >> kiosk.service
	@echo "" >> kiosk.service
	@echo "[Install]" >> kiosk.service
	@echo "WantedBy=multi-user.target" >> kiosk.service
	@echo "Created kiosk.service"

# Help
help:
	@echo "Kiosk Application Makefile"
	@echo ""
	@echo "Targets:"
	@echo "  all            - Install deps and build"
	@echo "  build          - Build for current platform"
	@echo "  build-pi       - Build for Raspberry Pi (ARM64, no CGO)"
	@echo "  build-pi-armv6 - Build for Raspberry Pi (ARMv6, no CGO)"
	@echo "  build-pi-docker - Build for Pi using fyne-cross Docker"
	@echo "  run            - Run locally (STANDARD mode)"
	@echo "  run-office     - Run locally (OFFICE mode)"
	@echo "  run-building   - Run locally (BUILDING mode)"
	@echo "  test           - Run tests"
	@echo "  clean          - Remove build artifacts"
	@echo "  deploy         - Deploy to Raspberry Pi"
	@echo "  service-file   - Generate systemd service file"
