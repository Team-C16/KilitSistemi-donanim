#include "libs.h"
#define MQTT_MAX_PACKET_SIZE 16384


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

unsigned long unlockTime = 0;
bool lockOpen = false;

// --- Global ayarlar ---
const char* ssid = "BlokZincirLab";
const char* password = "Network123!";
const String jwtSecret = "DENEME";
const int room_id = 2;
const int accessType = 1;
const String base_url = "https://pve.izu.edu.tr/kilitSistemi";
//AsyncWebServer server(80);

const char* mqtt_server = "pve.izu.edu.tr";
const int mqtt_port = 1883;
const String mqtt_base_topic = String("v1/") + String(room_id).c_str(); 
WiFiClient espClient;
PubSubClient mqttClient(espClient);

lv_obj_t* qrAltYazi = nullptr;
lv_obj_t* statusLabel = nullptr;
lv_obj_t* table = nullptr;
lv_obj_t* other_table = nullptr;
lv_obj_t* timeLabel = nullptr; // <-- added: simple time label (HH:MM)
lv_obj_t* status_card = nullptr;
bool showingMainTable = true;
unsigned long lastSwitch = 0;
const unsigned long mainTableDuration = 45000;  // 45 saniye
const unsigned long otherTableDuration = 15000; // 15 saniye

extern const lv_font_t open_sans_18;

// Response coordination
String mqttLastResponse = "";
String mqttLastCorrelation = "";
String expectedCorrelation = "";
unsigned long mqttResponseRecvTime = 0;

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  // Log message details
  Serial.println("=== MQTT CALLBACK START ===");
  Serial.print("Topic: ");
  Serial.println(topic);
  Serial.print("Message Length: ");
  Serial.println(length);
  Serial.print("Free Heap: ");
  Serial.println(ESP.getFreeHeap());
  
  // Check if we have enough memory
  if (ESP.getFreeHeap() < (length * 2 + 4096)) {
    Serial.println("ERROR: Not enough memory for message processing");
    return;
  }
  
  // Check message size limit
  if (length > (MQTT_MAX_PACKET_SIZE - 256)) {
    Serial.print("ERROR: Message too large: ");
    Serial.print(length);
    Serial.print(" bytes (max: ");
    Serial.print(MQTT_MAX_PACKET_SIZE - 256);
    Serial.println(")");
    return;
  }
  
  // Create message string with proper memory management
  String msg;
  msg.reserve(length + 100); // Reserve memory to prevent fragmentation
  
  for (unsigned int i = 0; i < length; i++) {
    msg += (char)payload[i];
  }
  
  String t = String(topic);
  
  // Print first 300 characters of message for debugging
  Serial.print("Message preview: ");
  Serial.println(msg.substring(0, min((int)msg.length(), 300)));
  if (msg.length() > 300) {
    Serial.println("... (message truncated for display)");
  }
  
  // Process topics
  String unlockTopic = mqtt_base_topic + "/opendoor";
  if (t.equals(unlockTopic)) {
    Serial.println("-> Processing unlock command");
    processUnlockCommand(msg);
    return;
  }

  String qrResponseTopic = mqtt_base_topic + "/qr/response";
  if (t.equals(qrResponseTopic)) {
    Serial.println("-> Processing QR response");
    processQRResponse(msg);
    return;
  }

  String scheduleResponseTopic = mqtt_base_topic + "/schedule/response";
  if (t.equals(scheduleResponseTopic)) {
    Serial.println("-> Processing schedule response");
    processScheduleResponse(msg);
    return;
  }

  /*String scheduleDetailsTopic = mqtt_base_topic + "/scheduleDetails/response";
  if (t.equals(scheduleDetailsTopic)) {
    Serial.println("-> Processing schedule details response");
    processScheduleDetailsResponse(msg);
    return;
  }*/

  Serial.println("-> No topic matched");
  Serial.println("=== MQTT CALLBACK END ===");
}

