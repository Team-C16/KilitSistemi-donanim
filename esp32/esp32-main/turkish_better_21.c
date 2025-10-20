/*******************************************************************************
 * Size: 20 px
 * Bpp: 1
 * Opts: --bpp 1 --size 20 --no-compress --use-color-info --stride 1 --align 1 --font Montserrat-Medium.ttf --symbols ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789ÇŞĞİÖÜçşğıöü.,:;!?%&@-+/*=() --format lvgl -o turkish_better_21.c
 ******************************************************************************/

#ifdef __has_include
    #if __has_include("lvgl.h")
        #ifndef LV_LVGL_H_INCLUDE_SIMPLE
            #define LV_LVGL_H_INCLUDE_SIMPLE
        #endif
    #endif
#endif

#ifdef LV_LVGL_H_INCLUDE_SIMPLE
    #include "lvgl.h"
#else
    #include "lvgl/lvgl.h"
#endif



#ifndef TURKISH_BETTER_21
#define TURKISH_BETTER_21 1
#endif

#if TURKISH_BETTER_21

/*-----------------
 *    BITMAPS
 *----------------*/

/*Store the image of the glyphs*/
static LV_ATTRIBUTE_LARGE_CONST const uint8_t glyph_bitmap[] = {
    /* U+0021 "!" */
    0xff, 0xff, 0xf0, 0x30,

    /* U+0025 "%" */
    0x38, 0x8, 0x6c, 0x10, 0xc6, 0x30, 0xc6, 0x20,
    0xc6, 0x40, 0x6c, 0xc0, 0x38, 0x9c, 0x1, 0x36,
    0x3, 0x63, 0x2, 0x63, 0x4, 0x63, 0xc, 0x63,
    0x8, 0x36, 0x10, 0x1c,

    /* U+0026 "&" */
    0x1f, 0x1, 0x8c, 0xc, 0x60, 0x63, 0x3, 0xb8,
    0xf, 0x80, 0x70, 0x7, 0xc0, 0x63, 0x36, 0xd,
    0xb0, 0x79, 0x81, 0xc6, 0x1f, 0x1f, 0x98, 0x0,
    0x40,

    /* U+0028 "(" */
    0x33, 0x66, 0x6c, 0xcc, 0xcc, 0xcc, 0xcc, 0x66,
    0x63, 0x30,

    /* U+0029 ")" */
    0xcc, 0x66, 0x63, 0x33, 0x33, 0x33, 0x33, 0x66,
    0x6c, 0xc0,

    /* U+002A "*" */
    0x11, 0x27, 0xf9, 0xcf, 0xf2, 0x44, 0x0,

    /* U+002B "+" */
    0x18, 0xc, 0x6, 0x3, 0xf, 0xf8, 0xc0, 0x60,
    0x30, 0x18, 0x0,

    /* U+002C "," */
    0xf6, 0x80,

    /* U+002D "-" */
    0xf8,

    /* U+002E "." */
    0xfc,

    /* U+002F "/" */
    0x1, 0x80, 0x80, 0xc0, 0x60, 0x20, 0x30, 0x18,
    0x8, 0xc, 0x6, 0x2, 0x3, 0x1, 0x80, 0x80,
    0xc0, 0x60, 0x20, 0x30, 0x18, 0x8, 0x0,

    /* U+0030 "0" */
    0x1f, 0x6, 0x31, 0x83, 0x30, 0x6c, 0x7, 0x80,
    0xf0, 0x1e, 0x3, 0xc0, 0x78, 0xd, 0x3, 0x30,
    0x63, 0x18, 0x3e, 0x0,

    /* U+0031 "1" */
    0xf8, 0xc6, 0x31, 0x8c, 0x63, 0x18, 0xc6, 0x31,
    0x8c,

    /* U+0032 "2" */
    0x7e, 0x30, 0xc0, 0x18, 0x6, 0x1, 0x80, 0xe0,
    0x30, 0x1c, 0xe, 0x7, 0x3, 0x81, 0xc0, 0x60,
    0x3f, 0xf0,

    /* U+0033 "3" */
    0x7f, 0xc0, 0x18, 0x6, 0x1, 0x80, 0x70, 0xc,
    0x3, 0xe0, 0x1e, 0x0, 0xe0, 0xc, 0x1, 0x80,
    0x36, 0xc, 0x7e, 0x0,

    /* U+0034 "4" */
    0x1, 0x80, 0x30, 0x7, 0x0, 0x60, 0xc, 0x1,
    0x80, 0x38, 0xc7, 0xc, 0x60, 0xcf, 0xff, 0x0,
    0xc0, 0xc, 0x0, 0xc0, 0xc,

    /* U+0035 "5" */
    0x7f, 0x98, 0x6, 0x1, 0x80, 0x60, 0x18, 0x7,
    0xf0, 0x6, 0x0, 0xc0, 0x30, 0xe, 0x3, 0xc1,
    0x9f, 0xc0,

    /* U+0036 "6" */
    0xf, 0xc6, 0x9, 0x80, 0x20, 0xc, 0x1, 0xbf,
    0x3c, 0x37, 0x3, 0xe0, 0x7c, 0xd, 0x81, 0xb0,
    0x33, 0xc, 0x3e, 0x0,

    /* U+0037 "7" */
    0xff, 0xf8, 0x1b, 0x3, 0x60, 0xc0, 0x18, 0x7,
    0x0, 0xc0, 0x18, 0x6, 0x0, 0xc0, 0x30, 0x6,
    0x1, 0xc0, 0x30, 0x0,

    /* U+0038 "8" */
    0x3f, 0x8c, 0x1b, 0x1, 0xe0, 0x3c, 0x6, 0xc1,
    0x8f, 0xe3, 0x6, 0xc0, 0x78, 0xf, 0x1, 0xe0,
    0x36, 0xc, 0x3e, 0x0,

    /* U+0039 "9" */
    0x3f, 0xc, 0x33, 0x3, 0x60, 0x6c, 0xf, 0x81,
    0xd8, 0x79, 0xfb, 0x0, 0x60, 0xc, 0x3, 0x0,
    0x64, 0x38, 0xfc, 0x0,

    /* U+003A ":" */
    0xfc, 0x0, 0xfc,

    /* U+003B ";" */
    0xfc, 0x0, 0x3d, 0xa0,

    /* U+003D "=" */
    0xff, 0x80, 0x0, 0x0, 0x0, 0x7, 0xfc,

    /* U+003F "?" */
    0x3f, 0x38, 0x64, 0xc, 0x3, 0x0, 0xc0, 0x70,
    0x38, 0x1c, 0xe, 0x3, 0x0, 0xc0, 0x0, 0x0,
    0x3, 0x0,

    /* U+0040 "@" */
    0x3, 0xf8, 0x1, 0xc1, 0xc0, 0x60, 0xc, 0x18,
    0x0, 0xc6, 0x1f, 0x6c, 0xce, 0x3d, 0xb1, 0x83,
    0x9e, 0x60, 0x33, 0xcc, 0x6, 0x79, 0x80, 0xcf,
    0x30, 0x19, 0xe3, 0x7, 0x36, 0x71, 0xec, 0xc3,
    0xe7, 0xc, 0x0, 0x0, 0xc0, 0x0, 0xe, 0x4,
    0x0, 0x7f, 0x0,

    /* U+0041 "A" */
    0x3, 0x80, 0x7, 0x0, 0x1e, 0x0, 0x36, 0x0,
    0xcc, 0x1, 0x8c, 0x6, 0x18, 0xc, 0x18, 0x38,
    0x30, 0x7f, 0xf0, 0x80, 0x63, 0x0, 0x66, 0x0,
    0xd8, 0x1, 0x80,

    /* U+0042 "B" */
    0xff, 0x8c, 0xc, 0xc0, 0x6c, 0x6, 0xc0, 0x6c,
    0xc, 0xff, 0xcc, 0x6, 0xc0, 0x3c, 0x3, 0xc0,
    0x3c, 0x3, 0xc0, 0x6f, 0xfc,

    /* U+0043 "C" */
    0x7, 0xe0, 0xc1, 0xcc, 0x4, 0xc0, 0xc, 0x0,
    0x60, 0x3, 0x0, 0x18, 0x0, 0xc0, 0x6, 0x0,
    0x18, 0x0, 0x60, 0x21, 0x83, 0x87, 0xf0,

    /* U+0044 "D" */
    0xff, 0x86, 0x6, 0x30, 0x19, 0x80, 0x6c, 0x1,
    0xe0, 0xf, 0x0, 0x78, 0x3, 0xc0, 0x1e, 0x0,
    0xf0, 0xd, 0x80, 0xec, 0xc, 0x7f, 0xc0,

    /* U+0045 "E" */
    0xff, 0xf0, 0xc, 0x3, 0x0, 0xc0, 0x30, 0xf,
    0xfb, 0x0, 0xc0, 0x30, 0xc, 0x3, 0x0, 0xc0,
    0x3f, 0xf0,

    /* U+0046 "F" */
    0xff, 0xf0, 0xc, 0x3, 0x0, 0xc0, 0x30, 0xc,
    0x3, 0xfe, 0xc0, 0x30, 0xc, 0x3, 0x0, 0xc0,
    0x30, 0x0,

    /* U+0047 "G" */
    0x7, 0xe0, 0xc1, 0xcc, 0x4, 0xc0, 0xc, 0x0,
    0x60, 0x3, 0x0, 0x18, 0x3, 0xc0, 0x1e, 0x0,
    0xd8, 0x6, 0x60, 0x31, 0x83, 0x83, 0xf8,

    /* U+0048 "H" */
    0xc0, 0x3c, 0x3, 0xc0, 0x3c, 0x3, 0xc0, 0x3c,
    0x3, 0xff, 0xfc, 0x3, 0xc0, 0x3c, 0x3, 0xc0,
    0x3c, 0x3, 0xc0, 0x3c, 0x3,

    /* U+0049 "I" */
    0xff, 0xff, 0xff, 0xf0,

    /* U+004A "J" */
    0x7f, 0x3, 0x3, 0x3, 0x3, 0x3, 0x3, 0x3,
    0x3, 0x3, 0x3, 0x83, 0xc6, 0x7c,

    /* U+004B "K" */
    0xc0, 0x6c, 0xc, 0xc1, 0xcc, 0x38, 0xc7, 0xc,
    0xe0, 0xdc, 0xf, 0xe0, 0xf7, 0xe, 0x38, 0xc1,
    0x8c, 0xc, 0xc0, 0x6c, 0x7,

    /* U+004C "L" */
    0xc0, 0x30, 0xc, 0x3, 0x0, 0xc0, 0x30, 0xc,
    0x3, 0x0, 0xc0, 0x30, 0xc, 0x3, 0x0, 0xc0,
    0x3f, 0xf0,

    /* U+004D "M" */
    0xc0, 0x7, 0xc0, 0x1f, 0x80, 0x3f, 0x80, 0xff,
    0x1, 0xfb, 0x6, 0xf3, 0x19, 0xe6, 0x33, 0xc6,
    0xc7, 0x8d, 0x8f, 0xe, 0x1e, 0x8, 0x3c, 0x0,
    0x78, 0x0, 0xc0,

    /* U+004E "N" */
    0xc0, 0x3e, 0x3, 0xf0, 0x3f, 0x3, 0xd8, 0x3c,
    0xc3, 0xce, 0x3c, 0x73, 0xc3, 0x3c, 0x1b, 0xc0,
    0xfc, 0xf, 0xc0, 0x7c, 0x3,

    /* U+004F "O" */
    0x7, 0xc0, 0x30, 0x60, 0xc0, 0x63, 0x0, 0x6c,
    0x0, 0x78, 0x0, 0xf0, 0x1, 0xe0, 0x3, 0xc0,
    0x7, 0x80, 0xd, 0x80, 0x31, 0x80, 0xc1, 0x83,
    0x0, 0xf8, 0x0,

    /* U+0050 "P" */
    0xff, 0x18, 0x3b, 0x1, 0xe0, 0x3c, 0x7, 0x80,
    0xf0, 0x3e, 0xe, 0xff, 0x18, 0x3, 0x0, 0x60,
    0xc, 0x1, 0x80, 0x0,

    /* U+0051 "Q" */
    0x7, 0xc0, 0x18, 0x30, 0x30, 0x18, 0x60, 0xc,
    0xc0, 0x6, 0xc0, 0x6, 0xc0, 0x6, 0xc0, 0x6,
    0xc0, 0x6, 0xc0, 0x6, 0x60, 0xc, 0x30, 0x18,
    0x18, 0x30, 0xf, 0xe0, 0x1, 0xc2, 0x0, 0xe2,
    0x0, 0x3c,

    /* U+0052 "R" */
    0xff, 0x18, 0x3b, 0x1, 0xe0, 0x3c, 0x7, 0x80,
    0xf0, 0x3e, 0xe, 0xff, 0x98, 0x63, 0x6, 0x60,
    0x6c, 0xd, 0x80, 0xc0,

    /* U+0053 "S" */
    0x3f, 0x98, 0x6c, 0x3, 0x0, 0xc0, 0x3c, 0x7,
    0xf0, 0xfe, 0x7, 0xc0, 0x70, 0xe, 0x3, 0xc1,
    0x9f, 0xc0,

    /* U+0054 "T" */
    0xff, 0xf0, 0x60, 0x6, 0x0, 0x60, 0x6, 0x0,
    0x60, 0x6, 0x0, 0x60, 0x6, 0x0, 0x60, 0x6,
    0x0, 0x60, 0x6, 0x0, 0x60,

    /* U+0055 "U" */
    0xc0, 0x3c, 0x3, 0xc0, 0x3c, 0x3, 0xc0, 0x3c,
    0x3, 0xc0, 0x3c, 0x3, 0xc0, 0x3c, 0x3, 0xc0,
    0x36, 0x6, 0x30, 0xc1, 0xf8,

    /* U+0056 "V" */
    0xc0, 0xd, 0x80, 0x36, 0x1, 0x8c, 0x6, 0x30,
    0x30, 0xe0, 0xc1, 0x86, 0x6, 0x18, 0xc, 0xe0,
    0x33, 0x0, 0x6c, 0x1, 0xe0, 0x7, 0x80, 0xc,
    0x0,

    /* U+0057 "W" */
    0xc0, 0x60, 0x1e, 0x3, 0x81, 0xb8, 0x1c, 0xc,
    0xc1, 0xa0, 0x66, 0xd, 0x86, 0x38, 0xcc, 0x30,
    0xc6, 0x21, 0x86, 0x31, 0x98, 0x3b, 0xc, 0xc0,
    0xd8, 0x26, 0x6, 0xc1, 0xe0, 0x3c, 0xf, 0x0,
    0xe0, 0x38, 0x7, 0x1, 0x80,

    /* U+0058 "X" */
    0x60, 0x31, 0x81, 0x8e, 0x18, 0x31, 0x80, 0xdc,
    0x3, 0xc0, 0x1c, 0x0, 0xe0, 0xf, 0x80, 0x66,
    0x6, 0x38, 0x60, 0xc7, 0x3, 0x30, 0xc,

    /* U+0059 "Y" */
    0x60, 0x19, 0xc0, 0x63, 0x3, 0x6, 0x18, 0x18,
    0x60, 0x33, 0x0, 0xec, 0x1, 0xe0, 0x3, 0x0,
    0xc, 0x0, 0x30, 0x0, 0xc0, 0x3, 0x0, 0xc,
    0x0,

    /* U+005A "Z" */
    0xff, 0xe0, 0xe, 0x1, 0xc0, 0x18, 0x3, 0x0,
    0x70, 0x6, 0x0, 0xc0, 0x1c, 0x1, 0x80, 0x30,
    0x7, 0x0, 0xe0, 0xf, 0xff,

    /* U+0061 "a" */
    0x7e, 0x21, 0x80, 0x60, 0x30, 0x1b, 0xff, 0x87,
    0x83, 0xc1, 0xf1, 0xdf, 0x60,

    /* U+0062 "b" */
    0xc0, 0x18, 0x3, 0x0, 0x60, 0xd, 0xf1, 0xe3,
    0x38, 0x36, 0x3, 0xc0, 0x78, 0xf, 0x1, 0xe0,
    0x3e, 0xd, 0xe3, 0xb7, 0xc0,

    /* U+0063 "c" */
    0x1f, 0xc, 0x76, 0xb, 0x0, 0xc0, 0x30, 0xc,
    0x3, 0x0, 0x60, 0x8c, 0x71, 0xf0,

    /* U+0064 "d" */
    0x0, 0x60, 0xc, 0x1, 0x80, 0x31, 0xf6, 0x63,
    0xd8, 0x3e, 0x3, 0xc0, 0x78, 0xf, 0x1, 0xe0,
    0x36, 0xe, 0xe3, 0xc7, 0xd8,

    /* U+0065 "e" */
    0x1f, 0x6, 0x31, 0x83, 0x60, 0x3c, 0x7, 0xff,
    0xf0, 0x6, 0x0, 0x60, 0x6, 0x18, 0x7e, 0x0,

    /* U+0066 "f" */
    0x1f, 0x30, 0x30, 0x30, 0xfe, 0x30, 0x30, 0x30,
    0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30,

    /* U+0067 "g" */
    0x1f, 0x6e, 0x3d, 0x83, 0xe0, 0x3c, 0x7, 0x80,
    0xf0, 0x1e, 0x3, 0x60, 0xe6, 0x3c, 0x7d, 0x80,
    0x30, 0x4, 0xc1, 0x8f, 0xc0,

    /* U+0068 "h" */
    0xc0, 0x30, 0xc, 0x3, 0x0, 0xdf, 0x38, 0x6e,
    0xf, 0x3, 0xc0, 0xf0, 0x3c, 0xf, 0x3, 0xc0,
    0xf0, 0x3c, 0xc,

    /* U+0069 "i" */
    0xc0, 0xff, 0xff, 0xfc,

    /* U+006A "j" */
    0x18, 0x0, 0x1, 0x8c, 0x63, 0x18, 0xc6, 0x31,
    0x8c, 0x63, 0x18, 0xfc,

    /* U+006B "k" */
    0xc0, 0x18, 0x3, 0x0, 0x60, 0xc, 0x1d, 0x87,
    0x31, 0xc6, 0x70, 0xdc, 0x1f, 0x83, 0xd8, 0x73,
    0x8c, 0x39, 0x83, 0x30, 0x30,

    /* U+006C "l" */
    0xff, 0xff, 0xff, 0xfc,

    /* U+006D "m" */
    0xdf, 0x1f, 0x38, 0x78, 0x6e, 0xe, 0xf, 0x3,
    0x3, 0xc0, 0xc0, 0xf0, 0x30, 0x3c, 0xc, 0xf,
    0x3, 0x3, 0xc0, 0xc0, 0xf0, 0x30, 0x3c, 0xc,
    0xc,

    /* U+006E "n" */
    0xdf, 0x38, 0x6e, 0xf, 0x3, 0xc0, 0xf0, 0x3c,
    0xf, 0x3, 0xc0, 0xf0, 0x3c, 0xc,

    /* U+006F "o" */
    0x1f, 0x6, 0x31, 0x83, 0x60, 0x3c, 0x7, 0x80,
    0xf0, 0x1e, 0x3, 0x60, 0xc6, 0x30, 0x7c, 0x0,

    /* U+0070 "p" */
    0xdf, 0x1e, 0x33, 0x83, 0x60, 0x3c, 0x7, 0x80,
    0xf0, 0x1e, 0x3, 0xe0, 0xde, 0x3b, 0x7c, 0x60,
    0xc, 0x1, 0x80, 0x30, 0x0,

    /* U+0071 "q" */
    0x1f, 0x66, 0x3d, 0x83, 0xe0, 0x3c, 0x7, 0x80,
    0xf0, 0x1e, 0x3, 0x60, 0xe6, 0x3c, 0x7d, 0x80,
    0x30, 0x6, 0x0, 0xc0, 0x18,

    /* U+0072 "r" */
    0xdf, 0x8e, 0x30, 0xc3, 0xc, 0x30, 0xc3, 0xc,
    0x0,

    /* U+0073 "s" */
    0x3f, 0x30, 0xb0, 0x18, 0xf, 0xc3, 0xf8, 0x7e,
    0x7, 0x1, 0xe1, 0xbf, 0x80,

    /* U+0074 "t" */
    0x30, 0x30, 0x30, 0xfe, 0x30, 0x30, 0x30, 0x30,
    0x30, 0x30, 0x30, 0x30, 0x30, 0x1f,

    /* U+0075 "u" */
    0xc0, 0xf0, 0x3c, 0xf, 0x3, 0xc0, 0xf0, 0x3c,
    0xf, 0x3, 0xc1, 0xd8, 0x73, 0xec,

    /* U+0076 "v" */
    0xc0, 0x6c, 0xd, 0x83, 0x30, 0x63, 0x18, 0x63,
    0x6, 0x40, 0xd8, 0xb, 0x1, 0xc0, 0x38, 0x0,

    /* U+0077 "w" */
    0xc0, 0xc0, 0xd0, 0x30, 0x26, 0x1e, 0x19, 0x87,
    0x86, 0x31, 0x21, 0xc, 0xcc, 0xc3, 0x33, 0x30,
    0x78, 0x78, 0x1e, 0x1e, 0x3, 0x3, 0x0, 0xc0,
    0xc0,

    /* U+0078 "x" */
    0x60, 0xc6, 0x30, 0xc6, 0xd, 0x80, 0xe0, 0x1c,
    0x3, 0x80, 0xd8, 0x31, 0x8e, 0x39, 0x83, 0x0,

    /* U+0079 "y" */
    0xc0, 0x6c, 0xd, 0x83, 0x30, 0x63, 0x8, 0x63,
    0x6, 0x40, 0xd8, 0x1b, 0x1, 0xc0, 0x38, 0x2,
    0x0, 0xc1, 0x10, 0x3c, 0x0,

    /* U+007A "z" */
    0xff, 0x81, 0xc1, 0xc0, 0xc0, 0xc0, 0xe0, 0x60,
    0x60, 0x70, 0x70, 0x3f, 0xe0,

    /* U+00C7 "Ç" */
    0xf, 0xe0, 0xc1, 0xcc, 0x4, 0xc0, 0xc, 0x0,
    0x60, 0x3, 0x0, 0x18, 0x0, 0xc0, 0x6, 0x0,
    0x18, 0x0, 0x60, 0x21, 0x83, 0x87, 0xf0, 0x8,
    0x0, 0x70, 0x1, 0x80, 0x78, 0x0,

    /* U+00D6 "Ö" */
    0x6, 0xc0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x7c, 0x3, 0x6, 0xc, 0x6, 0x30, 0x6, 0xc0,
    0x7, 0x80, 0xf, 0x0, 0x1e, 0x0, 0x3c, 0x0,
    0x78, 0x0, 0xd8, 0x3, 0x18, 0xc, 0x18, 0x30,
    0xf, 0x80,

    /* U+00DC "Ü" */
    0x19, 0x80, 0x0, 0x0, 0x0, 0x0, 0xc0, 0x3c,
    0x3, 0xc0, 0x3c, 0x3, 0xc0, 0x3c, 0x3, 0xc0,
    0x3c, 0x3, 0xc0, 0x3c, 0x3, 0xc0, 0x36, 0x6,
    0x30, 0xc1, 0xf8,

    /* U+00E7 "ç" */
    0x1f, 0xc, 0x76, 0xb, 0x0, 0xc0, 0x30, 0xc,
    0x3, 0x0, 0x60, 0x8c, 0x71, 0xf0, 0x20, 0xe,
    0x1, 0x81, 0xc0,

    /* U+00F6 "ö" */
    0x1b, 0x0, 0x0, 0x0, 0x0, 0x1, 0xf0, 0x63,
    0x18, 0x36, 0x3, 0xc0, 0x78, 0xf, 0x1, 0xe0,
    0x36, 0xc, 0x63, 0x7, 0xc0,

    /* U+00FC "ü" */
    0x33, 0x0, 0x0, 0x0, 0x0, 0xc0, 0xf0, 0x3c,
    0xf, 0x3, 0xc0, 0xf0, 0x3c, 0xf, 0x3, 0xc1,
    0xd8, 0x73, 0xec,

    /* U+011E "Ğ" */
    0xc, 0x60, 0x63, 0x1, 0xf0, 0x0, 0x0, 0x0,
    0x3, 0xf0, 0x60, 0xe6, 0x2, 0x60, 0x6, 0x0,
    0x30, 0x1, 0x80, 0xc, 0x1, 0xe0, 0xf, 0x0,
    0x6c, 0x3, 0x30, 0x18, 0xc1, 0xc1, 0xfc,

    /* U+011F "ğ" */
    0x31, 0x83, 0xe0, 0x0, 0x0, 0x1, 0xf6, 0xe3,
    0xd8, 0x3e, 0x3, 0xc0, 0x78, 0xf, 0x1, 0xe0,
    0x36, 0xe, 0x63, 0xc7, 0xd8, 0x3, 0x0, 0x4c,
    0x18, 0xfc, 0x0,

    /* U+0130 "İ" */
    0xc0, 0xff, 0xff, 0xff, 0xf0,

    /* U+0131 "ı" */
    0xff, 0xff, 0xfc,

    /* U+015E "Ş" */
    0x3f, 0x98, 0x6c, 0x3, 0x0, 0xc0, 0x3c, 0x7,
    0xf0, 0xfe, 0x7, 0xc0, 0x70, 0xe, 0x3, 0xc1,
    0x9f, 0xc0, 0x40, 0x3c, 0x3, 0x7, 0x80,

    /* U+015F "ş" */
    0x3f, 0x30, 0xb0, 0x18, 0xf, 0xc3, 0xf8, 0x7e,
    0x7, 0x1, 0xe1, 0xbf, 0x82, 0x1, 0xc0, 0x60,
    0xe0
};


