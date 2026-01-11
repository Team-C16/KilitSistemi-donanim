// Package ui - STANDARD mode UI (QR card + 5-day rolling schedule)
package ui

import (
	"image/color"
	"log"

	"fyne.io/fyne/v2"
	"fyne.io/fyne/v2/canvas"
	"fyne.io/fyne/v2/container"
)

// buildStandardUI creates the STANDARD mode layout
// Left: QR card with room name
// Right: 5-day rolling schedule grid
func (a *App) buildStandardUI() fyne.CanvasObject {
	log.Println("Building STANDARD mode UI")

	// Left panel: QR Card (fixed ~28% width)
	qrPanel := a.createQRCard()

	// Right panel: Schedule Grid
	days := GenerateDisplayDays()
	scheduleGrid := a.createScheduleGrid(days, false)

	// Use Border layout for fixed left panel width
	// This creates a non-interactive layout without a draggable divider
	mainContent := container.NewBorder(
		nil, nil, // top, bottom
		container.NewGridWrap(fyne.NewSize(400, 0), qrPanel), // left (fixed width)
		nil,                               // right
		container.NewPadded(scheduleGrid), // center fills remaining space
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

// createQRCard creates the QR code panel
func (a *App) createQRCard() fyne.CanvasObject {
	// Card background
	cardBg := canvas.NewRectangle(ColorLight)

	// Header
	headerBg := canvas.NewRectangle(ColorPrimary)
	headerBg.SetMinSize(fyne.NewSize(0, 50))

	headerText := canvas.NewText("Odaya Erişim", color.White)
	headerText.TextSize = 18
	headerText.TextStyle = fyne.TextStyle{Bold: true}
	headerText.Alignment = fyne.TextAlignCenter

	header := container.NewStack(headerBg, container.NewCenter(headerText))

	// QR Code placeholder (will be updated dynamically)
	qrPlaceholder := canvas.NewRectangle(ColorPrimary)
	qrPlaceholder.SetMinSize(fyne.NewSize(320, 320))

	qrContainer := container.NewCenter(qrPlaceholder)

	// Scan instruction
	scanText := canvas.NewText("QR Kodu Uygulamadan Taratın", ColorText)
	scanText.TextSize = 14
	scanText.Alignment = fyne.TextAlignCenter

	// Room name
	roomNameText := canvas.NewText("", ColorText)
	roomNameText.TextSize = 20
	roomNameText.TextStyle = fyne.TextStyle{Bold: true}
	roomNameText.Alignment = fyne.TextAlignCenter

	// Notification text (below room name)
	notifyText := canvas.NewText("", ColorAvailable)
	notifyText.TextSize = 40
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

	// Generate QR image
	qrImg, err := a.qrGen.GenerateCanvasImage(qrResp.Token, 320)
	if err != nil {
		log.Printf("Failed to generate QR: %v", err)
		return
	}

	// Update container
	qrContainer.Objects = []fyne.CanvasObject{qrImg}
	qrContainer.Refresh()
}
