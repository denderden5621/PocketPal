#pragma once
#include <stdint.h>
#include <stdbool.h>

// Kalıcı ayarlar ve rekorlar (NVS flash). Pil bitse bile kaybolmaz.
namespace store {

enum Style : uint8_t { STYLE_CAT = 0, STYLE_STAR = 1 };
enum { GAME_COUNT = 5 };

struct Data {
    uint8_t  version;
    uint8_t  sound;            // 1 = açık
    uint8_t  style;            // Style
    uint8_t  rotate180;        // 1 = ekran ters
    uint8_t  motion_wake;      // 1 = sallayınca/dokununca uyan
    uint8_t  tilt_rot;         // ivmeölçer montaj yönü 0..3 (90° adımlarla)
    uint16_t best[GAME_COUNT]; // oyun rekorları (Tepki için ms, 0 = yok)
    uint32_t games_played;
    uint32_t pets;             // sevilme sayısı
};

extern Data d;

void begin();
void save();                   // yalnızca değiştiyse yazar
void resetAll();

} // namespace store
