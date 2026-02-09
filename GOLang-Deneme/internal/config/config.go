// Package config handles loading and accessing application configuration
// from environment variables and .env files.
package config

import (
	"log"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/joho/godotenv"
)

// Version is the application version, set at build time via -ldflags
// Example: go build -ldflags "-X kiosk-go/internal/config.Version=v1.0.0"
var Version = "v0.0.0-dev"

// Mode represents the application display mode
type Mode string

const (
	ModeStandard Mode = "STANDARD" // QR card + 5-day rolling schedule
	ModeOffice   Mode = "OFFICE"   // Full-width Mon-Fri weekly grid
	ModeBuilding Mode = "BUILDING" // Multi-room sliding display
)

// EdgePadding holds padding values for all four edges (CSS-like)
type EdgePadding struct {
	Top    int
	Right  int
	Bottom int
	Left   int
}

// LockType represents the lock behavior type
type LockType int

const (
	// LockTypeFailSecure (0): Pin LOW = locked, Pin HIGH = unlocked. Lock stays locked on power loss.
	LockTypeFailSecure LockType = 0
	// LockTypeFailSafe (1): Pin HIGH = locked, Pin LOW = unlocked. Lock opens on power loss.
	LockTypeFailSafe LockType = 1
)

// Config holds all application configuration
type Config struct {
	// Core settings
	Mode       Mode
	JWTSecret  string
	RoomID     string
	APIBaseURL string
	APITimeout time.Duration // HTTP request timeout (default: 30s)
	BuildingID string

	// MQTT settings
	MQTTBrokerIP           string
	MQTTBrokerPort         int
	MQTTUseTLS             bool
	MQTTInsecureSkipVerify bool

	// Lock settings
	LockType    LockType // 0 = fail-secure (default), 1 = fail-safe
	LockGPIOPin int      // GPIO pin number for lock control (default: 12)

	// Optional services
	EnableLockMQTT      bool
	EnableFingerprint   bool
	EnableDeviceManager bool
	EnableUpdateService bool

	// Building Mode Settings
	BuildingMaxVisibleRooms int
	BuildingSlideStep       int

	// UI Settings
	// EdgePadding supports CSS-like syntax: "10" (all), "10 20" (top/bottom, left/right), "10 20 30 40" (top, right, bottom, left)
	EdgePadding EdgePadding

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
		APITimeout: time.Duration(getEnvInt("API_TIMEOUT", 30)) * time.Second,
		BuildingID: getEnv("BUILDING_ID", "1"),

		// MQTT settings
		MQTTBrokerIP:           getEnv("MQTT_BROKER_IP", getEnv("mqttbrokerip", "pve.izu.edu.tr")),
		MQTTBrokerPort:         getEnvInt("MQTT_BROKER_PORT", getEnvInt("mqttbrokerport", 8883)),
		MQTTUseTLS:             getEnvBool("MQTT_USE_TLS", true),
		MQTTInsecureSkipVerify: getEnvBool("MQTT_INSECURE_SKIP_VERIFY", false),

		// Lock settings
		LockType:    LockType(getEnvInt("LOCK_TYPE", 0)), // 0 = fail-secure, 1 = fail-safe
		LockGPIOPin: getEnvInt("LOCK_GPIO_PIN", 12),      // Default GPIO pin 12

		// Optional services
		EnableLockMQTT:      getEnvBool("ENABLE_LOCK_MQTT", false),
		EnableFingerprint:   getEnvBool("ENABLE_FINGERPRINT", false),
		EnableDeviceManager: getEnvBool("ENABLE_DEVICE_MANAGER", false),
		EnableUpdateService: getEnvBool("ENABLE_UPDATE_SERVICE", false),

		// Building Mode Settings
		BuildingMaxVisibleRooms: getEnvInt("BUILDING_MAX_VISIBLE_ROOMS", 4),
		BuildingSlideStep:       getEnvInt("BUILDING_SLIDE_STEP", 1),

		// UI Settings
		EdgePadding: parseEdgePadding(getEnv("EDGE_OFFSET", "0")),

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

// parseEdgePadding parses CSS-like padding syntax
// Supports: "10" (all), "10 20" (top/bottom, left/right), "10 20 30 40" (top, right, bottom, left)
func parseEdgePadding(s string) EdgePadding {
	parts := strings.Fields(s)
	if len(parts) == 0 {
		return EdgePadding{}
	}

	values := make([]int, len(parts))
	for i, p := range parts {
		v, err := strconv.Atoi(p)
		if err != nil {
			values[i] = 0
		} else {
			values[i] = v
		}
	}

	switch len(values) {
	case 1:
		// All sides same
		return EdgePadding{Top: values[0], Right: values[0], Bottom: values[0], Left: values[0]}
	case 2:
		// top/bottom, left/right
		return EdgePadding{Top: values[0], Right: values[1], Bottom: values[0], Left: values[1]}
	case 4:
		// top, right, bottom, left
		return EdgePadding{Top: values[0], Right: values[1], Bottom: values[2], Left: values[3]}
	default:
		// If 3 or more than 4, use first 4 or pad with zeros
		return EdgePadding{Top: values[0], Right: values[0], Bottom: values[0], Left: values[0]}
	}
}

// HasPadding returns true if any edge has non-zero padding
func (e EdgePadding) HasPadding() bool {
	return e.Top > 0 || e.Right > 0 || e.Bottom > 0 || e.Left > 0
}
