// Package ui - Main application setup and mode dispatcher
package ui

import (
	"image/color"
	"log"
	"sync"
	"time"

	"fyne.io/fyne/v2"
	"fyne.io/fyne/v2/app"
	"fyne.io/fyne/v2/canvas"
	"fyne.io/fyne/v2/container"

	"kiosk-go/internal/api"
	"kiosk-go/internal/config"
	"kiosk-go/internal/qr"
)

// App represents the main kiosk application
type App struct {
	fyneApp   fyne.App
	window    fyne.Window
	cfg       *config.Config
	apiClient *api.Client
	qrGen     *qr.Generator

	// UI state
	timeConfig TimeConfig
	roomName   string
	schedule   Schedule
	mu         sync.RWMutex

	// Update channels
	updateChan chan struct{}
	stopChan   chan struct{}

	// Notification system
	notifyMgr  *NotificationManager
	notifyText *canvas.Text // In-app notification label
}

// NewApp creates a new kiosk application
func NewApp(cfg *config.Config) *App {
	fyneApp := app.NewWithID("tr.edu.izu.kiosk")
	fyneApp.Settings().SetTheme(NewKioskTheme())

	window := fyneApp.NewWindow("Oda Rezervasyon Sistemi")

	a := &App{
		fyneApp:    fyneApp,
		window:     window,
		cfg:        cfg,
		apiClient:  api.NewClient(cfg),
		qrGen:      qr.NewGenerator(ColorPrimary, "assets/logo.png"),
		timeConfig: DefaultTimeConfig(),
		updateChan: make(chan struct{}, 1),
		stopChan:   make(chan struct{}),
	}

	// Initialize notification manager
	a.notifyMgr = NewNotificationManager(window)

	return a
}

// Run starts the application
func (a *App) Run() {
	// Setup fullscreen kiosk mode
	a.setupWindow()

	// Fetch initial configuration
	a.fetchTimeConfig()

	// Build UI based on mode
	content := a.buildModeUI()
	a.window.SetContent(content)

	// Start background update loops
	go a.startUpdateLoop()

	// Show and run
	a.window.ShowAndRun()

	// Cleanup
	close(a.stopChan)
}

// setupWindow configures the window for kiosk mode
func (a *App) setupWindow() {
	a.window.SetFullScreen(true)
	a.window.SetPadded(false)

	// Escape key to quit (for development)
	a.window.Canvas().SetOnTypedKey(func(ke *fyne.KeyEvent) {
		if ke.Name == fyne.KeyEscape {
			log.Println("Escape pressed, quitting...")
			a.fyneApp.Quit()
		}
	})
}

// Notify displays a notification message on screen
// This method is called by external handlers like the lock handler

// fetchTimeConfig fetches time format configuration from API
func (a *App) fetchTimeConfig() {
	configs, err := a.apiClient.GetIndexesRasp()
	if err != nil {
		log.Printf("Failed to fetch time config: %v", err)
		return
	}
	a.timeConfig = ParseTimeConfig(configs)
	log.Printf("Time config loaded: suffix=%s, hours=%d-%d",
		a.timeConfig.TimeSuffix, a.timeConfig.StartHour, a.timeConfig.EndHour)
}

// buildModeUI creates the appropriate UI based on the configured mode
func (a *App) buildModeUI() fyne.CanvasObject {
	log.Printf("Building UI for mode: %s", a.cfg.Mode)

	switch a.cfg.Mode {
	case config.ModeOffice:
		return a.buildOfficeUI()
	case config.ModeBuilding:
		return a.buildBuildingUI()
	default:
		return a.buildStandardUI()
	}
}

// startUpdateLoop runs periodic updates in the background
func (a *App) startUpdateLoop() {
	// Initial update
	a.updateData()

	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			a.updateData()
		case <-a.stopChan:
			return
		}
	}
}

// updateData fetches fresh data from the API
func (a *App) updateData() {
	log.Println("Updating data...")

	// Fetch room name and QR token for STANDARD mode
	if a.cfg.Mode == config.ModeStandard {
		qrResp, err := a.apiClient.GetQRCodeToken(true)
		if err == nil {
			a.mu.Lock()
			a.roomName = qrResp.RoomName
			a.mu.Unlock()
		}
	}

	// Fetch schedule
	schedResp, err := a.apiClient.GetSchedule()
	if err != nil {
		log.Printf("Failed to fetch schedule: %v", err)
		return
	}

	// Get date keys
	var dateKeys []string
	if a.cfg.Mode == config.ModeOffice {
		days := GenerateWeekDays()
		for _, d := range days {
			dateKeys = append(dateKeys, d.DateKey)
		}
	} else {
		days := GenerateDisplayDays()
		for _, d := range days {
			dateKeys = append(dateKeys, d.DateKey)
		}
	}

	// Transform schedule
	schedule := TransformSchedule(schedResp, dateKeys, a.timeConfig)
	a.mu.Lock()
	a.schedule = schedule
	a.mu.Unlock()

	// Signal UI update
	select {
	case a.updateChan <- struct{}{}:
	default:
	}
}

