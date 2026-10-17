#include "sound.h"
#include "config.h"
#include "driver/ledc.h"
#include "driver/gpio.h"
#include "esp_timer.h"

namespace sound {

static bool on = true, inited = false;
static const Note *cur = nullptr;
static Note single[2];
static uint32_t note_end = 0;
static bool playing = false;

static const ledc_mode_t MODE = LEDC_LOW_SPEED_MODE;
static const ledc_channel_t CH = LEDC_CHANNEL_0;
static const ledc_timer_t TMR = LEDC_TIMER_0;

static uint32_t ms() { return (uint32_t)(esp_timer_get_time() / 1000); }

void begin()
{
    gpio_hold_dis(PIN_PIEZO);
    ledc_timer_config_t t = {};
    t.speed_mode = MODE;
    t.duty_resolution = LEDC_TIMER_10_BIT;
    t.timer_num = TMR;
    t.freq_hz = 2000;
    t.clk_cfg = LEDC_AUTO_CLK;
    if (ledc_timer_config(&t) != ESP_OK) return;
    ledc_channel_config_t c = {};
    c.gpio_num = PIN_PIEZO;
    c.speed_mode = MODE;
    c.channel = CH;
    c.timer_sel = TMR;
    c.duty = 0;
    c.hpoint = 0;
    if (ledc_channel_config(&c) != ESP_OK) return;
    inited = true;
}

static void out(uint16_t hz)
{
    if (!inited) return;
    if (hz == 0 || !on) {
        ledc_set_duty(MODE, CH, 0);
    } else {
        ledc_set_freq(MODE, TMR, hz);
        ledc_set_duty(MODE, CH, 512);   // %50 görev oranı = en yüksek ses
    }
    ledc_update_duty(MODE, CH);
}

void setEnabled(bool e) { on = e; if (!on) stop(); }
bool enabled() { return on; }

void play(const Note *seq)
{
    if (!on || !seq) return;
    cur = seq;
    playing = true;
    out(cur->hz);
    note_end = ms() + cur->ms;
}

void tone(uint16_t hz, uint16_t len)
{
    single[0] = {hz, len};
    single[1] = {0, 0};
    play(single);
}

void update(uint32_t now)
{
    if (!playing) return;
    if ((int32_t)(now - note_end) < 0) return;
    cur++;
    if (cur->ms == 0) { stop(); return; }
    out(cur->hz);
    note_end = now + cur->ms;
}

bool busy() { return playing; }

void stop()
{
    playing = false;
    cur = nullptr;
    out(0);
}

void prepareSleep()
{
    stop();
    if (inited) ledc_stop(MODE, CH, 0);
    gpio_reset_pin(PIN_PIEZO);
    gpio_pullup_dis(PIN_PIEZO);       // düşük sürülen pinde pull-up boşa akım çeker
    gpio_pulldown_dis(PIN_PIEZO);
    gpio_set_direction(PIN_PIEZO, GPIO_MODE_OUTPUT);
    gpio_set_level(PIN_PIEZO, 0);
    gpio_hold_en(PIN_PIEZO);
}

// --- notalar (Hz) ---
enum : uint16_t {
    C5 = 523, D5 = 587, E5 = 659, F5 = 698, G5 = 784, A5 = 880, B5 = 988,
    C6 = 1047, D6 = 1175, E6 = 1319, F6 = 1397, G6 = 1568, A6 = 1760, C7 = 2093,
};

const Note HELLO[]    = {{C6, 70}, {0, 20}, {E6, 70}, {0, 20}, {G6, 120}, {0, 0}};
const Note HAPPY[]    = {{E6, 60}, {G6, 60}, {C7, 110}, {0, 0}};
const Note PURR[]     = {{A5, 40}, {0, 25}, {A5, 40}, {0, 25}, {B5, 40}, {0, 25}, {A5, 60}, {0, 0}};
const Note SURPRISE[] = {{C6, 40}, {G6, 90}, {0, 0}};
const Note DIZZY[]    = {{G6, 60}, {E6, 60}, {C6, 60}, {G5, 60}, {E5, 120}, {0, 0}};
const Note CLICK[]    = {{C7, 12}, {0, 0}};
const Note SELECT[]   = {{G6, 30}, {C7, 50}, {0, 0}};
const Note BACK[]     = {{C7, 30}, {G6, 50}, {0, 0}};
const Note JUMP[]     = {{C6, 25}, {E6, 25}, {G6, 25}, {0, 0}};
const Note COIN[]     = {{B5, 40}, {E6, 90}, {0, 0}};
const Note HIT[]      = {{G5, 50}, {C5, 120}, {0, 0}};
const Note GAMEOVER[] = {{G5, 120}, {0, 30}, {E5, 120}, {0, 30}, {C5, 250}, {0, 0}};
const Note LEVELUP[]  = {{C6, 60}, {E6, 60}, {G6, 60}, {C7, 160}, {0, 0}};
const Note SAD[]      = {{E5, 160}, {C5, 260}, {0, 0}};
const Note SLEEPY[]   = {{G5, 200}, {E5, 300}, {0, 0}};

} // namespace sound
