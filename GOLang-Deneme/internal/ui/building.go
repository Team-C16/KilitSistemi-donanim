// Package ui - BUILDING mode UI (multi-room sliding display)
package ui

import (
	"image/color"
	"log"
	"sync"
	"time"

	"fyne.io/fyne/v2"
	"fyne.io/fyne/v2/canvas"
	"fyne.io/fyne/v2/container"

	"kiosk-go/internal/api"
)

// BuildingState holds state for building mode
type BuildingState struct {
	rooms        []string
	roomExts     []string
	roomMap      map[int]string
	buildingName string
	schedule     RoomSchedule
	slideIndex   int
	mu           sync.RWMutex
}

// buildBuildingUI creates the BUILDING mode layout
// Multi-room schedule with sliding animation
func (a *App) buildBuildingUI() fyne.CanvasObject {
	state := &BuildingState{
		roomMap: make(map[int]string),
	}

	// Fetch building details first
	a.fetchBuildingDetails(state)

	// Create scrollable room grid
	roomGrid := a.createBuildingGrid(state)

	// Footer with building name
	footer := a.createBuildingFooter(state)

	// Start sliding animation
	go a.runBuildingSlider(state, roomGrid)

	// Start data updates
	go a.updateBuildingData(state)

	// Main layout
	return container.NewBorder(
		nil,    // top
		footer, // bottom
		nil,    // left
		nil,    // right
		roomGrid,
	)
}

// fetchBuildingDetails fetches building and room information
func (a *App) fetchBuildingDetails(state *BuildingState) {
	details, err := a.apiClient.GetBuildingDetails()
	if err != nil {
		log.Printf("Failed to fetch building details: %v", err)
		return
	}

	state.mu.Lock()
	defer state.mu.Unlock()

	// Extract building name
	if len(details.BuildingDetails) > 0 {
		state.buildingName = details.BuildingDetails[0].BuildingName
	}

	// Extract rooms
	state.rooms = make([]string, 0, len(details.Rooms))
	state.roomExts = make([]string, 0, len(details.Rooms))
	state.roomMap = make(map[int]string)

	for _, room := range details.Rooms {
		state.rooms = append(state.rooms, room.RoomName)
		state.roomExts = append(state.roomExts, room.RoomDesc)
		state.roomMap[room.RoomID] = room.RoomName
	}
}

// createBuildingGrid creates the multi-room schedule grid
// Rows are responsive - they fill the available screen height
func (a *App) createBuildingGrid(state *BuildingState) *fyne.Container {
	hours := a.timeConfig.GenerateHours()

	state.mu.RLock()
	rooms := state.rooms
	roomExts := state.roomExts
	state.mu.RUnlock()

	if len(rooms) == 0 {
		sizes := CalculateResponsiveSizes(a.window.Canvas().Size())
		placeholder := canvas.NewText("Odalar yükleniyor...", ColorText)
		placeholder.TextSize = sizes.FontTitle + 4
		return container.NewCenter(placeholder)
	}

	// Get responsive sizes
	sizes := CalculateResponsiveSizes(a.window.Canvas().Size())
	timeColWidth := sizes.TimeColWidth + 20 // Slightly wider for building mode

	// Helper to create a row with responsive-width time cell and flexible room cells
	createRow := func(timeCell fyne.CanvasObject, roomCells []fyne.CanvasObject) fyne.CanvasObject {
		roomGrid := container.NewGridWithColumns(len(roomCells), roomCells...)
		return container.NewBorder(nil, nil,
			container.NewGridWrap(fyne.NewSize(timeColWidth, 0), timeCell), // responsive time column
			nil,
			roomGrid, // remaining space for rooms
		)
	}

	// Create header row with rooms
	numVisible := 4
	roomCells := make([]fyne.CanvasObject, 0, numVisible)

	for i := 0; i < len(rooms) && i < numVisible; i++ {
		ext := ""
		if i < len(roomExts) {
			ext = roomExts[i]
		}
		roomCells = append(roomCells, a.createRoomHeaderCell(rooms[i], ext))
	}

	headerRow := createRow(a.createBuildingHeaderCell("Saat"), roomCells)

	// Create data rows
	rows := []fyne.CanvasObject{headerRow}

	for _, hour := range hours {
		roomCells := make([]fyne.CanvasObject, 0, numVisible)

		for i := 0; i < len(rooms) && i < numVisible; i++ {
			roomCells = append(roomCells, a.createBuildingScheduleCell(state, rooms[i], hour))
		}

		rows = append(rows, createRow(a.createBuildingHourCell(hour), roomCells))
	}

	// Use GridWithRows to make rows fill the available screen height
	return container.NewGridWithRows(len(rows), rows...)
}

