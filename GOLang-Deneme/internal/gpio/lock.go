// Package gpio provides door lock control via GPIO pins
package gpio

import (
	"log"
	"runtime"
	"sync"
	"time"

	"kiosk-go/internal/config"
)

// LockController manages the door lock GPIO
type LockController struct {
	pin       int
	isOpen    bool
	mu        sync.Mutex
	available bool
	lockType  config.LockType
}

// NewLockController creates a new lock controller on the specified GPIO pin
func NewLockController(pin int) *LockController {
	cfg := config.Get()
	lc := &LockController{
		pin:       pin,
		available: false,
		lockType:  cfg.LockType,
	}

	// Only initialize GPIO on Linux (Raspberry Pi)
	if runtime.GOOS == "linux" {
		if err := lc.initGPIO(); err != nil {
			log.Printf("GPIO: Failed to initialize: %v (using mock mode)", err)
			lc.available = false
		}
	}

	log.Printf("GPIO: Lock controller initialized with LockType=%d (%s)", lc.lockType, lc.lockTypeString())
	return lc
}

// lockTypeString returns a human-readable string for the lock type
func (lc *LockController) lockTypeString() string {
	if lc.lockType == config.LockTypeFailSafe {
		return "fail-safe"
	}
	return "fail-secure"
}

// initGPIO initializes the GPIO hardware
func (lc *LockController) initGPIO() error {
	// On Linux, initialize actual GPIO hardware
	if runtime.GOOS == "linux" {
		if err := initRPIO(); err != nil {
			return err
		}
		// Setup pin with initial locked state based on lock type
		initialState := lc.getLockedPinState()
		if err := setupPinWithState(lc.pin, initialState); err != nil {
			return err
		}
		lc.available = true
		return nil
	}

	return nil
}

// getLockedPinState returns the pin state for "locked" based on lock type
// Fail-secure (0): locked = LOW (false), unlocked = HIGH (true)
// Fail-safe (1): locked = HIGH (true), unlocked = LOW (false)
func (lc *LockController) getLockedPinState() bool {
	return lc.lockType == config.LockTypeFailSafe
}

// getUnlockedPinState returns the pin state for "unlocked" based on lock type
func (lc *LockController) getUnlockedPinState() bool {
	return lc.lockType == config.LockTypeFailSecure
}

// Open activates the lock for the specified duration
func (lc *LockController) Open(duration time.Duration) {
	lc.mu.Lock()
	defer lc.mu.Unlock()

	if lc.isOpen {
		return
	}

	lc.isOpen = true

	if lc.available {
		lc.setPin(lc.getUnlockedPinState())
	}

	// Close after duration
	go func() {
		time.Sleep(duration)
		lc.Close()
	}()
}

// Close deactivates the lock
func (lc *LockController) Close() {
	lc.mu.Lock()
	defer lc.mu.Unlock()

	if !lc.isOpen {
		return
	}

	lc.isOpen = false

	if lc.available {
		lc.setPin(lc.getLockedPinState())
	}
}

// setPin sets the GPIO pin state
func (lc *LockController) setPin(high bool) {
	if !lc.available {
		return
	}

	// Set the actual GPIO pin state
	if err := writePin(lc.pin, high); err != nil {
		log.Printf("GPIO: Error setting pin %d to %v: %v", lc.pin, high, err)
		return
	}
}

// IsAvailable returns whether GPIO hardware is available
func (lc *LockController) IsAvailable() bool {
	return lc.available
}

// IsOpen returns the current lock state
func (lc *LockController) IsOpen() bool {
	lc.mu.Lock()
	defer lc.mu.Unlock()
	return lc.isOpen
}
