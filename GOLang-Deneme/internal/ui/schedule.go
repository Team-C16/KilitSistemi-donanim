// Package ui - Schedule data structures and transformations
package ui

import (
	"fmt"
	"sort"
	"strings"
	"time"

	"kiosk-go/internal/api"
)

// SlotStatus represents the availability status of a time slot
type SlotStatus string

const (
	SlotEmpty    SlotStatus = "Boş"
	SlotOccupied SlotStatus = "Dolu"
)

// ScheduleSlot represents a single time slot in the schedule
type ScheduleSlot struct {
	Status       SlotStatus
	Activity     string
	Organizer    string
	RendezvousID string
}

// DaySchedule maps hour strings to schedule slots
type DaySchedule map[string]*ScheduleSlot

// Schedule maps date keys (YYYY-MM-DD) to day schedules
type Schedule map[string]DaySchedule

// RoomSchedule maps room names to their schedules (for building mode)
type RoomSchedule map[string]DaySchedule

// TimeConfig holds schedule time configuration
type TimeConfig struct {
	TimeSuffix string // e.g., ":30" or ":00"
	StartHour  int
	EndHour    int
	Interval   int // interval in minutes (e.g., 30, 60)
}

// DefaultTimeConfig returns the default time configuration
func DefaultTimeConfig() TimeConfig {
	return TimeConfig{
		TimeSuffix: ":00",
		StartHour:  9,
		EndHour:    18,
		Interval:   60, // default 60 minutes
	}
}

// RoomTimeConfig holds room-specific schedule time configuration
type RoomTimeConfig struct {
	TimeSuffix string // e.g., ":30" or ":00"
	StartHour  int
	EndHour    int
	Interval   int // interval in minutes (e.g., 30, 60, 120)
}

// RoomSlotPosition represents a room's position within the global grid
type RoomSlotPosition struct {
	StartOffset float64 // 0.0 = aligned, 0.5 = half slot offset
	SlotSpan    int     // how many global slots this room slot spans
	IsVisible   bool    // whether this slot falls within global bounds
}

// ParseRoomTimeConfig extracts room-specific time config from RoomInfo
// Falls back to global config if room-specific values are not set
func ParseRoomTimeConfig(room *api.RoomInfo, globalTC TimeConfig) RoomTimeConfig {
	rtc := RoomTimeConfig{
		TimeSuffix: globalTC.TimeSuffix,
		StartHour:  globalTC.StartHour,
		EndHour:    globalTC.EndHour,
		Interval:   globalTC.Interval,
	}

	if room.HourSuffix != nil && *room.HourSuffix != "" {
		rtc.TimeSuffix = *room.HourSuffix
	}

	if room.StartHour != nil && *room.StartHour != "" {
		var h int
		fmt.Sscanf(*room.StartHour, "%d", &h)
		if h > 0 {
			rtc.StartHour = h
			// If we have a custom start hour, but no custom suffix, default to :00!
			// Otherwise we inherit Global Suffix (e.g. :30) which shifts the room incorrectly.
			if room.HourSuffix == nil || *room.HourSuffix == "" {
				rtc.TimeSuffix = ":00"
			}
		}
	}

	if room.EndHour != nil && *room.EndHour != "" {
		var h int
		fmt.Sscanf(*room.EndHour, "%d", &h)
		if h > 0 {
			rtc.EndHour = h
		}
	}

	if room.Interval != nil && *room.Interval != "" {
		var i int
		fmt.Sscanf(*room.Interval, "%d", &i)
		if i > 0 {
			// API returns interval in hours, convert to minutes
			rtc.Interval = i * 60
		}
	}

	return rtc
}

