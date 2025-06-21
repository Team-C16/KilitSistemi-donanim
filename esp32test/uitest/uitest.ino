#include <lvgl.h>
#include <LovyanGFX.hpp>
#include <lgfx/v1/platforms/esp32s3/Panel_RGB.hpp>
#include <lgfx/v1/platforms/esp32s3/Bus_RGB.hpp>
// #include <lgfx/v1/platforms/esp32s3/Panel_RGB.hpp> // Eğer RGB panel kullanılıyorsa
// #include <lgfx/v1/platforms/esp32s3/Bus_RGB.hpp>   // Eğer RGB bus kullanılıyorsa
// Not: LovyanGFX'in kendisi genellikle doğru platform dosyalarını içerir.
// Eğer özel bir RGB paneliniz varsa ve tanımlaması gerekiyorsa bu satırları kullanın.
// Aksi takdirde LovyanGFX örneğine bakın.

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

LGFX lcd; // LovyanGFX nesnesi

#include "lv_lib_qrcode/lv_qrcode.h"

// LVGL tamponları
static lv_disp_draw_buf_t draw_buf;
static lv_color_t buf[800 * 480 / 1.7]; // Küçük bir tampon, performans için büyütülebilir
static lv_indev_drv_t indev_drv;

/* Ekran sürücüsü için çağrı fonksiyonu */
void lv_disp_flush(lv_disp_drv_t *disp, const lv_area_t *area, lv_color_t *color_p)
{
    lcd.pushImage(area->x1, area->y1, area->x2 - area->x1 + 1, area->y2 - area->y1 + 1, (lgfx::rgb565_t *)color_p);
    lv_disp_flush_ready(disp);
}

/* Dokunmatik sürücüsü için çağrı fonksiyonu */
void lv_touch_read(lv_indev_drv_t *indev_driver, lv_indev_data_t *data)
{
    uint16_t touchX, touchY;
    bool touched = lcd.getTouch(&touchX, &touchY);

    if (touched) {
        data->state = LV_INDEV_STATE_PR; // Basıldı
        data->point.x = touchX;
        data->point.y = touchY;
    } else {
        data->state = LV_INDEV_STATE_REL; // Bırakıldı
    }
}

// Global LVGL objeleri
lv_obj_t *screen;
lv_obj_t *left_panel;
lv_obj_t *right_panel;
lv_obj_t *calendar_table;
lv_obj_t *qr_code_obj;

