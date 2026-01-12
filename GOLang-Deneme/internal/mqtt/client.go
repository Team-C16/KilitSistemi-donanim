// Package mqtt provides MQTT client functionality for device communication
package mqtt

import (
	"encoding/json"
	"fmt"
	"log"
	"sync"
	"time"

	paho "github.com/eclipse/paho.mqtt.golang"
	"github.com/golang-jwt/jwt/v5"

	"kiosk-go/internal/config"
)

// Client manages MQTT connections and subscriptions
type Client struct {
	cfg        *config.Config
	client     paho.Client
	handlers   map[string]MessageHandler
	handlersMu sync.RWMutex
	connected  bool
}

// MessageHandler is a callback for MQTT messages
type MessageHandler func(topic string, payload []byte)

// NewClient creates a new MQTT client
func NewClient(cfg *config.Config) *Client {
	return &Client{
		cfg:      cfg,
		handlers: make(map[string]MessageHandler),
	}
}

// generateToken creates a JWT token for MQTT authentication
func (c *Client) generateToken() string {
	claims := jwt.MapClaims{
		"exp": time.Now().Add(30 * time.Second).Unix(),
	}
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	tokenStr, err := token.SignedString([]byte(c.cfg.JWTSecret))
	if err != nil {
		log.Printf("MQTT: Token generation failed: %v", err)
		return ""
	}
	return tokenStr
}

// Connect establishes connection to the MQTT broker
func (c *Client) Connect() error {
	brokerURL := fmt.Sprintf("tcp://%s:%d", c.cfg.MQTTBrokerIP, c.cfg.MQTTBrokerPort)

	opts := paho.NewClientOptions().
		AddBroker(brokerURL).
		SetClientID(fmt.Sprintf("kiosk-%s-%d", c.cfg.GetMQTTID(), time.Now().Unix())).
		SetUsername(c.cfg.GetMQTTID()).
		SetPassword(c.generateToken()).
		SetAutoReconnect(false). // We handle reconnection manually for token refresh
		SetOnConnectHandler(c.onConnect).
		SetConnectionLostHandler(c.onConnectionLost)

	c.client = paho.NewClient(opts)

	token := c.client.Connect()
	if token.Wait() && token.Error() != nil {
		return fmt.Errorf("MQTT connection failed: %w", token.Error())
	}

	c.connected = true
	log.Printf("MQTT: Connected to %s", brokerURL)
	return nil
}

// onConnect is called when MQTT connection is established
func (c *Client) onConnect(client paho.Client) {
	log.Println("MQTT: Connection established")
	c.connected = true

	// Resubscribe to all handlers
	c.handlersMu.RLock()
	defer c.handlersMu.RUnlock()

	for topic := range c.handlers {
		c.subscribe(topic)
	}
}

// onConnectionLost is called when MQTT connection is lost
func (c *Client) onConnectionLost(client paho.Client, err error) {
	log.Printf("MQTT: Connection lost: %v", err)
	c.connected = false

	// Attempt reconnection with fresh token
	go c.reconnect()
}

// reconnect attempts to reconnect with a fresh JWT token
// Retries indefinitely with backoff: 5 attempts with 3s delay, then 60s wait before next batch
func (c *Client) reconnect() {
	attempt := 0
	for {
		attempt++
		log.Printf("MQTT: Attempting reconnection (attempt %d)...", attempt)

		if err := c.Connect(); err != nil {
			log.Printf("MQTT: Reconnection failed: %v", err)

			// After every 5 attempts, wait 60 seconds before next batch
			if attempt%5 == 0 {
				log.Printf("MQTT: Waiting 60 seconds before next batch of attempts...")
				time.Sleep(60 * time.Second)
			} else {
				time.Sleep(3 * time.Second)
			}
			continue
		}

		log.Printf("MQTT: Reconnection successful after %d attempts", attempt)
		break
	}
}

// subscribe subscribes to a topic
// Retries indefinitely with backoff: 5 attempts with 1s delay, then 30s wait before next batch
func (c *Client) subscribe(topic string) {
	go func() {
		attempt := 0
		for {
			attempt++

			// Wait before retry (except first attempt)
			if attempt > 1 {
				// After every 5 attempts, wait 30 seconds before next batch
				if (attempt-1)%5 == 0 {
					log.Printf("MQTT: Waiting 30 seconds before next batch of subscribe attempts to %s...", topic)
					time.Sleep(30 * time.Second)
				} else {
					time.Sleep(1 * time.Second)
				}
			}

			token := c.client.Subscribe(topic, 1, func(client paho.Client, msg paho.Message) {
				c.handlersMu.RLock()
				handler, exists := c.handlers[topic]
				c.handlersMu.RUnlock()

				if exists && handler != nil {
					handler(msg.Topic(), msg.Payload())
				}
			})

			if token.Wait() && token.Error() != nil {
				log.Printf("MQTT: Subscribe to %s failed (attempt %d): %v", topic, attempt, token.Error())
				if token.Error().Error() == "not Connected" {
					log.Printf("MQTT: Client status: connected=%v", c.client.IsConnected())
				}
				// Continue retrying indefinitely
			} else {
				log.Printf("MQTT: Subscribed to %s (after %d attempts)", topic, attempt)
				return
			}
		}
	}()
}

// Subscribe registers a handler for a topic
func (c *Client) Subscribe(topic string, handler MessageHandler) {
	c.handlersMu.Lock()
	c.handlers[topic] = handler
	c.handlersMu.Unlock()

	// Always attempt to subscribe, even if we think we aren't connected
	// Paho might queue it, or if it fails, onConnect will retry later
	c.subscribe(topic)
}

// Publish sends a message to a topic
func (c *Client) Publish(topic string, payload interface{}) error {
	if !c.connected {
		return fmt.Errorf("MQTT: not connected")
	}

	var data []byte
	switch v := payload.(type) {
	case []byte:
		data = v
	case string:
		data = []byte(v)
	default:
		var err error
		data, err = json.Marshal(payload)
		if err != nil {
			return fmt.Errorf("MQTT: marshal failed: %w", err)
		}
	}

	token := c.client.Publish(topic, 1, false, data)
	if token.Wait() && token.Error() != nil {
		return fmt.Errorf("MQTT: publish failed: %w", token.Error())
	}

	return nil
}

// Disconnect closes the MQTT connection
func (c *Client) Disconnect() {
	if c.client != nil && c.connected {
		c.client.Disconnect(1000)
		c.connected = false
		log.Println("MQTT: Disconnected")
	}
}

// IsConnected returns the connection status
func (c *Client) IsConnected() bool {
	return c.connected
}

// VerifyJWT verifies a JWT token
func VerifyJWT(tokenStr string, secret string) (jwt.MapClaims, error) {
	token, err := jwt.Parse(tokenStr, func(token *jwt.Token) (interface{}, error) {
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
		}
		return []byte(secret), nil
	})

	if err != nil {
		return nil, err
	}

	if claims, ok := token.Claims.(jwt.MapClaims); ok && token.Valid {
		return claims, nil
	}

	return nil, fmt.Errorf("invalid token")
}