// CalculateRoomSlotPosition calculates where a room slot appears in the global grid
// globalHour: the global grid hour string (e.g., "09:00")
// roomTC: the room's time configuration
// globalTC: the global time configuration
func CalculateRoomSlotPosition(globalHour string, roomTC RoomTimeConfig, globalTC TimeConfig) RoomSlotPosition {
	// Parse global hour to minutes
	var globalH, globalM int
	fmt.Sscanf(globalHour, "%d:%d", &globalH, &globalM)
	globalMinutes := globalH*60 + globalM

	// Parse room start time suffix to get minutes offset
	var roomSuffixM int
	fmt.Sscanf(roomTC.TimeSuffix, ":%d", &roomSuffixM)

	// Calculate room start time in minutes
	roomStartMinutes := roomTC.StartHour*60 + roomSuffixM
	roomEndMinutes := roomTC.EndHour*60 + roomSuffixM

	// Check if this global slot is within room's operating hours
	// Room slot that contains this global time
	if globalMinutes < roomStartMinutes || globalMinutes >= roomEndMinutes {
		return RoomSlotPosition{IsVisible: false}
	}

	// Calculate offset: how much the room is offset from the global grid
	// If room starts at :30 and global is at :00, offset is 0.5
	globalInterval := globalTC.Interval
	if globalInterval <= 0 {
		globalInterval = 60
	}

	offset := float64(roomSuffixM) / float64(globalInterval)

	// Calculate slot span: how many global slots this room slot covers
	roomInterval := roomTC.Interval
	if roomInterval <= 0 {
		roomInterval = 60
	}
	slotSpan := roomInterval / globalInterval
	if slotSpan < 1 {
		slotSpan = 1
	}

	return RoomSlotPosition{
		StartOffset: offset,
		SlotSpan:    slotSpan,
		IsVisible:   true,
	}
}

// IsRoomSlotStart checks if this global hour is the start of a room slot
func IsRoomSlotStart(globalHour string, roomTC RoomTimeConfig, globalTC TimeConfig) bool {
	var globalH, globalM int
	fmt.Sscanf(globalHour, "%d:%d", &globalH, &globalM)
	globalMinutes := globalH*60 + globalM

	var roomSuffixM int
	fmt.Sscanf(roomTC.TimeSuffix, ":%d", &roomSuffixM)

	roomStartMinutes := roomTC.StartHour*60 + roomSuffixM
	roomEndMinutes := roomTC.EndHour*60 + roomSuffixM

	if globalMinutes < roomStartMinutes || globalMinutes >= roomEndMinutes {
		return false
	}

	// Check if this is aligned with room's interval
	roomInterval := roomTC.Interval
	if roomInterval <= 0 {
		roomInterval = 60
	}

	// Minutes since room start
	minutesSinceStart := globalMinutes - roomStartMinutes
	return minutesSinceStart%roomInterval == 0
}

// RoomSlotInfo contains detailed information about how a room slot maps to the global grid
type RoomSlotInfo struct {
	IsVisible    bool    // whether this global slot is within room's operating hours
	IsSlotStart  bool    // whether this is the start of a room slot
	IsSlotMiddle bool    // whether this is in the middle of a room slot (not start, not end)
	SlotSpan     int     // how many global slots the room slot spans
	OffsetRatio  float64 // offset from global grid (0.0 = aligned, 0.5 = half offset)
	RoomHour     string  // the room's hour for this slot (e.g., "09:30")
}

