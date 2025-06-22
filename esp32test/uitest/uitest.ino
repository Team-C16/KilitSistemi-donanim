#include <lvgl.h>
#include <LovyanGFX.hpp>
#include <lgfx/v1/platforms/esp32s3/Panel_RGB.hpp>
#include <lgfx/v1/platforms/esp32s3/Bus_RGB.hpp>
#include "lv_lib_qrcode/lv_qrcode.h"

class LGFX : public lgfx::LGFX_Device {
public:
  lgfx::Bus_RGB _bus_instance;
  lgfx::Panel_RGB _panel_instance;

  LGFX(void) {
    auto cfg = _bus_instance.config();
    cfg.panel = &_panel_instance;

    cfg.pin_d0  = GPIO_NUM_15; cfg.pin_d1  = GPIO_NUM_7;  cfg.pin_d2  = GPIO_NUM_6;
    cfg.pin_d3  = GPIO_NUM_5;  cfg.pin_d4  = GPIO_NUM_4;  cfg.pin_d5  = GPIO_NUM_9;
    cfg.pin_d6  = GPIO_NUM_46; cfg.pin_d7  = GPIO_NUM_3;  cfg.pin_d8  = GPIO_NUM_8;
    cfg.pin_d9  = GPIO_NUM_16; cfg.pin_d10 = GPIO_NUM_1;  cfg.pin_d11 = GPIO_NUM_14;
    cfg.pin_d12 = GPIO_NUM_21; cfg.pin_d13 = GPIO_NUM_47; cfg.pin_d14 = GPIO_NUM_48;
    cfg.pin_d15 = GPIO_NUM_45;

    cfg.pin_henable = GPIO_NUM_41; cfg.pin_vsync = GPIO_NUM_40;
    cfg.pin_hsync = GPIO_NUM_39;   cfg.pin_pclk  = GPIO_NUM_0;

    cfg.freq_write = 8000000;  // Daha stabil olması için düşürüldü
    cfg.hsync_polarity = 1; cfg.hsync_front_porch = 40; cfg.hsync_pulse_width = 48;
    cfg.hsync_back_porch = 40;
    cfg.vsync_polarity = 1; cfg.vsync_front_porch = 1; cfg.vsync_pulse_width = 31;
    cfg.vsync_back_porch = 13;

    cfg.pclk_active_neg = 0; cfg.de_idle_high = 1; cfg.pclk_idle_high = 0;

    _bus_instance.config(cfg);

    auto pcfg = _panel_instance.config();
    pcfg.memory_width = 800; pcfg.memory_height = 480;
    pcfg.panel_width = 800;  pcfg.panel_height = 480;
    pcfg.offset_x = 0;       pcfg.offset_y = 0;
    _panel_instance.config(pcfg);

    _panel_instance.setBus(&_bus_instance);
    setPanel(&_panel_instance);
  }
};

LGFX lcd;

// LVGL ile ilgili buffer ve driver
static lv_disp_draw_buf_t draw_buf;
static lv_color_t buf[800 * 60]; // Daha küçük buffer: RAM dostu
static lv_indev_drv_t indev_drv;

// Flush callback
void lv_disp_flush(lv_disp_drv_t *disp, const lv_area_t *area, lv_color_t *color_p) {
  lcd.pushImage(area->x1, area->y1, area->x2 - area->x1 + 1, area->y2 - area->y1 + 1, (lgfx::rgb565_t *)color_p);
  lv_disp_flush_ready(disp);
}

// Touch callback
void lv_touch_read(lv_indev_drv_t *indev_driver, lv_indev_data_t *data) {
  uint16_t touchX, touchY;
  bool touched = lcd.getTouch(&touchX, &touchY);

  if (touched) {
    data->state = LV_INDEV_STATE_PR;
    data->point.x = touchX;
    data->point.y = touchY;
  } else {
    data->state = LV_INDEV_STATE_REL;
  }
}