/*---------------------
 *  GLYPH DESCRIPTION
 *--------------------*/

static const lv_font_fmt_txt_glyph_dsc_t glyph_dsc[] = {
    {.bitmap_index = 0, .adv_w = 0, .box_w = 0, .box_h = 0, .ofs_x = 0, .ofs_y = 0} /* id = 0 reserved */,
    {.bitmap_index = 0, .adv_w = 86, .box_w = 2, .box_h = 14, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 4, .adv_w = 270, .box_w = 16, .box_h = 14, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 32, .adv_w = 220, .box_w = 13, .box_h = 15, .ofs_x = 1, .ofs_y = -1},
    {.bitmap_index = 57, .adv_w = 108, .box_w = 4, .box_h = 19, .ofs_x = 2, .ofs_y = -4},
    {.bitmap_index = 67, .adv_w = 108, .box_w = 4, .box_h = 19, .ofs_x = 1, .ofs_y = -4},
    {.bitmap_index = 77, .adv_w = 128, .box_w = 7, .box_h = 7, .ofs_x = 0, .ofs_y = 8},
    {.bitmap_index = 84, .adv_w = 186, .box_w = 9, .box_h = 9, .ofs_x = 1, .ofs_y = 3},
    {.bitmap_index = 95, .adv_w = 73, .box_w = 2, .box_h = 5, .ofs_x = 1, .ofs_y = -3},
    {.bitmap_index = 97, .adv_w = 123, .box_w = 5, .box_h = 1, .ofs_x = 1, .ofs_y = 5},
    {.bitmap_index = 98, .adv_w = 73, .box_w = 2, .box_h = 3, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 99, .adv_w = 113, .box_w = 9, .box_h = 20, .ofs_x = -1, .ofs_y = -2},
    {.bitmap_index = 122, .adv_w = 213, .box_w = 11, .box_h = 14, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 142, .adv_w = 118, .box_w = 5, .box_h = 14, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 151, .adv_w = 184, .box_w = 10, .box_h = 14, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 169, .adv_w = 183, .box_w = 11, .box_h = 14, .ofs_x = 0, .ofs_y = 0},
    {.bitmap_index = 189, .adv_w = 214, .box_w = 12, .box_h = 14, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 210, .adv_w = 184, .box_w = 10, .box_h = 14, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 228, .adv_w = 197, .box_w = 11, .box_h = 14, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 248, .adv_w = 191, .box_w = 11, .box_h = 14, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 268, .adv_w = 206, .box_w = 11, .box_h = 14, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 288, .adv_w = 197, .box_w = 11, .box_h = 14, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 308, .adv_w = 73, .box_w = 2, .box_h = 11, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 311, .adv_w = 73, .box_w = 2, .box_h = 14, .ofs_x = 1, .ofs_y = -3},
    {.bitmap_index = 315, .adv_w = 186, .box_w = 9, .box_h = 6, .ofs_x = 1, .ofs_y = 5},
    {.bitmap_index = 322, .adv_w = 183, .box_w = 10, .box_h = 14, .ofs_x = 0, .ofs_y = 0},
    {.bitmap_index = 340, .adv_w = 331, .box_w = 19, .box_h = 18, .ofs_x = 1, .ofs_y = -4},
    {.bitmap_index = 383, .adv_w = 234, .box_w = 15, .box_h = 14, .ofs_x = 0, .ofs_y = 0},
    {.bitmap_index = 410, .adv_w = 242, .box_w = 12, .box_h = 14, .ofs_x = 2, .ofs_y = 0},
    {.bitmap_index = 431, .adv_w = 231, .box_w = 13, .box_h = 14, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 454, .adv_w = 264, .box_w = 13, .box_h = 14, .ofs_x = 2, .ofs_y = 0},
    {.bitmap_index = 477, .adv_w = 214, .box_w = 10, .box_h = 14, .ofs_x = 2, .ofs_y = 0},
    {.bitmap_index = 495, .adv_w = 203, .box_w = 10, .box_h = 14, .ofs_x = 2, .ofs_y = 0},
    {.bitmap_index = 513, .adv_w = 247, .box_w = 13, .box_h = 14, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 536, .adv_w = 260, .box_w = 12, .box_h = 14, .ofs_x = 2, .ofs_y = 0},
    {.bitmap_index = 557, .adv_w = 99, .box_w = 2, .box_h = 14, .ofs_x = 2, .ofs_y = 0},
    {.bitmap_index = 561, .adv_w = 164, .box_w = 8, .box_h = 14, .ofs_x = 0, .ofs_y = 0},
    {.bitmap_index = 575, .adv_w = 230, .box_w = 12, .box_h = 14, .ofs_x = 2, .ofs_y = 0},
    {.bitmap_index = 596, .adv_w = 190, .box_w = 10, .box_h = 14, .ofs_x = 2, .ofs_y = 0},
    {.bitmap_index = 614, .adv_w = 306, .box_w = 15, .box_h = 14, .ofs_x = 2, .ofs_y = 0},
    {.bitmap_index = 641, .adv_w = 260, .box_w = 12, .box_h = 14, .ofs_x = 2, .ofs_y = 0},
    {.bitmap_index = 662, .adv_w = 269, .box_w = 15, .box_h = 14, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 689, .adv_w = 231, .box_w = 11, .box_h = 14, .ofs_x = 2, .ofs_y = 0},
    {.bitmap_index = 709, .adv_w = 269, .box_w = 16, .box_h = 17, .ofs_x = 1, .ofs_y = -3},
    {.bitmap_index = 743, .adv_w = 233, .box_w = 11, .box_h = 14, .ofs_x = 2, .ofs_y = 0},
    {.bitmap_index = 763, .adv_w = 199, .box_w = 10, .box_h = 14, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 781, .adv_w = 188, .box_w = 12, .box_h = 14, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 802, .adv_w = 253, .box_w = 12, .box_h = 14, .ofs_x = 2, .ofs_y = 0},
    {.bitmap_index = 823, .adv_w = 228, .box_w = 14, .box_h = 14, .ofs_x = 0, .ofs_y = 0},
    {.bitmap_index = 848, .adv_w = 360, .box_w = 21, .box_h = 14, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 885, .adv_w = 215, .box_w = 13, .box_h = 14, .ofs_x = 0, .ofs_y = 0},
    {.bitmap_index = 908, .adv_w = 207, .box_w = 14, .box_h = 14, .ofs_x = -1, .ofs_y = 0},
    {.bitmap_index = 933, .adv_w = 210, .box_w = 12, .box_h = 14, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 954, .adv_w = 191, .box_w = 9, .box_h = 11, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 967, .adv_w = 218, .box_w = 11, .box_h = 15, .ofs_x = 2, .ofs_y = 0},
    {.bitmap_index = 988, .adv_w = 183, .box_w = 10, .box_h = 11, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 1002, .adv_w = 218, .box_w = 11, .box_h = 15, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 1023, .adv_w = 196, .box_w = 11, .box_h = 11, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 1039, .adv_w = 113, .box_w = 8, .box_h = 15, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 1054, .adv_w = 221, .box_w = 11, .box_h = 15, .ofs_x = 1, .ofs_y = -4},
    {.bitmap_index = 1075, .adv_w = 218, .box_w = 10, .box_h = 15, .ofs_x = 2, .ofs_y = 0},
    {.bitmap_index = 1094, .adv_w = 89, .box_w = 2, .box_h = 15, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 1098, .adv_w = 91, .box_w = 5, .box_h = 19, .ofs_x = -1, .ofs_y = -4},
    {.bitmap_index = 1110, .adv_w = 197, .box_w = 11, .box_h = 15, .ofs_x = 2, .ofs_y = 0},
    {.bitmap_index = 1131, .adv_w = 89, .box_w = 2, .box_h = 15, .ofs_x = 2, .ofs_y = 0},
    {.bitmap_index = 1135, .adv_w = 338, .box_w = 18, .box_h = 11, .ofs_x = 2, .ofs_y = 0},
    {.bitmap_index = 1160, .adv_w = 218, .box_w = 10, .box_h = 11, .ofs_x = 2, .ofs_y = 0},
    {.bitmap_index = 1174, .adv_w = 203, .box_w = 11, .box_h = 11, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 1190, .adv_w = 218, .box_w = 11, .box_h = 15, .ofs_x = 2, .ofs_y = -4},
    {.bitmap_index = 1211, .adv_w = 218, .box_w = 11, .box_h = 15, .ofs_x = 1, .ofs_y = -4},
    {.bitmap_index = 1232, .adv_w = 131, .box_w = 6, .box_h = 11, .ofs_x = 2, .ofs_y = 0},
    {.bitmap_index = 1241, .adv_w = 160, .box_w = 9, .box_h = 11, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 1254, .adv_w = 132, .box_w = 8, .box_h = 14, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 1268, .adv_w = 217, .box_w = 10, .box_h = 11, .ofs_x = 2, .ofs_y = 0},
    {.bitmap_index = 1282, .adv_w = 179, .box_w = 11, .box_h = 11, .ofs_x = 0, .ofs_y = 0},
    {.bitmap_index = 1298, .adv_w = 288, .box_w = 18, .box_h = 11, .ofs_x = 0, .ofs_y = 0},
    {.bitmap_index = 1323, .adv_w = 177, .box_w = 11, .box_h = 11, .ofs_x = 0, .ofs_y = 0},
    {.bitmap_index = 1339, .adv_w = 179, .box_w = 11, .box_h = 15, .ofs_x = 0, .ofs_y = -4},
    {.bitmap_index = 1360, .adv_w = 167, .box_w = 9, .box_h = 11, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 1373, .adv_w = 231, .box_w = 13, .box_h = 18, .ofs_x = 1, .ofs_y = -4},
    {.bitmap_index = 1403, .adv_w = 269, .box_w = 15, .box_h = 18, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 1437, .adv_w = 253, .box_w = 12, .box_h = 18, .ofs_x = 2, .ofs_y = 0},
    {.bitmap_index = 1464, .adv_w = 183, .box_w = 10, .box_h = 15, .ofs_x = 1, .ofs_y = -4},
    {.bitmap_index = 1483, .adv_w = 203, .box_w = 11, .box_h = 15, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 1504, .adv_w = 217, .box_w = 10, .box_h = 15, .ofs_x = 2, .ofs_y = 0},
    {.bitmap_index = 1523, .adv_w = 247, .box_w = 13, .box_h = 19, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 1554, .adv_w = 221, .box_w = 11, .box_h = 19, .ofs_x = 1, .ofs_y = -4},
    {.bitmap_index = 1581, .adv_w = 99, .box_w = 2, .box_h = 18, .ofs_x = 2, .ofs_y = 0},
    {.bitmap_index = 1586, .adv_w = 89, .box_w = 2, .box_h = 11, .ofs_x = 2, .ofs_y = 0},
    {.bitmap_index = 1589, .adv_w = 199, .box_w = 10, .box_h = 18, .ofs_x = 1, .ofs_y = -4},
    {.bitmap_index = 1612, .adv_w = 160, .box_w = 9, .box_h = 15, .ofs_x = 1, .ofs_y = -4}
};

