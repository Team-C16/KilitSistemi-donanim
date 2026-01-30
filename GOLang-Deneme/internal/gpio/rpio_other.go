//go:build !linux
// +build !linux

// Package gpio - Mock GPIO implementation for non-Linux systems (Windows, macOS, etc.)
package gpio

import "fmt"

// initRPIO is a no-op on non-Linux systems
func initRPIO() error {
	return fmt.Errorf("GPIO not supported on this platform")
}

// setupPin is a no-op on non-Linux systems
func setupPin(pin int) error {
	return fmt.Errorf("GPIO not supported on this platform")
}

// setupPinWithState is a no-op on non-Linux systems
func setupPinWithState(pin int, initialHigh bool) error {
	return fmt.Errorf("GPIO not supported on this platform")
}

// writePin is a no-op on non-Linux systems
func writePin(pin int, high bool) error {
	return fmt.Errorf("GPIO not supported on this platform")
}

// CloseRPIO is a no-op on non-Linux systems
func CloseRPIO() {
	// No-op
}
