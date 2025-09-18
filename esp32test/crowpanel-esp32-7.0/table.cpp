#include "table.h"
#include "turkish_24.h"
#include <time.h>
#include <string.h>  // strlen için
#include <ArduinoJson.h>


// Event callback fonksiyonunun bildirimi
static void table_draw_cb(lv_event_t* e);


void getNext5DayNames(const char* days[5]) {
    // Turkish full weekday names (tm_wday: 0=Sun .. 6=Sat)
    static const char* turkish_days[] = {
        "Pazar", "Pazart.", "Salı", "Çarş.",
        "Perş.", "Cuma", "Cumat."
    };

    static char buffer[5][16];

    time_t now = time(NULL);
    struct tm t;
    localtime_r(&now, &t);

    // Normalize to local midnight to avoid DST/partial-day issues
    t.tm_hour = 0; t.tm_min = 0; t.tm_sec = 0;
    time_t today_mid = mktime(&t);

    for (int i = 0; i < 5; i++) {
        time_t day_ts = today_mid + (time_t)i * 86400;
        struct tm day_tm;
        localtime_r(&day_ts, &day_tm);
        // Format: "Pazartesi" or if you want include date: "Pazartesi 21"
        snprintf(buffer[i], sizeof(buffer[i]), "%s", turkish_days[day_tm.tm_wday]);
        days[i] = buffer[i];
    }
}

// update header cells (row 0, cols 1..5)
void update_table_headers(lv_obj_t* table) {
    const char* day_names[5];
    getNext5DayNames(day_names);
    for (int c = 0; c < 5; c++) {
        // header row is 0, columns 1..5
        lv_table_set_cell_value(table, 0, c + 1, day_names[c]);
    }
}

// call periodically to refresh header only when day changes
void refresh_table_headers_if_date_changed(lv_obj_t* table) {
    static int last_mday = -1;
    time_t now = time(NULL);
    struct tm t;
    localtime_r(&now, &t);
    if (t.tm_mday != last_mday) {
        last_mday = t.tm_mday;
        update_table_headers(table);
        Serial.print("Table headers updated for new day: ");
        Serial.println(last_mday);
    }
}

lv_obj_t* create_schedule_table(lv_obj_t* parent, lv_obj_t* qr) {
    lv_coord_t screen_w = 800;
    lv_coord_t screen_h = 480;

    // QR kod objesinin pozisyonunu al
    lv_area_t qr_area;
    lv_obj_get_coords(qr, &qr_area);

    lv_coord_t table_x = qr_area.x2 + 20;
    lv_coord_t table_w = screen_w - table_x - 10;
    lv_coord_t table_h = screen_h - 20;

    // Tablo oluştur
    lv_obj_t* table = lv_table_create(parent);
    lv_obj_set_size(table, table_w, table_h); // biraz küçültüp boşluk bırak
    lv_obj_set_pos(table, table_x, 10);

    lv_obj_set_scrollbar_mode(table, LV_SCROLLBAR_MODE_OFF); // Scrollbar'ı kapat

    // === Yeni stiller ===
    static lv_style_t style_table_main;
    static lv_style_t style_table_items;
    static lv_style_t style_table_header;

    lv_style_init(&style_table_main);
    lv_style_set_border_width(&style_table_main, 2);
    lv_style_set_border_color(&style_table_main, lv_color_hex(0x2F4858));
    lv_style_set_radius(&style_table_main, 6);
    lv_style_set_bg_color(&style_table_main, lv_color_hex(0x8E4162));
    lv_style_set_shadow_width(&style_table_main, 20);       // Gölge kalınlığı
    lv_style_set_shadow_spread(&style_table_main, 2);       // Gölge yayılımı
    lv_style_set_shadow_color(&style_table_main, lv_color_hex(0x8E4162)); // Gölge rengi

    lv_style_init(&style_table_header);
    lv_style_set_bg_color(&style_table_header, lv_color_hex(0x2F4858));
    lv_style_set_text_color(&style_table_header, lv_color_hex(0xFFFFFF));
    lv_style_set_border_width(&style_table_header, 2);
    lv_style_set_border_color(&style_table_header, lv_color_hex(0x33658A));

    lv_style_init(&style_table_items);
    lv_style_set_border_width(&style_table_items, 1);
    lv_style_set_border_color(&style_table_items, lv_color_hex(0x33658A));
    lv_style_set_pad_all(&style_table_items, 6);
    lv_style_set_text_align(&style_table_items, LV_TEXT_ALIGN_CENTER);

    // Uygula
    lv_obj_add_style(table, &style_table_main, LV_PART_MAIN);
    lv_obj_add_style(table, &style_table_items, LV_PART_ITEMS);

    // Font stili tanımla ve uygula
    static lv_style_t style_turkish_24;
    lv_style_init(&style_turkish_24);
    lv_style_set_text_font(&style_turkish_24, &turkish_24);
    lv_style_set_pad_top(&style_turkish_24, 8);
    lv_style_set_pad_bottom(&style_turkish_24, 8);
    lv_style_set_text_line_space(&style_turkish_24, 4);
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
        lv_table_set_col_width(table, c, (table_w - 90) / (col_count - 1) - 1);
    }

    // Çerçeve ve padding
    lv_obj_set_style_border_width(table, 1, LV_PART_MAIN);
    lv_obj_set_style_pad_all(table, 2, LV_PART_MAIN);
    return table;
}

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
            // 🔵 Şu anki saati göster
            //dsc->rect_dsc->bg_color = lv_color_hex(0x8E4162); // vişne/pembe ton
            dsc->rect_dsc->border_color = lv_color_hex(0x8E4162); 
            dsc->rect_dsc->border_width = 6;
        } else {
            dsc->rect_dsc->bg_color = lv_color_hex(0xFFFFFF); // beyaz
            dsc->rect_dsc->border_width = 1;
        }
    } else if (val && strlen(val) > 0) {
        dsc->rect_dsc->bg_color = lv_color_hex(0x8E4162);  // dolu hücre – mavi ton
        dsc->rect_dsc->border_color = lv_color_hex(0x8E4162);
        dsc->rect_dsc->border_width = 1;
    } else {
        dsc->rect_dsc->bg_color = lv_color_hex(0x86BBD8);  // boş hücre – açık mavi
        dsc->rect_dsc->border_color = lv_color_hex(0x2F4858);
        dsc->rect_dsc->border_width = 1;
    }

    // Özel örnek: sadece row=0 col=1 hücresine kalın border
    if (row == 0 && col == 1) {
        dsc->rect_dsc->border_color = lv_color_hex(0x8E4162);
        dsc->rect_dsc->border_width = 3;
    }
}

