// Package ui provides the Fyne-based graphical user interface
package ui

import (
	"image/color"

	"fyne.io/fyne/v2"
	"fyne.io/fyne/v2/theme"
)

// Base resolution for responsive calculations (design reference)
const (
	BaseWidth  float32 = 1920
	BaseHeight float32 = 1080
)

// KioskTheme implements the Fyne theme interface with custom colors
type KioskTheme struct {
	fyne.Theme
}

// Colors used throughout the application
var (
	ColorBackground  = color.NRGBA{R: 0xF0, G: 0xF0, B: 0xF0, A: 0xFF} // #F0F0F0
	ColorPrimary     = color.NRGBA{R: 0x33, G: 0x64, B: 0x8A, A: 0xFF} // #33648A Lapis-Lazuli
	ColorAvailable   = color.NRGBA{R: 0x86, G: 0xBB, B: 0xD8, A: 0xFF} // #86BBD8 Carolina-blue
	ColorUnavailable = color.NRGBA{R: 0x8E, G: 0x41, B: 0x62, A: 0xFF} // #8E4162 Magenta
	ColorHighlight   = color.NRGBA{R: 0xF1, G: 0xC4, B: 0x0F, A: 0xFF} // #F1C40F Yellow
	ColorLight       = color.NRGBA{R: 0xFF, G: 0xFF, B: 0xFF, A: 0xFF} // #FFFFFF
	ColorDark        = color.NRGBA{R: 0x2C, G: 0x3E, B: 0x50, A: 0xFF} // #2C3E50
	ColorText        = color.NRGBA{R: 0x00, G: 0x00, B: 0x00, A: 0xFF} // #000000

	// Building mode colors
	ColorBuildingPrimary = color.NRGBA{R: 0x6D, G: 0x3A, B: 0xFF, A: 0xFF} // #6D3AFF Purple
	ColorBuildingBG      = color.NRGBA{R: 0xFF, G: 0xFF, B: 0xFF, A: 0xFF} // #FFFFFF
)

// NewKioskTheme creates a new kiosk theme
func NewKioskTheme() *KioskTheme {
	return &KioskTheme{
		Theme: theme.DefaultTheme(),
	}
}

// Color returns the color for the specified theme color name
func (t *KioskTheme) Color(name fyne.ThemeColorName, variant fyne.ThemeVariant) color.Color {
	switch name {
	case theme.ColorNameBackground:
		return ColorBackground
	case theme.ColorNamePrimary:
		return ColorPrimary
	case theme.ColorNameForeground:
		return ColorText
	case theme.ColorNameButton:
		return ColorPrimary
	case theme.ColorNameDisabled:
		return ColorLight
	case theme.ColorNameHover:
		return ColorHighlight
	case theme.ColorNameFocus:
		return ColorHighlight
	default:
		return t.Theme.Color(name, variant)
	}
}

// Font returns the font resource for the given style
func (t *KioskTheme) Font(style fyne.TextStyle) fyne.Resource {
	// Use default fonts - Fyne handles this well
	return t.Theme.Font(style)
}

// Size returns the size for the specified theme size name
func (t *KioskTheme) Size(name fyne.ThemeSizeName) float32 {
	switch name {
	case theme.SizeNameText:
		return 16
	case theme.SizeNameHeadingText:
		return 24
	case theme.SizeNameSubHeadingText:
		return 20
	case theme.SizeNamePadding:
		return 8
	case theme.SizeNameInnerPadding:
		return 4
	case theme.SizeNameScrollBar:
		return 12
	default:
		return t.Theme.Size(name)
	}
}

// Icon returns the icon resource for the given icon name
func (t *KioskTheme) Icon(name fyne.ThemeIconName) fyne.Resource {
	return t.Theme.Icon(name)
}

