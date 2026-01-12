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

	// Create schedule grid container
	scheduleGrid := a.createScheduleGrid(days, true)
	scheduleContainer := container.NewPadded(scheduleGrid)

	// Start update loop to refresh grid when schedule data changes
	go func() {
		for {
			select {
			case <-a.updateChan:
				// Recreate schedule grid with latest data
				newDays := GenerateWeekDays()
				newGrid := a.createScheduleGrid(newDays, true)
				scheduleContainer.Objects = []fyne.CanvasObject{newGrid}
				scheduleContainer.Refresh()
			case <-a.stopChan:
				return
			}
		}
	}()

	// Footer
	footer := a.createFooter()

	// Main layout
	return container.NewBorder(
		nil,               // top
		footer,            // bottom
		nil,               // left
		nil,               // right
		scheduleContainer, // center
	)
}
