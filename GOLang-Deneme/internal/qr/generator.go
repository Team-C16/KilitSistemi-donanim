// Package qr provides QR code generation with styling support
package qr

import (
	"bytes"
	"image"
	"image/color"
	"image/draw"
	"image/png"

	"fyne.io/fyne/v2"
	"fyne.io/fyne/v2/canvas"
	qrcode "github.com/skip2/go-qrcode"
)

// Generator handles QR code creation
type Generator struct {
	primaryColor color.Color
	logoData     []byte

	// Cached processed logo (resized + with padding coordinates)
	cachedLogo     *image.RGBA
	cachedLogoSize int           // Size for which the logo was cached
	cachedLogoW    int           // Cached logo width
	cachedLogoH    int           // Cached logo height
	cachedPadMask  []image.Point // Pre-computed padding pixel positions
}

// NewGenerator creates a new QR generator with the specified primary color
func NewGenerator(primaryColor color.Color, logoData []byte) *Generator {
	return &Generator{
		primaryColor: primaryColor,
		logoData:     logoData,
	}
}

// Generate creates a QR code image for the given data
func (g *Generator) Generate(data string, size int) (fyne.Resource, error) {
	// Create QR code with high error correction (allows logo overlay)
	qr, err := qrcode.New(data, qrcode.High)
	if err != nil {
		return nil, err
	}

	// 1. Manually draw QR with rounded modules
	// Calculate module size
	bitmap := qr.Bitmap()
	moduleSize := float64(size) / float64(len(bitmap))
	padding := 0.0 // skip2/go-qrcode includes quiet zone in bitmap? Yes, usually.

	// Create output image
	rgba := image.NewRGBA(image.Rect(0, 0, size, size))

	// Fill background (White)
	draw.Draw(rgba, rgba.Bounds(), &image.Uniform{color.White}, image.Point{}, draw.Src)

	// Draw modules
	// Use primary color for modules
	fg := g.primaryColor

	// Helper to draw rounded rect/circle
	// Since modules are small, circles usually look like rounded rects if connected.
	// But Python's RoundedModuleDrawer usually draws individual circles or connected shapes.
	// For simplicity and performance in pure Go, we'll draw circles for true modules.
	// Note: Fully connecting them requires complex logic. Simple circles often look "rounded" enough.
	// Python's RoundedModuleDrawer effectively draws circles that merge.

	// We'll draw slightly overlapping circles to ensure connectivity
	radius := moduleSize * 0.55 // slightly larger than 0.5 to overlap

	for y, row := range bitmap {
		for x, v := range row {
			if v {
				// Calculate center
				cx := float64(x)*moduleSize + moduleSize/2 + padding
				cy := float64(y)*moduleSize + moduleSize/2 + padding

				g.drawCircle(rgba, cx, cy, radius, fg)
			}
		}
	}

	// 2. Overlay Logo with Contour Padding
	if len(g.logoData) > 0 {
		g.overlayLogo(rgba, size)
	}

	// Encode to PNG
	var buf bytes.Buffer
	if err := png.Encode(&buf, rgba); err != nil {
		return nil, err
	}

	return fyne.NewStaticResource("qr.png", buf.Bytes()), nil
}

// drawCircle draws a filled circle on the image
func (g *Generator) drawCircle(img *image.RGBA, cx, cy, r float64, c color.Color) {
	minX := int(cx - r - 1)
	minY := int(cy - r - 1)
	maxX := int(cx + r + 1)
	maxY := int(cy + r + 1)

	r2 := r * r

	for y := minY; y <= maxY; y++ {
		for x := minX; x <= maxX; x++ {
			dx := float64(x) - cx + 0.5
			dy := float64(y) - cy + 0.5
			if dx*dx+dy*dy <= r2 {
				img.Set(x, y, c)
			}
		}
	}
}

