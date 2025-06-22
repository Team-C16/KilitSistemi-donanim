/*******************************************************************************
 * Size: 16 px
 * Bpp: 1
 * Opts: --bpp 1 --size 16 --no-compress --font "Paneuropa Highway.ttf" --symbols "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789ÇŞĞİÖÜçşğıöü.,:;!?%&@-+/=()" --format lvgl -o turkish_16.c
 ******************************************************************************/



#include <lvgl.h>


#ifndef TURKISH_16
#define TURKISH_16 1
#endif

#if TURKISH_16

/*-----------------
 *    BITMAPS
 *----------------*/

/*Store the image of the glyphs*/
static LV_ATTRIBUTE_LARGE_CONST const uint8_t glyph_bitmap[] = {
    /* U+0021 "!" */
    0x6d, 0xb6, 0xc3, 0x60,

    /* U+0025 "%" */
    0x71, 0xb6, 0xcd, 0xa1, 0xd8, 0xc, 0x6, 0xe1,
    0x6c, 0xdb, 0x63, 0x80,

    /* U+0026 "&" */
    0x78, 0x19, 0x83, 0x30, 0x3c, 0x7, 0x99, 0xbb,
    0x33, 0xe6, 0x3c, 0x7f, 0xc0,

    /* U+0028 "(" */
    0x32, 0x64, 0xcc, 0xcc, 0xc4, 0x63, 0x30,

    /* U+0029 ")" */
    0xc4, 0x62, 0x33, 0x33, 0x36, 0x6c, 0xc0,

    /* U+002A "*" */
    0x2, 0xbe, 0xe5, 0x0,

    /* U+002B "+" */
    0x30, 0xcf, 0xcc, 0x30,

    /* U+002C "," */
    0x6f, 0x0,

    /* U+002D "-" */
    0xfc,

    /* U+002E "." */
    0x6c,

    /* U+002F "/" */
    0x18, 0xcc, 0x63, 0x19, 0x8c, 0x63, 0x31, 0x80,

    /* U+0030 "0" */
    0x7b, 0x3c, 0xf3, 0xcf, 0x3c, 0xf3, 0x78,

    /* U+0031 "1" */
    0x3b, 0xd6, 0x31, 0x8c, 0x63, 0x18,

    /* U+0032 "2" */
    0xfa, 0x30, 0xc7, 0x39, 0xce, 0x30, 0xfc,

    /* U+0033 "3" */
    0xf8, 0x30, 0xcc, 0xc, 0x30, 0xe7, 0xf8,

    /* U+0034 "4" */
    0x18, 0x30, 0xc3, 0x86, 0xd9, 0xbf, 0x86, 0xc,

    /* U+0035 "5" */
    0xff, 0xc, 0x3e, 0xc, 0x30, 0xc7, 0xf8,

    /* U+0036 "6" */
    0x39, 0x8c, 0x3e, 0xcf, 0x3c, 0xd3, 0x78,

    /* U+0037 "7" */
    0xfc, 0x30, 0x86, 0x18, 0xc3, 0xc, 0x60,

    /* U+0038 "8" */
    0x79, 0x9b, 0x33, 0xe7, 0x99, 0xf1, 0xe3, 0x7c,

    /* U+0039 "9" */
    0x7d, 0x8f, 0x1e, 0x3c, 0x6f, 0x83, 0xc, 0x70,

    /* U+003A ":" */
    0xf0, 0x3c,

    /* U+003B ";" */
    0x6c, 0x0, 0xde,

    /* U+003D "=" */
    0xfc, 0x0, 0x3f,

    /* U+003F "?" */
    0x78, 0x30, 0xc6, 0x30, 0xc0, 0xc, 0x30,

    /* U+0040 "@" */
    0xf, 0xc1, 0x83, 0x99, 0xfd, 0x99, 0xbd, 0x99,
    0xec, 0xcf, 0x66, 0x7b, 0x36, 0x6e, 0xe1, 0x80,
    0x7, 0xf0,

    /* U+0041 "A" */
    0x1c, 0x1c, 0x3c, 0x34, 0x36, 0x66, 0x7e, 0x63,
    0xc3,

    /* U+0042 "B" */
    0xf9, 0x9b, 0x36, 0x6f, 0x98, 0xf1, 0xe3, 0xfc,

    /* U+0043 "C" */
    0x3d, 0x8c, 0x30, 0xc3, 0xc, 0x18, 0x7c,

    /* U+0044 "D" */
    0xf9, 0x9b, 0x1e, 0x3c, 0x78, 0xf1, 0xe6, 0xf8,

    /* U+0045 "E" */
    0xff, 0xc, 0x30, 0xfb, 0xc, 0x30, 0xfc,

    /* U+0046 "F" */
    0xff, 0xc, 0x30, 0xfb, 0xc, 0x30, 0xc0,

    /* U+0047 "G" */
    0x3e, 0xc3, 0x6, 0xc, 0xf8, 0xf1, 0xb3, 0x3e,

    /* U+0048 "H" */
    0xc7, 0x8f, 0x1e, 0x3f, 0xf8, 0xf1, 0xe3, 0xc6,

    /* U+0049 "I" */
    0xf6, 0x66, 0x66, 0x66, 0xf0,

    /* U+004A "J" */
    0xc, 0x30, 0xc3, 0xc, 0x30, 0xc3, 0x78,

    /* U+004B "K" */
    0xcd, 0xbb, 0x67, 0x8f, 0x1f, 0x36, 0x66, 0xc6,

    /* U+004C "L" */
    0xc3, 0xc, 0x30, 0xc3, 0xc, 0x30, 0xfc,

    /* U+004D "M" */
    0xe7, 0xe7, 0xe7, 0xff, 0xff, 0xdb, 0xdb, 0xc3,
    0xc3,

    /* U+004E "N" */
    0xe7, 0xcf, 0xdf, 0xbd, 0x7b, 0xf7, 0xe7, 0xce,

    /* U+004F "O" */
    0x38, 0xdb, 0x1e, 0x3c, 0x78, 0xf1, 0xb6, 0x38,

    /* U+0050 "P" */
    0xfb, 0x3c, 0xf3, 0xcf, 0xec, 0x30, 0xc0,

    /* U+0051 "Q" */
    0x38, 0xdb, 0x1e, 0x3c, 0x78, 0xf5, 0xbe, 0x3c,
    0xc, 0x0,

    /* U+0052 "R" */
    0xf9, 0x9b, 0x36, 0x6f, 0x9b, 0x36, 0x66, 0xcc,

    /* U+0053 "S" */
    0x7f, 0x83, 0x7, 0x83, 0xc1, 0xc1, 0xc3, 0xfc,

    /* U+0054 "T" */
    0xfe, 0x30, 0x60, 0xc1, 0x83, 0x6, 0xc, 0x18,

    /* U+0055 "U" */
    0xc7, 0x8f, 0x1e, 0x3c, 0x78, 0xf1, 0xe3, 0x7c,

    /* U+0056 "V" */
    0xc3, 0x63, 0x66, 0x66, 0x36, 0x3c, 0x3c, 0x3c,
    0x1c,

    /* U+0057 "W" */
    0xc0, 0xf3, 0x2d, 0xdb, 0x76, 0xd5, 0xb5, 0xe7,
    0x79, 0xde, 0x63, 0x0,

    /* U+0058 "X" */
    0x63, 0x36, 0x36, 0x1c, 0x1c, 0x1c, 0x36, 0x77,
    0x63,

    /* U+0059 "Y" */
    0xc3, 0x66, 0x3e, 0x3c, 0x18, 0x18, 0x18, 0x18,
    0x18,

    /* U+005A "Z" */
    0xfc, 0x31, 0x8e, 0x31, 0x86, 0x30, 0xfc,

    /* U+0061 "a" */
    0xf8, 0x30, 0xdf, 0xcf, 0x37, 0xc0,

    /* U+0062 "b" */
    0xc3, 0xf, 0xb3, 0xcf, 0x3c, 0xf3, 0xf8,

    /* U+0063 "c" */
    0x7e, 0x31, 0x8c, 0x61, 0xe0,

    /* U+0064 "d" */
    0xc, 0x37, 0xf3, 0xcf, 0x3c, 0xf3, 0x7c,

    /* U+0065 "e" */
    0x3c, 0xcd, 0x9f, 0xf6, 0xc, 0xf, 0x80,

    /* U+0066 "f" */
    0x3d, 0x8f, 0x98, 0x61, 0x86, 0x18, 0x60,

    /* U+0067 "g" */
    0x7f, 0x3c, 0xf3, 0xcf, 0x37, 0xc3, 0xf8,

    /* U+0068 "h" */
    0xc3, 0xf, 0xb3, 0xcf, 0x3c, 0xf3, 0xcc,

    /* U+0069 "i" */
    0x6c, 0x76, 0xdb, 0x6c,

    /* U+006A "j" */
    0x33, 0x7, 0x33, 0x33, 0x33, 0x3e,

    /* U+006B "k" */
    0xc3, 0xc, 0xf6, 0xf3, 0xcf, 0xb6, 0xcc,

    /* U+006C "l" */
    0xdb, 0x6d, 0xb6, 0xe0,

    /* U+006D "m" */
    0xff, 0xb3, 0x3c, 0xcf, 0x33, 0xcc, 0xf3, 0x3c,
    0xcc,

    /* U+006E "n" */
    0xfb, 0x3c, 0xf3, 0xcf, 0x3c, 0xc0,

    /* U+006F "o" */
    0x7d, 0x8f, 0x1e, 0x3c, 0x78, 0xdf, 0x0,

    /* U+0070 "p" */
    0xfb, 0x3c, 0xf3, 0xcf, 0x3f, 0xb0, 0xc0,

    /* U+0071 "q" */
    0x7f, 0x3c, 0xf3, 0xcf, 0x37, 0xc3, 0xc,

    /* U+0072 "r" */
    0xfb, 0x18, 0xc6, 0x33, 0xc0,

    /* U+0073 "s" */
    0x7b, 0xe, 0x1e, 0x18, 0x6f, 0x80,

    /* U+0074 "t" */
    0x63, 0x3e, 0xc6, 0x31, 0x8c, 0x38,

    /* U+0075 "u" */
    0xcf, 0x3c, 0xf3, 0xcf, 0x37, 0xc0,

    /* U+0076 "v" */
    0xc6, 0xcd, 0x9b, 0x63, 0xc7, 0x8e, 0x0,

    /* U+0077 "w" */
    0x60, 0x6c, 0xcd, 0xbb, 0x37, 0x63, 0xbc, 0x77,
    0x8e, 0x60,

    /* U+0078 "x" */
    0x66, 0x3e, 0x3c, 0x18, 0x3c, 0x36, 0x66,

    /* U+0079 "y" */
    0x66, 0x66, 0x66, 0x34, 0x3c, 0x3c, 0x18, 0x18,
    0x70,

    /* U+007A "z" */
    0xf8, 0xcc, 0x46, 0x63, 0xe0,

    /* U+00C7 "Ç" */
    0x3d, 0x8c, 0x30, 0xc3, 0xc, 0x18, 0x7c, 0xe0,
    0xce,

    /* U+00D6 "Ö" */
    0x36, 0x6c, 0x1, 0xc6, 0xd8, 0xf1, 0xe3, 0xc7,
    0x8d, 0xb1, 0xc0,

    /* U+00DC "Ü" */
    0x4c, 0x98, 0x6, 0x3c, 0x78, 0xf1, 0xe3, 0xc7,
    0x8f, 0x1b, 0xe0,

    /* U+00E7 "ç" */
    0x7e, 0x31, 0x8c, 0x61, 0xe7, 0x38,

    /* U+00F6 "ö" */
    0xd9, 0xb1, 0xf6, 0x3c, 0x78, 0xf1, 0xe3, 0x7c,

    /* U+00FC "ü" */
    0xdb, 0x6c, 0xf3, 0xcf, 0x3c, 0xf3, 0x7c,

    /* U+011E "Ğ" */
    0x24, 0x78, 0x1, 0xf6, 0x18, 0x30, 0x67, 0xc7,
    0x8d, 0x99, 0xf0,

    /* U+011F "ğ" */
    0x48, 0xe0, 0x1f, 0xcf, 0x3c, 0xf3, 0xcd, 0xf0,
    0xfe,

    /* U+0130 "İ" */
    0x66, 0xf, 0x66, 0x66, 0x66, 0x6f,

    /* U+0131 "ı" */
    0xed, 0xb6, 0xd8,

    /* U+015E "Ş" */
    0x7f, 0x83, 0x7, 0x83, 0xc1, 0xc1, 0xc3, 0xfc,
    0x60, 0x73, 0xc0,

    /* U+015F "ş" */
    0x7b, 0xe, 0x1e, 0x18, 0x6f, 0x8c, 0x19, 0xc0
};