void create_ui() {
    screen = lv_obj_create(NULL);
    lv_obj_set_size(screen, LV_SIZE_CONTENT, LV_SIZE_CONTENT); // Ekran boyutunda olsun
    lv_disp_load_scr(screen);

    // Ana konteyner (ekranın tamamını kaplasın)
    lv_obj_set_size(screen, LV_HOR_RES, LV_VER_RES);
    lv_obj_set_style_pad_all(screen, 0, LV_PART_MAIN);
    lv_obj_set_style_bg_color(screen, lv_color_hex(0x1a213d), LV_PART_MAIN); // Koyu arka plan

    // Üst Bar
    lv_obj_t *top_bar = lv_obj_create(screen);
    lv_obj_set_size(top_bar, LV_PCT(100), 60); // Genişlik %100, yükseklik 60px
    lv_obj_align(top_bar, LV_ALIGN_TOP_MID, 0, 0);
    lv_obj_set_style_bg_color(top_bar, lv_color_hex(0x3f51b5), LV_PART_MAIN); // Mavi ton
    lv_obj_set_style_border_width(top_bar, 0, LV_PART_MAIN);
    lv_obj_set_style_radius(top_bar, 0, LV_PART_MAIN);
    lv_obj_set_style_pad_all(top_bar, 0, LV_PART_MAIN);

    lv_obj_t *header_label = lv_label_create(top_bar);
    lv_label_set_text(header_label, "Odaya Erişim");
    lv_obj_set_style_text_color(header_label, lv_color_white(), LV_PART_MAIN);
    lv_obj_set_style_text_font(header_label, &lv_font_montserrat_24, LV_PART_MAIN);
    lv_obj_align(header_label, LV_ALIGN_CENTER, 0, 0);

    // Alt Bar
    lv_obj_t *bottom_bar = lv_obj_create(screen);
    lv_obj_set_size(bottom_bar, LV_PCT(100), 50); // Genişlik %100, yükseklik 50px
    lv_obj_align(bottom_bar, LV_ALIGN_BOTTOM_MID, 0, 0);
    lv_obj_set_style_bg_color(bottom_bar, lv_color_hex(0x2196f3), LV_PART_MAIN); // Mavi ton
    lv_obj_set_style_border_width(bottom_bar, 0, LV_PART_MAIN);
    lv_obj_set_style_radius(bottom_bar, 0, LV_PART_MAIN);
    lv_obj_set_style_pad_all(bottom_bar, 0, LV_PART_MAIN);

    // Alt bar içeriği
    lv_obj_t *footer_label_left = lv_label_create(bottom_bar);
    lv_label_set_text(footer_label_left, LV_SYMBOL_FILE " Oda Rezervasyon Sistemi");
    lv_obj_set_style_text_color(footer_label_left, lv_color_white(), LV_PART_MAIN);
    lv_obj_set_style_text_font(footer_label_left, &lv_font_montserrat_16, LV_PART_MAIN);
    lv_obj_align(footer_label_left, LV_ALIGN_LEFT_MID, 10, 0);

    lv_obj_t *footer_label_right = lv_label_create(bottom_bar);
    lv_label_set_text(footer_label_right, "21.06.2025 • 22:41:58"); // Statik tarih/saat
    lv_obj_set_style_text_color(footer_label_right, lv_color_white(), LV_PART_MAIN);
    lv_obj_set_style_text_font(footer_label_right, &lv_font_montserrat_16, LV_PART_MAIN);
    lv_obj_align(footer_label_right, LV_ALIGN_RIGHT_MID, -10, 0);

    // Ana İçerik Alanı
    lv_obj_t *content_area = lv_obj_create(screen);
    lv_obj_set_size(content_area, LV_PCT(100), LV_SIZE_CONTENT);
    lv_obj_set_height(content_area, LV_VER_RES - lv_obj_get_height(top_bar) - lv_obj_get_height(bottom_bar));
    lv_obj_align_to(content_area, top_bar, LV_ALIGN_OUT_BOTTOM_LEFT, 0, 0);
    lv_obj_set_style_bg_color(content_area, lv_color_hex(0x1a213d), LV_PART_MAIN); // Koyu arka plan
    lv_obj_set_style_border_width(content_area, 0, LV_PART_MAIN);
    lv_obj_set_style_radius(content_area, 0, LV_PART_MAIN);
    lv_obj_set_style_pad_all(content_area, 0, LV_PART_MAIN);
    lv_obj_set_flex_flow(content_area, LV_FLEX_FLOW_ROW); // Yan yana düzen

    // Sol Panel (QR Kodu ve Metin)
    left_panel = lv_obj_create(content_area);
    lv_obj_set_width(left_panel, LV_PCT(30)); // %30 genişlik
    lv_obj_set_height(left_panel, LV_PCT(100));
    lv_obj_set_style_bg_color(left_panel, lv_color_white(), LV_PART_MAIN);
    lv_obj_set_style_border_width(left_panel, 0, LV_PART_MAIN);
    lv_obj_set_style_radius(left_panel, 0, LV_PART_MAIN);
    lv_obj_set_style_pad_all(left_panel, 10, LV_PART_MAIN);
    lv_obj_set_flex_flow(left_panel, LV_FLEX_FLOW_COLUMN);
    lv_obj_set_flex_align(left_panel, LV_FLEX_ALIGN_CENTER, LV_FLEX_ALIGN_CENTER, LV_FLEX_ALIGN_CENTER);

    // QR Kodu
    qr_code_obj = lv_qrcode_create(left_panel, 180, lv_color_black(), lv_color_white());
    lv_qrcode_update(qr_code_obj, "EGC16", strlen("EGC16")); // Statik QR kodu içeriği
    lv_obj_set_align(qr_code_obj, LV_ALIGN_CENTER);

    lv_obj_t *qr_label = lv_label_create(left_panel);
    lv_label_set_text(qr_label, "QR Kodu Uygulamadan Taratın");
    lv_obj_set_style_text_align(qr_label, LV_TEXT_ALIGN_CENTER, LV_PART_MAIN);
    lv_obj_set_style_text_font(qr_label, &lv_font_montserrat_18, LV_PART_MAIN);
    lv_obj_set_style_text_color(qr_label, lv_color_black(), LV_PART_MAIN);
    lv_obj_align(qr_label, LV_ALIGN_CENTER, 0, 10); // QR kodunun altına biraz boşluk

    lv_obj_t *egc_code_label = lv_label_create(left_panel);
    lv_label_set_text(egc_code_label, LV_SYMBOL_HOME " EGC16"); // Simgeli metin
    lv_obj_set_style_text_color(egc_code_label, lv_color_hex(0x2196f3), LV_PART_MAIN); // Mavi renk
    lv_obj_set_style_text_font(egc_code_label, &lv_font_montserrat_20, LV_PART_MAIN);
    lv_obj_align(egc_code_label, LV_ALIGN_CENTER, 0, 20);


    // Sağ Panel (Takvim Tablosu)
    right_panel = lv_obj_create(content_area);
    lv_obj_set_width(right_panel, LV_PCT(70)); // %70 genişlik
    lv_obj_set_height(right_panel, LV_PCT(100));
    lv_obj_set_style_bg_color(right_panel, lv_color_white(), LV_PART_MAIN);
    lv_obj_set_style_border_width(right_panel, 0, LV_PART_MAIN);
    lv_obj_set_style_radius(right_panel, 0, LV_PART_MAIN);
    lv_obj_set_style_pad_all(right_panel, 0, LV_PART_MAIN); // İç boşluk yok

    // Takvim Başlıkları
    lv_obj_t *calendar_header_cont = lv_obj_create(right_panel);
    lv_obj_set_size(calendar_header_cont, LV_PCT(100), 40);
    lv_obj_set_style_bg_color(calendar_header_cont, lv_color_hex(0x42A5F5), LV_PART_MAIN); // Açık mavi
    lv_obj_set_style_border_width(calendar_header_cont, 0, LV_PART_MAIN);
    lv_obj_set_style_radius(calendar_header_cont, 0, LV_PART_MAIN);
    lv_obj_set_style_pad_all(calendar_header_cont, 0, LV_PART_MAIN);
    lv_obj_set_flex_flow(calendar_header_cont, LV_FLEX_FLOW_ROW);
    lv_obj_set_flex_align(calendar_header_cont, LV_FLEX_ALIGN_SPACE_AROUND, LV_FLEX_ALIGN_CENTER, LV_FLEX_ALIGN_CENTER);

    const char *days[] = {"Saat", "Cumartesi", "Pazar", "Pazartesi", "Salı", "Çarşamba"};
    for (int i = 0; i < sizeof(days)/sizeof(days[0]); ++i) {
        lv_obj_t *day_label = lv_label_create(calendar_header_cont);
        lv_label_set_text(day_label, days[i]);
        lv_obj_set_style_text_color(day_label, lv_color_white(), LV_PART_MAIN);
        lv_obj_set_style_text_font(day_label, &lv_font_montserrat_16, LV_PART_MAIN);
        lv_obj_set_width(day_label, lv_pct(16)); // Her sütun eşit genişlik
        lv_obj_set_style_text_align(day_label, LV_TEXT_ALIGN_CENTER, LV_PART_MAIN);
    }

    // Takvim Tablosu (lv_table)
    calendar_table = lv_table_create(right_panel);
    lv_obj_set_size(calendar_table, LV_PCT(100), LV_SIZE_CONTENT);
    lv_obj_align_to(calendar_table, calendar_header_cont, LV_ALIGN_OUT_BOTTOM_LEFT, 0, 0);
    lv_obj_set_flex_grow(calendar_table, 1); // Kalan alanı kaplasın

    // Sütun ve satır sayıları
    int num_cols = 6; // Saat, Cumartesi, Pazar, Pazartesi, Salı, Çarşamba
    int num_rows = 11; // 09:00'dan 18:00'a kadar 10 saat + 1 başlık satırı

    lv_table_set_col_cnt(calendar_table, num_cols);
    lv_table_set_row_cnt(calendar_table, num_rows);

    // Sütun genişlikleri
    lv_table_set_col_width(calendar_table, 0, 70); // Saat sütunu
    for (int i = 1; i < num_cols; ++i) {
        lv_table_set_col_width(calendar_table, i, (lv_obj_get_width(right_panel) - 70) / (num_cols - 1));
    }

    // Tablo stilleri
    lv_obj_set_style_bg_color(calendar_table, lv_color_white(), LV_PART_MAIN);
    lv_obj_set_style_border_width(calendar_table, 1, LV_PART_MAIN);
    lv_obj_set_style_border_color(calendar_table, lv_color_hex(0xD3D3D3), LV_PART_MAIN); // Gri kenarlık

    // Hücre stilleri
    lv_obj_set_style_border_color(calendar_table, lv_color_hex(0xD3D3D3), LV_PART_ITEMS); // Hücre kenarlıkları
    lv_obj_set_style_border_width(calendar_table, 1, LV_PART_ITEMS);
    lv_obj_set_style_text_align(calendar_table, LV_TEXT_ALIGN_CENTER, LV_PART_ITEMS);
    lv_obj_set_style_text_font(calendar_table, &lv_font_montserrat_14, LV_PART_ITEMS);
    lv_obj_set_style_pad_all(calendar_table, 5, LV_PART_ITEMS);

    // Saatleri doldur
    const char *times[] = {"09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00"};
    for (int r = 0; r < 10; ++r) {
        lv_table_set_cell_value(calendar_table, r, 0, times[r]);
        lv_obj_set_style_bg_color(calendar_table, lv_color_hex(0xE0E0E0), LV_PART_ITEMS | (r * num_cols + 0)); // Saat sütunu arka planı
    }

    // Statik randevu durumlarını doldur (örnek)
    for (int r = 0; r < 10; ++r) { // Saatler
        for (int c = 1; c < num_cols; ++c) { // Günler (Saat sütununu atla)
            // Başlangıçta tüm hücreleri "Randevu Uygun" olarak ayarla
            lv_table_set_cell_value(calendar_table, r, c, "Randevu\nUygun");
            lv_obj_set_style_bg_color(calendar_table, lv_color_hex(0xE8F5E9), LV_PART_ITEMS | (r * num_cols + c)); // Açık yeşil
            lv_obj_set_style_text_color(calendar_table, lv_color_hex(0x4CAF50), LV_PART_ITEMS | (r * num_cols + c)); // Yeşil metin
        }
    }

    // Bazı statik dolu hücreler (örnek)
    // Cumartesi 10:00
    lv_table_set_cell_value(calendar_table, 1, 1, "DOLU");
    lv_obj_set_style_bg_color(calendar_table, lv_color_hex(0xFFEBEE), LV_PART_ITEMS | (1 * num_cols + 1)); // Açık kırmızı
    lv_obj_set_style_text_color(calendar_table, lv_color_hex(0xF44336), LV_PART_ITEMS | (1 * num_cols + 1)); // Kırmızı metin

    // Pazartesi 14:00
    lv_table_set_cell_value(calendar_table, 5, 3, "DOLU");
    lv_obj_set_style_bg_color(calendar_table, lv_color_hex(0xFFEBEE), LV_PART_ITEMS | (5 * num_cols + 3));
    lv_obj_set_style_text_color(calendar_table, lv_color_hex(0xF44336), LV_PART_ITEMS | (5 * num_cols + 3));

    // Salı 11:00
    lv_table_set_cell_value(calendar_table, 2, 4, "DOLU");
    lv_obj_set_style_bg_color(calendar_table, lv_color_hex(0xFFEBEE), LV_PART_ITEMS | (2 * num_cols + 4));
    lv_obj_set_style_text_color(calendar_table, lv_color_hex(0xF44336), LV_PART_ITEMS | (2 * num_cols + 4));

    // Hücre kenarlıklarını gizlemek veya özelleştirmek için:
    // lv_obj_set_style_border_width(calendar_table, 0, LV_PART_ITEMS); // Tüm hücre kenarlıklarını kaldır

}