// overlayLogo places the logo in the center of the QR code with contour padding
// Uses cached processed logo if available for the same size
func (g *Generator) overlayLogo(img *image.RGBA, qrSize int) {
	if len(g.logoData) == 0 {
		return
	}

	// Check if we need to process the logo (first time or size changed)
	if g.cachedLogo == nil || g.cachedLogoSize != qrSize {
		g.processAndCacheLogo(qrSize)
	}

	// If caching failed, skip
	if g.cachedLogo == nil {
		return
	}

	// Calculate center position
	centerX := (qrSize - g.cachedLogoW) / 2
	centerY := (qrSize - g.cachedLogoH) / 2

	white := color.White

	// PASS 1: Draw Padding using pre-computed mask positions
	for _, pt := range g.cachedPadMask {
		img.Set(centerX+pt.X, centerY+pt.Y, white)
	}

	// PASS 2: Draw Logo using cached resized image
	for y := 0; y < g.cachedLogoH; y++ {
		for x := 0; x < g.cachedLogoW; x++ {
			c := g.cachedLogo.At(x, y)
			_, _, _, a := c.RGBA()
			if a > 0 {
				dr := image.Rect(centerX+x, centerY+y, centerX+x+1, centerY+y+1)
				draw.Draw(img, dr, g.cachedLogo, image.Point{x, y}, draw.Over)
			}
		}
	}
}

// processAndCacheLogo decodes, resizes, and caches the logo for future use
func (g *Generator) processAndCacheLogo(qrSize int) {
	srcLogo, _, err := image.Decode(bytes.NewReader(g.logoData))
	if err != nil {
		return
	}

	// Calculate logo size (25% of QR size)
	targetSize := float64(qrSize) / 4.0
	logoBounds := srcLogo.Bounds()

	scale := targetSize / float64(logoBounds.Dx())
	newW := int(targetSize)
	newH := int(float64(logoBounds.Dy()) * scale)

	resizedLogo := image.NewRGBA(image.Rect(0, 0, newW, newH))

	// Resize logo
	for y := 0; y < newH; y++ {
		for x := 0; x < newW; x++ {
			srcX := int(float64(x) / scale)
			srcY := int(float64(y) / scale)
			if srcX < logoBounds.Dx() && srcY < logoBounds.Dy() {
				resizedLogo.Set(x, y, srcLogo.At(logoBounds.Min.X+srcX, logoBounds.Min.Y+srcY))
			}
		}
	}

	// Pre-compute padding mask (relative positions from logo top-left)
	paddingRadius := targetSize * 0.05
	paddingR2 := paddingRadius * paddingRadius
	var padMask []image.Point

	for ly := 0; ly < newH; ly++ {
		for lx := 0; lx < newW; lx++ {
			_, _, _, a := resizedLogo.At(lx, ly).RGBA()
			if a > 0 {
				// Compute all padding pixels relative to this logo pixel
				px := float64(lx)
				py := float64(ly)

				minX := int(px - paddingRadius)
				minY := int(py - paddingRadius)
				maxX := int(px + paddingRadius)
				maxY := int(py + paddingRadius)

				for pyy := minY; pyy <= maxY; pyy++ {
					for pxx := minX; pxx <= maxX; pxx++ {
						dx := float64(pxx) - px
						dy := float64(pyy) - py
						if dx*dx+dy*dy <= paddingR2 {
							padMask = append(padMask, image.Point{pxx, pyy})
						}
					}
				}
			}
		}
	}

	// Store in cache
	g.cachedLogo = resizedLogo
	g.cachedLogoSize = qrSize
	g.cachedLogoW = newW
	g.cachedLogoH = newH
	g.cachedPadMask = padMask
}

// GenerateCanvasImage creates a Fyne canvas image from QR data
func (g *Generator) GenerateCanvasImage(data string, size int) (*canvas.Image, error) {
	res, err := g.Generate(data, size)
	if err != nil {
		return nil, err
	}

	img := canvas.NewImageFromResource(res)
	img.FillMode = canvas.ImageFillContain
	img.SetMinSize(fyne.NewSize(float32(size), float32(size)))

	return img, nil
}
