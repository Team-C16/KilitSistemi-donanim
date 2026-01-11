// Package ui provides the Fyne-based graphical user interface
package ui

import (
	"image/color"

	"fyne.io/fyne/v2"
	"fyne.io/fyne/v2/theme"
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

// FontSizes holds calculated font sizes based on screen height
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

// CalculateFontSizes returns font sizes proportional to screen height
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