// UI
void create_ui() {
  lv_obj_t *scr = lv_scr_act();

  lv_obj_set_style_bg_color(scr, lv_color_hex(0x1a213d), LV_PART_MAIN);

  lv_obj_t *top_bar = lv_obj_create(scr);
  lv_obj_set_size(top_bar, LV_PCT(100), 60);
  lv_obj_align(top_bar, LV_ALIGN_TOP_MID, 0, 0);
  lv_obj_set_style_bg_color(top_bar, lv_color_hex(0x3f51b5), LV_PART_MAIN);
  lv_obj_set_style_border_width(top_bar, 0, LV_PART_MAIN);
  lv_obj_clear_flag(top_bar, LV_OBJ_FLAG_SCROLLABLE);

  lv_obj_t *header_label = lv_label_create(top_bar);
  lv_label_set_text(header_label, "Odaya Erişim");
  lv_obj_set_style_text_color(header_label, lv_color_white(), LV_PART_MAIN);
  lv_obj_set_style_text_font(header_label, &lv_font_montserrat_24, LV_PART_MAIN);
  lv_obj_align(header_label, LV_ALIGN_CENTER, 0, 0);

  lv_obj_t *left_panel = lv_obj_create(scr);
  lv_obj_set_size(left_panel, 240, 400);
  lv_obj_align(left_panel, LV_ALIGN_LEFT_MID, 10, 10);
  lv_obj_set_style_bg_color(left_panel, lv_color_white(), LV_PART_MAIN);

  // QR
  lv_obj_t *qr = lv_qrcode_create(left_panel, 180, lv_color_black(), lv_color_white());
  lv_qrcode_update(qr, "EGC16", strlen("EGC16"));
  lv_obj_align(qr, LV_ALIGN_CENTER, 0, -20);

  lv_obj_t *qr_label = lv_label_create(left_panel);
  lv_label_set_text(qr_label, "QR Kodu Taratın");
  lv_obj_set_style_text_color(qr_label, lv_color_black(), LV_PART_MAIN);
  lv_obj_align(qr_label, LV_ALIGN_CENTER, 0, 80);

  lv_obj_t *right_panel = lv_obj_create(scr);
  lv_obj_set_size(right_panel, 520, 400);
  lv_obj_align(right_panel, LV_ALIGN_RIGHT_MID, -10, 10);
  lv_obj_set_style_bg_color(right_panel, lv_color_white(), LV_PART_MAIN);

  lv_obj_t *calendar_table = lv_table_create(right_panel);
  lv_obj_set_size(calendar_table, lv_obj_get_width(right_panel), lv_obj_get_height(right_panel));
  lv_obj_align(calendar_table, LV_ALIGN_CENTER, 0, 0);

  int cols = 6, rows = 11;
  lv_table_set_col_cnt(calendar_table, cols);
  lv_table_set_row_cnt(calendar_table, rows);

  lv_table_set_col_width(calendar_table, 0, 70);
  for (int i = 1; i < cols; ++i) {
    lv_table_set_col_width(calendar_table, i, 70);
  }

  const char *days[] = {"Saat", "Cum", "Paz", "Pzt", "Sal", "Çar"};
  for (int i = 0; i < cols; ++i) {
    lv_table_set_cell_value(calendar_table, 0, i, days[i]);
  }

  const char *times[] = {"09:00", "10:00", "11:00", "12:00", "13:00",
                         "14:00", "15:00", "16:00", "17:00", "18:00"};

  for (int r = 1; r <= 10; ++r) {
    lv_table_set_cell_value(calendar_table, r, 0, times[r - 1]);
    for (int c = 1; c < cols; ++c) {
      lv_table_set_cell_value(calendar_table, r, c, "Uygun");
    }
  }

  // Dolu örnek hücreler
  lv_table_set_cell_value(calendar_table, 2, 1, "DOLU");
  lv_table_set_cell_value(calendar_table, 5, 3, "DOLU");
}

void setup() {
  pinMode(2, OUTPUT);
  digitalWrite(2, HIGH);  // BLK pinin bağlı olduğu GPIO numarası

  Serial.begin(115200);
  delay(1000);

  // lcd ve ekran
  lcd.begin();
  lcd.setBrightness(255);

  // PSRAM varsa bunu dene
  esp_spiram_init_cache();

  lv_init();
  lv_color_t* buf1 = (lv_color_t*)heap_caps_malloc(800 * 40 * sizeof(lv_color_t), MALLOC_CAP_DMA);
  lv_disp_draw_buf_init(&draw_buf, buf1, NULL, 800 * 40);

  lv_disp_drv_t disp_drv;
  lv_disp_drv_init(&disp_drv);
  disp_drv.hor_res = lcd.width();
  disp_drv.ver_res = lcd.height();
  disp_drv.flush_cb = lv_disp_flush;
  disp_drv.draw_buf = &draw_buf;
  lv_disp_drv_register(&disp_drv);

  lv_indev_drv_init(&indev_drv);
  indev_drv.type = LV_INDEV_TYPE_POINTER;
  indev_drv.read_cb = lv_touch_read;
  lv_indev_drv_register(&indev_drv);

  create_ui();

  Serial.println("Ekran Hazır!");
}

void loop() {
  lv_timer_handler();
  delay(5);
}