// GetSchedule returns the current schedule (thread-safe)
func (a *App) GetSchedule() Schedule {
	a.mu.RLock()
	defer a.mu.RUnlock()
	return a.schedule
}

// GetRoomName returns the current room name (thread-safe)
func (a *App) GetRoomName() string {
	a.mu.RLock()
	defer a.mu.RUnlock()
	return a.roomName
}

// Notify shows a notification to the user
func (a *App) Notify(message, textColor string, duration time.Duration) {
	log.Printf("NOTIFY: %s (color: %s, duration: %v)", message, textColor, duration)

	// Update in-app notification text
	if a.notifyText != nil {
		switch textColor {
		case "green":
			a.notifyText.Color = ColorAvailable
		case "red":
			a.notifyText.Color = ColorUnavailable
		default:
			a.notifyText.Color = ColorPrimary
		}
		a.notifyText.Text = message
		a.notifyText.Refresh()

		// Auto-hide after duration
		if duration > 0 {
			go func() {
				time.Sleep(duration)
				a.notifyText.Text = ""
				a.notifyText.Refresh()
			}()
		}
	}
}

// createFooter builds the common footer component
func (a *App) createFooter() fyne.CanvasObject {
	footerBg := canvas.NewRectangle(ColorPrimary)
	footerBg.SetMinSize(fyne.NewSize(0, 60))

	infoText := canvas.NewText("pve.izu.edu.tr/randevu ← Randevu İçin", color.White)
	infoText.TextSize = 20
	infoText.TextStyle = fyne.TextStyle{Bold: true}

	clockText := canvas.NewText("", color.White)
	clockText.TextSize = 20
	clockText.TextStyle = fyne.TextStyle{Bold: true}
	clockText.Alignment = fyne.TextAlignTrailing

	// Update clock every second
	go func() {
		for {
			select {
			case <-a.stopChan:
				return
			default:
				now := time.Now()
				clockText.Text = now.Format("⏰ 02.01.2006  •  15:04:05")
				clockText.Refresh()
				time.Sleep(time.Second)
			}
		}
	}()

	footerContent := container.NewBorder(
		nil, nil,
		container.NewPadded(infoText),
		container.NewPadded(clockText),
	)

	return container.NewStack(footerBg, footerContent)
}

// createScheduleGrid builds the schedule grid component
// Rows are responsive - they fill the available screen height
// Time column is narrow, day columns fill remaining space
func (a *App) createScheduleGrid(days []DayInfo, fullWidth bool) fyne.CanvasObject {
	hours := a.timeConfig.GenerateHours()

	// Build time column (header + hour labels)
	timeColumnCells := []fyne.CanvasObject{a.createHeaderCell("Saat", ColorPrimary)}
	for _, hour := range hours {
		timeColumnCells = append(timeColumnCells, a.createHourCell(hour))
	}
	timeColumn := container.NewGridWithRows(len(timeColumnCells), timeColumnCells...)

	// Build day columns grid
	dayRows := make([]fyne.CanvasObject, 0, len(hours)+1)

	// Header row for days
	dayHeaderCells := make([]fyne.CanvasObject, 0, len(days))
	for _, day := range days {
		dayHeaderCells = append(dayHeaderCells, a.createDayHeaderCell(day))
	}
	dayRows = append(dayRows, container.NewGridWithColumns(len(days), dayHeaderCells...))

	// Data rows for days
	for _, hour := range hours {
		dayCells := make([]fyne.CanvasObject, 0, len(days))
		for _, day := range days {
			dayCells = append(dayCells, a.createScheduleCell(day, hour))
		}
		dayRows = append(dayRows, container.NewGridWithColumns(len(days), dayCells...))
	}
	dayGrid := container.NewGridWithRows(len(dayRows), dayRows...)

	// Combine time column (narrow, fixed) with day grid (fills rest)
	// Using Border layout to avoid visible divider
	// Wrap time column in a container with max width
	timeColumnWrapper := container.New(&fixedWidthLayout{width: 60}, timeColumn)

	return container.NewBorder(
		nil, nil, // top, bottom
		timeColumnWrapper, // left: fixed 60px time column
		nil,
		dayGrid, // center: fills remaining space
	)
}