// ResponsiveSizes holds all calculated responsive sizes based on window dimensions
type ResponsiveSizes struct {
	// Font sizes
	FontTitle    float32 // Large titles (20px base)
	FontSubtitle float32 // Subtitles (18px base)
	FontBody     float32 // Body text (16px base)
	FontSmall    float32 // Small text (14px base)
	FontTiny     float32 // Tiny text (12px base)
	FontMicro    float32 // Micro text (10px base)
	FontNotify   float32 // Notification text (40px base)

	// Element heights
	HeaderHeight float32 // Header/footer height (50-60px base)
	FooterHeight float32 // Footer height (60-70px base)
	CellHeight   float32 // Schedule cell height (40-50px base)
	TimeColWidth float32 // Time column width (60-80px base)

	// Panel widths
	QRPanelWidth float32 // QR panel width (400px base, ~21% of 1920)
	QRCodeSize   float32 // QR code size (320px base)

	// Notification sizes
	NotifyWidth  float32 // Notification width (400px base)
	NotifyHeight float32 // Notification height (100px base)

	// Spacing & Padding
	Padding      float32 // Standard padding (8px base)
	Spacing      float32 // Standard spacing (8px base)
	InnerPadding float32 // Inner padding (4px base)
}

// CalculateResponsiveSizes returns all sizes scaled to the current window dimensions
// based on a 1920x1080 reference resolution
func CalculateResponsiveSizes(windowSize fyne.Size) ResponsiveSizes {
	// Calculate scale factors
	scaleW := windowSize.Width / BaseWidth
	scaleH := windowSize.Height / BaseHeight
	// Use geometric mean for balanced scaling
	scale := (scaleW + scaleH) / 2

	// Clamp scale to prevent extremes
	if scale < 0.5 {
		scale = 0.5
	}
	if scale > 2.0 {
		scale = 2.0
	}

	return ResponsiveSizes{
		// Font sizes (scaled from base values at 1920x1080)
		FontTitle:    clampFloat(20*scale, 14, 32),
		FontSubtitle: clampFloat(18*scale, 12, 28),
		FontBody:     clampFloat(16*scale, 10, 24),
		FontSmall:    clampFloat(14*scale, 9, 20),
		FontTiny:     clampFloat(12*scale, 8, 18),
		FontMicro:    clampFloat(10*scale, 7, 16),
		FontNotify:   clampFloat(40*scale, 24, 60),

		// Element heights (scaled)
		HeaderHeight: clampFloat(70*scale, 40, 120),
		FooterHeight: clampFloat(60*scale, 40, 100),
		CellHeight:   clampFloat(40*scale, 22, 55),
		TimeColWidth: clampFloat(60*scale, 45, 100),

		// Panel widths (proportional to window width)
		// QR panel is 16% of window width, QR code is smaller to fit carousel
		QRPanelWidth: clampFloat(windowSize.Width*0.16, 200, 450),
		QRCodeSize:   clampFloat(windowSize.Width*0.17, 200, 450), //clampFloat(windowSize.Width*0.12, 150, 320),

		// Notification sizes (scaled)
		NotifyWidth:  clampFloat(400*scale, 280, 600),
		NotifyHeight: clampFloat(100*scale, 70, 150),

		// Spacing & Padding (scaled)
		Padding:      clampFloat(8*scale, 4, 16),
		Spacing:      clampFloat(8*scale, 4, 16),
		InnerPadding: clampFloat(4*scale, 2, 8),
	}
}

// clampFloat clamps a float32 value between min and max
func clampFloat(value, min, max float32) float32 {
	if value < min {
		return min
	}
	if value > max {
		return max
	}
	return value
}

// FontSizes holds calculated font sizes based on screen height (legacy)
type FontSizes struct {
	Title    float32
	Subtitle float32
	Day      float32
	Hour     float32
	CellMain float32
	CellSub  float32
	Info     float32
	Footer   float32
}

// CalculateFontSizes returns font sizes proportional to screen height (legacy)
func CalculateFontSizes(screenHeight float32) FontSizes {
	return FontSizes{
		Title:    screenHeight * 0.030,
		Subtitle: screenHeight * 0.020,
		Day:      screenHeight * 0.022,
		Hour:     screenHeight * 0.021,
		CellMain: screenHeight * 0.020,
		CellSub:  screenHeight * 0.018,
		Info:     screenHeight * 0.016,
		Footer:   screenHeight * 0.025,
	}
}
