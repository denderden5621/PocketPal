#include "display.h"
#include <string.h>
#include <stdlib.h>
#include <math.h>
#include "driver/spi_master.h"
#include "driver/gpio.h"
#include "esp_log.h"
#include "font5x7.h"
#include "esp_heap_caps.h"

static const char *TAG = "ekran";

namespace display {

static const int ROW_BYTES = LCD_W / 8;           // 16
static uint8_t fb[LCD_H][ROW_BYTES];              // çalışma tamponu (1 = siyah)
static uint8_t sent[LCD_H][ROW_BYTES];            // panele en son giden içerik
static bool sent_valid = false;
static bool rot180 = LCD_ROTATE_180;           // çalışırken menüden değiştirilebilir
static spi_device_handle_t dev = nullptr;
// komut + 128 x (adres + 16 veri + 1 dolgu) + 1 son dolgu
static uint8_t *txbuf = nullptr;
static const size_t TXBUF_LEN = 1 + LCD_H * (1 + ROW_BYTES + 1) + 1;

void begin()
{
    if (dev) return;
    // derin uykuda tutulan (hold) pinleri serbest bırak
    gpio_hold_dis(PIN_LCD_SCS);
    gpio_hold_dis(PIN_LCD_SCLK);
    gpio_hold_dis(PIN_LCD_SI);
    spi_bus_config_t bus = {};
    bus.mosi_io_num = PIN_LCD_SI;
    bus.miso_io_num = -1;
    bus.sclk_io_num = PIN_LCD_SCLK;
    bus.quadwp_io_num = -1;
    bus.quadhd_io_num = -1;
    bus.max_transfer_sz = TXBUF_LEN;
    ESP_ERROR_CHECK(spi_bus_initialize(SPI2_HOST, &bus, SPI_DMA_CH_AUTO));

    spi_device_interface_config_t cfg = {};
    cfg.mode = 0;
    cfg.clock_speed_hz = LCD_SPI_HZ;
    cfg.spics_io_num = PIN_LCD_SCS;
    cfg.flags = SPI_DEVICE_POSITIVE_CS | SPI_DEVICE_TXBIT_LSBFIRST;  // SCS aktif yüksek, LSB önce
    cfg.cs_ena_pretrans = 4;   // tsSCS >= 3 us (1 MHz'de 1 bit = 1 us)
    cfg.cs_ena_posttrans = 2;  // thSCS >= 1 us
    cfg.queue_size = 1;
    ESP_ERROR_CHECK(spi_bus_add_device(SPI2_HOST, &cfg, &dev));

    txbuf = (uint8_t *)heap_caps_malloc(TXBUF_LEN, MALLOC_CAP_DMA);
    ESP_ERROR_CHECK(txbuf ? ESP_OK : ESP_ERR_NO_MEM);
    memset(fb, 0, sizeof(fb));
    sent_valid = false;
    ESP_LOGI(TAG, "hazır");
}

static void send(const uint8_t *buf, size_t len)
{
    spi_transaction_t t = {};
    t.length = len * 8;
    t.tx_buffer = buf;
    ESP_ERROR_CHECK(spi_device_polling_transmit(dev, &t));
}

void clearPanel()
{
    uint8_t cmd[2] = {0x04, 0x00};  // M2 = tümünü sil
    send(cmd, 2);
    memset(sent, 0, sizeof(sent));
    sent_valid = true;
}

// Panel satır numarası (1..128) ve satır verisini (1 = beyaz) yönlendirmeye göre hazırla
static void panelRow(int y, uint8_t *dst, uint8_t *addr)
{
    int src_y = rot180 ? (LCD_H - 1 - y) : y;
    bool flip_x = rot180 ^ (LCD_MIRROR_X != 0);
    for (int b = 0; b < ROW_BYTES; b++) {
        uint8_t v;
        if (!flip_x) {
            v = fb[src_y][b];
        } else {
            uint8_t s = fb[src_y][ROW_BYTES - 1 - b];
            v = 0;
            for (int i = 0; i < 8; i++) if (s & (1 << i)) v |= (0x80 >> i);
        }
        dst[b] = (uint8_t)~v;   // panelde 1 = beyaz
    }
    *addr = (uint8_t)(y + 1);
}

static void flushRows(bool all)
{
    size_t n = 0;
    txbuf[n++] = 0x01;          // M0 = veri güncelleme
    int rows = 0;
    for (int y = 0; y < LCD_H; y++) {
        int src_y = rot180 ? (LCD_H - 1 - y) : y;
        if (!all && sent_valid && memcmp(fb[src_y], sent[src_y], ROW_BYTES) == 0) continue;
        uint8_t addr;
        panelRow(y, &txbuf[n + 1], &addr);
        txbuf[n] = addr;
        n += 1 + ROW_BYTES;
        txbuf[n++] = 0x00;      // satır sonu dolgu
        memcpy(sent[src_y], fb[src_y], ROW_BYTES);
        rows++;
    }
    if (rows == 0) return;
    txbuf[n++] = 0x00;          // aktarım sonu dolgu
    send(txbuf, n);
    sent_valid = true;
}

void setRotate180(bool r) { if (r != rot180) { rot180 = r; sent_valid = false; } }

void assumeShown() { memcpy(sent, fb, sizeof(fb)); sent_valid = true; }

void flush()    { flushRows(false); }
void flushAll() { flushRows(true); }

void prepareSleep()
{
    // Uykuda SCS düşük kalmalı ki panele rastgele veri yazılmasın.
    // gpio_reset_pin() iç pull-up'ı açar; düşük sürülen pinde pull-up pin başına ~70 µA
    // boşa akım demektir, bu yüzden kapatılır.
    const gpio_num_t pins[3] = {PIN_LCD_SCS, PIN_LCD_SCLK, PIN_LCD_SI};
    for (gpio_num_t p : pins) {
        gpio_reset_pin(p);
        gpio_pullup_dis(p);
        gpio_pulldown_dis(p);
        gpio_set_direction(p, GPIO_MODE_OUTPUT);
        gpio_set_level(p, 0);
        gpio_hold_en(p);
    }
}

// ---------------- çizim ----------------
void clear(bool black) { memset(fb, black ? 0xFF : 0x00, sizeof(fb)); }

void pixel(int x, int y, bool on)
{
    if ((unsigned)x >= LCD_W || (unsigned)y >= LCD_H) return;
    uint8_t m = (uint8_t)(1 << (x & 7));            // LSB önce gönderildiği için bit0 = en sol
    if (on) fb[y][x >> 3] |= m; else fb[y][x >> 3] &= (uint8_t)~m;
}

bool getPixel(int x, int y)
{
    if ((unsigned)x >= LCD_W || (unsigned)y >= LCD_H) return false;
    return fb[y][x >> 3] & (1 << (x & 7));
}

void hline(int x, int y, int w, bool on) { for (int i = 0; i < w; i++) pixel(x + i, y, on); }
void vline(int x, int y, int h, bool on) { for (int i = 0; i < h; i++) pixel(x, y + i, on); }

void rect(int x, int y, int w, int h, bool fill, bool on)
{
    if (fill) { for (int j = 0; j < h; j++) hline(x, y + j, w, on); return; }
    hline(x, y, w, on); hline(x, y + h - 1, w, on);
    vline(x, y, h, on); vline(x + w - 1, y, h, on);
}

void roundRect(int x, int y, int w, int h, int r, bool fill, bool on)
{
    for (int j = 0; j < h; j++) {
        int inset = 0;
        int dy = (j < r) ? (r - j) : (j >= h - r ? (j - (h - r - 1)) : 0);
        if (dy) inset = r - (int)lroundf(sqrtf((float)(r * r - (dy - 0.5f) * (dy - 0.5f))));
        if (fill) hline(x + inset, y + j, w - 2 * inset, on);
        else {
            pixel(x + inset, y + j, on); pixel(x + w - 1 - inset, y + j, on);
            if (j == 0 || j == h - 1) hline(x + inset, y + j, w - 2 * inset, on);
        }
    }
}

void ellipse(int cx, int cy, int rx, int ry, bool fill, bool on)
{
    if (rx <= 0 || ry <= 0) { pixel(cx, cy, on); return; }
    for (int dy = -ry; dy <= ry; dy++) {
        float f = 1.0f - (float)(dy * dy) / (float)(ry * ry);
        int w = (int)lroundf(rx * sqrtf(f > 0 ? f : 0));
        if (fill) hline(cx - w, cy + dy, 2 * w + 1, on);
        else { pixel(cx - w, cy + dy, on); pixel(cx + w, cy + dy, on); }
    }
    if (!fill) {
        for (int dx = -rx; dx <= rx; dx++) {
            float f = 1.0f - (float)(dx * dx) / (float)(rx * rx);
            int h = (int)lroundf(ry * sqrtf(f > 0 ? f : 0));
            pixel(cx + dx, cy - h, on); pixel(cx + dx, cy + h, on);
        }
    }
}

void circle(int cx, int cy, int r, bool fill, bool on) { ellipse(cx, cy, r, r, fill, on); }

void line(int x0, int y0, int x1, int y1, bool on, int thick)
{
    int dx = abs(x1 - x0), sx = x0 < x1 ? 1 : -1;
    int dy = -abs(y1 - y0), sy = y0 < y1 ? 1 : -1;
    int err = dx + dy;
    while (true) {
        if (thick <= 1) pixel(x0, y0, on);
        else rect(x0 - thick / 2, y0 - thick / 2, thick, thick, true, on);
        if (x0 == x1 && y0 == y1) break;
        int e2 = 2 * err;
        if (e2 >= dy) { err += dy; x0 += sx; }
        if (e2 <= dx) { err += dx; y0 += sy; }
    }
}

void arc(int cx, int cy, int r, int deg0, int deg1, bool on, int thick)
{
    // açı: 0 = sağ, 90 = aşağı (ekran koordinatı)
    int px = 0, py = 0; bool first = true;
    int steps = (abs(deg1 - deg0) * r) / 20 + 6;
    for (int i = 0; i <= steps; i++) {
        float a = (deg0 + (deg1 - deg0) * (float)i / steps) * (float)M_PI / 180.0f;
        int x = cx + (int)lroundf(r * cosf(a));
        int y = cy + (int)lroundf(r * sinf(a));
        if (!first) line(px, py, x, y, on, thick);
        px = x; py = y; first = false;
    }
}

void bitmap(int x, int y, int w, int h, const uint8_t *rows, bool on)
{
    int stride = (w + 7) / 8;
    for (int j = 0; j < h; j++)
        for (int i = 0; i < w; i++)
            if (rows[j * stride + i / 8] & (0x80 >> (i & 7))) pixel(x + i, y + j, on);
}

void invertRect(int x, int y, int w, int h)
{
    for (int j = 0; j < h; j++) for (int i = 0; i < w; i++) pixel(x + i, y + j, !getPixel(x + i, y + j));
}

// UTF-8'den bir sonraki glifin indeksini al
static int nextGlyph(const char *&s)
{
    uint8_t c = (uint8_t)*s;
    if (!c) return -1;
    uint32_t cp;
    if (c < 0x80) { cp = c; s += 1; }
    else if ((c & 0xE0) == 0xC0 && s[1]) { cp = ((c & 0x1F) << 6) | (s[1] & 0x3F); s += 2; }
    else if ((c & 0xF0) == 0xE0 && s[1] && s[2]) { cp = ((c & 0x0F) << 12) | ((s[1] & 0x3F) << 6) | (s[2] & 0x3F); s += 3; }
    else { s += 1; return '?' - 32; }
    if (cp >= 32 && cp <= 126) return (int)cp - 32;
    for (int i = 0; i < FONT_TR_COUNT; i++) if (FONT_TR_MAP[i].cp == cp) return FONT_TR_MAP[i].idx;
    return '?' - 32;
}

int textWidth(const char *utf8, int scale)
{
    int n = 0; const char *s = utf8;
    while (nextGlyph(s) >= 0) n++;
    return n ? (n * 6 - 1) * scale : 0;
}

void text(int x, int y, const char *utf8, int scale, bool on)
{
    const char *s = utf8; int g;
    while ((g = nextGlyph(s)) >= 0) {
        for (int col = 0; col < 5; col++) {
            uint8_t bits = FONT5X7[g][col];
            for (int row = 0; row < 8; row++)
                if (bits & (1 << row)) rect(x + col * scale, y + row * scale, scale, scale, true, on);
        }
        x += 6 * scale;
    }
}

void textCentered(int y, const char *utf8, int scale, bool on)
{
    text((LCD_W - textWidth(utf8, scale)) / 2, y, utf8, scale, on);
}

} // namespace display
