// Package ui - Notification overlay system
package ui

import (
	"sync"
	"time"

	"fyne.io/fyne/v2"
	"fyne.io/fyne/v2/canvas"
	"fyne.io/fyne/v2/container"
	"fyne.io/fyne/v2/widget"
)

// NotificationManager handles overlay notifications
type NotificationManager struct {
	window      fyne.Window
	overlay     *fyne.Container
	currentText *canvas.Text
	mu          sync.Mutex
	hideTimer   *time.Timer
	visible     bool
}

// NewNotificationManager creates a new notification manager
func NewNotificationManager(window fyne.Window) *NotificationManager {
	nm := &NotificationManager{
		window: window,
	}
	nm.createOverlay()
	return nm
}

// createOverlay initializes the notification overlay
// Note: Uses default sizes as overlay is created before window is shown
func (nm *NotificationManager) createOverlay() {
	nm.currentText = canvas.NewText("", ColorText)
	// Default size - will be updated based on window size when shown
	nm.currentText.TextSize = 40
	nm.currentText.TextStyle = fyne.TextStyle{Bold: true}
	nm.currentText.Alignment = fyne.TextAlignCenter

	bg := canvas.NewRectangle(ColorLight)
	// Default min size - notification will scale with content
	bg.SetMinSize(fyne.NewSize(400, 100))

	nm.overlay = container.NewStack(
		bg,
		container.NewCenter(nm.currentText),
	)
}

// Show displays a notification with the given message
func (nm *NotificationManager) Show(message string, textColor string, duration time.Duration) {
	nm.mu.Lock()
	defer nm.mu.Unlock()

	// Cancel any pending hide timer
	if nm.hideTimer != nil {
		nm.hideTimer.Stop()
	}

	// Set text and color
	sizes := CalculateResponsiveSizes(nm.window.Canvas().Size())
	nm.currentText.TextSize = sizes.FontNotify
	nm.currentText.Text = message
	switch textColor {
	case "green":
		nm.currentText.Color = ColorAvailable
	case "red":
		nm.currentText.Color = ColorUnavailable
	case "blue":
		nm.currentText.Color = ColorPrimary
	default:
		nm.currentText.Color = ColorText
	}
	nm.currentText.Refresh()

	// Show overlay
	if !nm.visible {
		nm.visible = true
		// Position at bottom-left of screen
		// Note: Fyne overlay positioning is handled differently
	}

	// Schedule hide if duration > 0
	if duration > 0 {
		nm.hideTimer = time.AfterFunc(duration, func() {
			nm.Hide()
		})
	}
}

// Hide removes the notification overlay
func (nm *NotificationManager) Hide() {
	nm.mu.Lock()
	defer nm.mu.Unlock()

	if nm.hideTimer != nil {
		nm.hideTimer.Stop()
		nm.hideTimer = nil
	}

	nm.visible = false
	nm.currentText.Text = ""
	nm.currentText.Refresh()
}

// GetOverlay returns the overlay container
func (nm *NotificationManager) GetOverlay() *fyne.Container {
	return nm.overlay
}

// IsVisible returns whether the notification is currently visible
func (nm *NotificationManager) IsVisible() bool {
	nm.mu.Lock()
	defer nm.mu.Unlock()
	return nm.visible
}

// NotificationWidget is a custom widget for notifications
type NotificationWidget struct {
	widget.BaseWidget
	message   string
	textColor string
	visible   bool
	mu        sync.Mutex
}

// NewNotificationWidget creates a new notification widget
func NewNotificationWidget() *NotificationWidget {
	w := &NotificationWidget{}
	w.ExtendBaseWidget(w)
	return w
}

// Display shows the notification
func (w *NotificationWidget) Display(message string, textColor string, duration time.Duration) {
	w.mu.Lock()
	w.message = message
	w.textColor = textColor
	w.visible = true
	w.mu.Unlock()
	w.Refresh()

	if duration > 0 {
		go func() {
			time.Sleep(duration)
			w.Dismiss()
		}()
	}
}

// Dismiss hides the notification
func (w *NotificationWidget) Dismiss() {
	w.mu.Lock()
	w.visible = false
	w.message = ""
	w.mu.Unlock()
	w.Refresh()
}

// CreateRenderer implements fyne.Widget
func (w *NotificationWidget) CreateRenderer() fyne.WidgetRenderer {
	w.mu.Lock()
	defer w.mu.Unlock()

	// Use default font size (will be responsive based on parent container)
	text := canvas.NewText(w.message, ColorText)
	text.TextSize = 40 // Default, scales with parent
	text.TextStyle = fyne.TextStyle{Bold: true}

	bg := canvas.NewRectangle(ColorLight)

	return &notificationRenderer{
		widget: w,
		text:   text,
		bg:     bg,
	}
}

type notificationRenderer struct {
	widget *NotificationWidget
	text   *canvas.Text
	bg     *canvas.Rectangle
}

func (r *notificationRenderer) Layout(size fyne.Size) {
	r.bg.Resize(size)
	r.text.Move(fyne.NewPos(20, 10))
}

func (r *notificationRenderer) MinSize() fyne.Size {
	// Use proportional min size (roughly 15% width, 7% height of a 1920x1080 screen)
	return fyne.NewSize(300, 80)
}

func (r *notificationRenderer) Refresh() {
	r.widget.mu.Lock()
	r.text.Text = r.widget.message
	switch r.widget.textColor {
	case "green":
		r.text.Color = ColorAvailable
	case "red":
		r.text.Color = ColorUnavailable
	default:
		r.text.Color = ColorPrimary
	}
	r.widget.mu.Unlock()

	r.text.Refresh()
	r.bg.Refresh()
}

func (r *notificationRenderer) Objects() []fyne.CanvasObject {
	if r.widget.visible {
		return []fyne.CanvasObject{r.bg, r.text}
	}
	return []fyne.CanvasObject{}
}

func (r *notificationRenderer) Destroy() {}
