// Package gpio provides door lock control via GPIO pins
package gpio

import (
	"log"
	"runtime"
	"sync"
	"time"
)

// LockController manages the door lock GPIO
type LockController struct {
	pin       int
	isOpen    bool
	mu        sync.Mutex
	available bool
}

// NewLockController creates a new lock controller on the specified GPIO pin
func NewLockController(pin int) *LockController {
	lc := &LockController{
		pin:       pin,
		available: false,
	}

	// Only initialize GPIO on Linux (Raspberry Pi)
	if runtime.GOOS == "linux" {
		if err := lc.initGPIO(); err != nil {
			log.Printf("GPIO: Failed to initialize: %v (using mock mode)", err)
			lc.available = false
		}
	} else {
		log.Printf("GPIO: Running on %s, using mock mode", runtime.GOOS)
	}

	return lc
}

// initGPIO initializes the GPIO hardware
func (lc *LockController) initGPIO() error {
	// On Linux, initialize actual GPIO hardware
	if runtime.GOOS == "linux" {
		if err := initRPIO(); err != nil {
			return err
		}
		if err := setupPin(lc.pin); err != nil {
			return err
		}
		lc.available = true
		log.Printf("GPIO: Hardware initialized on pin %d", lc.pin)
		return nil
	}

	// On other platforms, use mock mode
	log.Printf("GPIO: Initializing pin %d for door lock (mock mode)", lc.pin)
	return nil
}

// Open activates the lock for the specified duration
func (lc *LockController) Open(duration time.Duration) {
	lc.mu.Lock()
	defer lc.mu.Unlock()

	if lc.isOpen {
		log.Println("GPIO: Lock already open, ignoring request")
		return
	}

	lc.isOpen = true
	log.Printf("GPIO: Opening lock for %v", duration)

	if lc.available {
		lc.setPin(true)
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

	log.Println("GPIO: Closing lock")
	lc.isOpen = false

	if lc.available {
		lc.setPin(false)
	}
}

// setPin sets the GPIO pin state
func (lc *LockController) setPin(high bool) {
	if !lc.available {
		log.Printf("GPIO: Mock - Pin %d set to %v", lc.pin, high)
		return
	}

	// Set the actual GPIO pin state
	if err := writePin(lc.pin, high); err != nil {
		log.Printf("GPIO: Error setting pin %d to %v: %v", lc.pin, high, err)
		return
	}
	log.Printf("GPIO: Pin %d set to %v", lc.pin, high)
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
