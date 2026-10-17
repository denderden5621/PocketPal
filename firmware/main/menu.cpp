#include "menu.h"
#include "display.h"
#include "input.h"
#include "sound.h"
#include "games.h"
#include "power.h"
#include "store.h"
#include "face.h"
#include "config.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include <stdio.h>

using namespace display;

namespace menu {

static uint32_t ms() { return (uint32_t)(esp_timer_get_time() / 1000); }

enum Key { K_NONE, K_NEXT, K_OK, K_BACK, K_TIMEOUT };

static Key waitKey(uint32_t &ev_out)
{
    vTaskDelay(pdMS_TO_TICKS(20));
    uint32_t now = ms();
    uint32_t ev = input::poll(now);
    sound::update(now);
    ev_out = ev;
    if (now - input::lastActivityMs() > AWAKE_TIMEOUT_MS) return K_TIMEOUT;
    if (ev & input::EV_L_LONG) return K_BACK;
    if (ev & input::EV_L) return K_NEXT;
    if (ev & input::EV_R) return K_OK;
    return K_NONE;
}

static void drawList(const char *title, const char *const *items, int n, int sel)
{
    clear();
    rect(0, 0, LCD_W, 15, true);
    textCentered(4, title, 1, false);
    const int ROWS = 7, RH = 14, Y0 = 18;
    int first = sel - ROWS / 2;
    if (first > n - ROWS) first = n - ROWS;
    if (first < 0) first = 0;
    for (int r = 0; r < ROWS && first + r < n; r++) {
        int i = first + r, y = Y0 + r * RH;
        if (i == sel) {
            roundRect(4, y, LCD_W - 8, RH - 1, 4, true);
            text(10, y + 3, items[i], 1, false);
        } else {
            text(10, y + 3, items[i], 1);
        }
    }
    // kaydırma çubuğu
    if (n > ROWS) {
        int h = 98 * ROWS / n, y = Y0 + (98 - h) * first / (n - ROWS);
        vline(LCD_W - 2, y, h);
    }
    hline(0, 116, LCD_W);
    textCentered(119, "Sol:aşağı  Sağ:seç", 1);
    flush();
}

// --- saat ayarı ---
static Result setClock()
{
    int m = power::minuteOfDay();
    if (m < 0) m = 12 * 60;
    int hh = m / 60, mm = (m / 5) % 12 * 5;
    while (true) {
        clear();
        textCentered(8, "Saati ayarla", 1);
        char b[8];
        snprintf(b, sizeof b, "%02d:%02d", hh, mm);
        textCentered(40, b, 3);
        textCentered(80, "Sol: saat +1", 1);
        textCentered(92, "Sağ: dakika +5", 1);
        textCentered(108, "Uzun Sağ: kaydet", 1);
        flush();
        uint32_t ev;
        Key k = waitKey(ev);
        if (k == K_TIMEOUT) return TIMEOUT;
        if (k == K_BACK) { sound::play(sound::BACK); return BACK; }
        if (k == K_NEXT) { hh = (hh + 1) % 24; sound::play(sound::CLICK); }
        if (k == K_OK)   { mm = (mm + 5) % 60; sound::play(sound::CLICK); }
        if (ev & input::EV_R_LONG) {
            power::setClock(hh, mm);
            sound::play(sound::SELECT);
            return BACK;
        }
    }
}

// --- durum ekranı ---
static Result status()
{
    int page = 0;
    while (true) {
        clear();
        char b[40];
        if (page == 0) {
            textCentered(6, "Durum", 2);
            int pct = power::batteryPct();
            int mv = power::batteryMv(true);
            if (pct >= 0) {
                face::batteryIcon(20, 34, pct);
                snprintf(b, sizeof b, "%%%d  %d.%02d V", pct, mv / 1000, (mv % 1000) / 10);
                text(42, 34, b, 1);
            } else {
                text(10, 34, "Pil ölçülemiyor", 1);
            }
            int mod = power::minuteOfDay();
            if (mod >= 0) snprintf(b, sizeof b, "Saat: %02d:%02d", mod / 60, mod % 60);
            else snprintf(b, sizeof b, "Saat: ayarlı değil");
            text(10, 50, b, 1);
            snprintf(b, sizeof b, "Oyun: %lu", (unsigned long)store::d.games_played);
            text(10, 64, b, 1);
            snprintf(b, sizeof b, "Sevgi: %lu", (unsigned long)store::d.pets);
            text(10, 78, b, 1);
            snprintf(b, sizeof b, "Uyanış: %lu", (unsigned long)power::rtc().boots);
            text(10, 92, b, 1);
        } else {
            textCentered(6, "Rekorlar", 2);
            for (int i = 0; i < games::COUNT; i++) {
                uint16_t v = store::d.best[i];
                text(10, 34 + i * 14, games::NAMES[i], 1);
                if (i == games::TEPKI && v) snprintf(b, sizeof b, "%u ms", v);
                else snprintf(b, sizeof b, "%u", v);
                text(LCD_W - 10 - textWidth(b, 1), 34 + i * 14, b, 1);
            }
        }
        hline(0, 116, LCD_W);
        textCentered(119, page == 0 ? "Sol:rekorlar Sağ:çık" : "Sol:durum  Sağ:çık", 1);
        flush();
        uint32_t ev;
        Key k = waitKey(ev);
        if (k == K_TIMEOUT) return TIMEOUT;
        if (k == K_BACK || k == K_OK) { sound::play(sound::BACK); return BACK; }
        if (k == K_NEXT) { page ^= 1; sound::play(sound::CLICK); }
    }
}

Result runGames()
{
    const char *items[games::COUNT + 1];
    for (int i = 0; i < games::COUNT; i++) items[i] = games::NAMES[i];
    items[games::COUNT] = "< Geri";
    int sel = 0;
    while (true) {
        drawList("Oyunlar", items, games::COUNT + 1, sel);
        uint32_t ev;
        Key k = waitKey(ev);
        if (k == K_TIMEOUT) return TIMEOUT;
        if (k == K_BACK) { sound::play(sound::BACK); return BACK; }
        if (k == K_NEXT) { sel = (sel + 1) % (games::COUNT + 1); sound::play(sound::CLICK); }
        if (k == K_OK) {
            if (sel == games::COUNT) { sound::play(sound::BACK); return BACK; }
            sound::play(sound::SELECT);
            if (games::play(sel)) return TIMEOUT;
            input::markActivity(ms());
        }
    }
}

Result run()
{
    int sel = 0;
    while (true) {
        char s_sound[24], s_style[24], s_motion[28], s_tilt[24];
        snprintf(s_sound, sizeof s_sound, "Ses: %s", store::d.sound ? "Açık" : "Kapalı");
        snprintf(s_style, sizeof s_style, "Yüz: %s", store::d.style == store::STYLE_CAT ? "Kedi" : "Yıldız");
        snprintf(s_motion, sizeof s_motion, "Hareket: %s", store::d.motion_wake ? "Açık" : "Kapalı");
        snprintf(s_tilt, sizeof s_tilt, "Eğim yönü: %d/4", store::d.tilt_rot + 1);
        const char *items[] = {"Oyunlar", s_sound, s_style, s_motion, s_tilt, "Saati ayarla", "Durum", "Ekranı çevir", "< Çıkış"};
        const int N = sizeof(items) / sizeof(items[0]);
        drawList("Menü", items, N, sel);
        uint32_t ev;
        Key k = waitKey(ev);
        if (k == K_TIMEOUT) { store::save(); return TIMEOUT; }
        if (k == K_BACK) { sound::play(sound::BACK); store::save(); return BACK; }
        if (k == K_NEXT) { sel = (sel + 1) % N; sound::play(sound::CLICK); continue; }
        if (k != K_OK) continue;
        Result r = BACK;
        switch (sel) {
        case 0: sound::play(sound::SELECT); r = runGames(); break;
        case 1:
            store::d.sound ^= 1;
            sound::setEnabled(store::d.sound);
            sound::play(sound::SELECT);
            break;
        case 2:
            store::d.style ^= 1;
            sound::play(sound::SELECT);
            break;
        case 3:
            store::d.motion_wake ^= 1;
            sound::play(sound::SELECT);
            break;
        case 4:
            store::d.tilt_rot = (store::d.tilt_rot + 1) & 3;
            input::setTiltRot(store::d.tilt_rot);
            sound::play(sound::SELECT);
            break;
        case 5: sound::play(sound::SELECT); r = setClock(); break;
        case 6: sound::play(sound::SELECT); r = status(); break;
        case 7:
            store::d.rotate180 ^= 1;
            display::setRotate180(store::d.rotate180);
            input::setRotate180(store::d.rotate180);
            sound::play(sound::SELECT);
            break;
        default:
            sound::play(sound::BACK);
            store::save();
            return BACK;
        }
        if (r == TIMEOUT) { store::save(); return TIMEOUT; }
        input::markActivity(ms());
    }
}

} // namespace menu
