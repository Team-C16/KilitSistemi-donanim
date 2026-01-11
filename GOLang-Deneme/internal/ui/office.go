// Package ui - OFFICE mode UI (full-width Mon-Fri weekly grid)
package ui

import (
	"log"

	"fyne.io/fyne/v2"
	"fyne.io/fyne/v2/container"
)

// buildOfficeUI creates the OFFICE mode layout
// Full-width Mon-Fri grid without QR card
// Weekend displays next week
func (a *App) buildOfficeUI() fyne.CanvasObject {
	log.Println("Building OFFICE mode UI")

	// Get week days (Mon-Fri)
	days := GenerateWeekDays()

	// Full-width schedule grid
	scheduleGrid := a.createScheduleGrid(days, true)

	// Footer
	footer := a.createFooter()

	// Main layout
	return container.NewBorder(
		nil,                               // top
		footer,                            // bottom
		nil,                               // left
		nil,                               // right
		container.NewPadded(scheduleGrid), // center
	)
}