/*---------------------
 *  GLYPH DESCRIPTION
 *--------------------*/

static const lv_font_fmt_txt_glyph_dsc_t glyph_dsc[] = {
    {.bitmap_index = 0, .adv_w = 0, .box_w = 0, .box_h = 0, .ofs_x = 0, .ofs_y = 0} /* id = 0 reserved */,
    {.bitmap_index = 0, .adv_w = 52, .box_w = 3, .box_h = 9, .ofs_x = 0, .ofs_y = 0},
    {.bitmap_index = 4, .adv_w = 184, .box_w = 10, .box_h = 9, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 16, .adv_w = 174, .box_w = 11, .box_h = 9, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 29, .adv_w = 73, .box_w = 4, .box_h = 13, .ofs_x = 1, .ofs_y = -2},
    {.bitmap_index = 36, .adv_w = 73, .box_w = 4, .box_h = 13, .ofs_x = 0, .ofs_y = -2},
    {.bitmap_index = 43, .adv_w = 98, .box_w = 5, .box_h = 5, .ofs_x = 1, .ofs_y = 5},
    {.bitmap_index = 47, .adv_w = 95, .box_w = 6, .box_h = 5, .ofs_x = 1, .ofs_y = 2},
    {.bitmap_index = 51, .adv_w = 51, .box_w = 3, .box_h = 3, .ofs_x = 0, .ofs_y = -2},
    {.bitmap_index = 53, .adv_w = 120, .box_w = 6, .box_h = 1, .ofs_x = 1, .ofs_y = 4},
    {.bitmap_index = 54, .adv_w = 52, .box_w = 3, .box_h = 2, .ofs_x = 0, .ofs_y = 0},
    {.bitmap_index = 55, .adv_w = 81, .box_w = 5, .box_h = 12, .ofs_x = 0, .ofs_y = -1},
    {.bitmap_index = 63, .adv_w = 123, .box_w = 6, .box_h = 9, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 70, .adv_w = 85, .box_w = 5, .box_h = 9, .ofs_x = -1, .ofs_y = 0},
    {.bitmap_index = 76, .adv_w = 117, .box_w = 6, .box_h = 9, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 83, .adv_w = 118, .box_w = 6, .box_h = 9, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 90, .adv_w = 115, .box_w = 7, .box_h = 9, .ofs_x = 0, .ofs_y = 0},
    {.bitmap_index = 98, .adv_w = 115, .box_w = 6, .box_h = 9, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 105, .adv_w = 119, .box_w = 6, .box_h = 9, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 112, .adv_w = 105, .box_w = 6, .box_h = 9, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 119, .adv_w = 125, .box_w = 7, .box_h = 9, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 127, .adv_w = 118, .box_w = 7, .box_h = 9, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 135, .adv_w = 56, .box_w = 2, .box_h = 7, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 137, .adv_w = 52, .box_w = 3, .box_h = 8, .ofs_x = 0, .ofs_y = -2},
    {.bitmap_index = 140, .adv_w = 111, .box_w = 6, .box_h = 4, .ofs_x = 1, .ofs_y = 2},
    {.bitmap_index = 143, .adv_w = 99, .box_w = 6, .box_h = 9, .ofs_x = 0, .ofs_y = 0},
    {.bitmap_index = 150, .adv_w = 222, .box_w = 13, .box_h = 11, .ofs_x = 1, .ofs_y = -2},
    {.bitmap_index = 168, .adv_w = 137, .box_w = 8, .box_h = 9, .ofs_x = 0, .ofs_y = 0},
    {.bitmap_index = 177, .adv_w = 129, .box_w = 7, .box_h = 9, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 185, .adv_w = 117, .box_w = 6, .box_h = 9, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 192, .adv_w = 132, .box_w = 7, .box_h = 9, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 200, .adv_w = 114, .box_w = 6, .box_h = 9, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 207, .adv_w = 105, .box_w = 6, .box_h = 9, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 214, .adv_w = 128, .box_w = 7, .box_h = 9, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 222, .adv_w = 145, .box_w = 7, .box_h = 9, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 230, .adv_w = 81, .box_w = 4, .box_h = 9, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 235, .adv_w = 105, .box_w = 6, .box_h = 9, .ofs_x = 0, .ofs_y = 0},
    {.bitmap_index = 242, .adv_w = 137, .box_w = 7, .box_h = 9, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 250, .adv_w = 106, .box_w = 6, .box_h = 9, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 257, .adv_w = 160, .box_w = 8, .box_h = 9, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 266, .adv_w = 138, .box_w = 7, .box_h = 9, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 274, .adv_w = 136, .box_w = 7, .box_h = 9, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 282, .adv_w = 118, .box_w = 6, .box_h = 9, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 289, .adv_w = 133, .box_w = 7, .box_h = 11, .ofs_x = 1, .ofs_y = -2},
    {.bitmap_index = 299, .adv_w = 133, .box_w = 7, .box_h = 9, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 307, .adv_w = 124, .box_w = 7, .box_h = 9, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 315, .adv_w = 120, .box_w = 7, .box_h = 9, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 323, .adv_w = 136, .box_w = 7, .box_h = 9, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 331, .adv_w = 134, .box_w = 8, .box_h = 9, .ofs_x = 0, .ofs_y = 0},
    {.bitmap_index = 340, .adv_w = 181, .box_w = 10, .box_h = 9, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 352, .adv_w = 144, .box_w = 8, .box_h = 9, .ofs_x = 0, .ofs_y = 0},
    {.bitmap_index = 361, .adv_w = 134, .box_w = 8, .box_h = 9, .ofs_x = 0, .ofs_y = 0},
    {.bitmap_index = 370, .adv_w = 121, .box_w = 6, .box_h = 9, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 377, .adv_w = 121, .box_w = 6, .box_h = 7, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 383, .adv_w = 117, .box_w = 6, .box_h = 9, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 390, .adv_w = 106, .box_w = 5, .box_h = 7, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 395, .adv_w = 117, .box_w = 6, .box_h = 9, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 402, .adv_w = 119, .box_w = 7, .box_h = 7, .ofs_x = 0, .ofs_y = 0},
    {.bitmap_index = 409, .adv_w = 93, .box_w = 6, .box_h = 9, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 416, .adv_w = 122, .box_w = 6, .box_h = 9, .ofs_x = 1, .ofs_y = -2},
    {.bitmap_index = 423, .adv_w = 117, .box_w = 6, .box_h = 9, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 430, .adv_w = 60, .box_w = 3, .box_h = 10, .ofs_x = 0, .ofs_y = 0},
    {.bitmap_index = 434, .adv_w = 74, .box_w = 4, .box_h = 12, .ofs_x = 0, .ofs_y = -2},
    {.bitmap_index = 440, .adv_w = 112, .box_w = 6, .box_h = 9, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 447, .adv_w = 63, .box_w = 3, .box_h = 9, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 451, .adv_w = 186, .box_w = 10, .box_h = 7, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 460, .adv_w = 125, .box_w = 6, .box_h = 7, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 466, .adv_w = 123, .box_w = 7, .box_h = 7, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 473, .adv_w = 116, .box_w = 6, .box_h = 9, .ofs_x = 1, .ofs_y = -2},
    {.bitmap_index = 480, .adv_w = 116, .box_w = 6, .box_h = 9, .ofs_x = 1, .ofs_y = -2},
    {.bitmap_index = 487, .adv_w = 108, .box_w = 5, .box_h = 7, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 492, .adv_w = 109, .box_w = 6, .box_h = 7, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 498, .adv_w = 91, .box_w = 5, .box_h = 9, .ofs_x = 0, .ofs_y = 0},
    {.bitmap_index = 504, .adv_w = 123, .box_w = 6, .box_h = 7, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 510, .adv_w = 125, .box_w = 7, .box_h = 7, .ofs_x = 0, .ofs_y = 0},
    {.bitmap_index = 517, .adv_w = 185, .box_w = 11, .box_h = 7, .ofs_x = 0, .ofs_y = 0},
    {.bitmap_index = 527, .adv_w = 135, .box_w = 8, .box_h = 7, .ofs_x = 0, .ofs_y = 0},
    {.bitmap_index = 534, .adv_w = 125, .box_w = 8, .box_h = 9, .ofs_x = 0, .ofs_y = -2},
    {.bitmap_index = 543, .adv_w = 115, .box_w = 5, .box_h = 7, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 548, .adv_w = 110, .box_w = 6, .box_h = 12, .ofs_x = 1, .ofs_y = -3},
    {.bitmap_index = 557, .adv_w = 133, .box_w = 7, .box_h = 12, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 568, .adv_w = 132, .box_w = 7, .box_h = 12, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 579, .adv_w = 100, .box_w = 5, .box_h = 9, .ofs_x = 1, .ofs_y = -2},
    {.bitmap_index = 585, .adv_w = 123, .box_w = 7, .box_h = 9, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 593, .adv_w = 120, .box_w = 6, .box_h = 9, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 600, .adv_w = 124, .box_w = 7, .box_h = 12, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 611, .adv_w = 117, .box_w = 6, .box_h = 12, .ofs_x = 1, .ofs_y = -2},
    {.bitmap_index = 620, .adv_w = 71, .box_w = 4, .box_h = 12, .ofs_x = 1, .ofs_y = 0},
    {.bitmap_index = 626, .adv_w = 63, .box_w = 3, .box_h = 7, .ofs_x = 0, .ofs_y = 0},
    {.bitmap_index = 629, .adv_w = 116, .box_w = 7, .box_h = 12, .ofs_x = 1, .ofs_y = -3},
    {.bitmap_index = 640, .adv_w = 102, .box_w = 6, .box_h = 10, .ofs_x = 1, .ofs_y = -3}
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


/*Pair left and right glyphs for kerning*/
static const uint8_t kern_pair_glyph_ids[] =
{
    27, 46,
    27, 48,
    27, 49,
    27, 51,
    27, 72,
    27, 74,
    27, 75,
    27, 77,
    37, 53,
    37, 73,
    38, 46,
    38, 48,
    38, 49,
    38, 51,
    38, 62,
    38, 74,
    38, 75,
    38, 77,
    40, 62,
    46, 27,
    48, 27,
    48, 57,
    49, 27,
    49, 53,
    49, 57,
    51, 27,
    55, 60,
    57, 70,
    57, 71,
    57, 74,
    57, 78,
    58, 53,
    58, 57,
    58, 58,
    58, 59,
    58, 64,
    58, 67,
    58, 72,
    58, 83,
    60, 61,
    60, 65,
    63, 67,
    67, 70,
    67, 74,
    67, 76,
    70, 59,
    70, 67,
    72, 72,
    74, 27,
    74, 57,
    74, 67,
    75, 27,
    75, 53,
    75, 57,
    75, 67,
    76, 67,
    77, 27,
    78, 67,
    84, 64
};

/* Kerning between the respective left and right glyphs
 * 4.4 format which needs to scaled with `kern_scale`*/
static const int8_t kern_pair_values[] =
{
    -24, -16, -19, -27, -11, -8, -11, -13,
    -8, -11, -29, -24, -16, -29, -16, -8,
    -11, -13, -16, -24, -24, -19, -13, -13,
    -13, -32, -11, -11, -5, -6, -11, -19,
    -21, -27, -17, 3, -13, -27, -11, 5,
    5, -8, -8, -8, -15, -8, -13, -19,
    -11, -11, -6, -16, -13, -11, -5, -19,
    -11, -8, 13
};

/*Collect the kern pair's data in one place*/
static const lv_font_fmt_txt_kern_pair_t kern_pairs =
{
    .glyph_ids = kern_pair_glyph_ids,
    .values = kern_pair_values,
    .pair_cnt = 59,
    .glyph_ids_size = 0
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
    .kern_dsc = &kern_pairs,
    .kern_scale = 16,
    .cmap_num = 4,
    .bpp = 1,
    .kern_classes = 0,
    .bitmap_format = 0,
#if LVGL_VERSION_MAJOR == 8
    .cache = &cache
#endif
};

extern const lv_font_t lv_font_montserrat_16;


/*-----------------
 *  PUBLIC FONT
 *----------------*/

/*Initialize a public general font descriptor*/
#if LVGL_VERSION_MAJOR >= 8
const lv_font_t turkish_16 = {
#else
lv_font_t turkish_16 = {
#endif
    .get_glyph_dsc = lv_font_get_glyph_dsc_fmt_txt,    /*Function pointer to get glyph's data*/
    .get_glyph_bitmap = lv_font_get_bitmap_fmt_txt,    /*Function pointer to get glyph's bitmap*/
    .line_height = 15,          /*The maximum line height required by the font*/
    .base_line = 3,             /*Baseline measured from the bottom of the line*/
#if !(LVGL_VERSION_MAJOR == 6 && LVGL_VERSION_MINOR == 0)
    .subpx = LV_FONT_SUBPX_NONE,
#endif
#if LV_VERSION_CHECK(7, 4, 0) || LVGL_VERSION_MAJOR >= 8
    .underline_position = 0,
    .underline_thickness = 0,
#endif
    .dsc = &font_dsc,          /*The custom font data. Will be accessed by `get_glyph_bitmap/dsc` */
#if LV_VERSION_CHECK(8, 2, 0) || LVGL_VERSION_MAJOR >= 9
    .fallback = &lv_font_montserrat_16,
#endif
    .user_data = NULL,
};



#endif /*#if TURKISH_16*/