// fixedWidthLayout is a custom layout that fixes width but fills height
type fixedWidthLayout struct {
	width float32
}

func (l *fixedWidthLayout) MinSize(objects []fyne.CanvasObject) fyne.Size {
	if len(objects) == 0 {
		return fyne.NewSize(l.width, 0)
	}
	return fyne.NewSize(l.width, objects[0].MinSize().Height)
}

func (l *fixedWidthLayout) Layout(objects []fyne.CanvasObject, size fyne.Size) {
	for _, o := range objects {
		o.Resize(fyne.NewSize(l.width, size.Height))
		o.Move(fyne.NewPos(0, 0))
	}
}

// createHeaderCell creates a header cell with text
func (a *App) createHeaderCell(text string, bgColor color.Color) fyne.CanvasObject {
	bg := canvas.NewRectangle(bgColor)
	bg.SetMinSize(fyne.NewSize(0, 50))

	label := canvas.NewText(text, color.White)
	label.TextSize = 18
	label.TextStyle = fyne.TextStyle{Bold: true}
	label.Alignment = fyne.TextAlignCenter

	return container.NewStack(bg, container.NewCenter(label))
}

// createDayHeaderCell creates a day header cell
func (a *App) createDayHeaderCell(day DayInfo) fyne.CanvasObject {
	bgColor := ColorPrimary
	fgColor := ColorLight
	if day.IsToday {
		bgColor = ColorAvailable
		fgColor = ColorDark
	}

	bg := canvas.NewRectangle(bgColor)
	bg.SetMinSize(fyne.NewSize(0, 50))

	dayLabel := canvas.NewText(day.DayNameTR, fgColor)
	dayLabel.TextSize = 16
	dayLabel.TextStyle = fyne.TextStyle{Bold: true}
	dayLabel.Alignment = fyne.TextAlignCenter

	dateLabel := canvas.NewText(day.DisplayDate, fgColor)
	dateLabel.TextSize = 12
	dateLabel.Alignment = fyne.TextAlignCenter

	content := container.NewVBox(
		container.NewCenter(dayLabel),
		container.NewCenter(dateLabel),
	)

	if day.IsToday {
		todayLabel := canvas.NewText("Bugün", fgColor)
		todayLabel.TextSize = 10
		todayLabel.Alignment = fyne.TextAlignCenter
		content.Add(container.NewCenter(todayLabel))
	}

	return container.NewStack(bg, container.NewCenter(content))
}

// createHourCell creates an hour label cell
func (a *App) createHourCell(hour string) fyne.CanvasObject {
	currentHour := GetCurrentHourString(a.timeConfig)
	bgColor := ColorLight
	fgColor := ColorText
	if hour == currentHour {
		bgColor = ColorHighlight
		fgColor = ColorDark
	}

	bg := canvas.NewRectangle(bgColor)
	bg.SetMinSize(fyne.NewSize(60, 40))

	label := canvas.NewText(hour, fgColor)
	label.TextSize = 14
	label.Alignment = fyne.TextAlignCenter

	return container.NewStack(bg, container.NewCenter(label))
}

// createScheduleCell creates a schedule cell for a specific day/hour
func (a *App) createScheduleCell(day DayInfo, hour string) fyne.CanvasObject {
	schedule := a.GetSchedule()

	bgColor := ColorAvailable
	fgColor := ColorLight
	line1 := "Randevuya"
	line2 := "Uygun"

	if daySchedule, ok := schedule[day.DateKey]; ok {
		if slot, ok := daySchedule[hour]; ok && slot.Status == SlotOccupied {
			bgColor = ColorUnavailable
			line1 = TruncateString(slot.Activity, 14)
			line2 = TruncateString(slot.Organizer, 14)
		}
	}

	bg := canvas.NewRectangle(bgColor)
	bg.SetMinSize(fyne.NewSize(0, 40))

	label1 := canvas.NewText(line1, fgColor)
	label1.TextSize = 12
	label1.TextStyle = fyne.TextStyle{Bold: true}
	label1.Alignment = fyne.TextAlignCenter

	label2 := canvas.NewText(line2, fgColor)
	label2.TextSize = 10
	label2.Alignment = fyne.TextAlignCenter

	content := container.NewVBox(
		container.NewCenter(label1),
		container.NewCenter(label2),
	)

	// Highlight current slot
	currentHour := GetCurrentHourString(a.timeConfig)
	if day.IsToday && hour == currentHour {
		border := canvas.NewRectangle(color.Transparent)
		border.StrokeColor = ColorHighlight
		border.StrokeWidth = 3
		return container.NewStack(bg, border, container.NewCenter(content))
	}

	return container.NewStack(bg, container.NewCenter(content))
}