// Separate function to handle unlock commands
void processUnlockCommand(const String& msg) {
  DynamicJsonDocument doc(1024);
  DeserializationError error = deserializeJson(doc, msg);
  
  if (error) {
    Serial.print("Unlock JSON error: ");
    Serial.println(error.c_str());
    return;
  }
  
  String token = doc["token"] | "";
  if (verifyJWT(token, jwtSecret)) {
    lv_label_set_text(statusLabel, "Kilit Açık");
    lv_obj_clear_flag(status_card, LV_OBJ_FLAG_HIDDEN);
    unlockTime = millis();
    lockOpen = true;
    Serial.println("Door unlocked successfully");
  } else {
    lv_label_set_text(statusLabel, "Geçersiz token");
    Serial.println("Invalid token for unlock");
  }
}

// Separate function to handle QR responses
void processQRResponse(const String& msg) {
  // Use larger buffer for QR response
  DynamicJsonDocument reply(2048);
  DeserializationError error = deserializeJson(reply, msg);
  
  if (error) {
    Serial.print("QR JSON error: ");
    Serial.println(error.c_str());
    return;
  }
  
  String qrToken = reply["token"].as<String>();
  String roomName = reply["room_name"].as<String>();
  
  lv_qrcode_update(qr, qrToken.c_str(), qrToken.length());
  lv_label_set_text_fmt(qrAltYazi, "Oda Adı: %s", roomName.c_str());
  
  Serial.println("QR code updated successfully");
}

// Separate function to handle schedule responses - WITH LARGE BUFFER
void processScheduleResponse(const String& msg) {
  Serial.println("*** PROCESSING SCHEDULE RESPONSE ***");
  
  // Use much larger buffer for schedule data
  DynamicJsonDocument reply(12288); // 12KB buffer for large schedule data
  
  DeserializationError error = deserializeJson(reply, msg);
  
  if (error) {
    Serial.print("Schedule JSON parsing failed: ");
    Serial.println(error.c_str());
    Serial.print("Message length was: ");
    Serial.println(msg.length());
    Serial.print("Buffer size was: ");
    Serial.println(reply.capacity());
    
    // Try with an even larger buffer
    Serial.println("Trying with larger buffer...");
    DynamicJsonDocument largeReply(20480); // 20KB buffer
    DeserializationError error2 = deserializeJson(largeReply, msg);
    
    if (error2) {
      Serial.print("Large buffer also failed: ");
      Serial.println(error2.c_str());
      return;
    } else {
      Serial.println("Large buffer succeeded!");
      reply = largeReply; // Use the successful parse
    }
  }
  
  Serial.println("Schedule JSON parsed successfully");
  Serial.print("Number of schedule items: ");
  
  JsonArray schedule = reply["schedule"].as<JsonArray>();
  Serial.println(schedule.size());
  
  // Update the table
  mark_schedule_from_json(table, msg.c_str());

  // Get current time
  time_t now = time(NULL);
  struct tm tmnow;
  localtime_r(&now, &tmnow);
  int currentHour = tmnow.tm_hour;

  const int hour_start = 9;
  int row = currentHour - hour_start + 1;
  int col = 1;
  const char* cellValue = lv_table_get_cell_value(table, row, col);

  Serial.print("Current hour: ");
  Serial.print(currentHour);
  Serial.print(", Row: ");
  Serial.print(row);
  Serial.print(", Cell value: ");
  Serial.println(cellValue ? cellValue : "NULL");

  // Check if current hour is busy
  if (cellValue && strcmp(cellValue, "DOLU") == 0) {
    Serial.println("Current slot is busy, looking for rendezvous details");
    
    String rendezvous_id = "-1";
    for (JsonObject item : schedule) {
      const char* hourStr = item["hour"];
      if (hourStr) {
        // Parse hour from "HH:MM:SS" format
        int hour = String(hourStr).substring(0, 2).toInt();
        Serial.print("Checking hour: ");
        Serial.print(hour);
        Serial.print(" against current: ");
        Serial.println(currentHour);
        
        if (hour == currentHour) {
          rendezvous_id = item["rendezvous_id"].as<String>();
          Serial.print("Found matching rendezvous_id: ");
          Serial.println(rendezvous_id);
          break;
        }
      }
    }
    
    if (rendezvous_id != "-1" && !other_table) {
      Serial.println("Requesting schedule details");
      processScheduleDetailsResponse(rendezvous_id);
    }
  } else {
    Serial.println("Current slot is empty");
    if (other_table) {
      lv_obj_del(other_table);
      other_table = nullptr;
    }
    lv_obj_clear_flag(table, LV_OBJ_FLAG_HIDDEN);
  }
  
  Serial.println("*** SCHEDULE RESPONSE PROCESSING COMPLETE ***");
}

