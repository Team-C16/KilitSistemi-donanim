// Package mqtt - Device Manager handler
package mqtt

import (
	"encoding/json"
	"fmt"
	"log"
	"os"
	"os/exec"
	"strings"
	"time"

	"kiosk-go/internal/config"
)

// DeviceManager handles device status and service management via MQTT
type DeviceManager struct {
	mqttClient *Client
	cfg        *config.Config
	log        *LogBuffer
}

// DeviceInfo contains hardware information
type DeviceInfo struct {
	IP      string  `json:"ip"`
	Model   string  `json:"model"`
	CPUTemp float64 `json:"cpu_temp"`
	RAM     RAMInfo `json:"ram"`
}

// RAMInfo contains memory usage information
type RAMInfo struct {
	TotalMB float64 `json:"total_mb"`
	UsedMB  float64 `json:"used_mb"`
	Percent float64 `json:"percent"`
}

// ServiceInfo contains service status information
type ServiceInfo struct {
	Active  string `json:"active"`
	Enabled string `json:"enabled"`
	Details string `json:"details"`
	Logs    string `json:"logs,omitempty"`
}

// StatusResponse is the response payload for status requests
type StatusResponse struct {
	DeviceID       string                 `json:"device_id"` // room_id or "b"+building_id based on mode
	CurrentVersion string                 `json:"current_version"`
	Timestamp      float64                `json:"timestamp"`
	DeviceInfo     DeviceInfo             `json:"device_info"`
	Services       map[string]ServiceInfo `json:"services"`
}

// RestartResponse is the response payload for restart requests
type RestartResponse struct {
	DeviceID         string  `json:"device_id"` // room_id or "b"+building_id based on mode
	RequestedService string  `json:"requested_service"`
	Status           string  `json:"status"`
	Message          string  `json:"message"`
	Timestamp        float64 `json:"timestamp"`
}

// NewDeviceManager creates a new device manager
func NewDeviceManager(mqttClient *Client, cfg *config.Config) *DeviceManager {
	return &DeviceManager{
		mqttClient: mqttClient,
		cfg:        cfg,
		log:        NewLogBuffer("DeviceManager", 50),
	}
}

// Start begins listening for device management commands
func (dm *DeviceManager) Start() {
	topicID := dm.cfg.GetMQTTID()
	topicGetStatus := fmt.Sprintf("v1/%s/getStatus", topicID)
	topicRestart := fmt.Sprintf("v1/%s/restartService", topicID)

	dm.mqttClient.Subscribe(topicGetStatus, dm.handleGetStatus)
	dm.mqttClient.Subscribe(topicRestart, dm.handleRestartService)

	dm.log.Info("Started, subscribed to %s", topicGetStatus)

	// Register with handler registry
	GetRegistry().Register("devicemanager", dm.log, dm.restart)
}

// restart performs a soft restart of the device manager handler
func (dm *DeviceManager) restart() error {
	dm.log.Info("Soft restart initiated")
	dm.log.Clear()
	dm.log.Info("Handler restarted")
	return nil
}

// handleGetStatus processes status query requests
func (dm *DeviceManager) handleGetStatus(topic string, payload []byte) {
	response := StatusResponse{
		DeviceID:       dm.cfg.GetMQTTID(), // Uses "b"+BuildingID in building mode, RoomID otherwise
		CurrentVersion: dm.getVersion(),
		Timestamp:      float64(time.Now().Unix()),
		DeviceInfo:     dm.getDeviceInfo(),
		Services:       dm.getServicesStatus(),
	}

	responseTopic := fmt.Sprintf("v1/%s/getStatus/response", dm.cfg.GetMQTTID())
	if err := dm.mqttClient.Publish(responseTopic, response); err != nil {
		log.Printf("DeviceManager: Failed to publish status: %v", err)
	}
}

// handleRestartService processes service restart requests
func (dm *DeviceManager) handleRestartService(topic string, payload []byte) {
	var request struct {
		Service string `json:"service"`
	}
	if err := json.Unmarshal(payload, &request); err != nil {
		log.Printf("DeviceManager: Invalid restart request: %v", err)
		return
	}

	response := RestartResponse{
		DeviceID:         dm.cfg.GetMQTTID(), // Uses "b"+BuildingID in building mode, RoomID otherwise
		RequestedService: request.Service,
		Timestamp:        float64(time.Now().Unix()),
	}

	// Map service keys to handler names
	handlerMap := map[string]string{
		"lock_service":    "lock",
		"update_listener": "update",
		"device_manager":  "devicemanager",
	}

	// QR service requires full systemctl restart
	if request.Service == "qr_service" {
		if err := dm.restartService(dm.cfg.ServiceQR); err != nil {
			response.Status = "error"
			response.Message = err.Error()
		} else {
			response.Status = "success"
			response.Message = "QR service restart initiated (full systemctl restart)"
		}
	} else if handlerName, exists := handlerMap[request.Service]; exists {
		// Soft restart for internal handlers
		registry := GetRegistry()
		if err := registry.SoftRestart(handlerName); err != nil {
			response.Status = "error"
			response.Message = err.Error()
		} else {
			response.Status = "success"
			response.Message = fmt.Sprintf("Handler %s restarted (soft restart)", handlerName)
		}
	} else if request.Service == "fingerprint_service" {
		// Fingerprint still uses systemctl (external Python script)
		if err := dm.restartService(dm.cfg.ServiceFinger); err != nil {
			response.Status = "error"
			response.Message = err.Error()
		} else {
			response.Status = "success"
			response.Message = "Fingerprint service restarted"
		}
	} else {
		response.Status = "error"
		response.Message = fmt.Sprintf("Service key '%s' not found", request.Service)
	}

	responseTopic := fmt.Sprintf("v1/%s/restartService/response", dm.cfg.GetMQTTID())
	dm.mqttClient.Publish(responseTopic, response)
}

