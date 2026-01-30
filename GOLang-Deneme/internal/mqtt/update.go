// Package mqtt - OTA Update handler
//
// Binary download based update system for Go deployment.
// Downloads binary from API when version update request is received via MQTT.
//

package mqtt

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"os/exec"
	"regexp"
	"strings"
	"time"

	"github.com/golang-jwt/jwt/v5"

	"kiosk-go/internal/config"
)

// UpdateHandler handles OTA update commands via MQTT
type UpdateHandler struct {
	mqttClient *Client
	cfg        *config.Config
	log        *LogBuffer
	httpClient *http.Client
}

// NewUpdateHandler creates a new update handler
func NewUpdateHandler(mqttClient *Client, cfg *config.Config) *UpdateHandler {
	return &UpdateHandler{
		mqttClient: mqttClient,
		cfg:        cfg,
		log:        NewLogBuffer("Update", 50),
		httpClient: &http.Client{
			Timeout: 5 * time.Minute, // Long timeout for binary download
		},
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
		Version string `json:"version"`
	}

	if err := json.Unmarshal(payload, &request); err != nil {
		uh.log.Error("Invalid payload: %v", err)
		return
	}

	if request.Version == "" {
		uh.log.Warn("No version provided")
		return
	}

	// Validate version format (vX.X.X or X.X.X)
	version := uh.normalizeVersion(request.Version)
	if !uh.isValidVersion(version) {
		uh.log.Error("Invalid version format: %s (expected X.X.X)", request.Version)
		return
	}

	uh.log.Info("Starting update to version %s", version)
	uh.applyUpdate(version)
}

// normalizeVersion removes 'v' prefix if present
func (uh *UpdateHandler) normalizeVersion(version string) string {
	return strings.TrimPrefix(version, "v")
}

// isValidVersion validates version format (X.X.X)
func (uh *UpdateHandler) isValidVersion(version string) bool {
	versionRegex := regexp.MustCompile(`^\d+\.\d+\.\d+$`)
	return versionRegex.MatchString(version)
}

// generateToken creates a JWT token for API authentication
func (uh *UpdateHandler) generateToken() (string, error) {
	claims := jwt.MapClaims{
		"exp": time.Now().Add(5 * time.Minute).Unix(), // Longer expiry for download
	}
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	return token.SignedString([]byte(uh.cfg.JWTSecret))
}

// applyUpdate downloads the binary and applies the update
func (uh *UpdateHandler) applyUpdate(version string) {
	// Step 1: Download binary
	uh.log.Info("Downloading binary for version %s...", version)
	binaryData, err := uh.downloadBinary(version)
	if err != nil {
		uh.log.Error("Binary download failed: %v", err)
		return
	}
	uh.log.Info("Downloaded %d bytes", len(binaryData))

	// Step 2: Get current executable path
	execPath, err := os.Executable()
	if err != nil {
		uh.log.Error("Failed to get executable path: %v", err)
		return
	}
	uh.log.Info("Current executable: %s", execPath)

	// Step 3: Backup current binary
	backupPath := execPath + ".backup"
	if err := uh.backupBinary(execPath, backupPath); err != nil {
		uh.log.Error("Backup failed: %v", err)
		return
	}
	uh.log.Info("Backup created: %s", backupPath)

	// Step 4: Write new binary
	tempPath := execPath + ".new"
	if err := uh.writeBinary(tempPath, binaryData); err != nil {
		uh.log.Error("Failed to write new binary: %v", err)
		return
	}

	// Step 5: Replace old binary with new one
	if err := uh.replaceBinary(execPath, tempPath); err != nil {
		uh.log.Error("Failed to replace binary: %v", err)
		// Try to restore backup
		if restoreErr := os.Rename(backupPath, execPath); restoreErr != nil {
			uh.log.Error("Failed to restore backup: %v", restoreErr)
		}
		return
	}
	uh.log.Info("Binary updated successfully to version %s", version)

	// Step 6: Restart service
	uh.restartServices()
}

