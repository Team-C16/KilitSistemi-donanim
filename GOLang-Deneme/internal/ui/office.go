// Package ui - OFFICE mode UI (full-width Mon-Fri weekly grid)
package ui

import (
	"fmt"
	"image/color"
	"time"

	"fyne.io/fyne/v2"
	"fyne.io/fyne/v2/canvas"
	"fyne.io/fyne/v2/container"
	"fyne.io/fyne/v2/theme"
	"fyne.io/fyne/v2/widget"
)

// buildOfficeUI creates the OFFICE mode layout
// Full-width Mon-Fri grid without QR card
// Weekend displays next week
// Left panel shows room info and occupant carousel (hidden if no data)
func (a *App) buildOfficeUI() fyne.CanvasObject {
	// Get responsive sizes
	sizes := CalculateResponsiveSizes(a.window.Canvas().Size())

	// Get week days (Mon-Fri)
	days := GenerateWeekDays()

	// Create schedule grid container
	scheduleGrid := a.createScheduleGrid(days, true)
	scheduleContainer := container.NewPadded(scheduleGrid)

	// Create left panel container (will be populated dynamically)
	leftPanelContent := container.NewVBox()
	occupantIndex := 0

	// Left panel wrapper with fixed width (compact)
	leftPanelWidth := sizes.QRPanelWidth * 0.6
	leftWrapper := container.NewGridWrap(fyne.NewSize(leftPanelWidth, 0), leftPanelContent)

	// Main content container - will be rebuilt when data changes
	mainContentContainer := container.NewMax()

	// Initial layout (full width schedule until data is loaded)
	mainContentContainer.Objects = []fyne.CanvasObject{scheduleContainer}

	// Start update loop to refresh grid when schedule data changes
	go func() {
		carouselTicker := time.NewTicker(10 * time.Second)
		defer carouselTicker.Stop()

		for {
			select {
			case <-a.updateChan:
				// Recreate schedule grid with latest data
				newDays := GenerateWeekDays()
				newGrid := a.createScheduleGrid(newDays, true)
				scheduleContainer.Objects = []fyne.CanvasObject{newGrid}
				scheduleContainer.Refresh()

				// Check if we have room details
				details := a.GetRoomDetails()
				hasData := details != nil && len(details.Occupants) > 0

				if hasData {
					// Update left panel and show it
					newPanel := a.createOfficeLeftPanelWithIndex(sizes, occupantIndex)
					leftPanelContent.Objects = []fyne.CanvasObject{newPanel}
					leftPanelContent.Refresh()

					// Layout with left panel
					mainContentContainer.Objects = []fyne.CanvasObject{
						container.NewBorder(
							nil, nil,
							leftWrapper,
							nil,
							scheduleContainer,
						),
					}
				} else {
					// Full width schedule (no left panel)
					mainContentContainer.Objects = []fyne.CanvasObject{scheduleContainer}
				}
				mainContentContainer.Refresh()

			case <-carouselTicker.C:
				// Auto-slide carousel
				details := a.GetRoomDetails()
				if details != nil && len(details.Occupants) > 1 {
					occupantIndex = (occupantIndex + 1) % len(details.Occupants)
					newPanel := a.createOfficeLeftPanelWithIndex(sizes, occupantIndex)
					leftPanelContent.Objects = []fyne.CanvasObject{newPanel}
					leftPanelContent.Refresh()
				}

			case <-a.stopChan:
				return
			}
		}
	}()

	// Footer
	footer := a.createFooter()

	// Main layout
	return container.NewBorder(
		nil,                  // top
		footer,               // bottom
		nil,                  // left
		nil,                  // right
		mainContentContainer, // center
	)
}