/*---------------------
 *  CHARACTER MAPPING
 *--------------------*/

static const uint8_t glyph_id_ofs_list_0[] = {
    0, 0, 0, 0, 1, 2, 0, 3,
    4, 5, 6, 7, 8, 9, 10, 11,
    12, 13, 14, 15, 16, 17, 18, 19,
    20, 21, 22, 0, 23
};

static const uint16_t unicode_list_3[] = {
    0x0, 0xf, 0x15, 0x20, 0x2f, 0x35, 0x57, 0x58,
    0x69, 0x6a, 0x97, 0x98
};

/*Collect the unicode lists and glyph_id offsets*/
static const lv_font_fmt_txt_cmap_t cmaps[] =
{
    {
        .range_start = 33, .range_length = 29, .glyph_id_start = 1,
        .unicode_list = NULL, .glyph_id_ofs_list = glyph_id_ofs_list_0, .list_length = 29, .type = LV_FONT_FMT_TXT_CMAP_FORMAT0_FULL
    },
    {
        .range_start = 63, .range_length = 28, .glyph_id_start = 25,
        .unicode_list = NULL, .glyph_id_ofs_list = NULL, .list_length = 0, .type = LV_FONT_FMT_TXT_CMAP_FORMAT0_TINY
    },
    {
        .range_start = 97, .range_length = 26, .glyph_id_start = 53,
        .unicode_list = NULL, .glyph_id_ofs_list = NULL, .list_length = 0, .type = LV_FONT_FMT_TXT_CMAP_FORMAT0_TINY
    },
    {
        .range_start = 199, .range_length = 153, .glyph_id_start = 79,
        .unicode_list = unicode_list_3, .glyph_id_ofs_list = NULL, .list_length = 12, .type = LV_FONT_FMT_TXT_CMAP_SPARSE_TINY
    }
};

