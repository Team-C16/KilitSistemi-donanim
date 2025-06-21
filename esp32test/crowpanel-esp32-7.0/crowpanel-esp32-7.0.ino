#include <lvgl.h>
#include <LovyanGFX.hpp>
#include <lgfx/v1/platforms/esp32s3/Panel_RGB.hpp>
#include <lgfx/v1/platforms/esp32s3/Bus_RGB.hpp>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <ESPAsyncWebServer.h>
#include <base64.h>
#include <time.h>
#include "jwt_helper.h"

#include "lv_lib_qrcode/lv_qrcode.h"

lv_obj_t *qr;

// --- Ekran sınıfı ---
class LGFX : public lgfx::LGFX_Device {
public:
  lgfx::Bus_RGB _bus_instance;
  lgfx::Panel_RGB _panel_instance;

  LGFX(void) {
    {
      auto cfg = _bus_instance.config();
      cfg.panel = &_panel_instance;
      cfg.pin_d0  = GPIO_NUM_15; cfg.pin_d1  = GPIO_NUM_7;  cfg.pin_d2  = GPIO_NUM_6;
      cfg.pin_d3  = GPIO_NUM_5;  cfg.pin_d4  = GPIO_NUM_4;  cfg.pin_d5  = GPIO_NUM_9;
      cfg.pin_d6  = GPIO_NUM_46; cfg.pin_d7  = GPIO_NUM_3;  cfg.pin_d8  = GPIO_NUM_8;
      cfg.pin_d9  = GPIO_NUM_16; cfg.pin_d10 = GPIO_NUM_1;  cfg.pin_d11 = GPIO_NUM_14;
      cfg.pin_d12 = GPIO_NUM_21; cfg.pin_d13 = GPIO_NUM_47; cfg.pin_d14 = GPIO_NUM_48;
      cfg.pin_d15 = GPIO_NUM_45;
      cfg.pin_henable = GPIO_NUM_41; cfg.pin_vsync = GPIO_NUM_40;
      cfg.pin_hsync = GPIO_NUM_39; cfg.pin_pclk = GPIO_NUM_0;
      cfg.freq_write = 15000000;
      cfg.hsync_polarity = 0; cfg.hsync_front_porch = 40; cfg.hsync_pulse_width = 48;
      cfg.hsync_back_porch = 40; cfg.vsync_polarity = 0; cfg.vsync_front_porch = 1;
      cfg.vsync_pulse_width = 31; cfg.vsync_back_porch = 13;
      cfg.pclk_active_neg = 1; cfg.de_idle_high = 0; cfg.pclk_idle_high = 0;
      _bus_instance.config(cfg);
    }
    {
      auto cfg = _panel_instance.config();
      cfg.memory_width = 800; cfg.memory_height = 480;
      cfg.panel_width = 800;  cfg.panel_height = 480;
      cfg.offset_x = 0; cfg.offset_y = 0;
      _panel_instance.config(cfg);
    }
    _panel_instance.setBus(&_bus_instance);
    setPanel(&_panel_instance);
  }
};

LGFX lcd;
static lv_disp_draw_buf_t draw_buf;
static lv_color_t disp_draw_buf[800 * 480 / 15];
static lv_disp_drv_t disp_drv;

void my_disp_flush(lv_disp_drv_t *disp, const lv_area_t *area, lv_color_t *color_p) {
  uint32_t w = area->x2 - area->x1 + 1;
  uint32_t h = area->y2 - area->y1 + 1;
  lcd.pushImageDMA(area->x1, area->y1, w, h, (lgfx::rgb565_t*)&color_p->full);
  lv_disp_flush_ready(disp);
}

// --- Global ayarlar ---
const char* ssid = "kerem";
const char* password = "Kerem332.";
const String jwtSecret = "DENEME";
AsyncWebServer server(80);

lv_obj_t* qrLabel = nullptr;
lv_obj_t* statusLabel = nullptr;