// GetRoomSlotInfo returns detailed slot information for a given global hour
// This is used to render room slots correctly on the global grid
func GetRoomSlotInfo(globalHour string, roomTC RoomTimeConfig, globalTC TimeConfig) RoomSlotInfo {
	// Parse global hour to minutes
	var globalH, globalM int
	fmt.Sscanf(globalHour, "%d:%d", &globalH, &globalM)
	globalMinutes := globalH*60 + globalM

	// Parse room suffix to get minutes offset
	var roomSuffixM int
	fmt.Sscanf(roomTC.TimeSuffix, ":%d", &roomSuffixM)

	// Calculate room time boundaries
	roomStartMinutes := roomTC.StartHour*60 + roomSuffixM
	roomEndMinutes := roomTC.EndHour*60 + roomSuffixM

	// Get intervals (with fallbacks)
	globalInterval := globalTC.Interval
	if globalInterval <= 0 {
		globalInterval = 60
	}
	roomInterval := roomTC.Interval
	if roomInterval <= 0 {
		roomInterval = 60
	}

	// Calculate slot span (how many global slots per room slot)
	slotSpan := roomInterval / globalInterval
	if slotSpan < 1 {
		slotSpan = 1
	}

	// Calculate offset ratio (how much room is offset from global grid)
	offsetRatio := float64(roomSuffixM%globalInterval) / float64(globalInterval)

	// Check if this global slot is outside room's operating hours
	if globalMinutes < roomStartMinutes || globalMinutes >= roomEndMinutes {
		return RoomSlotInfo{
			IsVisible:   false,
			OffsetRatio: offsetRatio,
			SlotSpan:    slotSpan,
		}
	}

	// Calculate which room slot this global slot belongs to
	minutesSinceRoomStart := globalMinutes - roomStartMinutes
	positionInRoomSlot := minutesSinceRoomStart % roomInterval

	isSlotStart := positionInRoomSlot == 0
	isSlotMiddle := positionInRoomSlot > 0 && (positionInRoomSlot+globalInterval) < roomInterval

	// Calculate the room's corresponding hour for this slot
	roomSlotStartMinutes := roomStartMinutes + (minutesSinceRoomStart/roomInterval)*roomInterval
	roomHour := fmt.Sprintf("%02d:%02d", roomSlotStartMinutes/60, roomSlotStartMinutes%60)

	return RoomSlotInfo{
		IsVisible:    true,
		IsSlotStart:  isSlotStart,
		IsSlotMiddle: isSlotMiddle,
		SlotSpan:     slotSpan,
		OffsetRatio:  offsetRatio,
		RoomHour:     roomHour,
	}
}

// GenerateHours creates a list of hour strings based on the time config
// Uses interval to generate time slots (e.g., 30 min interval: 09:00, 09:30, 10:00...)
func (tc TimeConfig) GenerateHours() []string {
	interval := tc.Interval
	if interval <= 0 {
		interval = 60 // fallback to 60 minutes
	}

	// Calculate slots per hour
	slotsPerHour := 60 / interval
	if slotsPerHour < 1 {
		slotsPerHour = 1
	}

	// Calculate total slots
	totalHours := tc.EndHour - tc.StartHour + 1
	hours := make([]string, 0, totalHours*slotsPerHour)

	// Parse suffix minutes
	var suffixMinutes int
	if tc.TimeSuffix != "" {
		fmt.Sscanf(tc.TimeSuffix, ":%d", &suffixMinutes)
	}

	for h := tc.StartHour; h <= tc.EndHour; h++ {
		for s := 0; s < slotsPerHour; s++ {
			// Calculate total minutes including suffix
			totalMinutes := (h * 60) + (s * interval) + suffixMinutes

			// Convert back to hour:minute
			slotH := totalMinutes / 60
			slotM := totalMinutes % 60

			// Optional: check if we exceeded 24 hours?
			// For simplicity, just format.
			if slotH >= 24 {
				slotH = slotH % 24
			}

			hours = append(hours, fmt.Sprintf("%02d:%02d", slotH, slotM))
		}
	}
	return hours
}

// ParseTimeConfig extracts time configuration from API response
func ParseTimeConfig(configs []api.IndexConfig) TimeConfig {
	tc := DefaultTimeConfig()

	for _, cfg := range configs {
		switch cfg.IndexName {
		case "hour":
			tc.TimeSuffix = cfg.IndexValue
		case "suffix":
			tc.TimeSuffix = cfg.IndexValue
		case "startHour":
			var h int
			fmt.Sscanf(cfg.IndexValue, "%d", &h)
			if h > 0 {
				tc.StartHour = h
			}
		case "endHour":
			var h int
			fmt.Sscanf(cfg.IndexValue, "%d", &h)
			if h > 0 {
				tc.EndHour = h
			}
		case "interval":
			var i int
			fmt.Sscanf(cfg.IndexValue, "%d", &i)
			if i > 0 {
				// API returns interval in hours, convert to minutes
				tc.Interval = i * 60
			}
		}
	}

	return tc
}

// DayInfo holds information about a display day
type DayInfo struct {
	Date        time.Time
	DateKey     string // YYYY-MM-DD format
	DayNameTR   string // Turkish day name
	DayNameEN   string // English day name
	DisplayDate string // DD.MM format
	IsToday     bool
}