// createBuildingHeaderCell creates a header cell with responsive sizing
func (a *App) createBuildingHeaderCell(text string) fyne.CanvasObject {
	sizes := CalculateResponsiveSizes(a.window.Canvas().Size())

	bg := canvas.NewRectangle(ColorPrimary)
	bg.SetMinSize(fyne.NewSize(sizes.TimeColWidth+20, sizes.HeaderHeight))

	label := canvas.NewText(text, color.White)
	label.TextSize = sizes.FontBody
	label.TextStyle = fyne.TextStyle{Bold: true}
	label.Alignment = fyne.TextAlignCenter

	return container.NewStack(bg, container.NewCenter(label))
}

// createRoomHeaderCell creates a room header cell with extension using responsive sizing
func (a *App) createRoomHeaderCell(roomName, ext string) fyne.CanvasObject {
	sizes := CalculateResponsiveSizes(a.window.Canvas().Size())

	bg := canvas.NewRectangle(ColorPrimary)
	bg.SetMinSize(fyne.NewSize(0, sizes.FooterHeight))

	roomLabel := canvas.NewText(roomName, color.White)
	roomLabel.TextSize = sizes.FontSmall
	roomLabel.TextStyle = fyne.TextStyle{Bold: true}
	roomLabel.Alignment = fyne.TextAlignCenter

	content := container.NewVBox(container.NewCenter(roomLabel))

	if ext != "" {
		extLabel := canvas.NewText("Dahili: "+ext, color.White)
		extLabel.TextSize = sizes.FontMicro
		extLabel.Alignment = fyne.TextAlignCenter
		content.Add(container.NewCenter(extLabel))
	}

	return container.NewStack(bg, container.NewCenter(content))
}

// createBuildingHourCell creates an hour cell for building mode with responsive sizing
func (a *App) createBuildingHourCell(hour string) fyne.CanvasObject {
	sizes := CalculateResponsiveSizes(a.window.Canvas().Size())

	now := time.Now()
	currentHour := now.Format("15:00")

	bgColor := ColorBackground
	fgColor := ColorText
	if hour == currentHour {
		bgColor = ColorHighlight
		fgColor = ColorDark
	}

	bg := canvas.NewRectangle(bgColor)
	bg.SetMinSize(fyne.NewSize(sizes.TimeColWidth+20, sizes.HeaderHeight))

	label := canvas.NewText(hour, fgColor)
	label.TextSize = sizes.FontSmall
	label.Alignment = fyne.TextAlignCenter

	return container.NewStack(bg, container.NewCenter(label))
}

