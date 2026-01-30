//go:build linux
// +build linux

// Package gpio - Linux-specific GPIO implementation using gpiod
package gpio

import (
	"fmt"

	"github.com/warthog618/gpiod"
)

var (
	gpioChip *gpiod.Chip
	gpioLine *gpiod.Line
	gpioPin  int
)

// initRPIO initializes the gpiod library (Linux only)
// Note: Function name kept for compatibility with existing code
func initRPIO() error {
	if gpioChip != nil {
		return nil // Already initialized
	}

	// Open the GPIO chip (gpiochip0 is default on Raspberry Pi)
	chip, err := gpiod.NewChip("gpiochip0")
	if err != nil {
		return fmt.Errorf("failed to open gpiochip0: %w", err)
	}

	gpioChip = chip
	return nil
}

// setupPin configures a GPIO pin for output (Linux only) - default to LOW
func setupPin(pin int) error {
	return setupPinWithState(pin, false)
}

// setupPinWithState configures a GPIO pin for output with a specific initial state (Linux only)
func setupPinWithState(pin int, initialHigh bool) error {
	if gpioChip == nil {
		return fmt.Errorf("GPIO chip not initialized")
	}

	// Request the GPIO line as output with specified initial state
	initialValue := 0
	if initialHigh {
		initialValue = 1
	}
	line, err := gpioChip.RequestLine(
		pin,
		gpiod.AsOutput(initialValue),
	)
	if err != nil {
		return fmt.Errorf("failed to request GPIO line %d: %w", pin, err)
	}

	gpioLine = line
	gpioPin = pin
	return nil
}

// writePin sets a GPIO pin to high or low (Linux only)
func writePin(pin int, high bool) error {
	if gpioLine == nil {
		return fmt.Errorf("GPIO line not initialized")
	}

	value := 0
	if high {
		value = 1
	}

	if err := gpioLine.SetValue(value); err != nil {
		return fmt.Errorf("failed to set GPIO pin %d to %v: %w", pin, high, err)
	}

	return nil
}

// CloseRPIO closes the gpiod library and releases resources (Linux only)
// Note: Function name kept for compatibility with existing code
func CloseRPIO() {
	if gpioLine != nil {
		gpioLine.Close()
		gpioLine = nil
	}
	if gpioChip != nil {
		gpioChip.Close()
		gpioChip = nil
	}
}
