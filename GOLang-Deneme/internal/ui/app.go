// Package ui - Main application setup and mode dispatcher
package ui

import (
	"image"
	"image/color"
	_ "image/jpeg"
	_ "image/png"
	"log"
	"math"
	"net/http"
	"runtime/debug"
	"strings"
	"sync"
	"time"

	"fyne.io/fyne/v2"
	"fyne.io/fyne/v2/app"
	"fyne.io/fyne/v2/canvas"
	"fyne.io/fyne/v2/container"

	"kiosk-go/assets"
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
	timeConfig  TimeConfig
	roomName    string
	schedule    Schedule
	roomDetails *api.RoomDetailsResponse
	lockStatus  string
	qrSize      int // Responsive QR code size (calculated from window dimensions)
	mu          sync.RWMutex

	// Update channels
	updateChan chan struct{}
	stopChan   chan struct{}

	// Notification system
	notifyMgr      *NotificationManager
	notifyText     *canvas.Text // In-app notification label
	lockStatusText *canvas.Text // Lock status in footer center
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
		qrGen:      qr.NewGenerator(ColorPrimary, assets.LogoData),
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

	// Fetch initial configuration (skip for BUILDING mode - it handles its own config)
	if a.cfg.Mode != config.ModeBuilding {
		a.fetchTimeConfig()
	}

	// Build UI based on mode
	content := a.buildModeUI()

	// Apply edge padding if configured (CSS-like padding around entire app)
	if a.cfg.EdgePadding.HasPadding() {
		p := a.cfg.EdgePadding
		content = container.New(&edgePaddingLayout{
			top:    float32(p.Top),
			right:  float32(p.Right),
			bottom: float32(p.Bottom),
			left:   float32(p.Left),
		}, content)
	}

	a.window.SetContent(content)

	// Start background update loops
	go a.startUpdateLoop()

	// Set memory limit to 150MB - Go's GC will trigger automatically when approaching limit
	debug.SetMemoryLimit(150 * 1024 * 1024)

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
}