/*-----------------
 *    KERNING
 *----------------*/


/*Map glyph_ids to kern left classes*/
static const uint8_t kern_left_class_mapping[] =
{
    0, 1, 2, 3, 4, 5, 6, 7,
    8, 7, 8, 9, 10, 0, 11, 12,
    13, 14, 15, 16, 17, 10, 18, 18,
    0, 19, 20, 21, 22, 23, 20, 24,
    25, 26, 27, 27, 28, 29, 30, 27,
    27, 20, 31, 32, 33, 34, 35, 28,
    36, 36, 37, 38, 39, 40, 41, 42,
    43, 44, 45, 46, 40, 46, 46, 47,
    43, 40, 40, 41, 41, 48, 49, 50,
    51, 46, 52, 52, 53, 52, 54, 23,
    20, 28, 42, 41, 46, 26, 46, 27,
    46, 34, 50
};

/*Map glyph_ids to kern right classes*/
static const uint8_t kern_right_class_mapping[] =
{
    0, 1, 2, 3, 4, 5, 6, 7,
    8, 7, 8, 9, 10, 11, 12, 13,
    14, 15, 10, 16, 17, 18, 19, 19,
    0, 20, 21, 22, 23, 21, 23, 23,
    23, 21, 23, 23, 24, 23, 23, 23,
    23, 21, 23, 21, 23, 25, 26, 27,
    28, 28, 29, 30, 31, 32, 33, 34,
    34, 34, 0, 34, 33, 35, 36, 33,
    33, 37, 37, 34, 37, 34, 37, 38,
    39, 40, 41, 41, 42, 41, 43, 21,
    21, 27, 34, 34, 40, 21, 34, 23,
    37, 25, 38
};

