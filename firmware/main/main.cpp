// ======================================================================
//  Pocket Pal - ESP32-C6 anahtarlık
//  Akış: uyan -> (yüz / menü / oyun) -> 20 sn dokunulmazsa derin uyku.
//  Ekran bellek LCD olduğu için uykuda yüz görünmeye devam eder;
//  LP çekirdek EXTCOMIN'i 1 Hz çevirir, ana işlemci tamamen kapalıdır.
// ======================================================================
#include "config.h"
#include "display.h"
#include "input.h"
#include "lis3dh.h"
#include "sound.h"
#include "face.h"
#include "menu.h"
#include "power.h"
#include "store.h"
#include "esp_timer.h"
#include "esp_random.h"
#include "esp_log.h"
#include "esp_sleep.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static const char *TAG = "pal";

static uint32_t ms() { return (uint32_t)(esp_timer_get_time() / 1000); }
static void sleepMs(uint32_t t) { vTaskDelay(pdMS_TO_TICKS(t)); }
// Zamanlayıcı uyanışlarındaki kısa beklemeler: hafif uyku (~0,2 mA) ile, işlemci açık beklemekten (~20 mA) çok daha ucuz
static void nap(uint32_t t)
{
    esp_sleep_enable_timer_wakeup((uint64_t)t * 1000ULL);
    esp_light_sleep_start();
}

// Bir sonraki zamanlayıcı uyanışı (saniye)
static uint32_t nextTimer(face::Mood m)
{
    if (power::batteryCritical()) return 0;      // pil bitmek üzere: yalnızca sol düğme uyandırır
    if (m == face::SLEEPING) {
        int mod = power::minuteOfDay();
        if (mod >= 0) {
            int until = ((NIGHT_END_H * 60 - mod + 1440) % 1440) * 60 + 30;
            if (until < NIGHT_CHECK_S) return until;
        }
        return NIGHT_CHECK_S;
    }
    return IDLE_WAKE_MIN_S + esp_random() % (IDLE_WAKE_MAX_S - IDLE_WAKE_MIN_S + 1);
}

[[noreturn]] static void goSleep()
{
    face::Mood m = face::idleMood();
    face::drawIdle(m, false);
    display::flush();
    power::rtc().idle_mood = m;
    store::save();
    uint32_t t0 = ms();
    while (sound::busy() && ms() - t0 < 600) { sound::update(ms()); sleepMs(10); }
    bool motion = store::d.motion_wake && !power::batteryCritical();
    power::sleep(nextTimer(m), motion);
}

// Zamanlayıcı uyanışı: yüzü güncelle ya da göz kırp, hemen uyu
[[noreturn]] static void idleTick()
{
    power::batteryMv(true);
    face::Mood prev = (face::Mood)power::rtc().idle_mood;
    face::Mood m = face::idleMood();
    if (m != prev) {
        face::drawIdle(m, false);
        display::flushAll();
    } else if (m != face::SLEEPING) {
        face::drawIdle(prev, false);
        display::assumeShown();          // panelde zaten bu görüntü var
        face::drawIdle(m, true);         // göz kırp
        display::flush();
        nap(130);
        if (esp_random() % 4 == 0) {     // bazen etrafa bakın
            face::drawIdle(m, false, -0.9f); display::flush(); nap(450);
            face::drawIdle(m, false, 0.9f);  display::flush(); nap(450);
        }
        face::drawIdle(m, false);
        display::flush();
    }
    goSleep();
}

// Hareketle uyanış: kısa bakış; düğme ya da çift vuruş gelirse tam uyan
static bool glance()
{
    lis3dh::configAwake();
    face::Mood prev = (face::Mood)power::rtc().idle_mood;
    face::drawIdle(prev, false);
    display::assumeShown();
    uint32_t t0 = ms();
    input::syncHeld(t0);
    while (ms() - t0 < 1400) {
        uint32_t now = ms();
        uint32_t ev = input::poll(now);
        if (ev & (input::EV_L_DOWN | input::EV_R_DOWN | input::EV_DTAP)) return true;
        face::glanceFrame(now - t0, input::tiltX() * 1.5f, input::tiltY() * 1.5f);
        display::flush();
        sleepMs(33);
    }
    return false;
}

// Tam uyanık oturum: yüz + menü + oyunlar
static void session(bool cold)
{
    lis3dh::configAwake();
    uint32_t now = ms();
    input::syncHeld(now);
    face::enter(now, cold);
    uint32_t timeout = power::batteryCritical() ? 6000 : AWAKE_TIMEOUT_MS;
    uint32_t next_bat = now + 30000;
    while (true) {
        sleepMs(1000 / GAME_FPS);
        now = ms();
        uint32_t ev = input::poll(now);
        sound::update(now);
        face::Action a = face::update(ev, now);
        if (a == face::ACT_MENU || a == face::ACT_GAMES) {
            menu::Result r = (a == face::ACT_MENU) ? menu::run() : menu::runGames();
            if (r == menu::TIMEOUT) break;
            now = ms();
            input::markActivity(now);
            continue;
        }
        face::render(now);
        display::flush();
        if (now >= next_bat) { power::batteryMv(true); next_bat = now + 30000; }
        if (now - input::lastActivityMs() > timeout) break;
    }
    // esneyip uykuya dal
    display::clear();
    face::draw(face::SLEEPY, 0, 0, false, 0);
    display::flush();
    sleepMs(500);
}

extern "C" void app_main(void)
{
    power::Wake w = power::begin();
    store::begin();
    display::begin();
    display::setRotate180(store::d.rotate180);
    input::begin();
    input::setRotate180(store::d.rotate180);
    input::setTiltRot(store::d.tilt_rot);
    lis3dh::begin();
    sound::begin();
    sound::setEnabled(store::d.sound);
    ESP_LOGI(TAG, "uyanış nedeni %d, pil %d mV", (int)w, power::batteryMv());

    switch (w) {
    case power::WAKE_COLD:
        display::clearPanel();
        power::batteryMv(true);
        session(true);
        break;
    case power::WAKE_TIMER:
        idleTick();
        break;
    case power::WAKE_MOTION:
        power::noteMotionWake();
        if (glance()) session(false);
        break;
    default:
        session(false);
        break;
    }
    goSleep();
}