#define BACKLIGHT_PIN 2
#define PWM_CHANNEL 0
#define PWM_FREQ 5000      // 5kHz genellikle ekranlar için ideal
#define PWM_RESOLUTION 8  

void setup() {
  Serial.begin(115200);
  pinMode(2, OUTPUT);
  digitalWrite(2, HIGH);



  lcd.begin();
  lcd.setBrightness(255);

  lv_init();

  lv_disp_draw_buf_init(&draw_buf, disp_draw_buf, NULL, sizeof(disp_draw_buf)/sizeof(disp_draw_buf[0]));
  lv_disp_drv_init(&disp_drv);
  disp_drv.hor_res = lcd.width(); disp_drv.ver_res = lcd.height();
  disp_drv.flush_cb = my_disp_flush;
  disp_drv.draw_buf = &draw_buf;
  lv_disp_drv_register(&disp_drv);

  qrLabel = lv_label_create(lv_scr_act());
  lv_obj_align(qrLabel, LV_ALIGN_LEFT_MID, 10, 0);
  statusLabel = lv_label_create(lv_scr_act());
  lv_label_set_text(statusLabel, "Durum: Kapalı");
  lv_obj_align(statusLabel, LV_ALIGN_BOTTOM_MID, 0, -20);

  qr = lv_qrcode_create(lv_scr_act(), 150, lv_color_black(), lv_color_white());  // boyut 150x150
  lv_obj_align(qr, LV_ALIGN_CENTER, 0, 0); 

  // WiFi bağlan
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500); Serial.print(".");
  }
  Serial.println("\nWiFi bağlı");

  // Web server (kilit açma)
  server.on("/unlock", HTTP_POST, [](AsyncWebServerRequest *request){
    if (!request->hasParam("token", true)) {
      request->send(400, "text/plain", "Token yok");
      return;
    }
    String token = request->getParam("token", true)->value();
    if (token.indexOf(jwtSecret) != -1) {
      lv_label_set_text(statusLabel, "Durum: Kilit Açık");
      request->send(200, "text/plain", "Doğrulandı");
    } else {
      request->send(401, "text/plain", "Geçersiz token");
    }
  });
  server.begin();

  configTime(3 * 3600, 0, "pool.ntp.org", "time.nist.gov");

  struct tm timeinfo;
  Serial.println("Zaman senkronize ediliyor...");
  while (!getLocalTime(&timeinfo)) {
    delay(100);
  }
  Serial.println("Zaman senkronize edildi.");
}

void loop() {
  static unsigned long lastJwt = 0;

  if ((millis() - lastJwt > 60000 || lastJwt == 0) && WiFi.status() == WL_CONNECTED) {
    lastJwt = millis();

    String token = createJWT(jwtSecret, 300);
    Serial.println(token);

    HTTPClient http;
    http.begin("https://pve.izu.edu.tr/kilitSistemi/getQRCodeToken");
    http.addHeader("Content-Type", "application/json");

    DynamicJsonDocument doc(256);
    doc["room_id"] = 2;
    doc["token"] = token;
    doc["room_name"] = 1;

    String requestBody;
    serializeJson(doc, requestBody);

    int code = http.POST(requestBody);
    String responseBody = http.getString();

    Serial.print("Status code: ");
    Serial.println(code);
    Serial.print("Response body: ");
    Serial.println(responseBody);
    http.end();

    if (code == 200) {
      DynamicJsonDocument reply(256);
      DeserializationError err = deserializeJson(reply, responseBody);
      if (!err) {
        String qrToken = reply["token"].as<String>();
        lv_label_set_text_fmt(qrLabel, "QR:\n%s", qrToken.c_str());
        lv_qrcode_update(qr, qrToken.c_str(), qrToken.length());
      } else {
        lv_label_set_text_fmt(qrLabel, "JSON Error");
      }
    } else {
      lv_label_set_text_fmt(qrLabel, "HTTP Error: %d", code);
    }
  }

  lv_timer_handler();
  delay(5);
}