// Separate function to handle schedule details responses
void processScheduleDetailsResponse(String rendezvous_id) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi bağlı değil!");
    return;
  }

  HTTPClient http;
  http.begin(base_url + "/getScheduleDetails");
  http.addHeader("Content-Type", "application/json");
  String token = createJWT(jwtSecret, 30);
  // JSON body (rendezvous_id + room_id + token)
  String body = "{\"rendezvous_id\":\"" + rendezvous_id + 
                "\",\"room_id\":\"" + String(room_id) + 
                "\",\"token\":\"" + token + "\"}";

  int httpResponseCode = http.POST(body);
  if (httpResponseCode > 0) {
    String payload = http.getString();
    Serial.println("Schedule Details geldi: " + payload);

    DynamicJsonDocument reply(12288);
    DeserializationError error = deserializeJson(reply, payload);
    if (error) {
      Serial.print("Schedule details JSON error: ");
      Serial.println(error.c_str());
      http.end();
      return;
    }

    if (other_table) {
      lv_obj_del(other_table);
      other_table = nullptr;
    }

    other_table = create_details_screen(lv_scr_act(), qr, payload.c_str());
    lv_obj_add_flag(other_table, LV_OBJ_FLAG_HIDDEN);

    Serial.println("Schedule details screen created");
  } else {
    Serial.print("HTTP Hatası: ");
    Serial.println(httpResponseCode);
  }

  http.end();
}


