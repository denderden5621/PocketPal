#pragma once
#include <stdint.h>
#include <stdbool.h>

// Pasif piezo (LEDC PWM). Notalar arka planda çalar; update() her karede çağrılır.
namespace sound {

struct Note { uint16_t hz; uint16_t ms; };   // hz = 0 -> sessizlik; ms = 0 -> dizinin sonu

void begin();
void setEnabled(bool on);
bool enabled();
void play(const Note *seq);      // diziyi baştan çal (öncekini keser)
void tone(uint16_t hz, uint16_t ms);
void update(uint32_t now_ms);
bool busy();
void stop();
void prepareSleep();

// Hazır sesler
extern const Note HELLO[], HAPPY[], PURR[], SURPRISE[], DIZZY[], CLICK[], SELECT[],
                  BACK[], JUMP[], COIN[], HIT[], GAMEOVER[], LEVELUP[], SAD[], SLEEPY[];

} // namespace sound