// DayNamesTR maps English day names to Turkish
var DayNamesTR = map[string]string{
	"Monday":    "Pazartesi",
	"Tuesday":   "Salı",
	"Wednesday": "Çarşamba",
	"Thursday":  "Perşembe",
	"Friday":    "Cuma",
	"Saturday":  "Cumartesi",
	"Sunday":    "Pazar",
}

// GenerateDisplayDays creates a list of days to display (rolling 5 days from today)
func GenerateDisplayDays() []DayInfo {
	now := time.Now()
	days := make([]DayInfo, 5)

	for i := 0; i < 5; i++ {
		date := now.AddDate(0, 0, i)
		dayNameEN := date.Weekday().String()

		days[i] = DayInfo{
			Date:        date,
			DateKey:     date.Format("2006-01-02"),
			DayNameTR:   DayNamesTR[dayNameEN],
			DayNameEN:   dayNameEN,
			DisplayDate: date.Format("02.01"),
			IsToday:     i == 0,
		}
	}

	return days
}

// GenerateWeekDays creates a list of days for Mon-Fri view (office mode)
func GenerateWeekDays() []DayInfo {
	now := time.Now()
	weekday := int(now.Weekday())

	// If weekend, show next week
	var startDate time.Time
	if weekday == 0 { // Sunday
		startDate = now.AddDate(0, 0, 1) // Next Monday
	} else if weekday == 6 { // Saturday
		startDate = now.AddDate(0, 0, 2) // Next Monday
	} else {
		// Go back to Monday of current week
		startDate = now.AddDate(0, 0, -(weekday - 1))
	}

	days := make([]DayInfo, 5)
	for i := 0; i < 5; i++ {
		date := startDate.AddDate(0, 0, i)
		dayNameEN := date.Weekday().String()
		isToday := date.Year() == now.Year() && date.YearDay() == now.YearDay()

		days[i] = DayInfo{
			Date:        date,
			DateKey:     date.Format("2006-01-02"),
			DayNameTR:   DayNamesTR[dayNameEN],
			DayNameEN:   dayNameEN,
			DisplayDate: date.Format("02.01"),
			IsToday:     isToday,
		}
	}

	return days
}

// TransformSchedule converts API response to internal schedule format
func TransformSchedule(apiData *api.ScheduleResponse, dateKeys []string, tc TimeConfig) Schedule {
	schedule := make(Schedule)
	hours := tc.GenerateHours()

	// Initialize empty schedule
	for _, dateKey := range dateKeys {
		schedule[dateKey] = make(DaySchedule)
		for _, hour := range hours {
			schedule[dateKey][hour] = &ScheduleSlot{
				Status: SlotEmpty,
			}
		}
	}

	// Fill in from API data
	for _, entry := range apiData.Schedule {
		// Parse date with timezone support
		dayStr := entry.Day
		if idx := strings.Index(dayStr, "."); idx != -1 {
			dayStr = dayStr[:idx]
		}

		// Parse as RFC3339 with timezone (e.g., "2026-01-08T21:00:00Z")
		// API returns UTC time that represents local midnight
		var parsedTime time.Time
		var err error

		// Try parsing with Z suffix
		if !strings.HasSuffix(dayStr, "Z") {
			dayStr = dayStr + "Z"
		}
		parsedTime, err = time.Parse(time.RFC3339, dayStr)

		if err != nil {
			// Fallback to basic format
			parsedTime, err = time.Parse("2006-01-02T15:04:05", strings.TrimSuffix(dayStr, "Z"))
			if err != nil {
				fmt.Printf("[DEBUG TRANSFORM]     Fallback parse also failed: %v\n", err)
				continue
			}
		}

		// Convert UTC to local time and extract date
		localTime := parsedTime.In(time.Local)
		dateKey := localTime.Format("2006-01-02")

		// Parse hour and minute from API format (e.g., "09:30:00" -> "09:30")
		hourParts := strings.Split(entry.Hour, ":")
		var h, m int
		if len(hourParts) >= 2 {
			fmt.Sscanf(hourParts[0], "%d", &h)
			fmt.Sscanf(hourParts[1], "%d", &m)
		}
		hourStr := fmt.Sprintf("%02d:%02d", h, m)

		// Update schedule
		if daySchedule, exists := schedule[dateKey]; exists {
			if slot, slotExists := daySchedule[hourStr]; slotExists {
				slot.Status = SlotOccupied
				slot.Activity = entry.Title
				slot.Organizer = entry.FullName
				slot.RendezvousID = entry.RendezvousID
			}
		}
	}

	return schedule
}

