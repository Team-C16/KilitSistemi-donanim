// Package ui - STANDARD mode UI (QR card + 5-day rolling schedule)
package ui

import (
	"image/color"
	"log"
	"time"

	"fyne.io/fyne/v2"
	"fyne.io/fyne/v2/canvas"
	"fyne.io/fyne/v2/container"
)

// buildStandardUI creates the STANDARD mode layout
// Left: QR card with room name
// Right: 5-day rolling schedule grid
func (a *App) buildStandardUI() fyne.CanvasObject {
	// Get responsive sizes
	sizes := CalculateResponsiveSizes(a.window.Canvas().Size())

	// Right panel: Schedule Grid in a container that can be updated
	days := GenerateDisplayDays()
	scheduleGrid := a.createScheduleGrid(days, false)
	scheduleContainer := container.NewPadded(scheduleGrid)

	// Left panel: QR Card (pass schedule container for updates)
	qrPanel := a.createQRCardWithScheduleUpdate(scheduleContainer)

	// Use Border layout for responsive left panel width
	// This creates a non-interactive layout without a draggable divider
	mainContent := container.NewBorder(
		nil, nil, // top, bottom
		container.NewGridWrap(fyne.NewSize(sizes.QRPanelWidth, 0), qrPanel), // left (responsive width)
		nil,               // right
		scheduleContainer, // center fills remaining space
	)

	// Footer
	footer := a.createFooter()

	// Main layout
	return container.NewBorder(
		nil,    // top
		footer, // bottom
		nil,    // left
		nil,    // right
		mainContent,
	)
}

// createQRCardWithScheduleUpdate creates the QR code panel and handles both QR and schedule updates
func (a *App) createQRCardWithScheduleUpdate(scheduleContainer *fyne.Container) fyne.CanvasObject {
	// Card background
	cardBg := canvas.NewRectangle(ColorLight)
	// Get responsive sizes
	sizes := CalculateResponsiveSizes(a.window.Canvas().Size())
	// Header with responsive height
	headerBg := canvas.NewRectangle(ColorPrimary)
	headerBg.SetMinSize(fyne.NewSize(0, sizes.HeaderHeight))
	headerText := canvas.NewText("Odaya Erişim", color.White)
	headerText.TextSize = sizes.FontSubtitle
	headerText.TextStyle = fyne.TextStyle{Bold: true}
	headerText.Alignment = fyne.TextAlignCenter
	header := container.NewStack(headerBg, container.NewCenter(headerText))
	// Store QR size for updates
	a.qrSize = int(sizes.QRCodeSize)
	// QR Code placeholder (will be updated dynamically)
	qrPlaceholder := canvas.NewRectangle(ColorPrimary)
	qrPlaceholder.SetMinSize(fyne.NewSize(sizes.QRCodeSize, sizes.QRCodeSize))
	qrContainer := container.NewCenter(qrPlaceholder)
	// Scan instruction with responsive font
	scanText := canvas.NewText("QR Kodu Uygulamadan Taratın", ColorText)
	scanText.TextSize = sizes.FontSmall
	scanText.Alignment = fyne.TextAlignCenter
	// Room name with responsive font
	roomNameText := canvas.NewText("", ColorText)
	roomNameText.TextSize = sizes.FontTitle
	roomNameText.TextStyle = fyne.TextStyle{Bold: true}
	roomNameText.Alignment = fyne.TextAlignCenter

	// Owner carousel container (replaces notification text)
	ownerCarouselContainer := container.NewVBox()
	ownerIndex := 0

	// Update both QR and schedule dynamically in a single goroutine
	go func() {
		carouselTicker := time.NewTicker(3 * time.Second)
		defer carouselTicker.Stop()

		for {
			select {
			case <-a.updateChan:
				// Update room name
				name := a.GetRoomName()
				if name != "" {
					roomNameText.Text = "➡️ " + name
					roomNameText.Refresh()
				}
				// Update QR code
				a.updateQRImage(qrContainer)

				// Update owner carousel
				a.updateOwnerCarousel(ownerCarouselContainer, ownerIndex, sizes)

				// Update schedule grid
				newDays := GenerateDisplayDays()
				newGrid := a.createScheduleGrid(newDays, false)
				scheduleContainer.Objects = []fyne.CanvasObject{newGrid}
				scheduleContainer.Refresh()

			case <-carouselTicker.C:
				// Auto-slide carousel
				details := a.GetRoomDetails()
				if details != nil && len(details.Owners) > 1 {
					ownerIndex = (ownerIndex + 1) % len(details.Owners)
					a.updateOwnerCarousel(ownerCarouselContainer, ownerIndex, sizes)
				}

			case <-a.stopChan:
				return
			}
		}
	}()
	// Assemble card content
	content := container.NewVBox(
		header,
		container.NewPadded(qrContainer),
		container.NewCenter(scanText),
		container.NewCenter(roomNameText),
		container.NewPadded(ownerCarouselContainer),
	)
	return container.NewStack(cardBg, container.NewPadded(content))
}