// downloadBinary fetches the binary from the API
func (uh *UpdateHandler) downloadBinary(version string) ([]byte, error) {
	token, err := uh.generateToken()
	if err != nil {
		return nil, fmt.Errorf("token generation failed: %w", err)
	}

	// Prepare request body
	requestBody := map[string]interface{}{
		"token":   token,
		"version": version,
	}

	// Use building_id in BUILDING mode, room_id otherwise
	if uh.cfg.Mode == config.ModeBuilding && uh.cfg.BuildingID != "" {
		requestBody["building_id"] = uh.cfg.BuildingID
	} else {
		requestBody["room_id"] = uh.cfg.RoomID
	}

	body, err := json.Marshal(requestBody)
	if err != nil {
		return nil, fmt.Errorf("json marshal failed: %w", err)
	}

	// Make POST request
	url := uh.cfg.APIBaseURL + "/getRaspBinary"
	req, err := http.NewRequest("POST", url, strings.NewReader(string(body)))
	if err != nil {
		return nil, fmt.Errorf("request creation failed: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := uh.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		respBody, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API error: status %d, body: %s", resp.StatusCode, string(respBody))
	}

	// Read binary data
	binaryData, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response body: %w", err)
	}

	if len(binaryData) == 0 {
		return nil, fmt.Errorf("empty binary received")
	}

	return binaryData, nil
}

// backupBinary creates a backup of the current binary using sudo
func (uh *UpdateHandler) backupBinary(srcPath, dstPath string) error {
	// Remove old backup if exists
	exec.Command("sudo", "rm", "-f", dstPath).Run()

	// Copy current binary to backup using sudo
	cmd := exec.Command("sudo", "cp", srcPath, dstPath)
	if out, err := cmd.CombinedOutput(); err != nil {
		return fmt.Errorf("failed to create backup: %v - %s", err, string(out))
	}

	return nil
}

// writeBinary writes the new binary to a temp file using sudo
func (uh *UpdateHandler) writeBinary(path string, data []byte) error {
	// Write to temp location first (in /tmp which is writable)
	tempFile := "/tmp/kiosk_update_binary"
	if err := os.WriteFile(tempFile, data, 0755); err != nil {
		return fmt.Errorf("failed to write temp binary: %w", err)
	}

	// Move to target location using sudo
	cmd := exec.Command("sudo", "mv", tempFile, path)
	if out, err := cmd.CombinedOutput(); err != nil {
		os.Remove(tempFile) // Clean up
		return fmt.Errorf("failed to move binary: %v - %s", err, string(out))
	}

	// Set executable permission
	cmd = exec.Command("sudo", "chmod", "755", path)
	if out, err := cmd.CombinedOutput(); err != nil {
		return fmt.Errorf("failed to set permissions: %v - %s", err, string(out))
	}

	return nil
}

// replaceBinary replaces the old binary with the new one using sudo
func (uh *UpdateHandler) replaceBinary(oldPath, newPath string) error {
	// On Linux, we can replace a running binary
	// The new binary takes effect after restart
	cmd := exec.Command("sudo", "mv", newPath, oldPath)
	if out, err := cmd.CombinedOutput(); err != nil {
		return fmt.Errorf("failed to rename binary: %v - %s", err, string(out))
	}
	return nil
}

// restartServices restarts all managed services
// In fail-safe mode, uses pinctrl to hold GPIO state during restart
func (uh *UpdateHandler) restartServices() {
	// For fail-safe mode, hold the GPIO state using pinctrl before restart
	// This prevents the lock from briefly unlocking during service restart
	if uh.cfg.LockType == config.LockTypeFailSafe && uh.cfg.EnableLockMQTT {
		uh.holdGPIOState()
	}

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

// holdGPIOState uses pinctrl to set the GPIO pin to locked state
// This persists even after gpiod releases the pin during service restart
// Locked state depends on lock type:
// - Fail-secure (0): locked = LOW  -> pinctrl set <pin> op dl
// - Fail-safe (1):   locked = HIGH -> pinctrl set <pin> op dh
func (uh *UpdateHandler) holdGPIOState() {
	pin := uh.cfg.LockGPIOPin

	// Determine the locked state based on lock type
	var state string
	if uh.cfg.LockType == config.LockTypeFailSafe {
		state = "dh" // HIGH = locked in fail-safe mode
	} else {
		state = "dl" // LOW = locked in fail-secure mode
	}

	uh.log.Info("Holding GPIO %d in locked state (%s) using pinctrl", pin, state)

	// pinctrl set <pin> op <dl|dh>
	// op = output, dl = drive low, dh = drive high
	cmd := exec.Command("pinctrl", "set", fmt.Sprintf("%d", pin), "op", state)
	if out, err := cmd.CombinedOutput(); err != nil {
		uh.log.Error("Failed to hold GPIO state: %v - %s", err, string(out))
	} else {
		uh.log.Info("GPIO %d set to %s via pinctrl", pin, state)
	}
}
