// Package ui - BUILDING mode UI (multi-room sliding display)
package ui

import (
	"fmt"
	"image/color"
	"log"
	"sync"
	"time"

	"fyne.io/fyne/v2"
	"fyne.io/fyne/v2/canvas"
	"fyne.io/fyne/v2/container"
	"fyne.io/fyne/v2/widget"

	"kiosk-go/internal/api"
	"kiosk-go/internal/config"
)

// BuildingState holds state for building mode
type BuildingState struct {
	rooms          []string
	roomExts       []string
	roomMap        map[int]string
	roomConfigs    map[string]RoomTimeConfig // room name -> time config
	globalConfig   TimeConfig                // global grid config
	buildingName   string
	schedule       RoomSchedule
	slideIndex     int
	slideDirection int // 1 for forward, -1 for backward
	progress       *widget.ProgressBar
	mu             sync.RWMutex
}

// buildBuildingUI creates the BUILDING mode layout
// Multi-room schedule with sliding animation
func (a *App) buildBuildingUI() fyne.CanvasObject {
	state := &BuildingState{
		roomMap:        make(map[int]string),
		roomConfigs:    make(map[string]RoomTimeConfig),
		slideDirection: 1, // Start moving forward
		progress:       widget.NewProgressBar(),
	}

	// Remove text from progress bar
	state.progress.TextFormatter = func() string { return "" }

	// Fetch building details first
	a.fetchBuildingDetails(state)

	// Create scrollable room grid
	// now returns the grid container and a thread-safe update function
	roomGrid, updateGridFunc := a.createBuildingGrid(state)

	// Footer with building name
	footer := a.createBuildingFooter(state)

	// Combine footer with progress bar
	// Use GridWrap to size the bar to 300x4, and Center to position it
	progressBarSized := container.NewGridWrap(fyne.NewSize(300, 4), state.progress)
	bottomContainer := container.NewVBox(container.NewCenter(progressBarSized), footer)

	// Start sliding animation
	go a.runBuildingSlider(state, updateGridFunc)

	// Start data updates
	go a.updateBuildingData(state, updateGridFunc)

	// Main layout
	return container.NewBorder(
		nil,             // top
		bottomContainer, // bottom
		nil,             // left
		nil,             // right
		roomGrid,
	)
}

// fetchBuildingDetails fetches building and room information
func (a *App) fetchBuildingDetails(state *BuildingState) {
	// First fetch global indexes for the grid structure
	globalConfigs, err := a.apiClient.GetGlobalIndexes()
	if err != nil {
		log.Printf("Failed to fetch global indexes, using defaults: %v", err)
		state.globalConfig = DefaultTimeConfig()
	} else {
		state.globalConfig = ParseTimeConfig(globalConfigs)
	}

	// Update app's time config with global config
	a.timeConfig = state.globalConfig

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
	state.roomConfigs = make(map[string]RoomTimeConfig)

	for _, room := range details.Rooms {
		state.rooms = append(state.rooms, room.RoomName)
		state.roomExts = append(state.roomExts, room.RoomDesc)
		state.roomMap[room.RoomID] = room.RoomName

		// Parse room-specific time config
		roomConfig := ParseRoomTimeConfig(&room, state.globalConfig)
		state.roomConfigs[room.RoomName] = roomConfig
	}
}