// Fix the mqttReconnect function to ensure proper subscription
bool mqttReconnect() {
  if (!mqttClient.connected()) {
    String token = createJWT(jwtSecret, 30);
    Serial.print("MQTT connecting...");
    
    // Use a unique client ID to avoid conflicts
    String clientId = "crowpanel-" + String(room_id) + "-" + String(random(0xffff), HEX);
    
    if (mqttClient.connect(clientId.c_str(), String(room_id).c_str(), token.c_str())) {
      Serial.println("connected");

      String saveipTopic = "v1/" + String(room_id) + "/saveip";
      bool ok = mqttClient.publish(saveipTopic.c_str(), "");  // boş payload
      if (ok) {
          Serial.printf("[SAVEIP] MQTT publish -> %s\n", saveipTopic.c_str());
      } else {
          Serial.printf("[SAVEIP] Hata: MQTT publish başarısız -> %s\n", saveipTopic.c_str());
      }
      
      // Subscribe to topics with QoS 1 for reliability
      String scheduleResponseTopic = mqtt_base_topic + "/schedule/response";
      String unlockTopic = mqtt_base_topic + "/opendoor";
      String qrResponseTopic = mqtt_base_topic + "/qr/response";
      String scheduleDetailsTopic = mqtt_base_topic + "/scheduleDetails/response";
      
      Serial.print("Subscribing to: ");
      Serial.println(scheduleResponseTopic);
      bool sub1 = mqttClient.subscribe(scheduleResponseTopic.c_str(), 1);
      
      Serial.print("Subscribing to: ");
      Serial.println(unlockTopic);
      bool sub2 = mqttClient.subscribe(unlockTopic.c_str(), 1);
      
      Serial.print("Subscribing to: ");
      Serial.println(qrResponseTopic);
      bool sub3 = mqttClient.subscribe(qrResponseTopic.c_str(), 1);
      
      Serial.print("Subscribing to: ");
      Serial.println(scheduleDetailsTopic);
      bool sub4 = mqttClient.subscribe(scheduleDetailsTopic.c_str(), 1);
      
      Serial.print("Subscription results: ");
      Serial.print(sub1); Serial.print(" ");
      Serial.print(sub2); Serial.print(" ");
      Serial.print(sub3); Serial.print(" ");
      Serial.println(sub4);
      
    } else {
      Serial.print("failed, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" try again in 2s");
      return false;
    }
  }
  return true;
}

// Fix the publishRequest function with better error handling
bool publishRequest(const String &topic, const String &payload) {
  Serial.print("Publishing to topic: ");
  Serial.println(topic);
  Serial.print("Payload: ");
  Serial.println(payload);
  
  unsigned long startConnect = millis();
  while (!mqttClient.connected() && millis() - startConnect < 5000) { // Increased timeout
    Serial.println("MQTT not connected, attempting reconnection...");
    mqttReconnect();
    delay(100);
  }
  
  if (!mqttClient.connected()) {
    Serial.println("Failed to connect to MQTT broker");
    return false;
  }
  
  // Use QoS 1 for reliable delivery
  bool result = mqttClient.publish(topic.c_str(), payload.c_str(), true); // retained = true
  Serial.print("Publish result: ");
  Serial.println(result ? "SUCCESS" : "FAILED");
  
  return result;
}


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

  static lv_style_t bg_style;
  lv_style_init(&bg_style);
  
  // Gradient tipini dikey yap (yukarıdan aşağıya)
  lv_style_set_bg_grad_dir(&bg_style, LV_GRAD_DIR_VER);
  
  // Gradient renkleri (örnek: üst beyaz -> alt açık gri)
  lv_style_set_bg_color(&bg_style, lv_color_hex(0xFFFFFF));   // üst
  lv_style_set_bg_grad_color(&bg_style, lv_color_hex(0xBABABA)); // alt
  
  // Bu stili main_screen’e uygula
  lv_style_set_bg_opa(&bg_style, LV_OPA_COVER);
  lv_obj_add_style(main_screen, &bg_style, LV_PART_MAIN);

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
  lv_obj_t* qr_card = lv_obj_create(main_screen);
  lv_obj_set_size(qr_card, 220, 220); // Kart boyutu (QR boyutundan biraz büyük)
  lv_obj_align(qr_card, LV_ALIGN_LEFT_MID, 0, 0);

  lv_obj_set_scrollbar_mode(qr_card, LV_SCROLLBAR_MODE_OFF);
  lv_obj_set_scroll_dir(qr_card, LV_DIR_NONE);
  
  // Kart stil
  lv_obj_set_style_radius(qr_card, 16, 0); // Köşe yuvarlama
  lv_obj_set_style_bg_color(qr_card, lv_color_hex(0xFFFFFF), 0); // Beyaz arka plan
  lv_obj_set_style_shadow_width(qr_card, 20, 0); // Gölge kalınlığı
  lv_obj_set_style_shadow_spread(qr_card, 2, 0); // Gölge yayılımı
  lv_obj_set_style_shadow_color(qr_card, lv_color_hex(0x8E4162), 0); // Gölge rengi

  lv_obj_set_style_pad_bottom(qr_card, 50, 0);
  lv_obj_set_style_pad_top(qr_card, 20, 0);
  
  // QR kod objesi kartın içinde
  qr = lv_qrcode_create(qr_card, 160, lv_color_black(), lv_color_white());
  lv_obj_center(qr); // Kartın ortasına hizala
  lv_qrcode_update(qr, "örnek veri", strlen("örnek veri"));
  
  lv_timer_handler();// To Update Spinner

  // Room Name
  qrAltYazi = lv_label_create(main_screen);
  lv_label_set_text(qrAltYazi, "");
  lv_obj_align_to(qrAltYazi, qr, LV_ALIGN_OUT_BOTTOM_LEFT, -10, 10);
  lv_obj_add_style(qrAltYazi, &NormalFontStyle, LV_PART_MAIN);
  
  lv_timer_handler();// To Update Spinner

  // Table
  

  
  lv_timer_handler();// To Update Spinner

  // --- Status Card ---
  status_card = lv_obj_create(main_screen);
  lv_obj_set_size(status_card, LV_SIZE_CONTENT, LV_SIZE_CONTENT);  
  lv_obj_align_to(status_card, qrAltYazi, LV_ALIGN_OUT_BOTTOM_LEFT, -10, 25);

  // Stil: yeşil arka plan + radius + padding + gölge
  lv_obj_set_style_radius(status_card, 12, 0);
  lv_obj_set_style_bg_color(status_card, lv_color_hex(0x4CAF50), 0);   // Başlangıç yeşil
  lv_obj_set_style_bg_grad_color(status_card, lv_color_hex(0x81C784), 0); // Daha açık yeşil
  lv_obj_set_style_bg_grad_dir(status_card, LV_GRAD_DIR_VER, 0);       // Dikey gradient
  lv_obj_set_style_shadow_width(status_card, 15, 0);
  lv_obj_set_style_shadow_color(status_card, lv_color_hex(0x2F4858), 0);
  lv_obj_set_style_pad_all(status_card, 10, 0); 

  // --- Status Label ---
  statusLabel = lv_label_create(status_card);
  lv_label_set_text(statusLabel, "");  
  lv_obj_add_style(statusLabel, &NormalFontStyle, LV_PART_MAIN);
  lv_obj_set_style_text_color(statusLabel, lv_color_hex(0xFFFFFF), 0); // beyaz yazı
  lv_obj_set_style_text_font(statusLabel, &turkish_24, 0);
  lv_timer_handler();// To Update Spinner
  lv_obj_add_flag(status_card, LV_OBJ_FLAG_HIDDEN);

  // simple time label (bottom-left) - shows HH:MM
	lv_obj_t* time_card = lv_obj_create(main_screen);
  lv_obj_set_scrollbar_mode(time_card, LV_SCROLLBAR_MODE_OFF);
	lv_obj_set_size(time_card, 820, LV_SIZE_CONTENT);  // İçeriğe göre boyut
	lv_obj_align(time_card, LV_ALIGN_BOTTOM_LEFT, -12, 4);

  lv_obj_set_style_pad_all(time_card, 12, 0);
  lv_obj_set_style_bg_color(time_card, lv_color_hex(0x8E4162), 0);        // Başlangıç rengi
  lv_obj_set_style_bg_grad_color(time_card, lv_color_hex(0x853c43), 0);   // Bitiş rengi (kırmızı ton)
  lv_obj_set_style_bg_grad_dir(time_card, LV_GRAD_DIR_VER, 0);            // Yatay gradient (sol→sağ)
  lv_obj_set_style_shadow_width(time_card, 20, 0);
  lv_obj_set_style_shadow_color(time_card, lv_color_hex(0x2F4858), 0);

	// --- Sol Label (yazı) ---
  lv_obj_t* leftLabel = lv_label_create(time_card);
  lv_label_set_text(leftLabel, " UzLock.com");  
  lv_obj_set_style_text_font(leftLabel, &turkish_better_21, 0);
  lv_obj_set_style_text_color(leftLabel, lv_color_hex(0xFFFFFF), 0);
  lv_obj_align(leftLabel, LV_ALIGN_LEFT_MID, 0, 0);
  
  // --- Sağ Label (saat) ---
  lv_obj_t* rightLabel = lv_label_create(time_card);
  lv_label_set_text(rightLabel, "--:--");
  lv_obj_set_style_text_font(rightLabel, &turkish_better_21, 0);
  lv_obj_set_style_text_color(rightLabel, lv_color_hex(0xFFFFFF), 0);
  lv_obj_align(rightLabel, LV_ALIGN_RIGHT_MID, 0, 0);
  
  // global değişken yapmak istersen
  timeLabel = rightLabel;

  lv_timer_handler();// To Update Spinner
  // --- WiFi ---
  WiFi.begin(ssid, password);
  WiFi.setSleep(false);
  while (WiFi.status() != WL_CONNECTED) {
    delay(100); Serial.print(".");
    lv_timer_handler();  
  }
  Serial.println("\nWiFi bağlı");

  mqttClient.setServer(mqtt_server, mqtt_port);
  mqttClient.setCallback(mqttCallback);
  mqttClient.setSocketTimeout(15);
  mqttReconnect();

  lv_timer_handler(); // To Update Spinner

  configTime(+3*3600, 0, "time.ume.tubitak.gov.tr", "0.tr.pool.ntp.org");


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

  table = create_schedule_table(main_screen, qr);
}

