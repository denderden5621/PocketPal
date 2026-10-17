#pragma once
#include <stdint.h>
#include <stdbool.h>

// Yüz çizimi + etkileşimli yüz modu (kedi ve yıldız stilleri)
namespace face {

enum Mood : uint8_t {
    NEUTRAL, HAPPY, LOVE, SURPRISED, DIZZY, BORED, SLEEPY, SLEEPING, SAD, WINK, LAUGH, ANGRY, MOOD_COUNT
};

enum Action { ACT_NONE, ACT_MENU, ACT_GAMES };

// Ham çizim (önce display::clear çağrılmış olmalı)
void draw(Mood m, float look_x, float look_y, bool blink, uint32_t t_ms);
void bubble(const char *utf8);              // üstte konuşma balonu ("\n" ile iki satır)
void batteryIcon(int x, int y, int pct);
void heart(int cx, int cy, int s, bool on = true);
void triFill(int x0, int y0, int x1, int y1, int x2, int y2, bool on = true);
void smallSprite(int x, int y, bool on = true);  // oyunlar için 12x12 kahraman (stile göre)

// Uyku yüzü (ekranda kalıcı duran)
Mood idleMood();
void drawIdle(Mood m, bool blink, float look_x = 0);

// Etkileşimli mod
void enter(uint32_t now_ms, bool from_cold);
Action update(uint32_t ev, uint32_t now_ms);
void render(uint32_t now_ms);

// Hareketle uyanınca kısa bakış (ms)
void glanceFrame(uint32_t t_in, float lx, float ly);

} // namespace face
