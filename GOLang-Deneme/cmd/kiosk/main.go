// Kiosk Application - Main Entry Point
//
// A fullscreen kiosk application for room reservation display.
// Supports three display modes controlled by QR_MODE environment variable:
//   - STANDARD: QR card + 5-day rolling schedule
//   - OFFICE: Full-width Mon-Fri weekly grid
//   - BUILDING: Multi-room sliding display
//
// Optional MQTT services can be enabled via environment variables:
//   - ENABLE_LOCK_MQTT: Door lock control
//   - ENABLE_DEVICE_MANAGER: Device status reporting
//   - ENABLE_UPDATE_SERVICE: OTA updates
//   - ENABLE_FINGERPRINT: Fingerprint registration
package main

import (
	"log"
	"os"
	"os/signal"
	"syscall"

	"kiosk-go/internal/config"
	"kiosk-go/internal/gpio"
	"kiosk-go/internal/mqtt"
	"kiosk-go/internal/ui"
)

func main() {
	// Load configuration
	cfg := config.Load()

	// Create UI application first (needed for notification callback)
	app := ui.NewApp(cfg)

	// Initialize MQTT client if any MQTT services are enabled
	var mqttClient *mqtt.Client
	if cfg.EnableLockMQTT || cfg.EnableDeviceManager || cfg.EnableUpdateService {
		mqttClient = mqtt.NewClient(cfg)
		if err := mqttClient.Connect(); err != nil {
			log.Printf("MQTT connection failed: %v", err)
		} else {
			defer mqttClient.Disconnect()
		}
	}

	// Initialize GPIO for lock control
	var lockController *gpio.LockController
	if cfg.EnableLockMQTT {
		lockController = gpio.NewLockController(12)
	}

	// Start optional MQTT services
	if cfg.EnableLockMQTT && mqttClient != nil && lockController != nil {
		lockHandler := mqtt.NewLockHandler(mqttClient, cfg, lockController)
		// Connect notification callback to UI
		lockHandler.SetNotifyCallback(app.Notify)
		// Connect footer lock status callback to UI
		lockHandler.SetLockStatusCallback(app.SetLockStatus)
		lockHandler.Start()
	}

	if cfg.EnableDeviceManager && mqttClient != nil {
		deviceManager := mqtt.NewDeviceManager(mqttClient, cfg)
		deviceManager.Start()
	}

	if cfg.EnableUpdateService && mqttClient != nil {
		updateHandler := mqtt.NewUpdateHandler(mqttClient, cfg)
		updateHandler.Start()
	}

	// Setup signal handling for graceful shutdown
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
	go func() {
		<-sigChan
		os.Exit(0)
	}()

	// Run the UI application
	app.Run()
}