// Bu fonksiyon JSON'daki dolu saatleri tabloya işler
void mark_schedule_from_json(lv_obj_t* table, const char* jsonStr) {
    StaticJsonDocument<1024> doc;
    DeserializationError error = deserializeJson(doc, jsonStr);
    if (error) {
        Serial.println("JSON parse hatası!");
        return;
    }

    JsonArray schedules = doc["schedule"].as<JsonArray>();

    const int hour_start = 9;
    const int hour_end   = 18;

    // Şimdiki zaman
    time_t now = time(NULL);
    struct tm t;
    localtime_r(&now, &t);

    // Önce tüm tabloyu BOŞ olarak doldur
    uint16_t rows = lv_table_get_row_cnt(table);
    uint16_t cols = lv_table_get_col_cnt(table);

    for (uint16_t r = 1; r < rows; r++) {     // 0. satır header
        for (uint16_t c = 1; c < cols; c++) { // 0. kolon saatler
            lv_table_set_cell_value(table, r, c, "");
        }
    }

    // JSON'daki doluları işle
    for (JsonObject sch : schedules) {
        const char* hourStr = sch["hour"];
        const char* dayStr  = sch["day"];
        int confirm = sch["confirm"];

        if (confirm != 1) continue;

        int h = atoi(hourStr);
        if (h < hour_start || h > hour_end) continue;

        struct tm event_tm = {};
        strptime(dayStr, "%Y-%m-%dT%H:%M:%S", &event_tm);
        time_t event_time = mktime(&event_tm);

        double diff_days = difftime(event_time, now) / (60*60*24);
        int col_offset = (int)diff_days;
        if (col_offset < 0 || col_offset > 4) continue;

        int row = (h - hour_start) + 1;
        int col = col_offset + 1;

        lv_table_set_cell_value(table, row, col, "DOLU");
    }
}

