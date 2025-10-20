#ifndef SCHEDULE_TABLE_H
#define SCHEDULE_TABLE_H

#include <lvgl.h>

// Tabloyu oluşturur
lv_obj_t* create_schedule_table(lv_obj_t* parent, lv_obj_t* qr);
void mark_schedule_from_json(lv_obj_t* table, const char* jsonStr);
lv_obj_t* create_details_screen(lv_obj_t* parent, lv_obj_t* qr, const char* text);
void refresh_table_headers_if_date_changed(lv_obj_t* table);
#endif