// getDeviceInfo collects hardware information
func (dm *DeviceManager) getDeviceInfo() DeviceInfo {
	return DeviceInfo{
		IP:      dm.getIP(),
		Model:   dm.getModel(),
		CPUTemp: dm.getCPUTemp(),
		RAM:     dm.getRAMUsage(),
	}
}

// getIP retrieves the device IP address
func (dm *DeviceManager) getIP() string {
	out, err := exec.Command("hostname", "-I").Output()
	if err != nil {
		return "unknown"
	}
	return strings.TrimSpace(string(out))
}

// getModel retrieves the device model
func (dm *DeviceManager) getModel() string {
	data, err := os.ReadFile("/sys/firmware/devicetree/base/model")
	if err != nil {
		return "Unknown Device"
	}
	return strings.TrimRight(string(data), "\x00\n")
}

// getCPUTemp retrieves the CPU temperature
func (dm *DeviceManager) getCPUTemp() float64 {
	data, err := os.ReadFile("/sys/class/thermal/thermal_zone0/temp")
	if err != nil {
		return 0
	}
	var temp int
	fmt.Sscanf(string(data), "%d", &temp)
	return float64(temp) / 1000.0
}

// getRAMUsage retrieves memory usage information
func (dm *DeviceManager) getRAMUsage() RAMInfo {
	data, err := os.ReadFile("/proc/meminfo")
	if err != nil {
		return RAMInfo{}
	}

	var total, available int64
	lines := strings.Split(string(data), "\n")
	for _, line := range lines {
		if strings.HasPrefix(line, "MemTotal:") {
			fmt.Sscanf(line, "MemTotal: %d kB", &total)
		} else if strings.HasPrefix(line, "MemAvailable:") {
			fmt.Sscanf(line, "MemAvailable: %d kB", &available)
		}
	}

	if total == 0 {
		return RAMInfo{}
	}

	used := total - available
	return RAMInfo{
		TotalMB: float64(total) / 1024.0,
		UsedMB:  float64(used) / 1024.0,
		Percent: float64(used) / float64(total) * 100.0,
	}
}

// getVersion returns the current application version from config
func (dm *DeviceManager) getVersion() string {
	return config.Version
}

// getServicesStatus retrieves status of all managed services
func (dm *DeviceManager) getServicesStatus() map[string]ServiceInfo {
	result := make(map[string]ServiceInfo)
	registry := GetRegistry()

	// Map handler names to service keys
	handlerToServiceKey := map[string]string{
		"lock":          "lock_service",
		"update":        "update_listener",
		"devicemanager": "device_manager",
	}

	// Get status for internal handlers from registry
	for handlerName, serviceKey := range handlerToServiceKey {
		handler := registry.GetHandler(handlerName)
		info := ServiceInfo{
			Active:  "inactive",
			Enabled: "disabled",
		}
		if handler != nil {
			if handler.Enabled {
				info.Active = "active"
				info.Enabled = "enabled"
			}
			if handler.LogBuffer != nil {
				info.Details = handler.LogBuffer.GetLogsAsString(20)
			}
		}
		result[serviceKey] = info
	}

	// QR service - check systemctl
	result["qr_service"] = dm.getServiceInfo(dm.cfg.ServiceQR)

	// Fingerprint service - external, check systemctl
	result["fingerprint_service"] = dm.getServiceInfo(dm.cfg.ServiceFinger)

	return result
}

// getServiceInfo retrieves status for a single service
func (dm *DeviceManager) getServiceInfo(serviceName string) ServiceInfo {
	info := ServiceInfo{Active: "unknown", Enabled: "unknown"}

	if serviceName == "" {
		info.Active = "not_configured"
		info.Enabled = "not_configured"
		info.Details = "Service name not configured in environment"
		return info
	}

	// Check if running on Windows
	if os.PathSeparator == '\\' {
		info.Active = "windows_mock"
		info.Enabled = "windows_mock"
		info.Details = fmt.Sprintf("Service '%s' check mocked on Windows", serviceName)
		return info
	}

	// Get active status
	out, err := exec.Command("systemctl", "is-active", serviceName).Output()
	if err != nil {
		info.Active = "error"
		info.Details = fmt.Sprintf("Error checking status: %v", err)
	} else {
		info.Active = strings.TrimSpace(string(out))
	}

	// Get enabled status
	out, _ = exec.Command("systemctl", "is-enabled", serviceName).Output()
	info.Enabled = strings.TrimSpace(string(out))

	// Get detailed status
	out, _ = exec.Command("systemctl", "status", serviceName, "-n", "10", "--no-pager").Output()
	if info.Details == "" { // Only set if not already set by error
		info.Details = string(out)
	}

	return info
}

// restartService restarts a systemd service
func (dm *DeviceManager) restartService(serviceName string) error {
	cmd := exec.Command("sudo", "systemctl", "restart", serviceName)
	return cmd.Run()
}