// --- Detay ekranı ---
lv_obj_t* create_details_screen(lv_obj_t* parent, lv_obj_t* qr, const char* json_text) {
    // Ekran boyutları
    lv_coord_t screen_w = 800;
    lv_coord_t screen_h = 480;

    // QR pozisyonu
    lv_area_t qr_area;
    lv_obj_get_coords(qr, &qr_area);

    lv_coord_t container_x = qr_area.x2;
    lv_coord_t container_w = screen_w - container_x;
    lv_coord_t container_h = screen_h;

    // Container (scrollable)
    lv_obj_t* container = lv_obj_create(parent);
    lv_obj_set_size(container, container_w, container_h);
    lv_obj_set_pos(container, container_x, 0);
    lv_obj_set_scrollbar_mode(container, LV_SCROLLBAR_MODE_AUTO);
    lv_obj_set_flex_flow(container, LV_FLEX_FLOW_COLUMN);
    lv_obj_set_style_pad_all(container, 16, 0);
    lv_obj_set_style_pad_gap(container, 12, 0);

    // JSON parse
    DynamicJsonDocument doc(8192);
    deserializeJson(doc, json_text);

    JsonArray dataArr;
    JsonArray groupArr;
    bool isGroup = false;

    if (doc.containsKey("dataResult")) {
        dataArr = doc["dataResult"].as<JsonArray>();
        groupArr = doc["groupResult"].as<JsonArray>();
        isGroup = true;
    } else {
        dataArr = doc.as<JsonArray>();
    }

    JsonObject detail = dataArr[0];
    const char* title    = detail["title"];
    const char* message  = detail["message"];
    const char* dayStr   = detail["day"];
    const char* hourStr  = detail["hour"];
    const char* fullName = detail["fullName"];

    // --- Zaman formatlama ---
    struct tm tm{};
    strptime(dayStr, "%Y-%m-%dT%H:%M:%S.000Z", &tm);

    char dateBuf[32];
    strftime(dateBuf, sizeof(dateBuf), "%d %B %Y", &tm);

    // hourStr "17:00:00" -> "17:00"
    char hourBuf[6];
    strncpy(hourBuf, hourStr, 5);
    hourBuf[5] = '\0';

    // === Başlık ===
    lv_obj_t* lbl_title = lv_label_create(container);
    lv_label_set_text_fmt(lbl_title, "%s", title);
    lv_obj_set_style_text_font(lbl_title, &lv_font_montserrat_22, 0);
    lv_obj_set_style_text_align(lbl_title, LV_TEXT_ALIGN_CENTER, 0);

    // === Mesaj ===
    lv_obj_t* lbl_msg = lv_label_create(container);
    lv_label_set_text(lbl_msg, message);
    lv_label_set_long_mode(lbl_msg, LV_LABEL_LONG_WRAP);
    lv_obj_set_width(lbl_msg, container_w - 40);
    lv_obj_set_style_text_font(lbl_msg, &lv_font_montserrat_18, 0);
    lv_obj_set_style_text_align(lbl_msg, LV_TEXT_ALIGN_CENTER, 0);

    // === Tarih & Saat ===
    lv_obj_t* lbl_dt = lv_label_create(container);
    lv_label_set_text_fmt(lbl_dt, "%s   %s", dateBuf, hourBuf);
    lv_obj_set_style_text_font(lbl_dt, &lv_font_montserrat_16, 0);
    lv_obj_set_style_text_color(lbl_dt, lv_palette_darken(LV_PALETTE_GREY, 2), 0);
    lv_obj_set_style_text_align(lbl_dt, LV_TEXT_ALIGN_CENTER, 0);

    // === Katılımcılar ===
    lv_obj_t* lbl_part = lv_label_create(container);
    lv_label_set_text(lbl_part, "Katılımcılar:");
    lv_obj_set_style_text_font(lbl_part, &lv_font_montserrat_18, 0);
    lv_obj_set_style_text_color(lbl_part, lv_palette_main(LV_PALETTE_BLUE), 0);
    lv_obj_set_style_text_align(lbl_part, LV_TEXT_ALIGN_CENTER, 0);

    if (isGroup) {
        for (JsonObject member : groupArr) {
            const char* memberName = member["fullName"];
            lv_obj_t* lbl_member = lv_label_create(container);
            lv_label_set_text_fmt(lbl_member, "- %s", memberName);
            lv_obj_set_style_text_font(lbl_member, &lv_font_montserrat_16, 0);
            lv_obj_set_style_text_align(lbl_member, LV_TEXT_ALIGN_CENTER, 0);
        }
    } else {
        lv_obj_t* lbl_member = lv_label_create(container);
        lv_label_set_text_fmt(lbl_member, "- %s", fullName);
        lv_obj_set_style_text_font(lbl_member, &lv_font_montserrat_16, 0);
        lv_obj_set_style_text_align(lbl_member, LV_TEXT_ALIGN_CENTER, 0);
    }

    return container;
}
