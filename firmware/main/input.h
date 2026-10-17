#pragma once
#include <stdint.h>
#include <stdbool.h>

// Düğmeler + ivmeölçer olayları. poll() her karede çağrılır.
namespace input {

enum Event : uint32_t {
    EV_NONE      = 0,
    EV_L         = 1 << 0,   // sol düğme bırakıldı (kısa basış)
    EV_R         = 1 << 1,   // sağ düğme bırakıldı (kısa basış)
    EV_L_DOWN    = 1 << 2,   // sol düğmeye basıldı (anında, oyunlar için)
    EV_R_DOWN    = 1 << 3,
    EV_BOTH      = 1 << 4,   // ikisi birlikte ~0.3 sn -> menü
    EV_L_LONG    = 1 << 5,
    EV_R_LONG    = 1 << 6,
    EV_TAP       = 1 << 7,   // kasaya tek vuruş
    EV_DTAP      = 1 << 8,   // çift vuruş
    EV_SHAKE     = 1 << 9,
};

void begin();
uint32_t poll(uint32_t now_ms);      // olay maskesi
bool leftHeld();
bool rightHeld();
float tiltX();                        // -1..1 (sağa eğim +)
float tiltY();                        // -1..1 (öne eğim +)
uint32_t lastActivityMs();
void markActivity(uint32_t now_ms);
bool anyStuck();
void setRotate180(bool r);           // ekran çevrildiyse eğim yönünü de çevir
void setTiltRot(int k);              // LIS3DH montaj yönü: 0..3 (90° adımlar)
bool leftRaw();
void syncHeld(uint32_t now_ms);      // o an basılı düğmeleri "kullanıldı" say                      // sol düğme şu an basılı mı (debounce yok)

} // namespace input