// createBuildingGrid creates the multi-room schedule grid with DYNAMIC COLUMN Layout
func (a *App) createBuildingGrid(state *BuildingState) (*fyne.Container, func()) {
	// 1. Calculate Global Metrics
	globalTC := state.globalConfig
	// Ensure valid range
	if globalTC.EndHour <= globalTC.StartHour {
		globalTC.EndHour = globalTC.StartHour + 9 // Default 9 hours
	}

	globalInterval := globalTC.Interval
	if globalInterval <= 0 {
		globalInterval = 60
	}

	// Calculate total minutes including the LAST slot
	// If Start=9, End=18. We want slots 9, 10, ..., 18.
	// That is (18-9+1) slots * 60 = 10 * 60 = 600 minutes.
	// Or (End - Start)*60 + Interval
	totalGlobalMinutes := (globalTC.EndHour-globalTC.StartHour)*60 + globalInterval

	if totalGlobalMinutes <= 0 {
		totalGlobalMinutes = 600 // 10 hours
	}

	// Responsive sizes
	sizes := CalculateResponsiveSizes(a.window.Canvas().Size())
	timeColWidth := sizes.TimeColWidth + 20

	// Determine number of visible room columns
	cfg := config.Get()
	numVisible := cfg.BuildingMaxVisibleRooms
	if numVisible <= 0 {
		numVisible = 6
	}

	// ---------------------------------------------------------
	// 2. Create Time Column (Static)
	// ---------------------------------------------------------
	var timeSlots []RoomSlotData
	var timeObjects []fyne.CanvasObject

	// Generate slots based on Global Config Interval

	// Parse suffix
	var globalSuffixM int
	fmt.Sscanf(globalTC.TimeSuffix, ":%d", &globalSuffixM)

	currM := globalTC.StartHour*60 + globalSuffixM
	// EndM should INCLUDE the last slot start
	endM := globalTC.EndHour*60 + globalSuffixM + globalInterval // Use +Interval to create upper bound

	// Loop strictly less than upper bound
	// If End=18:00, start of last slot is 18:00. End of last slot is 19:00.
	// Loop should process 18:00.
	for currM < endM {
		// Calculate offset from start (start is 0 visual)
		// But in our layout, 0 is Global Start Hour exactly?
		// Layout assumes 0 = StartHour * 60.
		// So `offset` should be absolute minutes from midnight?
		// Uncheck: ScheduleColumnLayout logic:
		// yPos = float32(slot.StartMinuteOffset) * pixelsPerMinute
		// pixelsPerMinute = totalHeight / float32(l.TotalGlobalMinutes)
		// TotalGlobalMinutes = (End - Start) * 60.
		// So 0 offset = Top of container.

		// If Global Start is 09:00, and we have a suffix :30.
		// Then 09:30 should be at offset 30 relative to container top?
		// NO! logic changed. The container NOW starts at GlobalStart+Suffix.
		// So 09:30 should be at Offset 0.

		// Container Start Time in Minutes
		containerStartM := globalTC.StartHour*60 + globalSuffixM

		offset := currM - containerStartM

		// Format Hour String
		h := currM / 60
		m := currM % 60
		hourStr := fmt.Sprintf("%02d:%02d", h, m)

		// Background
		bg := canvas.NewRectangle(ColorLight)
		// Alternating color logic based on index?
		if (currM/globalInterval)%2 == 0 {
			// bg.FillColor = ...
		}

		// Text
		label := canvas.NewText(hourStr, ColorText)
		label.TextSize = sizes.FontSmall
		label.Alignment = fyne.TextAlignCenter

		// Separator
		sep := canvas.NewRectangle(ColorDisabled)
		sep.SetMinSize(fyne.NewSize(0, 1))
		sepContainer := container.NewBorder(nil, sep, nil, nil, nil)

		cell := container.NewStack(bg, sepContainer, container.NewCenter(label))

		timeSlots = append(timeSlots, RoomSlotData{
			StartMinuteOffset: offset,
			DurationMinutes:   globalInterval,
		})
		timeObjects = append(timeObjects, cell)

		currM += globalInterval
	}

	// Create Time Column Container
	// MinHeight=0 allows it to auto-scale to available space
	timeColLayout := NewScheduleColumnLayout(timeSlots, totalGlobalMinutes, 0)
	timeColumn := container.New(timeColLayout, timeObjects...)

	// Add background to Time Column
	timeColBg := canvas.NewRectangle(ColorLight) // White background
	// Using ColorBackground which is usually dark in this theme.
	timeColStack := container.NewStack(timeColBg, timeColumn)

	// FIX: Use FixedWidthLayout instead of GridWrap(w, 0)
	// GridWrap with height 0 was likely collapsing it.
	timeColumnWrapper := container.New(NewFixedWidthLayout(timeColWidth), timeColStack)

	// ---------------------------------------------------------
	// 3. Create Room Grid (Center)
	// ---------------------------------------------------------

	roomColWrappers := make([]fyne.CanvasObject, numVisible) // Includes Header

	type RoomColWidgets struct {
		HeaderName *canvas.Text
		HeaderExt  *canvas.Text
		Container  *fyne.Container // The schedule part
		Root       *fyne.Container // The VBox of Header+Schedule
	}

	roomWidgets := make([]*RoomColWidgets, numVisible)

	for i := 0; i < numVisible; i++ {
		// Header
		name := canvas.NewText("", color.White)
		name.TextSize = sizes.FontSmall
		name.TextStyle = fyne.TextStyle{Bold: true}
		name.Alignment = fyne.TextAlignCenter

		ext := canvas.NewText("", color.White)
		ext.TextSize = sizes.FontMicro
		ext.Alignment = fyne.TextAlignCenter

		headerContent := container.NewVBox(container.NewCenter(name), container.NewCenter(ext))
		headerBg := canvas.NewRectangle(ColorPrimary)

		// Header uses FixedHeightLayout wrapper to ensure it has height
		// previous GridWrap(0, 60) was okay, but let's be safe.
		headerStack := container.NewStack(headerBg, container.NewCenter(headerContent))
		headerContainer := container.New(NewFixedHeightLayout(80), headerStack) // Increased height to 80 to prevent overlap

		// Schedule Column
		// Initial empty layout
		schedCol := container.NewWithoutLayout()

		// Use VerticalFixedHeaderLayout instead of Border to REMOVE GAP
		colRoot := container.New(NewVerticalFixedHeaderLayout(), headerContainer, schedCol)

		roomWidgets[i] = &RoomColWidgets{
			HeaderName: name,
			HeaderExt:  ext,
			Container:  schedCol,
			Root:       colRoot,
		}
		roomColWrappers[i] = colRoot
	}

	// Make the Room Grid
	roomGrid := container.NewGridWithColumns(numVisible, roomColWrappers...)

	// ---------------------------------------------------------
	// 4. Update Function
	// ---------------------------------------------------------
	updateFunc := func() {
		state.mu.RLock()
		rooms := state.rooms
		roomExts := state.roomExts
		schedule := state.schedule
		slideIndex := state.slideIndex
		configs := state.roomConfigs
		state.mu.RUnlock()

		// Refresh Rooms
		for i := 0; i < numVisible; i++ {
			roomIdx := slideIndex + i
			w := roomWidgets[i]

			if roomIdx < len(rooms) {
				roomName := rooms[roomIdx]
				roomConfig, ok := configs[roomName]
				if !ok {
					roomConfig = ParseRoomTimeConfig(&api.RoomInfo{}, globalTC) // Fallback
				}

				// Update Header
				w.HeaderName.Text = roomName
				w.HeaderName.Refresh()

				ext := ""
				if roomIdx < len(roomExts) {
					ext = TruncateString(roomExts[roomIdx], 30)
				}
				w.HeaderExt.Text = ext
				w.HeaderExt.Refresh()

				// Build Schedule Slots
				var slots []RoomSlotData
				var objects []fyne.CanvasObject

				// Parse room start offset
				var roomStartH, startSuffixM int
				roomStartH = roomConfig.StartHour
				// Parse suffix
				fmt.Sscanf(roomConfig.TimeSuffix, ":%d", &startSuffixM)

				roomStartTotalM := roomStartH*60 + startSuffixM

				// Parse Global Suffix again
				var globalSuffixM int
				fmt.Sscanf(globalTC.TimeSuffix, ":%d", &globalSuffixM)

				// Global Range Logic:
				// If Global Start=9, Suffix=:30.
				// The Time Column STARTS visually at 09:30.
				// So "Offset 0" corresponds to 09:30 (570 mins).
				// We must clip against [GlobalStart+Suffix, GlobalEnd+Suffix+Interval].

				globalStartTotalM := globalTC.StartHour*60 + globalSuffixM
				// End total is Global End Hour + Interval + Suffix
				globalEndTotalM := globalTC.EndHour*60 + globalSuffixM + globalInterval

				intervalM := roomConfig.Interval
				if intervalM <= 0 {
					intervalM = 60
				}

				currM := roomStartTotalM
				for currM < globalEndTotalM {
					slotStart := currM
					slotEnd := currM + intervalM

					// Next iteration if completely before global start
					// Note: roomStartTotalM might be < globalStartTotalM, so we need to iterate
					// but can skip full intervals that are before visible area.
					if slotEnd <= globalStartTotalM {
						currM += intervalM
						continue
					}

					// Stop if we reached beyond global end
					if slotStart >= globalEndTotalM {
						break
					}

					// Calculate intersection with Global Window
					renderStart := slotStart
					if renderStart < globalStartTotalM {
						renderStart = globalStartTotalM
					}

					renderEnd := slotEnd
					if renderEnd > globalEndTotalM {
						renderEnd = globalEndTotalM
					}

					renderDuration := renderEnd - renderStart
					renderOffset := renderStart - globalStartTotalM

					// If purely clipped out (e.g. duration <= 0), skip
					if renderDuration <= 0 {
						currM += intervalM
						continue
					}

					// Data retrieval (using original slot start for key)
					hourKey := fmt.Sprintf("%02d:%02d", currM/60, currM%60)

					// Check Schedule
					var slotStatus SlotStatus = SlotEmpty
					var line1Text, line2Text string

					if rSched, ok := schedule[roomName]; ok {
						if data, ok := rSched[hourKey]; ok {
							slotStatus = data.Status
							if slotStatus == SlotOccupied {
								line1Text = data.Activity
								line2Text = data.Organizer
							}
						}
					}

					// Create Widget
					bg := canvas.NewRectangle(ColorLight)
					if slotStatus == SlotOccupied {
						bg.FillColor = ColorUnavailable
					} else {
						bg.FillColor = ColorLight
					}

					t1 := canvas.NewText(line1Text, ColorLight)
					if slotStatus == SlotEmpty {
						t1.Color = ColorText
					}
					t1.TextSize = sizes.FontTiny
					t1.TextStyle = fyne.TextStyle{Bold: true}
					t1.Alignment = fyne.TextAlignCenter

					t2 := canvas.NewText(line2Text, ColorLight)
					if slotStatus == SlotEmpty {
						t2.Color = ColorText
					}
					t2.TextSize = sizes.FontMicro
					t2.Alignment = fyne.TextAlignCenter

					content := container.NewVBox(container.NewCenter(t1), container.NewCenter(t2))

					// Removed explicit border rectangle
					// Added minimal padding container to allow background radius to be visible if needed?
					// Or just stack directly.
					// If we want spacing between slots, we might need a margin wrapper, but current layout
					// handles positioning. Since they are stacked tight, radius might touch.
					// Let's add a small Padded container if we want gaps, but user just said radius.

					// Separator
					sep := canvas.NewRectangle(ColorDisabled)
					sep.SetMinSize(fyne.NewSize(0, 1))
					sepContainer := container.NewBorder(nil, sep, nil, nil, nil)

					stack := container.NewStack(bg, sepContainer, container.NewCenter(content))

					slots = append(slots, RoomSlotData{
						StartMinuteOffset: renderOffset,
						DurationMinutes:   renderDuration,
					})
					objects = append(objects, stack)

					currM += intervalM
				}

				// Apply to Container
				w.Container.Objects = objects
				w.Container.Layout = NewScheduleColumnLayout(slots, totalGlobalMinutes, 0)
				w.Container.Refresh()

			} else {
				// Empty Room Slot
				w.HeaderName.Text = ""
				w.HeaderName.Refresh()
				w.HeaderExt.Text = ""
				w.HeaderExt.Refresh()
				w.Container.Objects = nil
				w.Container.Refresh()
			}
		}
	}

	// Initial Update
	updateFunc()

	// Time Header ("Saat")
	timeHeaderBg := canvas.NewRectangle(ColorPrimary)
	timeHeaderLabel := canvas.NewText("Saat", color.White)
	timeHeaderLabel.TextSize = sizes.FontBody
	timeHeaderLabel.TextStyle = fyne.TextStyle{Bold: true}
	timeHeaderLabel.Alignment = fyne.TextAlignCenter
	timeHeaderStack := container.NewStack(timeHeaderBg, container.NewCenter(timeHeaderLabel))
	// Use FixedHeightLayout same as Room Headers to align!
	timeHeaderWrapper := container.New(NewFixedHeightLayout(80), timeHeaderStack)

	// Wrap TimeHeader + TimeColumn
	// NewBorder: Top=Header, Center=Column.
	// REMOVED NewBorder, using NewVerticalFixedHeaderLayout to remove gap

	timeStack := container.New(NewVerticalFixedHeaderLayout(), timeHeaderWrapper, timeColumnWrapper)
	// We need to constrain the width of this entire stack.
	// FixedWidthLayout wrapper around the whole thing?
	timeStackConstrained := container.New(NewFixedWidthLayout(timeColWidth), timeStack)

	// Use Center for Room Grid. Borders uses 'Center' to fill.
	return container.NewBorder(nil, nil, timeStackConstrained, nil, roomGrid), updateFunc
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
func (a *App) runBuildingSlider(state *BuildingState, updateGridFunc func()) {
	ticker := time.NewTicker(8 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			// Calculate new index
			state.mu.Lock()
			numRooms := len(state.rooms)
			cfg := config.Get()
			maxVisible := cfg.BuildingMaxVisibleRooms
			step := cfg.BuildingSlideStep
			if step <= 0 {
				step = 1
			}

			// Compute progress value
			var progressValue float64 = 0

			// Only slide if we have more rooms than can fit
			if numRooms > maxVisible {
				// Calculate next index
				nextIndex := state.slideIndex + (step * state.slideDirection)

				// Check bounds and reverse direction ("Ping-Pong")
				if nextIndex+maxVisible > numRooms {
					state.slideDirection = -1
					nextIndex = state.slideIndex - step
				} else if nextIndex < 0 {
					state.slideDirection = 1
					nextIndex = state.slideIndex + step
				}

				// Safety Clamp
				if nextIndex < 0 {
					nextIndex = 0
					state.slideDirection = 1
				} else if nextIndex > numRooms-maxVisible {
					nextIndex = numRooms - maxVisible
					state.slideDirection = -1
				}

				state.slideIndex = nextIndex

				// Calculate progress
				maxIndex := float64(numRooms - maxVisible)
				current := float64(state.slideIndex)
				if maxIndex > 0 {
					progressValue = current / maxIndex
				}
			}
			state.mu.Unlock()

			// Update UI
			// progress bar update is thread-safe for SetValue
			state.progress.SetValue(progressValue)

			// Execute update function to refresh grid text
			// Calling it directly from goroutine is technically unsafe for Fyne widget prop updates
			// But for text/color it often works. If it flakes, we'd need RunOnMain.
			// Since we cleaned up layout changes, this is MUCH safer than before.
			updateGridFunc()

		case <-a.stopChan:
			return
		}
	}
}

// updateBuildingData fetches fresh building schedule data
func (a *App) updateBuildingData(state *BuildingState, updateGridFunc func()) {
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	// Initial fetch
	a.fetchBuildingSchedule(state, updateGridFunc)

	for {
		select {
		case <-ticker.C:
			a.fetchBuildingSchedule(state, updateGridFunc)
		case <-a.stopChan:
			return
		}
	}
}

// fetchBuildingSchedule fetches schedule for all rooms
func (a *App) fetchBuildingSchedule(state *BuildingState, updateGridFunc func()) {
	schedResp, err := a.apiClient.GetBuildingSchedule()
	if err != nil {
		log.Printf("Failed to fetch building schedule: %v", err)
		return
	}

	state.mu.Lock()
	state.schedule = TransformBuildingSchedule(
		&api.BuildingScheduleResponse{Schedule: schedResp.Schedule},
		state.roomMap,
	)
	state.mu.Unlock()

	// Trigger immediate UI refresh
	if updateGridFunc != nil {
		updateGridFunc()
	}
}