// createQRCard creates the QR code panel with responsive sizing (legacy method for other modes)
func (a *App) createQRCard() fyne.CanvasObject {
	// Card background
	cardBg := canvas.NewRectangle(ColorLight)
	// Get responsive sizes
	sizes := CalculateResponsiveSizes(a.window.Canvas().Size())
	// Header with responsive height
	headerBg := canvas.NewRectangle(ColorPrimary)
	headerBg.SetMinSize(fyne.NewSize(0, sizes.HeaderHeight))
	headerText := canvas.NewText("Odaya Erişim", color.White)
	headerText.TextSize = sizes.FontSubtitle
	headerText.TextStyle = fyne.TextStyle{Bold: true}
	headerText.Alignment = fyne.TextAlignCenter
	header := container.NewStack(headerBg, container.NewCenter(headerText))
	// Store QR size for updates
	a.qrSize = int(sizes.QRCodeSize)
	// QR Code placeholder (will be updated dynamically)
	qrPlaceholder := canvas.NewRectangle(ColorPrimary)
	qrPlaceholder.SetMinSize(fyne.NewSize(sizes.QRCodeSize, sizes.QRCodeSize))
	qrContainer := container.NewCenter(qrPlaceholder)
	// Scan instruction with responsive font
	scanText := canvas.NewText("QR Kodu Uygulamadan Taratın", ColorText)
	scanText.TextSize = sizes.FontSmall
	scanText.Alignment = fyne.TextAlignCenter
	// Room name with responsive font
	roomNameText := canvas.NewText("", ColorText)
	roomNameText.TextSize = sizes.FontTitle
	roomNameText.TextStyle = fyne.TextStyle{Bold: true}
	roomNameText.Alignment = fyne.TextAlignCenter
	// Notification text with responsive font
	notifyText := canvas.NewText("", ColorAvailable)
	notifyText.TextSize = sizes.FontNotify
	notifyText.TextStyle = fyne.TextStyle{Bold: true}
	notifyText.Alignment = fyne.TextAlignCenter
	a.notifyText = notifyText // Store reference for Notify() method
	// Update room name dynamically
	go func() {
		for {
			select {
			case <-a.updateChan:
				name := a.GetRoomName()
				if name != "" {
					roomNameText.Text = "➡️ " + name
					roomNameText.Refresh()
				}
				// Update QR code
				a.updateQRImage(qrContainer)
			case <-a.stopChan:
				return
			}
		}
	}()
	// Assemble card content
	content := container.NewVBox(
		header,
		container.NewPadded(qrContainer),
		container.NewCenter(scanText),
		container.NewCenter(roomNameText),
		container.NewCenter(notifyText),
	)
	return container.NewStack(cardBg, container.NewPadded(content))
}

// updateQRImage fetches a new QR token and updates the display
func (a *App) updateQRImage(qrContainer *fyne.Container) {
	qrResp, err := a.apiClient.GetQRCodeToken(false)
	if err != nil {
		log.Printf("Failed to fetch QR token: %v", err)
		return
	}
	if qrResp.Token == "" {
		return
	}
	// Use responsive QR size from app state
	qrSize := a.qrSize
	if qrSize == 0 {
		qrSize = 280 // fallback default
	}
	// Generate QR image with responsive size
	qrImg, err := a.qrGen.GenerateCanvasImage(qrResp.Token, qrSize)
	if err != nil {
		log.Printf("Failed to generate QR: %v", err)
		return
	}
	// Update container
	qrContainer.Objects = []fyne.CanvasObject{qrImg}
	qrContainer.Refresh()
}
