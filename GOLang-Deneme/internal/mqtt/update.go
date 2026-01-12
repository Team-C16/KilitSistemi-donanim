// Package mqtt - OTA Update handler
//
//
// Update must be change for the Go deployment
// the current update is for the Python deployment and a place holder
//
//

package mqtt

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"

	"kiosk-go/internal/config"
)

// UpdateHandler handles OTA update commands via MQTT
type UpdateHandler struct {
	mqttClient *Client
	cfg        *config.Config
	log        *LogBuffer
}

// NewUpdateHandler creates a new update handler
func NewUpdateHandler(mqttClient *Client, cfg *config.Config) *UpdateHandler {
	return &UpdateHandler{
		mqttClient: mqttClient,
		cfg:        cfg,
		log:        NewLogBuffer("Update", 50),
	}
}

// Start begins listening for update commands
func (uh *UpdateHandler) Start() {
	topic := fmt.Sprintf("v1/%s/update", uh.cfg.GetMQTTID())
	uh.mqttClient.Subscribe(topic, uh.handleUpdate)

	uh.log.Info("Started, subscribed to %s", topic)

	// Register with handler registry
	GetRegistry().Register("update", uh.log, uh.restart)
}

// restart performs a soft restart of the update handler
func (uh *UpdateHandler) restart() error {
	uh.log.Info("Soft restart initiated")
	uh.log.Clear()
	uh.log.Info("Handler restarted")
	return nil
}

// handleUpdate processes update requests
func (uh *UpdateHandler) handleUpdate(topic string, payload []byte) {
	var request struct {
		CommitID string `json:"commitID"`
	}

	if err := json.Unmarshal(payload, &request); err != nil {
		uh.log.Error("Invalid payload: %v", err)
		return
	}

	if request.CommitID == "" {
		uh.log.Warn("No commitID provided")
		return
	}

	uh.log.Info("Starting update to %s", request.CommitID)
	uh.applyUpdate(request.CommitID)
}

// applyUpdate performs the git update and service restart
func (uh *UpdateHandler) applyUpdate(commitID string) {
	destDir := uh.cfg.DestinationDir
	branch := uh.cfg.BranchName

	// Step 1: Git fetch
	uh.log.Info("Fetching from origin %s...", branch)
	cmd := exec.Command("sudo", "git", "fetch", "origin", branch)
	cmd.Dir = destDir
	if out, err := cmd.CombinedOutput(); err != nil {
		uh.log.Error("Git fetch failed: %v - %s", err, string(out))
		return
	}

	// Step 2: Git reset
	uh.log.Info("Resetting to %s...", commitID)
	cmd = exec.Command("sudo", "git", "reset", "--hard", commitID)
	cmd.Dir = destDir
	if out, err := cmd.CombinedOutput(); err != nil {
		uh.log.Error("Git reset failed: %v - %s", err, string(out))
		return
	}
	uh.log.Info("Files updated successfully")

	// Step 3: Install requirements if exists
	reqFile := filepath.Join(destDir, "requirements.txt")
	if _, err := os.Stat(reqFile); err == nil {
		uh.log.Info("Installing Python requirements...")
		cmd = exec.Command("pip", "install", "-r", reqFile, "--break-system-packages")
		cmd.Dir = destDir
		if out, err := cmd.CombinedOutput(); err != nil {
			uh.log.Warn("Pip install warning: %v - %s", err, string(out))
			// Continue even if pip fails
		}
	}

	// Step 4: Restart services
	uh.restartServices()
}

// restartServices restarts all managed services
func (uh *UpdateHandler) restartServices() {
	services := []string{
		uh.cfg.ServiceQR,
		uh.cfg.ServiceLock,
	}

	for _, svc := range services {
		if svc == "" {
			continue
		}
		svc = strings.TrimSpace(svc)

		uh.log.Info("Restarting %s...", svc)
		cmd := exec.Command("sudo", "systemctl", "restart", svc)
		if out, err := cmd.CombinedOutput(); err != nil {
			uh.log.Error("Failed to restart %s: %v - %s", svc, err, string(out))
		} else {
			uh.log.Info("%s restarted successfully", svc)
		}
	}
}