/*Kern values between classes*/
static const int8_t kern_class_values[] =
{
    0, 0, 0, 0, 0, 0, 0, 1,
    0, 0, 3, 0, 0, 0, 0, 2,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, -39, 0, 0, -6,
    0, 6, 10, 0, 0, -6, 3, 3,
    11, 6, -5, 6, 0, 0, -18, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, -4, -13,
    -2, 0, 0, 0, 0, 1, 12, 0,
    -10, -3, -1, 1, 0, -5, 0, 0,
    -2, -24, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 11, 0, 3, 0, 0, -6, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, -12, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 2,
    10, -3, 0, 0, 6, -3, -11, -44,
    2, 9, 6, 1, -4, 0, 12, 0,
    10, 0, 10, 0, -30, 0, -4, 3,
    10, 0, 11, -3, 6, 3, 0, 0,
    -5, 26, 0, 26, 0, 10, 0, 13,
    4, 5, 0, -12, 0, 0, 0, 0,
    1, -2, 0, 2, -6, -4, -6, 2,
    0, -3, 0, 0, 0, -13, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 1, -20, 0,
    0, 0, 0, -2, 0, 32, -4, -4,
    3, 3, -3, 0, -4, 3, 0, 0,
    -17, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, -12, 0, 11, 0, -22, -31,
    -22, -6, 10, 0, 0, -21, 0, 4,
    -7, 0, -5, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    2, 2, -4, -6, 0, -1, -1, -3,
    0, 0, -2, 0, 0, 0, -6, 0,
    -3, 0, -7, 0, -6, 0, -8, -11,
    -11, -6, 0, 0, 0, 0, -3, 0,
    0, 3, 0, 2, -3, 0, 0, 3,
    -2, 0, 0, 0, -2, 3, 3, -1,
    0, 0, 0, -6, 0, -1, 0, 0,
    0, 0, 0, 1, 0, 4, 0, -2,
    0, -4, 0, -5, 0, 0, 0, -3,
    0, 0, 0, 0, 0, -1, 1, -2,
    -2, 0, -3, 0, 0, 0, 0, 0,
    0, 0, 0, 0, -2, -2, 0, -3,
    -4, 0, 0, 0, 0, 0, 1, 0,
    0, 0, -2, 0, -3, -3, -3, 0,
    0, 0, 0, 0, -2, 0, 0, 0,
    0, -2, -4, 0, 0, -10, 6, 0,
    0, -6, 3, 6, 9, 0, -8, -1,
    -4, 0, -1, -15, 3, -2, 2, -17,
    3, 0, 0, 1, -2, -17, 0, -17,
    -3, -28, -2, 9, 0, 4, 0, 0,
    0, 0, 1, 0, -6, -4, 0, 0,
    -3, 0, 0, 0, -3, 0, 0, 0,
    0, 0, -2, -2, 0, -2, -4, 0,
    0, 0, 0, 0, 0, 0, -3, 0,
    -3, 0, -2, -4, -3, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, -3,
    -3, 0, 0, -6, 3, 0, 0, -4,
    2, 3, 3, 0, 0, 0, 0, 0,
    0, -2, 0, 0, 0, 0, 0, 2,
    0, 0, 0, -3, 0, -3, -2, -4,
    0, 0, 0, 3, 0, -3, 0, 0,
    0, 0, -4, -5, 0, 0, 1, -10,
    0, 0, 9, -16, -17, -13, -6, 3,
    0, -3, -21, -6, 0, -6, 0, -6,
    5, -6, -20, 0, -9, -2, 0, 0,
    2, -1, 3, -2, -12, 0, -16, -8,
    -7, -8, -10, -4, -9, -1, -6, -9,
    0, -3, 0, 0, 0, 2, 0, 3,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, -3, 0, -2, 0, -1,
    0, -3, 0, -5, -7, -7, -1, 0,
    0, 0, 0, -3, 0, 0, 0, 0,
    1, -2, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 15, 0, 0, 0, 0,
    0, 0, 2, 0, 0, 0, -3, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, -2, 0,
    -6, 0, 0, 0, 0, -16, -10, 0,
    0, 0, -5, -16, 0, 0, -3, 3,
    0, -9, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 4, 0, 2,
    -6, -6, 0, -3, -3, -4, 0, 0,
    0, 0, 0, 0, -10, 0, -3, 0,
    -5, 0, -3, 0, -7, -8, -10, -3,
    0, 0, 0, 0, 26, 0, 0, 2,
    0, 0, -4, 0, 0, 0, 0, 0,
    0, -30, -6, 11, 10, -3, -13, 0,
    3, -5, 0, -16, -2, -4, 3, -22,
    -3, 4, 0, 5, 0, -11, -5, -12,
    -11, -13, 0, 0, 0, -2, 0, 0,
    0, -2, -2, -3, -9, -11, -1, 0,
    0, 0, 0, 0, 0, 0, 1, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    -3, 0, -2, -3, -5, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, -6, 0, 0, 6,
    -1, 4, 0, -7, 3, -2, -1, -8,
    -3, 0, -4, -3, -2, 0, -5, -5,
    0, 0, -1, -3, -1, -2, -5, -4,
    0, -2, 0, -7, 0, 0, 0, -6,
    0, -5, 0, -5, -5, 0, 0, 0,
    0, 0, 0, -6, 3, 0, -4, 0,
    -2, -4, -10, -2, -2, -2, -1, -2,
    -4, -1, 0, 0, 0, 0, 0, 0,
    -3, -3, -3, 0, -2, 0, -2, 0,
    0, 0, -2, -4, -2, -3, -4, -3,
    3, 0, -9, 0, -2, 6, 0, -3,
    -13, -4, 5, 0, 0, -15, -5, 3,
    -5, 2, 0, -2, -3, -10, 0, -5,
    -1, 2, 0, 0, -5, 0, 0, -6,
    0, -5, -3, -5, -3, -3, 0, -5,
    2, -6, -5, 0, 0, 0, 0, 0,
    0, 0, 3, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, -2, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    -3, -3, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, -5, 0,
    0, 0, -4, 0, 0, -3, -3, 0,
    0, 0, 0, 0, -2, 0, 0, 0,
    0, 0, -2, 0, 0, 0, -6, 0,
    0, 0, -11, 0, 2, -7, 6, 1,
    -2, -15, 0, 0, -7, -3, 0, -13,
    -8, -9, 0, 0, -5, -14, -3, -13,
    -12, -15, 0, -4, 0, -7, -3, -1,
    -3, -5, -9, -6, -12, -13, -7, 0,
    0, 1, 0, 0, -22, -3, 10, 7,
    -7, -12, 0, 1, -10, 0, -16, -2,
    -3, 6, -29, -4, 1, 0, 0, -2,
    -21, -4, -17, -3, -23, 0, 1, 0,
    -2, 0, 0, 0, 0, -2, -2, -12,
    -2, 0, 0, 0, -10, 0, -3, 0,
    -1, -9, -15, 0, 0, -2, -5, -10,
    -3, 0, -2, 0, 0, 0, 0, -14,
    -3, -11, 0, -10, -3, -5, -8, -3,
    -5, -5, 0, -4, -6, -3, -6, 0,
    2, 0, -2, -11, 0, 0, 0, 0,
    0, 4, 0, 2, -6, 13, 0, -3,
    -3, -4, 0, 0, 0, 0, 0, 0,
    -10, 0, -3, 0, -5, 0, -3, 0,
    -7, -8, -10, -3, 0, 0, 0, 0,
    26, 0, 0, 2, 0, 0, -4, 0,
    0, 0, 0, 0, 0, 0, -1, 0,
    0, 0, 0, 0, -2, -6, 0, 0,
    0, 0, 0, -2, 0, 0, 0, -3,
    0, -3, 0, 0, -6, -3, 0, -2,
    0, 0, 0, 0, 0, 0, 2, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    -6, 5, 6, 0, 0, -3, 0, -2,
    3, 0, -3, 0, -3, -2, -6, 0,
    0, 0, 0, 0, -3, 0, 0, -4,
    -5, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, -3, -3, 0, 6, 0,
    -10, -5, 0, 10, -11, -10, -6, -6,
    13, 6, 3, -28, -2, 6, -3, 0,
    -3, 4, -3, -11, 0, -3, -3, 3,
    -4, -3, -10, -3, 0, -9, 0, -18,
    -4, 9, -4, -12, 1, -4, -11, -11,
    -3, 3, 0, -9, 0, 3, 11, -7,
    -12, -13, -8, 10, 0, 1, -23, -3,
    3, -5, -2, -7, 0, -7, -12, -5,
    -5, -5, -3, 0, 0, -7, -7, -3,
    -18, 0, -18, -4, 0, -11, -19, -1,
    -10, -5, -11, -9, 0, 0, -6, -3,
    0, -3, -6, 0, 5, -11, 3, 0,
    0, -17, 0, -3, -7, -5, -2, -10,
    -8, -11, -7, 0, -4, -10, -3, -7,
    -6, -10, -3, -5, 0, -10, -3, 0,
    -3, -6, -7, -9, -9, -12, -4, 6,
    0, -16, -4, 2, 6, -10, -12, -6,
    -11, 11, -3, 2, -30, -6, 6, -7,
    -5, -12, 0, -10, -13, -4, -3, -5,
    -3, -3, -7, -10, -1, 0, -21, 0,
    -19, -7, 8, -12, -22, -6, -11, -13,
    -16, -11, 0, 0, -4, 0, 0, 3,
    -4, 6, 2, -6, 6, 0, 0, -10,
    -1, 0, -1, 0, 1, 1, -3, 0,
    0, 0, 0, 0, 0, 0, -3, 0,
    0, 1, 0, -4, 0, 0, 0, 0,
    -2, -2, -4, 0, 0, 0, -9, 0,
    0, 0, -9, 0, 0, 0, 0, -7,
    -2, 0, 0, 0, -7, 0, -4, 0,
    -15, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 1, 0,
    0, 0, 0, 0, 0, -3, 0, 0,
    0, -9, 0, 0, 0, -5, 3, -4,
    0, 0, -9, -3, -7, 0, 0, -9,
    0, -3, 0, -15, 0, -4, 0, 0,
    0, -26, -6, -13, -4, -12, 0, -2,
    0, 0, 0, 0, 0, 0, 0, 0,
    -5, -6, -3, 0, 0, -7, 0, -7,
    4, -4, 6, 0, -2, -7, -2, -5,
    -6, 0, -4, -2, -2, 2, -9, -1,
    0, 0, 0, 0, -28, -3, -4, 0,
    -7, 0, 0, -2, -3, 0, 0, 0,
    0, 2, 0, -2, -5, -2, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 4, 0, 0, 0,
    0, 0, -2, 0, 0, 0, -6, 3,
    0, 0, 0, -9, -3, -6, 0, 0,
    -9, 0, -3, 0, -15, 0, 0, 0,
    0, 0, -31, 0, -6, -12, -16, 0,
    -5, 0, 0, 0, 0, 0, 0, 0,
    0, -3, -5, -2, 1, 5, -4, 0,
    10, 16, -3, -3, -10, 4, 16, 5,
    7, -9, 4, 13, 4, 9, 7, 9,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, -3, 0, -3, 26, 14,
    26, 0, 0, 0, 3, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, -2, 0, 0, 0, 0, 0, 0,
    0, 0, 4, 0, 0, 0, 0, -5,
    -27, -4, -3, -13, -16, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, -3, 0, 0, 0,
    -7, 3, 0, -3, 3, 6, 3, -10,
    0, -1, -3, 3, 0, 3, 0, 0,
    0, 0, 0, -8, 0, -3, -2, -6,
    0, -3, 0, -7, -2, 0, -2, -5,
    0, -3, -9, -6, -4, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, -2,
    0, 0, 0, 0, 0, 0, 0, 0,
    4, 0, 0, 0, 0, -5, -27, -4,
    -3, -13, -16, 0, 0, 0, 0, 0,
    16, 0, 0, 0, 0, 0, 0, 0,
    0, 0, -10, -4, -3, 10, -3, -3,
    -13, 1, -2, 1, -2, -9, 1, 7,
    1, 3, 1, 3, -8, -13, -4, 0,
    -5, -12, -6, -9, -13, -12, 0, -3,
    -2, -4, -2, 0, -2, -1, 5, 0,
    5, -2, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, -2, -3, -3,
    0, 0, -9, 0, -2, 0, -5, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, -3, -3, 0, 0, 0,
    -3, 0, 0, -5, -3, 3, 0, -5,
    -6, -2, 0, -9, -2, -7, -2, -4,
    0, -5, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, -6,
    0, 0, 0, 0, -4, 0, -3, 0,
    0, 0, 0, -7, 0, 0, 13, -4,
    -11, -10, 2, 4, 4, -1, -9, 2,
    5, 2, 10, 2, 11, -2, -9, 0,
    0, -2, -13, 0, 0, -10, -9, 0,
    -5, 0, -5, 0, -5, 0, -2, 5,
    0, -3, -10, -3, 0, 0, -6, 0,
    0, 4, -7, 0, 3, -3, 3, 0,
    0, -11, 0, -2, -1, 0, -3, 4,
    -3, 0, 0, 0, -3, -13, -4, -7,
    0, -10, 0, -3, 0, -6, 0, 2,
    0, -3, 0, -3, -10, 0, -3, 0,
    0, -2, 0, 0, 3, -4, 1, 0,
    0, -4, -2, 0, -4, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    -3, 0, 0, 0, 0, 1, 0, -3,
    -3, 0
};


