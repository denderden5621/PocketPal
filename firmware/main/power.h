#pragma once
#include <stdint.h>
#include <stdbool.h>
#include "config.h"

// Uyku / uyanma, LP çekirdek (EXTCOMIN), pil ölçümü, saat.
namespace power {

enum Wake { WAKE_COLD, WAKE_TIMER, WAKE_BUTTON, WAKE_MOTION, WAKE_OTHER };

// Derin uykuda korunan durum (RTC belleği)
struct RtcState {
    uint32_t magic;
    uint32_t boots;
    uint32_t last_interact_s;      // son oynama/sevme zamanı
    uint32_t joy_until_s;          // bu zamana kadar "mutlu" yüz
    int32_t  clock_offset_s;       // saat ayarı: gün içi saniye = (now + offset) % 86400
    uint8_t  clock_set;
    uint8_t  idle_mood;            // ekranda kalan yüz
    uint8_t  motion_idx;
    uint8_t  storm_level;          // art arda fırtınalarda susturma süresi katlanır
    uint32_t motion_times[MOTION_STORM_COUNT];
    uint32_t motion_mute_until_s;
    uint32_t last_storm_s;
    uint16_t bat_mv;
    uint16_t low_warned;
};

Wake begin();                      // en başta çağır
RtcState &rtc();
uint32_t nowS();                   // derin uykuda da sayan saniye sayacı
int  batteryMv(bool fresh = false);
int  batteryPct();
bool batteryLow();
bool batteryCritical();

bool clockSet();
int  minuteOfDay();                // 0..1439 (saat ayarlı değilse -1)
void setClock(int hour, int minute);
bool isNight();

void noteInteraction();            // "biriyle oynandı" -> mutluluk zamanlayıcıları
void noteMotionWake();             // hareket fırtınası takibi
bool motionMuted();

// Derin uykuya gir. Bu fonksiyon geri dönmez.
// timer_s: zamanlayıcı uyanışı (0 = yok), motion: hareketle uyanma izni
[[noreturn]] void sleep(uint32_t timer_s, bool motion);

} // namespace power
