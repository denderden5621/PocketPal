#include "input.h"
#include "config.h"
#include "lis3dh.h"
#include "driver/gpio.h"
#include <math.h>

namespace input {

struct Btn {
    gpio_num_t pin;
    bool raw = false, state = false, stuck = false;
    uint32_t changed_ms = 0, down_ms = 0;
    bool long_sent = false, used_in_combo = false;
};

static Btn L{PIN_WAKE_L}, R{PIN_BTN_R};
static float tx = 0, ty = 0;
static uint32_t last_activity = 0;
static uint32_t shake_hits = 0, shake_t0 = 0;
static bool both_sent = false;
static bool rot = false;
static int tilt_k = 0;

void begin()
{
    // uyku öncesi IDF, uyandırma pinini "hold" ile kilitler; serbest bırak
    gpio_hold_dis(PIN_WAKE_L);
    gpio_config_t c = {};
    c.pin_bit_mask = (1ULL << PIN_WAKE_L) | (1ULL << PIN_BTN_R);
    c.mode = GPIO_MODE_INPUT;
    c.pull_up_en = GPIO_PULLUP_ENABLE;
    c.pull_down_en = GPIO_PULLDOWN_DISABLE;
    c.intr_type = GPIO_INTR_DISABLE;
    gpio_config(&c);
}

static void updateBtn(Btn &b, uint32_t now, uint32_t &ev, uint32_t ev_short, uint32_t ev_down, uint32_t ev_long)
{
    bool raw = gpio_get_level(b.pin) == 0;   // basılı = düşük
    if (raw != b.raw) { b.raw = raw; b.changed_ms = now; }
    if (now - b.changed_ms < 15 || raw == b.state) {
        if (b.state && !b.stuck && now - b.down_ms > BUTTON_STUCK_MS) b.stuck = true;
        if (b.state && !b.long_sent && !b.used_in_combo && !b.stuck && now - b.down_ms > 800) {
            b.long_sent = true; ev |= ev_long; last_activity = now;
        }
        return;
    }
    b.state = raw;
    if (raw) {
        b.down_ms = now; b.long_sent = false; b.used_in_combo = false;
        ev |= ev_down; last_activity = now;
    } else {
        if (!b.stuck && !b.long_sent && !b.used_in_combo) ev |= ev_short;
        b.stuck = false;
        last_activity = now;
    }
}

uint32_t poll(uint32_t now)
{
    uint32_t ev = 0;
    updateBtn(L, now, ev, EV_L, EV_L_DOWN, EV_L_LONG);
    updateBtn(R, now, ev, EV_R, EV_R_DOWN, EV_R_LONG);

    if (L.state && R.state && !L.stuck && !R.stuck) {
        uint32_t t = now - (L.down_ms > R.down_ms ? L.down_ms : R.down_ms);
        if (t > 300 && !both_sent) { ev |= EV_BOTH; both_sent = true; }
        L.used_in_combo = R.used_in_combo = true;
    } else if (!L.state && !R.state) {
        both_sent = false;
    }

    if (lis3dh::present()) {
        lis3dh::Accel a;
        if (lis3dh::read(a)) {
            // Ekran yukarı bakarken: x sağa, y yukarı (montaja göre işaretleri buradan çevirin)
            // Modül eksenlerini cihaz eksenine döndür (k x 90°), ekran çevrildiyse +180°.
            // Gözler "yuvarlanan bilye" gibi aşağı tarafa bakar: ekran x = -ax, ekran y (aşağı) = +ay
            int k = (tilt_k + (rot ? 2 : 0)) & 3;
            float ax = a.x, ay = a.y;
            for (int i = 0; i < k; i++) { float t = ax; ax = -ay; ay = t; }
            tx = tx * 0.7f + (-ax) * 0.3f;
            ty = ty * 0.7f + (ay) * 0.3f;
            float mag = sqrtf(a.x * a.x + a.y * a.y + a.z * a.z);
            if (fabsf(mag - 1.0f) > 0.9f) {
                if (now - shake_t0 > 700) { shake_t0 = now; shake_hits = 0; }
                if (++shake_hits >= 4) { ev |= EV_SHAKE; shake_hits = 0; shake_t0 = 0; last_activity = now; }
            }
        }
        uint8_t cs = lis3dh::clickSource();
        if (cs & 0x40) {
            if (cs & 0x20) ev |= EV_DTAP; else if (cs & 0x10) ev |= EV_TAP;
            last_activity = now;
        }
    }
    return ev;
}

bool leftHeld() { return L.state && !L.stuck; }
bool rightHeld() { return R.state && !R.stuck; }
float tiltX() { return tx > 1 ? 1 : (tx < -1 ? -1 : tx); }
float tiltY() { return ty > 1 ? 1 : (ty < -1 ? -1 : ty); }
uint32_t lastActivityMs() { return last_activity; }
void markActivity(uint32_t now) { last_activity = now; }
bool anyStuck() { return L.stuck || R.stuck; }
void setRotate180(bool r) { rot = r; }
void setTiltRot(int k) { tilt_k = k & 3; }

void syncHeld(uint32_t now)
{
    // Uyandıran basışı yut: bırakılınca olay üretmesin
    Btn *btns[2] = {&L, &R};
    for (Btn *b : btns) {
        bool raw = gpio_get_level(b->pin) == 0;
        b->raw = b->state = raw;
        b->changed_ms = now;
        if (raw) { b->down_ms = now; b->used_in_combo = true; b->long_sent = true; }
    }
    last_activity = now;
}
bool leftRaw() { return gpio_get_level(PIN_WAKE_L) == 0; }

} // namespace input