// createOfficeLeftPanelWithIndex creates the left panel with room info and occupant carousel
func (a *App) createOfficeLeftPanelWithIndex(sizes ResponsiveSizes, occupantIndex int) fyne.CanvasObject {
	details := a.GetRoomDetails()
	if details == nil || len(details.Occupants) == 0 {
		// Return empty/minimal container if no occupants
		return container.NewVBox()
	}

	// Panel background
	panelBg := canvas.NewRectangle(ColorLight)

	// Room name header (Responsive Size, No Wrapping)
	headerBg := canvas.NewRectangle(ColorPrimary)
	headerBg.SetMinSize(fyne.NewSize(0, sizes.HeaderHeight))

	roomName := details.RoomName
	if roomName == "" {
		roomName = "Oda"
	}
	headerText := canvas.NewText(roomName, color.White)
	headerText.TextSize = sizes.FontSubtitle // Responsive size
	headerText.TextStyle = fyne.TextStyle{Bold: true}
	headerText.Alignment = fyne.TextAlignCenter

	header := container.NewStack(headerBg, container.NewPadded(headerText))

	// Room description (Fixed Size, With Wrapping)
	var descWidget fyne.CanvasObject
	if details.Description != "" {
		descSegment := &widget.TextSegment{
			Text: details.Description,
			Style: widget.RichTextStyle{
				SizeName:  theme.SizeNameCaptionText,
				ColorName: theme.ColorNameForeground,
			},
		}
		descLabel := widget.NewRichText(descSegment)
		descLabel.Wrapping = fyne.TextWrapWord
		descWidget = container.NewPadded(descLabel)
	} else {
		descWidget = container.NewVBox()
	}

	// Room capacity info
	var capacityWidget fyne.CanvasObject
	if details.MaxPerson > 0 {
		capacityStr := fmt.Sprintf("👥 Kapasite: %d-%d kişi", details.MinPerson, details.MaxPerson)
		capacityText := canvas.NewText(capacityStr, ColorDark)
		capacityText.TextSize = sizes.FontSmall
		capacityText.Alignment = fyne.TextAlignCenter
		capacityWidget = container.NewCenter(capacityText)
	} else {
		capacityWidget = container.NewVBox()
	}

	// Divider
	divider := canvas.NewRectangle(ColorPrimary)
	divider.SetMinSize(fyne.NewSize(0, 2))

	// Occupant section header
	occupantHeaderText := canvas.NewText("Oda Sahipleri", ColorPrimary)
	occupantHeaderText.TextSize = sizes.FontSmall
	occupantHeaderText.TextStyle = fyne.TextStyle{Bold: true}
	occupantHeaderText.Alignment = fyne.TextAlignCenter

	// Current occupant
	occupant := details.Occupants[occupantIndex%len(details.Occupants)]

	// Photo container (circle with photo or initial)
	photoSize := sizes.HeaderHeight
	photoContainer := a.createOccupantPhotoContainer(occupant, photoSize, sizes.FontTitle)

	// Occupant name
	nameText := canvas.NewText(occupant.Name+" "+occupant.Surname, ColorText)
	nameText.TextSize = sizes.FontBody
	nameText.TextStyle = fyne.TextStyle{Bold: true}
	nameText.Alignment = fyne.TextAlignCenter

	// Count indicator (dots)
	var countWidget fyne.CanvasObject
	if len(details.Occupants) > 1 {
		dots := ""
		for i := 0; i < len(details.Occupants); i++ {
			if i == occupantIndex {
				dots += "●"
			} else {
				dots += "○"
			}
		}
		countText := canvas.NewText(dots, ColorDark)
		countText.TextSize = sizes.FontSmall
		countText.Alignment = fyne.TextAlignCenter
		countWidget = container.NewCenter(countText)
	} else {
		countWidget = container.NewVBox()
	}

	// Assemble content
	content := container.NewVBox(
		header,
		container.NewPadded(descWidget),
		capacityWidget,
		container.NewPadded(divider),
		container.NewCenter(occupantHeaderText),
		container.NewPadded(container.NewCenter(photoContainer)),
		container.NewCenter(nameText),
		countWidget,
	)

	return container.NewStack(panelBg, container.NewPadded(content))
}
