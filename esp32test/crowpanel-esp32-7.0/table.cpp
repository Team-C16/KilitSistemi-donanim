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
    if (!qr) {
        Serial.println("QR objesi null! schedule ekranı oluşturulamayacak.");
        return nullptr;
    }
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

    if (!qr) {
        Serial.println("QR objesi null! Detay ekranı oluşturulamayacak.");
        return nullptr;
    }
    Serial.println("=== Gelen JSON ===");
    DynamicJsonDocument debugDoc(8192);
    DeserializationError err = deserializeJson(debugDoc, json_text);
    if (err) {
        Serial.print("JSON parse hatası: ");
        Serial.println(err.f_str());
    } else {
        serializeJsonPretty(debugDoc, Serial);
        Serial.println();
    }


    // Ekran boyutları
    lv_coord_t screen_w = 800;
    lv_coord_t screen_h = 480;

    // QR pozisyonu
    lv_area_t qr_area;
    lv_obj_get_coords(qr, &qr_area);

    lv_coord_t container_x = qr_area.x2 + 30;
    lv_coord_t container_w = screen_w - container_x - 10;
    lv_coord_t container_h = screen_h - 20;


    // Ana container
    lv_obj_t* container = lv_obj_create(parent);
    lv_obj_set_style_bg_color(container, lv_color_hex(0x000000), 0);
    lv_obj_set_style_bg_opa(container, LV_OPA_TRANSP, 0);
    lv_obj_set_size(container, container_w, container_h);
    lv_obj_set_pos(container, container_x, 10);
    lv_obj_set_scrollbar_mode(container, LV_SCROLLBAR_MODE_OFF);
    lv_obj_set_flex_flow(container, LV_FLEX_FLOW_COLUMN);
    lv_obj_set_style_pad_all(container, 12, 0);
    lv_obj_set_style_pad_gap(container, 8, 0);
    lv_obj_set_style_border_width(container, 0, 0); // border kalınlığı 0
    lv_obj_set_style_border_opa(container, LV_OPA_TRANSP, 0); // border tamamen saydam


    lv_obj_set_scrollbar_mode(container, LV_SCROLLBAR_MODE_OFF); // Scrollbar'ı kapat
        
    // JSON parse
    DynamicJsonDocument doc(8192);
    deserializeJson(doc, json_text);

    JsonArray dataArr;
    JsonArray groupArr;
    bool isGroup = false;

    if (doc.containsKey("dataResult")) {
        dataArr = doc["dataResult"].as<JsonArray>();
    
        if (doc.containsKey("groupResult") && !doc["groupResult"].isNull()) {
            groupArr = doc["groupResult"].as<JsonArray>();
            isGroup = true;
        } else {
            isGroup = false;
        }
    } else {
        dataArr = doc.as<JsonArray>();
    }
    JsonObject detail = dataArr[0];
    const char* title    = detail["title"];
    const char* message  = detail["message"];
    const char* hourStr  = detail["hour"];
    const char* fullName = detail["fullName"];


    // hourStr "17:00:00" -> "17:00"
    char hourBuf[6];
    strncpy(hourBuf, hourStr, 5);
    hourBuf[5] = '\0';
    // === En üst başlık ===
    lv_obj_t* lbl_header = lv_label_create(container);
    lv_label_set_text(lbl_header, "Toplantı Detayları");
    lv_obj_set_style_text_font(lbl_header, &turkish_24, 0);
    lv_obj_set_style_text_align(lbl_header, LV_TEXT_ALIGN_CENTER, 0);

    // === Tek satır info bar ===
    lv_obj_t* info_bar = lv_obj_create(container);
    lv_obj_set_size(info_bar, container_w - 20, 40);
    lv_obj_set_flex_flow(info_bar, LV_FLEX_FLOW_ROW);
    lv_obj_set_flex_align(info_bar, LV_FLEX_ALIGN_SPACE_EVENLY, LV_FLEX_ALIGN_CENTER, LV_FLEX_ALIGN_CENTER);
    lv_obj_set_style_shadow_width(info_bar, 20, 0); // Gölge kalınlığı
    lv_obj_set_style_shadow_spread(info_bar, 2, 0); // Gölge yayılımı
    lv_obj_set_style_shadow_color(info_bar, lv_color_hex(0x8E4162), 0); // Gölge rengi

    lv_obj_t* lbl_title = lv_label_create(info_bar);
    lv_label_set_text_fmt(lbl_title, "%s", title);
    lv_obj_set_style_text_font(lbl_title, &turkish_24, 0); 

    lv_obj_t* lbl_hour = lv_label_create(info_bar);
    lv_label_set_text(lbl_hour, hourBuf);
    lv_obj_set_style_text_font(lbl_hour, &turkish_24, 0);

    // === Mesaj alanı ===
    lv_obj_t* msg_cont = lv_obj_create(container);
    lv_obj_set_size(msg_cont, container_w - 20, container_h / 2 - 60);
    lv_obj_t* lbl_msg = lv_label_create(msg_cont);
    lv_label_set_text(lbl_msg, message);
    lv_label_set_long_mode(lbl_msg, LV_LABEL_LONG_WRAP);
    lv_obj_set_width(lbl_msg, container_w - 40);
    lv_obj_center(lbl_msg);
    lv_obj_set_style_text_font(lbl_msg, &turkish_24, 0);
    lv_obj_set_style_shadow_width(msg_cont, 20, 0); // Gölge kalınlığı
    lv_obj_set_style_shadow_spread(msg_cont, 2, 0); // Gölge yayılımı
    lv_obj_set_style_shadow_color(msg_cont, lv_color_hex(0x8E4162), 0); // Gölge rengi

    // === Katılımcılar alanı ===
    lv_obj_t* member_cont = lv_obj_create(container);
    lv_obj_set_size(member_cont, container_w - 20, container_h / 2 - 60);
    lv_obj_set_flex_flow(member_cont, LV_FLEX_FLOW_ROW);
    lv_obj_set_scroll_dir(member_cont, LV_DIR_HOR);
    lv_obj_set_scrollbar_mode(member_cont, LV_SCROLLBAR_MODE_OFF);
    lv_obj_set_style_shadow_width(member_cont, 20, 0); // Gölge kalınlığı
    lv_obj_set_style_shadow_spread(member_cont, 2, 0); // Gölge yayılımı
    lv_obj_set_style_shadow_color(member_cont, lv_color_hex(0x8E4162), 0); // Gölge rengi
    // Katılımcı ekleme
    auto add_member = [&](const char* name) {
        lv_obj_t* card = lv_obj_create(member_cont);
        lv_obj_set_size(card, (container_w - 40) / 4, 100); // max 4 tane yan yana
        lv_obj_set_style_radius(card, 12, 0);
        lv_obj_set_style_bg_color(card, lv_color_hex(0x2F4858), 0);

        lv_obj_t* lbl = lv_label_create(card);
        lv_label_set_text(lbl, name);
        lv_obj_set_style_text_font(lbl, &turkish_24, 0);
        lv_obj_set_style_text_color(lbl, lv_color_hex(0xFFFFFF), 0);
        lv_obj_center(lbl);
    };

    add_member(fullName);
    if (isGroup && groupArr.size() > 0) {
    
        for (JsonObject member : groupArr) {
            const char* memberName = member["fullName"] | "Bilinmiyor";
            add_member(memberName);
        }
    } 
        
    

    // === Otomatik scroll animasyonu ===
    lv_anim_t a;
    lv_anim_init(&a);
    lv_anim_set_var(&a, member_cont);
    lv_anim_set_exec_cb(&a, [](void* obj, int32_t v) {
        lv_obj_scroll_to_x((lv_obj_t*)obj, v, LV_ANIM_OFF);
    });
    lv_anim_set_values(&a, 0, lv_obj_get_scroll_right(member_cont));
    lv_anim_set_time(&a, 8000);     // 8 sn’de kay
    lv_anim_set_playback_time(&a, 8000);
    lv_anim_set_repeat_count(&a, LV_ANIM_REPEAT_INFINITE);
    lv_anim_start(&a);
    return container;
}
