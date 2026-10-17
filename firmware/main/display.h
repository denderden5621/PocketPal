#pragma once
#include <stdint.h>
#include <stdbool.h>
#include "config.h"

// Sharp bellek ekranı sürücüsü + 1-bit çizim fonksiyonları.
// Çerçeve tamponunda 1 = siyah piksel. Yalnızca değişen satırlar gönderilir.
namespace display {

void begin();                  // SPI'yı kur (panel içeriğine dokunmaz)
void clearPanel();             // donanım "tümünü sil" komutu
void flush();                  // değişen satırları gönder
void flushAll();               // tüm satırları gönder
void prepareSleep();           // SPI pinlerini sabitle (derin uyku öncesi)
void setRotate180(bool r);
void assumeShown();            // tampondaki görüntünün panelde zaten olduğunu varsay (uyanışta)     // ekranı 180° çevir (montaj ters olduysa)

void clear(bool black = false);
void pixel(int x, int y, bool on = true);
bool getPixel(int x, int y);
void hline(int x, int y, int w, bool on = true);
void vline(int x, int y, int h, bool on = true);
void rect(int x, int y, int w, int h, bool fill, bool on = true);
void roundRect(int x, int y, int w, int h, int r, bool fill, bool on = true);
void circle(int cx, int cy, int r, bool fill, bool on = true);
void ellipse(int cx, int cy, int rx, int ry, bool fill, bool on = true);
void line(int x0, int y0, int x1, int y1, bool on = true, int thick = 1);
void arc(int cx, int cy, int r, int deg0, int deg1, bool on = true, int thick = 1);
void bitmap(int x, int y, int w, int h, const uint8_t *rows, bool on = true); // satır başına ceil(w/8) bayt, MSB solda
void invertRect(int x, int y, int w, int h);

int  textWidth(const char *utf8, int scale);
void text(int x, int y, const char *utf8, int scale = 1, bool on = true);
void textCentered(int y, const char *utf8, int scale = 1, bool on = true);

} // namespace display