/*Collect the kern class' data in one place*/
static const lv_font_fmt_txt_kern_classes_t kern_classes =
{
    .class_pair_values   = kern_class_values,
    .left_class_mapping  = kern_left_class_mapping,
    .right_class_mapping = kern_right_class_mapping,
    .left_class_cnt      = 54,
    .right_class_cnt     = 43,
};

/*--------------------
 *  ALL CUSTOM DATA
 *--------------------*/

#if LVGL_VERSION_MAJOR == 8
/*Store all the custom data of the font*/
static  lv_font_fmt_txt_glyph_cache_t cache;
#endif

#if LVGL_VERSION_MAJOR >= 8
static const lv_font_fmt_txt_dsc_t font_dsc = {
#else
static lv_font_fmt_txt_dsc_t font_dsc = {
#endif
    .glyph_bitmap = glyph_bitmap,
    .glyph_dsc = glyph_dsc,
    .cmaps = cmaps,
    .kern_dsc = &kern_classes,
    .kern_scale = 16,
    .cmap_num = 4,
    .bpp = 1,
    .kern_classes = 1,
    .bitmap_format = 0,
#if LVGL_VERSION_MAJOR == 8
    .cache = &cache
#endif

};

extern const lv_font_t lv_font_montserrat_20;


/*-----------------
 *  PUBLIC FONT
 *----------------*/

/*Initialize a public general font descriptor*/
#if LVGL_VERSION_MAJOR >= 8
const lv_font_t turkish_better_21 = {
#else
lv_font_t turkish_better_21 = {
#endif
    .get_glyph_dsc = lv_font_get_glyph_dsc_fmt_txt,    /*Function pointer to get glyph's data*/
    .get_glyph_bitmap = lv_font_get_bitmap_fmt_txt,    /*Function pointer to get glyph's bitmap*/
    .line_height = 23,          /*The maximum line height required by the font*/
    .base_line = 4,             /*Baseline measured from the bottom of the line*/
#if !(LVGL_VERSION_MAJOR == 6 && LVGL_VERSION_MINOR == 0)
    .subpx = LV_FONT_SUBPX_NONE,
#endif
#if LV_VERSION_CHECK(7, 4, 0) || LVGL_VERSION_MAJOR >= 8
    .underline_position = -1,
    .underline_thickness = 1,
#endif
    .dsc = &font_dsc,          /*The custom font data. Will be accessed by `get_glyph_bitmap/dsc` */
#if LV_VERSION_CHECK(8, 2, 0) || LVGL_VERSION_MAJOR >= 9
    .fallback = &lv_font_montserrat_20,
#endif
    .user_data = NULL,
};



#endif /*#if TURKISH_BETTER_21*/
