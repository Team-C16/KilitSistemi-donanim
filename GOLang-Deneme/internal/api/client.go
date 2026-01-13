// Package api provides HTTP client functionality for communicating
// with the backend API server.
package api

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"

	"github.com/golang-jwt/jwt/v5"

	"kiosk-go/internal/config"
)

// Client is the API client for backend communication
type Client struct {
	baseURL    string
	jwtSecret  string
	roomID     string
	buildingID string
	mode       config.Mode
	httpClient *http.Client
}

// NewClient creates a new API client instance
func NewClient(cfg *config.Config) *Client {
	return &Client{
		baseURL:    cfg.APIBaseURL,
		jwtSecret:  cfg.JWTSecret,
		roomID:     cfg.RoomID,
		buildingID: cfg.BuildingID,
		mode:       cfg.Mode,
		httpClient: &http.Client{
			Timeout: 10 * time.Second,
		},
	}
}

// generateToken creates a JWT token with 30-second expiry
func (c *Client) generateToken() (string, error) {
	claims := jwt.MapClaims{
		"exp": time.Now().Add(30 * time.Second).Unix(),
	}
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	return token.SignedString([]byte(c.jwtSecret))
}

// post makes a POST request to the API
func (c *Client) post(endpoint string, payload interface{}) ([]byte, error) {
	token, err := c.generateToken()
	if err != nil {
		return nil, fmt.Errorf("token generation failed: %w", err)
	}

	// Add token to payload if it's a map
	if m, ok := payload.(map[string]interface{}); ok {
		m["token"] = token
	}

	body, err := json.Marshal(payload)
	if err != nil {
		return nil, fmt.Errorf("json marshal failed: %w", err)
	}

	req, err := http.NewRequest("POST", c.baseURL+endpoint, bytes.NewBuffer(body))
	if err != nil {
		return nil, fmt.Errorf("request creation failed: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("response read failed: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("API error: status %d, body: %s", resp.StatusCode, string(respBody))
	}

	return respBody, nil
}

// ScheduleEntry represents a single schedule item
type ScheduleEntry struct {
	Day          string `json:"day"`
	Hour         string `json:"hour"`
	Title        string `json:"title"`
	FullName     string `json:"fullName"`
	RendezvousID string `json:"rendezvous_id"`
	Message      string `json:"message,omitempty"`
	Picture      string `json:"picture,omitempty"`
}

// ScheduleResponse represents the API response for schedule data
type ScheduleResponse struct {
	Schedule []ScheduleEntry `json:"schedule"`
}

// QRTokenResponse represents the response from getQRCodeToken
type QRTokenResponse struct {
	Token    string `json:"token"`
	RoomName string `json:"room_name"`
}

// IndexConfig represents a configuration index from the API
type IndexConfig struct {
	IndexName  string `json:"indexName"`
	IndexValue string `json:"indexValue"`
}

// RoomInfo represents room information from building details
type RoomInfo struct {
	RoomID   int    `json:"room_id"`
	RoomName string `json:"room_name"`
	RoomDesc string `json:"roomDesc"`
}

// BuildingDetailsResponse represents the response from getBuildingDetails
type BuildingDetailsResponse struct {
	Rooms           []RoomInfo        `json:"rooms"`
	BuildingDetails []BuildingDetails `json:"buildingDetails"`
}

// BuildingDetails represents building metadata
type BuildingDetails struct {
	BuildingName string `json:"building_name"`
}

// BuildingScheduleEntry represents a schedule entry for building mode
type BuildingScheduleEntry struct {
	RoomID       int    `json:"room_id"`
	Hour         string `json:"hour"`
	Title        string `json:"title"`
	FullName     string `json:"fullName"`
	RendezvousID string `json:"rendezvous_id"`
}

// BuildingScheduleResponse represents the response from getBuildingSchedule
type BuildingScheduleResponse struct {
	Schedule []BuildingScheduleEntry `json:"schedule"`
}

// Owner represents a room owner
type Owner struct {
	Name    string `json:"name"`
	Surname string `json:"surname"`
	Photo   string `json:"photo"` // URL to photo, can be placeholder
}

// RoomDetailsResponse represents the response from getRoomDetails
type RoomDetailsResponse struct {
	RoomName    string  `json:"room_name"`
	Description string  `json:"description"`
	MinPerson   int     `json:"min_person"`
	MaxPerson   int     `json:"max_person"`
	Owners      []Owner `json:"owners"`
}

// GetQRCodeToken fetches a new QR code token and optionally the room name
func (c *Client) GetQRCodeToken(includeRoomName bool) (*QRTokenResponse, error) {
	payload := map[string]interface{}{
		"room_id":    c.roomID,
		"accessType": "1",
	}
	if includeRoomName {
		payload["room_name"] = 1
	}

	body, err := c.post("/getQRCodeToken", payload)
	if err != nil {
		return nil, err
	}

	var resp QRTokenResponse
	if err := json.Unmarshal(body, &resp); err != nil {
		return nil, fmt.Errorf("json unmarshal failed: %w", err)
	}

	return &resp, nil
}

// GetSchedule fetches the room schedule
func (c *Client) GetSchedule() (*ScheduleResponse, error) {
	payload := map[string]interface{}{
		"room_id": c.roomID,
	}

	body, err := c.post("/getSchedule", payload)
	if err != nil {
		fmt.Printf("[DEBUG API] GetSchedule API call failed: %v\n", err)
		return nil, err
	}

	// API may return array or object
	var scheduleResp ScheduleResponse

	// Try to unmarshal as array first
	var arr []ScheduleResponse
	if err := json.Unmarshal(body, &arr); err == nil && len(arr) > 0 {
		return &arr[0], nil
	}

	// Try as direct object
	if err := json.Unmarshal(body, &scheduleResp); err != nil {
		fmt.Printf("[DEBUG API] Unmarshal failed: %v\n", err)
		return nil, fmt.Errorf("json unmarshal failed: %w", err)
	}

	return &scheduleResp, nil
}

// GetScheduleDetails fetches details for a specific meeting
func (c *Client) GetScheduleDetails(rendezvousID string) ([]ScheduleEntry, error) {
	payload := map[string]interface{}{
		"room_id":       c.roomID,
		"rendezvous_id": rendezvousID,
	}

	body, err := c.post("/getScheduleDetails", payload)
	if err != nil {
		return nil, err
	}

	var entries []ScheduleEntry
	if err := json.Unmarshal(body, &entries); err != nil {
		return nil, fmt.Errorf("json unmarshal failed: %w", err)
	}

	return entries, nil
}

// GetIndexesRasp fetches room configuration (time suffix, hours)
func (c *Client) GetIndexesRasp() ([]IndexConfig, error) {
	payload := map[string]interface{}{}

	if c.mode == config.ModeBuilding && c.buildingID != "" {
		payload["building_id"] = c.buildingID
	} else {
		payload["room_id"] = c.roomID
	}

	body, err := c.post("/getIndexesRasp", payload)
	if err != nil {
		return nil, err
	}

	var configs []IndexConfig
	if err := json.Unmarshal(body, &configs); err != nil {
		return nil, fmt.Errorf("json unmarshal failed: %w", err)
	}

	return configs, nil
}

// GetBuildingDetails fetches building information and rooms
func (c *Client) GetBuildingDetails() (*BuildingDetailsResponse, error) {
	payload := map[string]interface{}{
		"building_id": c.buildingID,
	}

	body, err := c.post("/getBuildingDetails", payload)
	if err != nil {
		return nil, err
	}

	var resp BuildingDetailsResponse
	if err := json.Unmarshal(body, &resp); err != nil {
		return nil, fmt.Errorf("json unmarshal failed: %w", err)
	}

	return &resp, nil
}

// GetBuildingSchedule fetches schedule for all rooms in a building
func (c *Client) GetBuildingSchedule() (*BuildingScheduleResponse, error) {
	payload := map[string]interface{}{
		"building_id": c.buildingID,
	}

	body, err := c.post("/getBuildingSchedule", payload)
	if err != nil {
		return nil, err
	}

	var resp BuildingScheduleResponse
	if err := json.Unmarshal(body, &resp); err != nil {
		return nil, fmt.Errorf("json unmarshal failed: %w", err)
	}

	return &resp, nil
}

// SaveIP reports the device IP to the backend
func (c *Client) SaveIP(ip string) error {
	payload := map[string]interface{}{
		"room_id": c.roomID,
		"ip":      ip,
	}

	_, err := c.post("/saveIPForRaspberry", payload)
	return err
}

// GetRoomDetails fetches room details including owners
func (c *Client) GetRoomDetails() (*RoomDetailsResponse, error) {
	payload := map[string]interface{}{
		"room_id": c.roomID,
	}

	body, err := c.post("/getRoomDetails", payload)
	if err != nil {
		return nil, err
	}

	var resp RoomDetailsResponse
	if err := json.Unmarshal(body, &resp); err != nil {
		return nil, fmt.Errorf("json unmarshal failed: %w", err)
	}

	return &resp, nil
}