void handleTableToggle() {
    if (!other_table)
    {
      return; // diğer tablo yoksa çık
    }
    unsigned long nowMillis = millis();
    unsigned long duration = showingMainTable ? mainTableDuration : otherTableDuration;

    if (nowMillis - lastSwitch >= duration) {
        lastSwitch = nowMillis;
        showingMainTable = !showingMainTable;
        if (showingMainTable) {
            lv_obj_clear_flag(table, LV_OBJ_FLAG_HIDDEN);
            lv_obj_add_flag(other_table, LV_OBJ_FLAG_HIDDEN);
        } else {
            lv_obj_add_flag(table, LV_OBJ_FLAG_HIDDEN);
            lv_obj_clear_flag(other_table, LV_OBJ_FLAG_HIDDEN);
        }
    }
}




unsigned long lastJwt = 0;
const unsigned long interval = 60000;   // 60 sn
void loop() {
    unsigned long now = millis();

    if (lockOpen) {
        if (now - unlockTime > 10000) {  // 10 saniye geçti
            lv_obj_add_flag(status_card, LV_OBJ_FLAG_HIDDEN);
            lv_label_set_text(statusLabel, "");
            lockOpen = false;
        }
    }

    // QR isteği: her 60 sn
    if (now - lastJwt > interval || lastJwt == 0) {
        lastJwt = now;
        {
        DynamicJsonDocument doc(1024);
        doc["room_name"] = 1;
        doc["accessType"] = accessType;
        String requestBody;
        serializeJson(doc, requestBody);

        publishRequest(mqtt_base_topic + "/qr", requestBody);
        }
        {
        HTTPClient http;
        http.begin(base_url + "/getSchedule");
        http.addHeader("Content-Type", "application/json");

        DynamicJsonDocument doc2(1024);
        doc2["room_id"] = room_id;
        doc2["token"] = createJWT(jwtSecret, 30);

        String requestBody;
        serializeJson(doc2, requestBody);

        int code = http.POST(requestBody);
        String responseBody = http.getString();
        http.end();
        Serial.println(responseBody);
          if (code == 200) {
              processScheduleResponse(responseBody);
          }
        }
    }

    mqttClient.loop();
    // update simple time label once per second
    static unsigned long lastTimeUpdate = 0;
    if (millis() - lastTimeUpdate >= 1000) {
        lastTimeUpdate = millis();
        if (timeLabel) {
            struct tm timeinfo;
            if (getLocalTime(&timeinfo)) {
                char buf[6];
                strftime(buf, sizeof(buf), "%H:%M", &timeinfo);
                lv_label_set_text(timeLabel, buf);
            } else {
                lv_label_set_text(timeLabel, "--:--");
            }
        }
    }

    handleTableToggle();
    lv_timer_handler();
    delay(5);
}
