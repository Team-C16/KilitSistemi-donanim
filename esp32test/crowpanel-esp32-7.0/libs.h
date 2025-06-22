#pragma once

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
#include "table.h"
#include "turkish_24.h"

#include "lv_lib_qrcode/lv_qrcode.h"
