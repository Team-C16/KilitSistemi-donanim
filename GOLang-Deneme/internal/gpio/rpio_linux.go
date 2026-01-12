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

// setupPin configures a GPIO pin for output (Linux only)
func setupPin(pin int) error {
	if gpioChip == nil {
		return fmt.Errorf("GPIO chip not initialized")
	}

	// Request the GPIO line as output with initial low state
	line, err := gpioChip.RequestLine(
		pin,
		gpiod.AsOutput(0), // 0 = Low (lock closed by default)
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
