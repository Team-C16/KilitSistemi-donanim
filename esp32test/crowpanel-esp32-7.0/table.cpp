#include "table.h"
#include "turkish_24.h"
#include <time.h>
#include <string.h>  // strlen için

// Event callback fonksiyonunun bildirimi
static void table_draw_cb(lv_event_t* e);

void getNext5DayNames(const char* days[5]) {
    static const char* turkish_days[] = {
        "Pazar", "Pazarte-", "Salı", "Çarşam-",
        "Perşem-", "Cuma", "Cumart-"
    };

    static char buffer[5][12];

    time_t now = time(NULL);
    struct tm t;
    localtime_r(&now, &t);

    for (int i = 0; i < 5; i++) {
        int wday = t.tm_wday; // 0 = Pazar, 1 = Pazartesi, ...
        const char* turk_day = turkish_days[wday];

        strncpy(buffer[i], turk_day, sizeof(buffer[i]) - 1);
        buffer[i][sizeof(buffer[i]) - 1] = '\0';

        days[i] = buffer[i];

        // sonraki güne geç
        t.tm_mday++;
        mktime(&t);
    }
}

void create_schedule_table(lv_obj_t* parent, lv_obj_t* qr) {
    lv_coord_t screen_w = 800;
    lv_coord_t screen_h = 480;

    // QR kod objesinin pozisyonunu al
    lv_area_t qr_area;
    lv_obj_get_coords(qr, &qr_area);

    lv_coord_t table_x = qr_area.x2;
    lv_coord_t table_w = screen_w - table_x;
    lv_coord_t table_h = screen_h;

    // Tablo oluştur
    lv_obj_t* table = lv_table_create(parent);
    lv_obj_set_size(table, table_w, table_h);
    lv_obj_set_pos(table, table_x, 0);

    lv_obj_set_scrollbar_mode(table, LV_SCROLLBAR_MODE_OFF); // Scrollbar'ı kapat

    // Font stili tanımla ve uygula
    static lv_style_t style_turkish_24;
    lv_style_init(&style_turkish_24);
    lv_style_set_text_font(&style_turkish_24, &turkish_24);
    lv_style_set_pad_top(&style_turkish_24, 9);
    lv_style_set_pad_bottom(&style_turkish_24, 9);
    lv_style_set_text_line_space(&style_turkish_24, 4);
    lv_style_set_pad_left(&style_turkish_24, 0);
    lv_style_set_pad_right(&style_turkish_24, 0);
    lv_style_set_text_align(&style_turkish_24, LV_TEXT_ALIGN_CENTER);
    lv_style_set_border_width(&style_turkish_24, 1);
    lv_style_set_border_color(&style_turkish_24, lv_color_black());
    lv_style_set_border_side(&style_turkish_24, LV_BORDER_SIDE_FULL);

    lv_obj_add_style(table, &style_turkish_24, LV_PART_MAIN);
    lv_obj_add_style(table, &style_turkish_24, LV_PART_ITEMS);

    const int hour_start = 9;
    const int hour_end = 18;
    const int row_count = (hour_end - hour_start) + 1;
    const int col_count = 6; // 5 gün + saat

    lv_table_set_col_cnt(table, col_count);
    lv_table_set_row_cnt(table, row_count + 1); // +1 for header

    // Gün adlarını al
    const char* day_names[5];
    getNext5DayNames(day_names);

    // Tüm hücreleri ayarla
    for (int r = 0; r <= row_count; r++) {
        for (int c = 0; c < col_count; c++) {
            if (r == 0 && c == 0) {
                lv_table_set_cell_value(table, r, c, "Saat");
            } else if (r == 0) {
                lv_table_set_cell_value(table, r, c, day_names[c - 1]);
            } else if (c == 0) {
                char buf[8];
                snprintf(buf, sizeof(buf), "%02d:00", hour_start + r - 1);
                lv_table_set_cell_value(table, r, c, buf);
            } else {
                lv_table_set_cell_value(table, r, c, "");
            }
        }
    }

    // Stil ve draw callback ekle
    static lv_style_t style_table;
    lv_style_init(&style_table);
    lv_style_set_border_width(&style_table, 1);
    lv_obj_add_style(table, &style_table, LV_PART_ITEMS);
    lv_obj_add_event_cb(table, table_draw_cb, LV_EVENT_DRAW_PART_BEGIN, NULL);

    // Kolon genişlikleri
    lv_table_set_col_width(table, 0, 90); // saat sütunu genişliği
    for (int c = 1; c < col_count; c++) {
        lv_table_set_col_width(table, c, (table_w - 90) / (col_count - 1));
    }

    // Çerçeve ve padding
    lv_obj_set_style_border_width(table, 1, LV_PART_MAIN);
    lv_obj_set_style_pad_all(table, 2, LV_PART_MAIN);
}

// Event callback fonksiyonu
static void table_draw_cb(lv_event_t* e) {
    lv_obj_t* table = lv_event_get_target(e);
    lv_obj_draw_part_dsc_t* dsc = static_cast<lv_obj_draw_part_dsc_t*>(lv_event_get_param(e));

    if (dsc->part != LV_PART_ITEMS) return;

    uint16_t col_cnt = lv_table_get_col_cnt(table);
    uint16_t row = dsc->id / col_cnt;
    uint16_t col = dsc->id % col_cnt;

    const char* val = lv_table_get_cell_value(table, row, col);

    if (row == 0 || col == 0) {
        // Saat başlangıcı
        const int hour_start = 9;

        // Şu anki saati al
        time_t now = time(NULL);
        struct tm t;
        localtime_r(&now, &t);
        int current_hour = t.tm_hour;

        // Hücre saatini hesapla
        int cell_hour = hour_start + row - 1;

        if (cell_hour == current_hour) {
            dsc->rect_dsc->bg_color = lv_color_hex(0xFFFF00); // Sarı arka plan
            dsc->rect_dsc->border_color = lv_color_hex(0x000000); // Siyah çerçeve
            dsc->rect_dsc->border_width = 1;
        } else {
            dsc->rect_dsc->bg_color = lv_color_white(); // Diğer saat hücreleri beyaz
            dsc->rect_dsc->border_width = 1;
        }
    } else if (val && strlen(val) > 0) {
        dsc->rect_dsc->bg_color = lv_color_hex(0xE74C3C);  // Kırmızı dolu hücre
    } else {
        dsc->rect_dsc->bg_color = lv_color_hex(0x2ECC71);  // Yeşil boş hücre
    }

    // Sadece row=0 ve col=1 hücresi için border rengini sarı yap
    if (row == 0 && col == 1) {
        dsc->rect_dsc->border_color = lv_color_hex(0xFFFF00); // Sarı
        dsc->rect_dsc->border_width = 5;                      // İstersen kalınlık da arttır
    }
}
