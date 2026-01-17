package ui

import (
	"math"

	"fyne.io/fyne/v2"
)

// FixedHeightLayout strictly forces the height of all objects to a specific value
// while letting them expand to the full width of the container.
type FixedHeightLayout struct {
	Height float32
}

// NewFixedHeightLayout creates a new FixedHeightLayout with the specified height.
func NewFixedHeightLayout(height float32) fyne.Layout {
	return &FixedHeightLayout{Height: height}
}

// Layout places objects at 0,0 with full width and fixed height.
func (f *FixedHeightLayout) Layout(objects []fyne.CanvasObject, size fyne.Size) {
	for _, o := range objects {
		o.Resize(fyne.NewSize(size.Width, f.Height))
		o.Move(fyne.NewPos(0, 0))
	}
}

// MinSize returns a size with 0 width (flexible) and fixed height.
func (f *FixedHeightLayout) MinSize(objects []fyne.CanvasObject) fyne.Size {
	return fyne.NewSize(0, f.Height)
}

// FixedWidthLayout forces a fixed width but allows height to vary/expand.
type FixedWidthLayout struct {
	Width float32
}

func NewFixedWidthLayout(width float32) fyne.Layout {
	return &FixedWidthLayout{Width: width}
}

func (f *FixedWidthLayout) Layout(objects []fyne.CanvasObject, size fyne.Size) {
	for _, o := range objects {
		o.Resize(fyne.NewSize(f.Width, size.Height))
		o.Move(fyne.NewPos(0, 0))
	}
}

func (f *FixedWidthLayout) MinSize(objects []fyne.CanvasObject) fyne.Size {
	// Loop to find max min-height of children?
	var maxH float32
	for _, o := range objects {
		h := o.MinSize().Height
		if h > maxH {
			maxH = h
		}
	}
	return fyne.NewSize(f.Width, maxH)
}

// VerticalFixedHeaderLayout places the first object at the top with its minimum (or fixed) height,
// and the second object fills the rest of the vertical space.
// Crucially, it leaves 0 GAP between them.
type VerticalFixedHeaderLayout struct {
}

func NewVerticalFixedHeaderLayout() fyne.Layout {
	return &VerticalFixedHeaderLayout{}
}

func (v *VerticalFixedHeaderLayout) Layout(objects []fyne.CanvasObject, size fyne.Size) {
	if len(objects) == 0 {
		return
	}

	header := objects[0]
	headerHeight := header.MinSize().Height

	header.Resize(fyne.NewSize(size.Width, headerHeight))
	header.Move(fyne.NewPos(0, 0))

	if len(objects) > 1 {
		body := objects[1]
		bodyHeight := size.Height - headerHeight
		if bodyHeight < 0 {
			bodyHeight = 0
		}

		body.Resize(fyne.NewSize(size.Width, bodyHeight))
		body.Move(fyne.NewPos(0, headerHeight))
	}
}

func (v *VerticalFixedHeaderLayout) MinSize(objects []fyne.CanvasObject) fyne.Size {
	if len(objects) == 0 {
		return fyne.NewSize(0, 0)
	}

	headerMin := objects[0].MinSize()
	width := headerMin.Width
	height := headerMin.Height

	if len(objects) > 1 {
		bodyMin := objects[1].MinSize()
		width = float32(math.Max(float64(width), float64(bodyMin.Width)))
		height += bodyMin.Height
	}

	return fyne.NewSize(width, height)
}

// RoomSlotData defines the position and size of a slot
type RoomSlotData struct {
	StartMinuteOffset int // Minutes from global start
	DurationMinutes   int // Duration of this slot
}

// ScheduleColumnLayout is a custom layout that positions children based on provided slot data.
// The `objects` slice passed to Layout() must correspond 1:1 to `Slots`.
type ScheduleColumnLayout struct {
	Slots              []RoomSlotData
	TotalGlobalMinutes int
	MinHeight          float32
}

func NewScheduleColumnLayout(slots []RoomSlotData, totalMinutes int, minHeight float32) fyne.Layout {
	return &ScheduleColumnLayout{
		Slots:              slots,
		TotalGlobalMinutes: totalMinutes,
		MinHeight:          minHeight,
	}
}

func (l *ScheduleColumnLayout) Layout(objects []fyne.CanvasObject, size fyne.Size) {
	// If height is less than min, use min (though scroll container usually handles this)
	totalHeight := size.Height
	if totalHeight < l.MinHeight {
		totalHeight = l.MinHeight
	}

	// Calculate pixels per minute
	pixelsPerMinute := totalHeight / float32(l.TotalGlobalMinutes)

	for i, obj := range objects {
		if i >= len(l.Slots) {
			break
		}
		slot := l.Slots[i]

		// Calculate Y position relative to top (Global Start)
		yPos := float32(slot.StartMinuteOffset) * pixelsPerMinute
		height := float32(slot.DurationMinutes) * pixelsPerMinute

		obj.Move(fyne.NewPos(0, yPos))
		obj.Resize(fyne.NewSize(size.Width, height))
	}
}

func (l *ScheduleColumnLayout) MinSize(objects []fyne.CanvasObject) fyne.Size {
	// Width is flexible (0), Height is fixed minimum
	return fyne.NewSize(0, l.MinHeight)
}
