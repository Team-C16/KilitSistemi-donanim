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
		lc.initGPIO()
	} else {
		log.Printf("GPIO: Running on %s, using mock mode", runtime.GOOS)
	}

	return lc
}

// initGPIO initializes the GPIO hardware
func (lc *LockController) initGPIO() {
	// Note: Actual GPIO initialization would use go-rpio
	// We keep this separate to avoid build issues on non-Linux systems
	log.Printf("GPIO: Initializing pin %d for door lock", lc.pin)
	lc.available = true
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

	// Note: Actual implementation would use go-rpio here
	// rpio.Pin(lc.pin).Output()
	// if high {
	//     rpio.Pin(lc.pin).High()
	// } else {
	//     rpio.Pin(lc.pin).Low()
	// }
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