// createBuildingScheduleCell creates a schedule cell for building mode with responsive sizing
func (a *App) createBuildingScheduleCell(state *BuildingState, roomName, hour string) fyne.CanvasObject {
	sizes := CalculateResponsiveSizes(a.window.Canvas().Size())

	state.mu.RLock()
	schedule := state.schedule
	state.mu.RUnlock()

	bgColor := ColorLight
	fgColor := ColorText
	line1 := ""
	line2 := ""

	if roomSchedule, ok := schedule[roomName]; ok {
		if slot, ok := roomSchedule[hour]; ok && slot.Status == SlotOccupied {
			bgColor = ColorUnavailable
			fgColor = ColorLight
			line1 = TruncateString(slot.Activity, 18)
			line2 = TruncateString(slot.Organizer, 18)
		}
	}

	bg := canvas.NewRectangle(bgColor)
	bg.SetMinSize(fyne.NewSize(0, sizes.HeaderHeight))

	content := container.NewVBox()

	if line1 != "" {
		label1 := canvas.NewText(line1, fgColor)
		label1.TextSize = sizes.FontTiny
		label1.TextStyle = fyne.TextStyle{Bold: true}
		label1.Alignment = fyne.TextAlignCenter
		content.Add(container.NewCenter(label1))
	}

	if line2 != "" {
		label2 := canvas.NewText(line2, fgColor)
		label2.TextSize = sizes.FontMicro
		label2.Alignment = fyne.TextAlignCenter
		content.Add(container.NewCenter(label2))
	}

	// Highlight current hour
	now := time.Now()
	if hour == now.Format("15:00") {
		border := canvas.NewRectangle(color.Transparent)
		border.StrokeColor = ColorHighlight
		border.StrokeWidth = 2
		return container.NewStack(bg, border, container.NewCenter(content))
	}

	return container.NewStack(bg, container.NewCenter(content))
}

// createBuildingFooter creates the footer with building name using responsive sizing
func (a *App) createBuildingFooter(state *BuildingState) fyne.CanvasObject {
	sizes := CalculateResponsiveSizes(a.window.Canvas().Size())

	footerBg := canvas.NewRectangle(ColorPrimary)
	footerBg.SetMinSize(fyne.NewSize(0, sizes.FooterHeight+10))

	infoText := canvas.NewText("pve.izu.edu.tr/randevu ← Randevu İçin", color.White)
	infoText.TextSize = sizes.FontBody

	state.mu.RLock()
	buildingName := state.buildingName
	state.mu.RUnlock()

	buildingText := canvas.NewText(buildingName, color.White)
	buildingText.TextSize = sizes.FontTitle
	buildingText.TextStyle = fyne.TextStyle{Bold: true}
	buildingText.Alignment = fyne.TextAlignCenter

	clockText := canvas.NewText("", color.White)
	clockText.TextSize = sizes.FontBody

	// Update clock
	go func() {
		for {
			select {
			case <-a.stopChan:
				return
			default:
				now := time.Now()
				days := []string{"Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"}
				dayIdx := int(now.Weekday())
				if dayIdx == 0 {
					dayIdx = 6
				} else {
					dayIdx--
				}
				clockText.Text = now.Format("⏰ 02.01.2006") + " " + days[dayIdx] + " • " + now.Format("15:04:05")
				clockText.Refresh()
				time.Sleep(time.Second)
			}
		}
	}()

	content := container.NewHBox(
		container.NewPadded(infoText),
		container.NewCenter(buildingText),
		container.NewPadded(clockText),
	)

	return container.NewStack(footerBg, container.NewCenter(content))
}

// runBuildingSlider runs the sliding animation loop
func (a *App) runBuildingSlider(state *BuildingState, _ *fyne.Container) {
	ticker := time.NewTicker(8 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			state.mu.Lock()
			numRooms := len(state.rooms)
			if numRooms > 4 {
				state.slideIndex = (state.slideIndex + 4) % numRooms
			}
			state.mu.Unlock()
		case <-a.stopChan:
			return
		}
	}
}

// updateBuildingData fetches fresh building schedule data
func (a *App) updateBuildingData(state *BuildingState) {
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	// Initial fetch
	a.fetchBuildingSchedule(state)

	for {
		select {
		case <-ticker.C:
			a.fetchBuildingSchedule(state)
		case <-a.stopChan:
			return
		}
	}
}

// fetchBuildingSchedule fetches schedule for all rooms
func (a *App) fetchBuildingSchedule(state *BuildingState) {
	schedResp, err := a.apiClient.GetBuildingSchedule()
	if err != nil {
		log.Printf("Failed to fetch building schedule: %v", err)
		return
	}

	hours := a.timeConfig.GenerateHours()

	state.mu.Lock()
	state.schedule = TransformBuildingSchedule(
		&api.BuildingScheduleResponse{Schedule: schedResp.Schedule},
		state.roomMap,
		hours,
	)
	state.mu.Unlock()
}
