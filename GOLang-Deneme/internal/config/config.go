// Package config handles loading and accessing application configuration
// from environment variables and .env files.
package config

import (
	"log"
	"os"
	"strconv"
	"strings"

	"github.com/joho/godotenv"
)

// Mode represents the application display mode
type Mode string

const (
	ModeStandard Mode = "STANDARD" // QR card + 5-day rolling schedule
	ModeOffice   Mode = "OFFICE"   // Full-width Mon-Fri weekly grid
	ModeBuilding Mode = "BUILDING" // Multi-room sliding display
)

// Config holds all application configuration
type Config struct {
	// Core settings
	Mode       Mode
	JWTSecret  string
	RoomID     string
	APIBaseURL string
	BuildingID string

	// MQTT settings
	MQTTBrokerIP           string
	MQTTBrokerPort         int
	MQTTUseTLS             bool
	MQTTInsecureSkipVerify bool

	// Optional services
	EnableLockMQTT      bool
	EnableFingerprint   bool
	EnableDeviceManager bool
	EnableUpdateService bool

	// Service configuration (for device manager and updates)
	DestinationDir       string
	BranchName           string
	ServiceQR            string
	ServiceLock          string
	ServiceFinger        string
	ServiceUpdate        string
	ServiceDeviceManager string
}

// Global configuration instance
var cfg *Config

// Load initializes the configuration from environment variables
func Load() *Config {
	// Try to load .env file (ignore error if not present)
	godotenv.Load()

	cfg = &Config{
		// Core settings
		Mode:       parseMode(getEnv("QR_MODE", "STANDARD")),
		JWTSecret:  getEnv("JWT_SECRET", ""),
		RoomID:     getEnv("ROOM_ID", "1"),
		APIBaseURL: getEnv("API_BASE_URL", getEnv("nodeip", "https://pve.izu.edu.tr/randevu/device")),
		BuildingID: getEnv("BUILDING_ID", "1"),

		// MQTT settings
		MQTTBrokerIP:           getEnv("MQTT_BROKER_IP", getEnv("mqttbrokerip", "pve.izu.edu.tr")),
		MQTTBrokerPort:         getEnvInt("MQTT_BROKER_PORT", getEnvInt("mqttbrokerport", 8883)),
		MQTTUseTLS:             getEnvBool("MQTT_USE_TLS", true),
		MQTTInsecureSkipVerify: getEnvBool("MQTT_INSECURE_SKIP_VERIFY", false),

		// Optional services
		EnableLockMQTT:      getEnvBool("ENABLE_LOCK_MQTT", false),
		EnableFingerprint:   getEnvBool("ENABLE_FINGERPRINT", false),
		EnableDeviceManager: getEnvBool("ENABLE_DEVICE_MANAGER", false),
		EnableUpdateService: getEnvBool("ENABLE_UPDATE_SERVICE", false),

		// Service configuration
		DestinationDir:       getEnv("DESTINATION_DIR", "/home/pi/kiosk"),
		BranchName:           getEnv("BRANCH_NAME", "main"),
		ServiceQR:            getEnv("SERVICE_QR", "kiosk-qr.service"),
		ServiceLock:          getEnv("SERVICE_LOCK", "kiosk-lock.service"),
		ServiceFinger:        getEnv("SERVICE_FINGER", "kiosk-finger.service"),
		ServiceUpdate:        getEnv("SERVICE_UPDATE", "kiosk-update.service"),
		ServiceDeviceManager: getEnv("SERVICE_DEVICEMANAGER", "kiosk-dm.service"),
	}

	// Validate required settings
	if cfg.JWTSecret == "" {
		log.Println("WARNING: JWT_SECRET is not set!")
	}

	return cfg
}

// Get returns the current configuration instance
func Get() *Config {
	if cfg == nil {
		return Load()
	}
	return cfg
}

// parseMode converts a string to a Mode enum
func parseMode(s string) Mode {
	switch strings.ToUpper(s) {
	case "OFFICE":
		return ModeOffice
	case "BUILDING":
		return ModeBuilding
	default:
		return ModeStandard
	}
}

// getEnv retrieves an environment variable with a fallback default
func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

// getEnvInt retrieves an integer environment variable
func getEnvInt(key string, defaultValue int) int {
	if value := os.Getenv(key); value != "" {
		if i, err := strconv.Atoi(value); err == nil {
			return i
		}
	}
	return defaultValue
}

// getEnvBool retrieves a boolean environment variable
func getEnvBool(key string, defaultValue bool) bool {
	if value := os.Getenv(key); value != "" {
		return strings.ToLower(value) == "true" || value == "1"
	}
	return defaultValue
}

// GetMQTTID returns the ID to use for MQTT topics
// In Building mode, it returns "b" + BuildingID
// In other modes, it returns RoomID
func (c *Config) GetMQTTID() string {
	if c.Mode == ModeBuilding {
		return "b" + c.BuildingID
	}
	return c.RoomID
}
