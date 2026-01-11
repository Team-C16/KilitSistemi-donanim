// Package mqtt - Handler registry for managing handlers and their logs
package mqtt

import (
	"sync"
)

// HandlerInfo contains information about a registered handler
type HandlerInfo struct {
	Name      string
	LogBuffer *LogBuffer
	Enabled   bool
	RestartFn func() error // Function to soft-restart the handler
}

// HandlerRegistry manages all MQTT handlers and their logs
type HandlerRegistry struct {
	handlers map[string]*HandlerInfo
	mu       sync.RWMutex
}

// Global registry instance
var globalRegistry = &HandlerRegistry{
	handlers: make(map[string]*HandlerInfo),
}

// GetRegistry returns the global handler registry
func GetRegistry() *HandlerRegistry {
	return globalRegistry
}

// Register adds a handler to the registry
func (hr *HandlerRegistry) Register(name string, logBuffer *LogBuffer, restartFn func() error) {
	hr.mu.Lock()
	defer hr.mu.Unlock()

	hr.handlers[name] = &HandlerInfo{
		Name:      name,
		LogBuffer: logBuffer,
		Enabled:   true,
		RestartFn: restartFn,
	}
}

// GetHandler returns a handler by name
func (hr *HandlerRegistry) GetHandler(name string) *HandlerInfo {
	hr.mu.RLock()
	defer hr.mu.RUnlock()
	return hr.handlers[name]
}

// GetAllHandlers returns all registered handlers
func (hr *HandlerRegistry) GetAllHandlers() map[string]*HandlerInfo {
	hr.mu.RLock()
	defer hr.mu.RUnlock()

	result := make(map[string]*HandlerInfo)
	for k, v := range hr.handlers {
		result[k] = v
	}
	return result
}

// GetLogs returns logs for a specific handler
func (hr *HandlerRegistry) GetLogs(name string, n int) string {
	hr.mu.RLock()
	handler, exists := hr.handlers[name]
	hr.mu.RUnlock()

	if !exists || handler.LogBuffer == nil {
		return ""
	}
	return handler.LogBuffer.GetLogsAsString(n)
}

// IsEnabled checks if a handler is enabled
func (hr *HandlerRegistry) IsEnabled(name string) bool {
	hr.mu.RLock()
	handler, exists := hr.handlers[name]
	hr.mu.RUnlock()

	if !exists {
		return false
	}
	return handler.Enabled
}

// SetEnabled enables or disables a handler
func (hr *HandlerRegistry) SetEnabled(name string, enabled bool) {
	hr.mu.Lock()
	defer hr.mu.Unlock()

	if handler, exists := hr.handlers[name]; exists {
		handler.Enabled = enabled
		if handler.LogBuffer != nil {
			handler.LogBuffer.SetEnabled(enabled)
		}
	}
}

// SoftRestart performs a soft restart of a handler
func (hr *HandlerRegistry) SoftRestart(name string) error {
	hr.mu.RLock()
	handler, exists := hr.handlers[name]
	hr.mu.RUnlock()

	if !exists {
		return nil
	}

	if handler.RestartFn != nil {
		return handler.RestartFn()
	}
	return nil
}
