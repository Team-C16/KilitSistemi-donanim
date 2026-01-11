// Package qr provides QR code generation with styling support
package qr

import (
	"bytes"
	"image"
	"image/color"
	"image/draw"
	"image/png"
	"os"

	"fyne.io/fyne/v2"
	"fyne.io/fyne/v2/canvas"
	qrcode "github.com/skip2/go-qrcode"
)

// Generator handles QR code creation
type Generator struct {
	primaryColor color.Color
	logoPath     string
}

// NewGenerator creates a new QR generator with the specified primary color
func NewGenerator(primaryColor color.Color, logoPath string) *Generator {
	return &Generator{
		primaryColor: primaryColor,
		logoPath:     logoPath,
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
	if g.logoPath != "" {
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
func (g *Generator) overlayLogo(img *image.RGBA, qrSize int) {
	// Try to load logo file
	logoFile, err := os.Open(g.logoPath)
	if err != nil {
		return
	}
	defer logoFile.Close()

	srcLogo, _, err := image.Decode(logoFile)
	if err != nil {
		return
	}

	// Calculate logo size (25% of QR size)
	targetSize := float64(qrSize) / 4.0
	logoBounds := srcLogo.Bounds()

	// Create resized logo
	// Since we don't want to import heavy x/image packages if not needed, we'll use simple nearest neighbor referencing
	// or simple implementation. But manual scaling (bilinear) is better.
	// For now, let's use a simple scaling loop which is good enough for 25% reduction usually.

	scale := targetSize / float64(logoBounds.Dx())
	newW := int(targetSize)
	newH := int(float64(logoBounds.Dy()) * scale)

	resizedLogo := image.NewRGBA(image.Rect(0, 0, newW, newH))

	// Manual Bilinear or Nearest Neighbor scaling + Alpha extraction for mask
	// We'll do a simple mapping.
	for y := 0; y < newH; y++ {
		for x := 0; x < newW; x++ {
			srcX := int(float64(x) / scale)
			srcY := int(float64(y) / scale)
			if srcX < logoBounds.Dx() && srcY < logoBounds.Dy() {
				resizedLogo.Set(x, y, srcLogo.At(logoBounds.Min.X+srcX, logoBounds.Min.Y+srcY))
			}
		}
	}

	// Calculate position
	centerX := (qrSize - newW) / 2
	centerY := (qrSize - newH) / 2

	// Contour Padding
	// Simulate dilation: for every non-transparent pixel in logo, draw a white circle of radius P on output.
	// Python uses 5% of logo size as padding.
	paddingRadius := targetSize * 0.05
	paddingR2 := paddingRadius * paddingRadius

	// We iterate the resized logo. If alpha > 0, we "draw" white circles on the main image at that pos.
	// To optimize, we can compute the mask first.
	// But drawing directly is fine if logo isn't huge (80x80 px).

	white := color.White

	// PASS 1: Draw Padding
	// Warning: heavy loop O(W*H * R*R). 80*80 * 4*4 = 6400 * 16 operations ~100k, fast enough.
	for ly := 0; ly < newH; ly++ {
		for lx := 0; lx < newW; lx++ {
			_, _, _, a := resizedLogo.At(lx, ly).RGBA()
			if a > 0 { // If pixel exists
				// Draw white circle at (centerX+lx, centerY+ly)
				px := float64(centerX + lx)
				py := float64(centerY + ly)

				// Draw filled circle for padding
				// Inline optimization
				minX := int(px - paddingRadius)
				minY := int(py - paddingRadius)
				maxX := int(px + paddingRadius)
				maxY := int(py + paddingRadius)

				for pyy := minY; pyy <= maxY; pyy++ {
					for pxx := minX; pxx <= maxX; pxx++ {
						dx := float64(pxx) - px
						dy := float64(pyy) - py
						if dx*dx+dy*dy <= paddingR2 {
							img.Set(pxx, pyy, white)
						}
					}
				}
			}
		}
	}

	// PASS 2: Draw Logo
	// Simple overlay
	for y := 0; y < newH; y++ {
		for x := 0; x < newW; x++ {
			c := resizedLogo.At(x, y)
			_, _, _, a := c.RGBA()
			if a > 0 {
				// Naive blending usually fine for logo on white
				// But we want to preserve the logo's own alpha blending if partial
				// img.Set(centerX+x, centerY+y, c) overwrites.
				// We should blend if needed, but usually simple Set is ok if logo is opaque or we cleared bg.
				// Since we drew white padding underneath, simple Alpha comp is:
				// dest = src * alpha + dst * (1-alpha)
				// Since dst is white (from padding), and src is logo.

				// Standard Draw does blending.
				dr := image.Rect(centerX+x, centerY+y, centerX+x+1, centerY+y+1)
				draw.Draw(img, dr, resizedLogo, image.Point{x, y}, draw.Over)
			}
		}
	}
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