void setup() {
    Serial.begin(115200);
    delay(1000); // LovyanGFX init için biraz bekleme

    pinMode(2, OUTPUT);
    digitalWrite(2, HIGH);

    // LovyanGFX'i başlat
    lcd.begin();
    lcd.setBrightness(255);

    // LVGL'yi başlat
    lv_init();

    // LVGL display driver'ı kaydet
    lv_disp_drv_t disp_drv;
    lv_disp_drv_init(&disp_drv);
    disp_drv.hor_res = lcd.width();
    disp_drv.ver_res = lcd.height();
    disp_drv.flush_cb = lv_disp_flush;
    disp_drv.draw_buf = &draw_buf;
    lv_disp_drv_register(&disp_drv);

    lv_disp_draw_buf_init(&draw_buf, buf, NULL, sizeof(buf) / sizeof(lv_color_t));

    // LVGL input device (dokunmatik) driver'ı kaydet
    lv_indev_drv_init(&indev_drv);
    indev_drv.type = LV_INDEV_TYPE_POINTER;
    indev_drv.read_cb = lv_touch_read;
    lv_indev_drv_register(&indev_drv);

    // Arayüzü oluştur
    create_ui();

    Serial.println("LVGL UI Hazır!");
}

void loop() {
    lv_timer_handler(); // LVGL görevlerini çalıştır
    delay(5);          // Küçük bir bekleme
}
