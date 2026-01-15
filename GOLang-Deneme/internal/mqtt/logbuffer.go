// Package mqtt - Log buffer for handler logging
package mqtt

import (
	"fmt"
	"sync"
	"time"
)

// LogBuffer stores a ring buffer of log messages for a handler
type LogBuffer struct {
	name    string
	logs    []LogEntry
	maxSize int
	mu      sync.RWMutex
	enabled bool
}

// LogEntry represents a single log entry
type LogEntry struct {
	Time    time.Time
	Level   string
	Message string
}

// NewLogBuffer creates a new log buffer with the given name and max size
func NewLogBuffer(name string, maxSize int) *LogBuffer {
	return &LogBuffer{
		name:    name,
		logs:    make([]LogEntry, 0, maxSize),
		maxSize: maxSize,
		enabled: true,
	}
}

// Log adds a log entry to the buffer
func (lb *LogBuffer) Log(level, format string, args ...interface{}) {
	lb.mu.Lock()
	defer lb.mu.Unlock()

	entry := LogEntry{
		Time:    time.Now(),
		Level:   level,
		Message: fmt.Sprintf(format, args...),
	}

	// Add to ring buffer
	if len(lb.logs) >= lb.maxSize {
		lb.logs = lb.logs[1:] // Remove oldest
	}
	lb.logs = append(lb.logs, entry)

	// Only print ERROR level to console
	if level == "ERROR" {
		fmt.Printf("%s [%s] %s: %s\n", entry.Time.Format("15:04:05"), entry.Level, lb.name, entry.Message)
	}
}

// Info logs an info message
func (lb *LogBuffer) Info(format string, args ...interface{}) {
	lb.Log("INFO", format, args...)
}

// Error logs an error message
func (lb *LogBuffer) Error(format string, args ...interface{}) {
	lb.Log("ERROR", format, args...)
}

// Warn logs a warning message
func (lb *LogBuffer) Warn(format string, args ...interface{}) {
	lb.Log("WARN", format, args...)
}

// GetLogs returns the last n log entries as formatted strings
func (lb *LogBuffer) GetLogs(n int) []string {
	lb.mu.RLock()
	defer lb.mu.RUnlock()

	start := 0
	if len(lb.logs) > n {
		start = len(lb.logs) - n
	}

	result := make([]string, 0, n)
	for i := start; i < len(lb.logs); i++ {
		entry := lb.logs[i]
		result = append(result, fmt.Sprintf("[%s] %s: %s",
			entry.Time.Format("15:04:05"), entry.Level, entry.Message))
	}
	return result
}

// GetLogsAsString returns logs as a single string
func (lb *LogBuffer) GetLogsAsString(n int) string {
	logs := lb.GetLogs(n)
	result := ""
	for _, log := range logs {
		result += log + "\n"
	}
	return result
}

// Clear clears the log buffer
func (lb *LogBuffer) Clear() {
	lb.mu.Lock()
	defer lb.mu.Unlock()
	lb.logs = lb.logs[:0]
}

// SetEnabled sets the enabled state
func (lb *LogBuffer) SetEnabled(enabled bool) {
	lb.mu.Lock()
	defer lb.mu.Unlock()
	lb.enabled = enabled
}

// IsEnabled returns the enabled state
func (lb *LogBuffer) IsEnabled() bool {
	lb.mu.RLock()
	defer lb.mu.RUnlock()
	return lb.enabled
}

// GetName returns the buffer name
func (lb *LogBuffer) GetName() string {
	return lb.name
}
