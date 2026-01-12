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
}

// DefaultTimeConfig returns the default time configuration
func DefaultTimeConfig() TimeConfig {
	return TimeConfig{
		TimeSuffix: ":30",
		StartHour:  9,
		EndHour:    19,
	}
}

// GenerateHours creates a list of hour strings based on the time config
// Both StartHour and EndHour are inclusive (e.g., 9-18 produces 9:30,...,18:30)
func (tc TimeConfig) GenerateHours() []string {
	hours := make([]string, 0, tc.EndHour-tc.StartHour+1)
	for h := tc.StartHour; h <= tc.EndHour; h++ {
		hours = append(hours, fmt.Sprintf("%02d%s", h, tc.TimeSuffix))
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

		// Parse hour and apply suffix
		hourPart := strings.Split(entry.Hour, ":")[0]
		var h int
		fmt.Sscanf(hourPart, "%d", &h)
		hourStr := fmt.Sprintf("%02d%s", h, tc.TimeSuffix)

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
func TransformBuildingSchedule(apiData *api.BuildingScheduleResponse, roomMap map[int]string, hours []string) RoomSchedule {
	schedule := make(RoomSchedule)

	// Initialize empty schedule for each room
	for _, roomName := range roomMap {
		schedule[roomName] = make(DaySchedule)
		for _, hour := range hours {
			schedule[roomName][hour] = &ScheduleSlot{
				Status: SlotEmpty,
			}
		}
	}

	// Fill in from API data
	for _, entry := range apiData.Schedule {
		roomName, exists := roomMap[entry.RoomID]
		if !exists {
			continue
		}

		// Parse hour (format: "09:00:00" -> "09:00")
		hourFmt := entry.Hour
		if len(hourFmt) > 5 {
			hourFmt = hourFmt[:5]
		}

		if roomSchedule, exists := schedule[roomName]; exists {
			if slot, slotExists := roomSchedule[hourFmt]; slotExists {
				slot.Status = SlotOccupied
				slot.Activity = entry.Title
				if slot.Activity == "" {
					slot.Activity = "Dolu"
				}
				slot.Organizer = entry.FullName
				slot.RendezvousID = entry.RendezvousID
			}
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

	// Parse hour from hourStr
	var slotHour int
	fmt.Sscanf(hourStr, "%d", &slotHour)

	// Parse minute from suffix
	suffixMinute := 0
	if len(tc.TimeSuffix) > 1 {
		fmt.Sscanf(tc.TimeSuffix[1:], "%d", &suffixMinute)
	}

	// Create slot start and end times
	startTime := time.Date(now.Year(), now.Month(), now.Day(), slotHour, suffixMinute, 0, 0, now.Location())
	endTime := startTime.Add(time.Hour)

	return now.After(startTime) && now.Before(endTime)
}

// GetCurrentHourString returns the formatted hour string for the current time
func GetCurrentHourString(tc TimeConfig) string {
	now := time.Now()
	suffixMinute := 0
	if len(tc.TimeSuffix) > 1 {
		fmt.Sscanf(tc.TimeSuffix[1:], "%d", &suffixMinute)
	}

	targetHour := now.Hour()
	if now.Minute() < suffixMinute {
		targetHour--
	}

	return fmt.Sprintf("%02d%s", targetHour, tc.TimeSuffix)
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
