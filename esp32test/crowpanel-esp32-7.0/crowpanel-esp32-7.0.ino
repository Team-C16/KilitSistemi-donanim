#include "libs.h"


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
const char* ssid = "SUPERONLINE_WiFi_99A7";
const char* password = "UPRX4RHWHXXE";
const String jwtSecret = "DENEME";
const int room_id = 2;
const String base_url = "https://pve.izu.edu.tr/kilitSistemi/";
AsyncWebServer server(80);

lv_obj_t* qrAltYazi = nullptr;
lv_obj_t* statusLabel = nullptr;

extern const lv_font_t open_sans_18; 

unsigned long unlockTime = 0;
bool lockOpen = false;
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

  lv_obj_t* main_screen = lv_obj_create(NULL); // create a seperate main screen and loading screen
  lv_obj_remove_style_all(main_screen);

  lv_obj_t* loading_screen = lv_obj_create(NULL);
  lv_obj_remove_style_all(loading_screen);  // tüm stilleri kaldır (arka plan vs.)
  lv_scr_load(loading_screen);

  lv_obj_t* spinner = lv_spinner_create(loading_screen, 1000, 60);  // 1s full rotation, 60 arc degrees
  lv_obj_center(spinner);
  lv_timer_handler();

  static lv_style_t NormalFontStyle;
  lv_style_init(&NormalFontStyle);
  lv_style_set_text_font(&NormalFontStyle, &turkish_24);

  lv_timer_handler();// To Update Spinner

  // --- UI: QR ve Tablo ---
  // QR kodu sola koy
  qr = lv_qrcode_create(main_screen, 200, lv_color_black(), lv_color_white());
  lv_obj_align(qr, LV_ALIGN_LEFT_MID, 10, 0);
  
  lv_timer_handler();// To Update Spinner

  // Room Name
  qrAltYazi = lv_label_create(main_screen);
  lv_label_set_text(qrAltYazi, "");
  lv_obj_align_to(qrAltYazi, qr, LV_ALIGN_OUT_BOTTOM_LEFT, 0, 10);
  lv_obj_add_style(qrAltYazi, &NormalFontStyle, LV_PART_MAIN);
  
  lv_timer_handler();// To Update Spinner

  // Table
  

  
  lv_timer_handler();// To Update Spinner

  statusLabel = lv_label_create(main_screen);
  lv_label_set_text(statusLabel, "");
  lv_obj_align_to(statusLabel,qrAltYazi, LV_ALIGN_OUT_BOTTOM_LEFT, 0, 30);
  lv_obj_add_style(statusLabel, &NormalFontStyle, LV_PART_MAIN);
  
  lv_timer_handler();// To Update Spinner
  // --- WiFi ---
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(100); Serial.print(".");
    lv_timer_handler();  
  }
  Serial.println("\nWiFi bağlı");

  server.on("/unlock", HTTP_POST, [](AsyncWebServerRequest *request){
    lv_label_set_text(statusLabel, "Durum: Istek Geldi");
    if (!request->hasParam("token", true)) {
      request->send(400, "text/plain", "Token yok");
      return;
    }
    String token = request->getParam("token", true)->value();
    if (verifyJWT(token,jwtSecret)) {
      lv_label_set_text(statusLabel, "Kilit Açık");
      unlockTime = millis();   // Açılma zamanı kaydediliyor
      lockOpen = true; 
      request->send(200, "text/plain", "Doğrulandı");
    } else {
      request->send(401, "text/plain", "Geçersiz token");
    }
  });
  server.begin();

  lv_timer_handler(); // To Update Spinner

  configTime(3 * 3600, 0, "time.ume.tubitak.gov.tr", "0.tr.pool.ntp.org");


  lv_timer_handler();
  struct tm timeinfo;
  Serial.println("Zaman senkronize ediliyor...");
  while (!getLocalTime(&timeinfo)) {
    lv_timer_handler();// To Update Spinner
    delay(10);
    lv_timer_handler();  // To Update Spinner
  }
  Serial.println("Zaman senkronize edildi.");
  lv_timer_handler();// To Update Spinner
  lv_obj_clean(loading_screen);// To Delete Spinner
  lv_scr_load(main_screen); // load main screen before deleting loading
  lv_obj_del(loading_screen);

  create_schedule_table(main_screen, qr);
}

void loop() {
  static unsigned long lastJwt = 0;
  if (lockOpen) {
    if (millis() - unlockTime > 10000) {  // 10 saniye geçti
      lv_label_set_text(statusLabel, "");
      lockOpen = false;
    }
  }

  if ((millis() - lastJwt > 60000 || lastJwt == 0) && WiFi.status() == WL_CONNECTED) {
    lastJwt = millis();

    String token = createJWT(jwtSecret, 30);
    Serial.println(token);

    HTTPClient http;
    http.begin(base_url + "/getQRCodeToken");
    http.addHeader("Content-Type", "application/json");

    DynamicJsonDocument doc(256);
    doc["room_id"] = room_id;
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
        String roomName = reply["room_name"].as<String>();

        lv_qrcode_update(qr, qrToken.c_str(), qrToken.length());

        
        // Alt yazıya oda adı yaz:
        lv_label_set_text_fmt(qrAltYazi, "Oda Adı: %s", roomName.c_str());
      } else {
        Serial.println("JSON Error");
      }
    } else {
      Serial.println( "HTTP Error: " + code);
    }
  }

  lv_timer_handler();
  delay(5);
}