// TransformBuildingSchedule converts building API response to room schedule format
func TransformBuildingSchedule(apiData *api.BuildingScheduleResponse, roomMap map[int]string) RoomSchedule {
	schedule := make(RoomSchedule)

	// Initialize empty schedule map for each room to ensure safe access
	for _, roomName := range roomMap {
		schedule[roomName] = make(DaySchedule)
	}

	// Fill in from API data
	for _, entry := range apiData.Schedule {
		roomName, exists := roomMap[entry.RoomID]
		if !exists {
			continue
		}

		// Parse hour (format: "09:00:00" -> "09:00")
		hourParts := strings.Split(entry.Hour, ":")
		var h, m int
		if len(hourParts) >= 2 {
			fmt.Sscanf(hourParts[0], "%d", &h)
			fmt.Sscanf(hourParts[1], "%d", &m)
		}
		hourFmt := fmt.Sprintf("%02d:%02d", h, m)

		schedule[roomName][hourFmt] = &ScheduleSlot{
			Status:       SlotOccupied,
			Activity:     entry.Title,
			Organizer:    entry.FullName,
			RendezvousID: entry.RendezvousID,
		}

		if schedule[roomName][hourFmt].Activity == "" {
			schedule[roomName][hourFmt].Activity = "Dolu"
		}
	}

	return schedule
}

// IsCurrentSlot checks if a given time slot is the current one
func IsCurrentSlot(dayName string, hourStr string, tc TimeConfig) bool {
	now := time.Now()
	todayName := now.Weekday().String()

	// Convert Turkish day name to English if needed
	englishDayName := dayName
	for en, tr := range DayNamesTR {
		if tr == dayName {
			englishDayName = en
			break
		}
	}

	if englishDayName != todayName {
		return false
	}

	// Parse hour and minute from hourStr (format: "09:30")
	var slotHour, slotMinute int
	fmt.Sscanf(hourStr, "%d:%d", &slotHour, &slotMinute)

	// Get interval in minutes
	interval := tc.Interval
	if interval <= 0 {
		interval = 60
	}

	// Create slot start and end times
	startTime := time.Date(now.Year(), now.Month(), now.Day(), slotHour, slotMinute, 0, 0, now.Location())
	endTime := startTime.Add(time.Duration(interval) * time.Minute)

	return now.After(startTime) && now.Before(endTime)
}

// GetCurrentHourString returns the formatted hour string for the current time
func GetCurrentHourString(tc TimeConfig) string {
	now := time.Now()

	// Get interval in minutes
	interval := tc.Interval
	if interval <= 0 {
		interval = 60
	}

	// Calculate which slot the current time falls into
	currentMinutes := now.Hour()*60 + now.Minute()
	slotStartMinutes := (currentMinutes / interval) * interval

	slotHour := slotStartMinutes / 60
	slotMinute := slotStartMinutes % 60

	return fmt.Sprintf("%02d:%02d", slotHour, slotMinute)
}

// TruncateString truncates a string to maxLen characters with ellipsis
func TruncateString(s string, maxLen int) string {
	if len(s) <= maxLen {
		return s
	}
	return s[:maxLen] + "..."
}

// SortedRoomNames returns room names sorted for consistent display
func SortedRoomNames(roomMap map[int]string) []string {
	// Get sorted keys
	keys := make([]int, 0, len(roomMap))
	for k := range roomMap {
		keys = append(keys, k)
	}
	sort.Ints(keys)

	// Build result
	result := make([]string, len(keys))
	for i, k := range keys {
		result[i] = roomMap[k]
	}
	return result
}
