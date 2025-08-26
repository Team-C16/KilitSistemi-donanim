# Use Arduino IDE believe me i used every other thing and only this worked
Wiki: https://www.elecrow.com/wiki/Get_Started_with_Arduino_IDE.html

## First Setup
first add additional board manager url to arduino ide URL:  https://espressif.github.io/arduino-esp32/package_esp32_index.json

then install this in the board manager esp32 > 2.0.15

## Libraries 
lvgl > 8.3.3

LovyanGFX > 1.2.7

WiFi > 1.2.5

ArduinoJson > 7.4.2

ESP Async WebServer > 3.7.8

## Board Settings:

### Board Name: ESP32S3 Dev Module
USB CDC On Boot: Disabled
CPU Freq: 240MHz (Wifi)
Core debug level: None
USB DFU On Boot: Disabled
Erase All Flash Before Sketch Upload: Disabled
Events Run On: Core 1
Flash Mode: QIO 80MHz
### Flash Size: 4MB(32Mb)
JTAG Adapter: Disabled
Arduino Runs On: Core 1
### Partition Scheme: Huge APP (3MB No OTA / 1MB SPIFFS)
### PSRAM: OPI PSRAM
Upload Mode: UART0 /Hardware CDC
Upload Speed: 921600
USB Mode: Hardware CDC and JTAG