// buildModeUI creates the appropriate UI based on the configured mode
func (a *App) buildModeUI() fyne.CanvasObject {
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

	ticker := time.NewTicker(1 * time.Minute)
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

	// Fetch room details (owners) for STANDARD and OFFICE modes
	// Fetch room details (owners) for STANDARD and OFFICE modes
	if a.cfg.Mode == config.ModeStandard || a.cfg.Mode == config.ModeOffice {
		details, err := a.apiClient.GetRoomDetails()
		if err != nil {
			log.Printf("Failed to fetch room details: %v", err)
		} else {
			a.mu.Lock()
			a.roomDetails = details
			a.roomName = details.RoomName
			a.mu.Unlock()
		}
	}

	// Fetch schedule (ONLY if not in Building mode)
	// Building mode handles its own schedule fetching independently
	if a.cfg.Mode != config.ModeBuilding {

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

		schedule := TransformSchedule(schedResp, dateKeys, a.timeConfig)

		a.mu.Lock()
		a.schedule = schedule
		a.mu.Unlock()
	}

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

// GetRoomDetails returns the current room details (thread-safe)
func (a *App) GetRoomDetails() *api.RoomDetailsResponse {
	a.mu.RLock()
	defer a.mu.RUnlock()
	return a.roomDetails
}

// SetLockStatus sets the lock status text (thread-safe)
func (a *App) SetLockStatus(status string) {
	a.mu.Lock()
	a.lockStatus = status
	a.mu.Unlock()
	// Update UI if lockStatusText is set
	if a.lockStatusText != nil {
		a.lockStatusText.Text = status
		a.lockStatusText.Refresh()
	}
}

// Notify shows a notification to the user
func (a *App) Notify(message, textColor string, duration time.Duration) {
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

// createFooter builds the common footer component with responsive sizing
func (a *App) createFooter() fyne.CanvasObject {
	// Calculate responsive sizes
	sizes := CalculateResponsiveSizes(a.window.Canvas().Size())
	footerBg := canvas.NewRectangle(ColorPrimary)
	footerBg.SetMinSize(fyne.NewSize(0, sizes.FooterHeight))

	infoText := canvas.NewText("pve.izu.edu.tr/randevu ← Randevu İçin", color.White)
	infoText.TextSize = sizes.FontTitle
	infoText.TextStyle = fyne.TextStyle{Bold: true}

	// Lock status text in center with green text and bigger font
	lockText := canvas.NewText("", ColorSuccess)
	lockText.TextSize = sizes.FontNotify // Bigger font
	lockText.TextStyle = fyne.TextStyle{Bold: true}
	lockText.Alignment = fyne.TextAlignCenter
	a.lockStatusText = lockText // Store reference for updates

	clockText := canvas.NewText("", color.White)
	clockText.TextSize = sizes.FontTitle
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
		lockText, // Center: lock status
	)
	return container.NewStack(footerBg, footerContent)
}

// getImageURL builds the full image URL from a path
func (a *App) getImageURL(path string) string {
	if path == "" {
		return ""
	}
	if strings.HasPrefix(path, "http") {
		return path
	}
	return a.cfg.APIBaseURL + path
}

// loadImageFromURL loads an image from URL and returns it as a circular canvas.Image
func (a *App) loadImageFromURL(url string, size float32) *canvas.Image {
	resp, err := http.Get(url)
	if err != nil {
		return nil
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil
	}

	img, _, err := image.Decode(resp.Body)
	if err != nil {
		return nil
	}

	// Create circular cropped image
	circularImg := a.createCircularImage(img, int(size))

	canvasImg := canvas.NewImageFromImage(circularImg)
	canvasImg.FillMode = canvas.ImageFillContain
	canvasImg.SetMinSize(fyne.NewSize(size, size))
	return canvasImg
}

// createCircularImage crops an image to a circle
func (a *App) createCircularImage(src image.Image, size int) image.Image {
	// Create a new RGBA image with the desired size
	dst := image.NewRGBA(image.Rect(0, 0, size, size))

	// Get source bounds and scale
	srcBounds := src.Bounds()
	srcW := srcBounds.Dx()
	srcH := srcBounds.Dy()

	// Calculate center and radius
	centerX := float64(size) / 2
	centerY := float64(size) / 2
	radius := float64(size) / 2

	// Draw the source image scaled to fit, with circular mask
	for y := 0; y < size; y++ {
		for x := 0; x < size; x++ {
			// Check if point is inside circle
			dx := float64(x) - centerX + 0.5
			dy := float64(y) - centerY + 0.5
			distance := math.Sqrt(dx*dx + dy*dy)

			if distance <= radius {
				// Map to source image coordinates
				srcX := int(float64(x) * float64(srcW) / float64(size))
				srcY := int(float64(y) * float64(srcH) / float64(size))

				if srcX >= srcW {
					srcX = srcW - 1
				}
				if srcY >= srcH {
					srcY = srcH - 1
				}

				dst.Set(x, y, src.At(srcBounds.Min.X+srcX, srcBounds.Min.Y+srcY))
			}
			// Outside circle remains transparent (zero value)
		}
	}

	return dst
}

// createOccupantPhotoContainer creates a circular photo container for an occupant
func (a *App) createOccupantPhotoContainer(occupant api.Occupant, photoSize float32, initialFontSize float32) fyne.CanvasObject {
	// Background circle
	photoBg := canvas.NewRectangle(ColorPrimary)
	photoBg.SetMinSize(fyne.NewSize(photoSize, photoSize))
	photoBg.CornerRadius = photoSize / 2

	// Try to load actual photo if available
	photoURL := a.getImageURL(occupant.Photo)
	if photoURL != "" {
		if img := a.loadImageFromURL(photoURL, photoSize); img != nil {
			// Create circular mask effect by stacking with round container
			return container.NewStack(photoBg, container.NewCenter(img))
		}
	}

	// Fallback to initial letter
	var initial string
	if len(occupant.Name) > 0 {
		initial = string([]rune(occupant.Name)[0])
	}
	photoInitial := canvas.NewText(initial, color.White)
	photoInitial.TextSize = initialFontSize
	photoInitial.TextStyle = fyne.TextStyle{Bold: true}
	photoInitial.Alignment = fyne.TextAlignCenter

	return container.NewStack(photoBg, container.NewCenter(photoInitial))
}

// updateOccupantCarousel updates the occupant carousel display (compact version)
func (a *App) updateOccupantCarousel(carouselContainer *fyne.Container, index int, sizes ResponsiveSizes) {
	details := a.GetRoomDetails()
	if details == nil || len(details.Occupants) == 0 {
		carouselContainer.Objects = nil
		carouselContainer.Refresh()
		return
	}

	// Get current occupant
	occupant := details.Occupants[index%len(details.Occupants)]

	// Photo container (smaller circle)
	photoSize := sizes.HeaderHeight * 0.8
	photoContainer := a.createOccupantPhotoContainer(occupant, photoSize, sizes.FontSmall)

	// Name and surname (smaller font)
	nameText := canvas.NewText(occupant.Name+" "+occupant.Surname, ColorText)
	nameText.TextSize = sizes.FontSmall
	nameText.TextStyle = fyne.TextStyle{Bold: true}
	nameText.Alignment = fyne.TextAlignCenter

	// Occupant count indicator (dots style)
	var countWidget fyne.CanvasObject
	if len(details.Occupants) > 1 {
		dots := ""
		for i := 0; i < len(details.Occupants); i++ {
			if i == index%len(details.Occupants) {
				dots += "●"
			} else {
				dots += "○"
			}
		}
		countText := canvas.NewText(dots, ColorDark)
		countText.TextSize = sizes.FontMicro
		countText.Alignment = fyne.TextAlignCenter
		countWidget = container.NewCenter(countText)
	} else {
		countWidget = container.NewVBox()
	}

	// Assemble compact card (horizontal layout)
	card := container.NewHBox(
		photoContainer,
		container.NewVBox(
			nameText,
			countWidget,
		),
	)

	carouselContainer.Objects = []fyne.CanvasObject{container.NewCenter(card)}
	carouselContainer.Refresh()
}

// createScheduleGrid builds the schedule grid component with responsive sizing
// Rows are responsive - they fill the available screen height
// Time column is narrow, day columns fill remaining space
func (a *App) createScheduleGrid(days []DayInfo, fullWidth bool) fyne.CanvasObject {
	hours := a.timeConfig.GenerateHours()
	sizes := CalculateResponsiveSizes(a.window.Canvas().Size())

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
	// Use configurable-gap vertical layout (0.001 = 0.1% of height between rows)
	dayGrid := container.New(&gapVBoxLayout{gapRatio: 0.01}, dayRows...)

	// Combine time column (narrow, fixed) with day grid (fills rest)
	// Using Border layout to avoid visible divider
	// Wrap time column in a container with max width
	// Use same gap layout for time column too
	timeColumn = container.New(&gapVBoxLayout{gapRatio: 0.01}, timeColumnCells...)
	timeColumnWrapper := container.New(&fixedWidthLayout{width: sizes.TimeColWidth}, timeColumn)

	return container.NewBorder(
		nil, nil, // top, bottom
		timeColumnWrapper, // left: fixed width time column
		nil,
		dayGrid, // center: fills remaining space
	)
}

// createTightVBox creates a vertical box with tight, custom spacing
// Used for text lines that need to be closer than standard theme padding
func (a *App) createTightVBox(gap float32, objects ...fyne.CanvasObject) *fyne.Container {
	return container.New(&tightVBoxLayout{gap: gap}, objects...)
}

// tightVBoxLayout implements a vertical layout with custom gap
type tightVBoxLayout struct {
	gap float32
}

func (l *tightVBoxLayout) Layout(objs []fyne.CanvasObject, size fyne.Size) {
	y := float32(0)
	for _, o := range objs {
		o.Resize(o.MinSize())
		// Center horizontally
		x := (size.Width - o.MinSize().Width) / 2
		o.Move(fyne.NewPos(x, y))
		y += o.MinSize().Height + l.gap
	}
}

func (l *tightVBoxLayout) MinSize(objs []fyne.CanvasObject) fyne.Size {
	w, h := float32(0), float32(0)
	for i, o := range objs {
		childSize := o.MinSize()
		if childSize.Width > w {
			w = childSize.Width
		}
		h += childSize.Height
		if i < len(objs)-1 {
			h += l.gap
		}
	}
	return fyne.NewSize(w, h)
}

// gapVBoxLayout implements a vertical layout with configurable gap ratio
// gapRatio is a fraction of total height used as gap between rows (e.g., 0.001 = 0.1%)
type gapVBoxLayout struct {
	gapRatio float32
}

func (l *gapVBoxLayout) Layout(objs []fyne.CanvasObject, size fyne.Size) {
	if len(objs) == 0 {
		return
	}
	y := float32(0)
	// Calculate gap based on ratio of total height
	gap := size.Height * l.gapRatio
	totalGap := gap * float32(len(objs)-1)
	rowHeight := (size.Height - totalGap) / float32(len(objs))
	for i, o := range objs {
		o.Resize(fyne.NewSize(size.Width, rowHeight))
		o.Move(fyne.NewPos(0, y))
		y += rowHeight
		if i < len(objs)-1 {
			y += gap
		}
	}
}

func (l *gapVBoxLayout) MinSize(objs []fyne.CanvasObject) fyne.Size {
	h := float32(0)
	w := float32(0)
	for _, o := range objs {
		childSize := o.MinSize()
		if childSize.Width > w {
			w = childSize.Width
		}
		h += childSize.Height
	}
	return fyne.NewSize(w, h)
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

// createHeaderCell creates a header cell with text using responsive sizing
func (a *App) createHeaderCell(text string, bgColor color.Color) fyne.CanvasObject {
	sizes := CalculateResponsiveSizes(a.window.Canvas().Size())

	bg := canvas.NewRectangle(bgColor)
	bg.SetMinSize(fyne.NewSize(0, sizes.HeaderHeight))

	label := canvas.NewText(text, color.White)
	label.TextSize = sizes.FontSubtitle
	label.TextStyle = fyne.TextStyle{Bold: true}
	label.Alignment = fyne.TextAlignCenter

	return container.NewStack(bg, container.NewCenter(label))
}

// createDayHeaderCell creates a day header cell with responsive sizing
func (a *App) createDayHeaderCell(day DayInfo) fyne.CanvasObject {
	sizes := CalculateResponsiveSizes(a.window.Canvas().Size())
	bgColor := ColorPrimary
	fgColor := ColorLight
	if day.IsToday {
		bgColor = ColorAvailable
		fgColor = ColorDark
	}
	bg := canvas.NewRectangle(bgColor)
	bg.SetMinSize(fyne.NewSize(0, sizes.HeaderHeight))
	dayLabel := canvas.NewText(day.DayNameTR, fgColor)
	dayLabel.TextSize = sizes.FontBody
	dayLabel.TextStyle = fyne.TextStyle{Bold: true}
	dayLabel.Alignment = fyne.TextAlignCenter
	dateLabel := canvas.NewText(day.DisplayDate, fgColor)
	dateLabel.TextSize = sizes.FontTiny
	dateLabel.Alignment = fyne.TextAlignCenter
	// Use tight VBox for closer line spacing
	// Gap is InnerPadding (approx 4px) which is half of standard padding
	content := a.createTightVBox(sizes.InnerPadding, dayLabel, dateLabel)
	if day.IsToday {
		todayLabel := canvas.NewText("Bugün", fgColor)
		todayLabel.TextSize = sizes.FontMicro
		todayLabel.Alignment = fyne.TextAlignCenter
		content.Add(todayLabel)
	}
	return container.NewStack(bg, container.NewCenter(content))
}

// createHourCell creates an hour label cell with responsive sizing
func (a *App) createHourCell(hour string) fyne.CanvasObject {
	sizes := CalculateResponsiveSizes(a.window.Canvas().Size())

	currentHour := GetCurrentHourString(a.timeConfig)
	bgColor := ColorLight
	fgColor := ColorText
	if hour == currentHour {
		bgColor = ColorHighlight
		fgColor = ColorDark
	}

	bg := canvas.NewRectangle(bgColor)
	bg.SetMinSize(fyne.NewSize(sizes.TimeColWidth, sizes.CellHeight))

	label := canvas.NewText(hour, fgColor)
	label.TextSize = sizes.FontSmall
	label.Alignment = fyne.TextAlignCenter

	return container.NewStack(bg, container.NewCenter(label))
}

// createScheduleCell creates a schedule cell for a specific day/hour with responsive sizing
func (a *App) createScheduleCell(day DayInfo, hour string) fyne.CanvasObject {
	sizes := CalculateResponsiveSizes(a.window.Canvas().Size())
	schedule := a.GetSchedule()

	bgColor := ColorAvailable
	fgColor := ColorLight
	isOccupied := false
	var line1, line2 string

	if daySchedule, ok := schedule[day.DateKey]; ok {
		if slot, ok := daySchedule[hour]; ok && slot.Status == SlotOccupied {
			isOccupied = true
			bgColor = ColorUnavailable
			line1 = TruncateString(slot.Activity, 14)
			line2 = TruncateString(slot.Organizer, 14)
		}
	}

	bg := canvas.NewRectangle(bgColor)
	bg.SetMinSize(fyne.NewSize(0, sizes.CellHeight))

	var content fyne.CanvasObject
	if isOccupied {
		// Occupied: show activity + organizer
		label1 := canvas.NewText(line1, fgColor)
		label1.TextSize = sizes.FontTiny
		label1.TextStyle = fyne.TextStyle{Bold: true}
		label1.Alignment = fyne.TextAlignCenter

		label2 := canvas.NewText(line2, fgColor)
		label2.TextSize = sizes.FontMicro
		label2.Alignment = fyne.TextAlignCenter

		content = a.createTightVBox(sizes.InnerPadding, label1, label2)
	} else {
		// Empty: show only "Uygun" with bigger font
		label := canvas.NewText("Uygun", fgColor)
		label.TextSize = sizes.FontBody
		label.TextStyle = fyne.TextStyle{Bold: true}
		label.Alignment = fyne.TextAlignCenter
		content = label
	}

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

// edgePaddingLayout applies CSS-like padding around all edges of content
// Supports different values for top, right, bottom, left
type edgePaddingLayout struct {
	top, right, bottom, left float32
}

func (l *edgePaddingLayout) Layout(objects []fyne.CanvasObject, size fyne.Size) {
	for _, o := range objects {
		// Position content with left/top padding offset
		o.Move(fyne.NewPos(l.left, l.top))
		// Resize to available space minus padding on all sides
		o.Resize(fyne.NewSize(size.Width-l.left-l.right, size.Height-l.top-l.bottom))
	}
}

func (l *edgePaddingLayout) MinSize(objects []fyne.CanvasObject) fyne.Size {
	if len(objects) == 0 {
		return fyne.NewSize(l.left+l.right, l.top+l.bottom)
	}
	childMin := objects[0].MinSize()
	return fyne.NewSize(childMin.Width+l.left+l.right, childMin.Height+l.top+l.bottom)
}
