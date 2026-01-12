// Package mqtt - Lock handler for door control via MQTT
package mqtt

import (
	"encoding/json"
	"fmt"
	"time"

	"kiosk-go/internal/config"
	"kiosk-go/internal/gpio"
)

// LockHandler handles door lock commands via MQTT
type LockHandler struct {
	mqttClient     *Client
	cfg            *config.Config
	lockController *gpio.LockController
	onNotify       func(message string, color string, duration time.Duration)
	log            *LogBuffer
}

// NewLockHandler creates a new lock handler
func NewLockHandler(mqttClient *Client, cfg *config.Config, lockController *gpio.LockController) *LockHandler {
	return &LockHandler{
		mqttClient:     mqttClient,
		cfg:            cfg,
		lockController: lockController,
		log:            NewLogBuffer("Lock", 50),
	}
}

// SetNotifyCallback sets the notification callback for UI updates
func (lh *LockHandler) SetNotifyCallback(callback func(message string, color string, duration time.Duration)) {
	lh.onNotify = callback
}

// Start begins listening for door commands
func (lh *LockHandler) Start() {
	topic := fmt.Sprintf("v1/%s/opendoor", lh.cfg.GetMQTTID())
	lh.mqttClient.Subscribe(topic, lh.handleOpenDoor)

	// Publish initial IP
	lh.publishIP()

	lh.log.Info("Started, subscribed to %s", topic)

	// Register with handler registry
	GetRegistry().Register("lock", lh.log, lh.restart)
}

// restart performs a soft restart of the lock handler
func (lh *LockHandler) restart() error {
	lh.log.Info("Soft restart initiated")
	lh.log.Clear()
	lh.log.Info("Handler restarted")
	return nil
}

// handleOpenDoor processes door open requests
func (lh *LockHandler) handleOpenDoor(topic string, payload []byte) {
	lh.log.Info("Open door request received")

	var request struct {
		JWT   string `json:"jwt"`
		Token string `json:"token"` // Alternative field name
	}

	if err := json.Unmarshal(payload, &request); err != nil {
		lh.log.Error("Invalid payload: %v", err)
		return
	}

	tokenStr := request.JWT
	if tokenStr == "" {
		tokenStr = request.Token
	}

	if tokenStr == "" {
		lh.log.Warn("No token provided")
		return
	}

	// Verify JWT
	if _, err := VerifyJWT(tokenStr, lh.cfg.JWTSecret); err != nil {
		lh.log.Error("Invalid token: %v", err)
		return
	}

	lh.log.Info("Token valid, opening door for 5s")

	// Open the lock for 5 seconds
	lh.lockController.Open(5 * time.Second)

	// Show notification
	if lh.onNotify != nil {
		lh.onNotify("Kilit Açık!", "green", 5*time.Second)
	}

	lh.log.Info("Door opened successfully")
}

// publishIP publishes the device IP to MQTT
func (lh *LockHandler) publishIP() {
	topic := fmt.Sprintf("v1/%s/saveip", lh.cfg.GetMQTTID())
	payload := map[string]string{
		"ip": "dynamic_ip",
	}
	lh.mqttClient.Publish(topic, payload)
	lh.log.Info("Published IP to %s", topic)
}

// PublishOpenDoor sends an open door command (used by fingerprint handler)
func (lh *LockHandler) PublishOpenDoor() error {
	topic := fmt.Sprintf("v1/%s/opendoor", lh.cfg.GetMQTTID())

	// Generate token
	claims := map[string]interface{}{
		"exp": time.Now().Add(30 * time.Second).Unix(),
	}
	tokenBytes, _ := json.Marshal(claims)
	token := string(tokenBytes) // Simplified - actual impl would use JWT

	payload := map[string]string{
		"jwt": token,
	}

	return lh.mqttClient.Publish(topic, payload)
}
