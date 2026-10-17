// Ana bilgisayarda ekran çizimlerini PNG'ye dökmek için küçük simülatör.
// Derleme: tools/host_sim/build.sh
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <string>
#include <functional>
#include "display.h"
#include "face.h"
#include "input.h"
#include "sound.h"
#include "power.h"
#include "store.h"
#include "lis3dh.h"
#include "games.h"
#include "menu.h"

// ---------------- zaman ----------------
static uint32_t sim_ms = 1000;
static uint32_t frame_no = 0;
static std::function<void(uint32_t)> on_frame;
struct StopSim {};
int64_t esp_timer_get_time(void) { return (int64_t)sim_ms * 1000; }
void vTaskDelay(uint32_t t) { sim_ms += t ? t : 1; frame_no++; if (on_frame) on_frame(frame_no); }

// ---------------- saplamalar ----------------
static std::function<uint32_t(uint32_t)> script;
static bool held_l = false, held_r = false;
static float tilt_x = 0, tilt_y = 0;
namespace input {
void begin() {}
uint32_t poll(uint32_t now) { return script ? script(now) : 0; }
bool leftHeld() { return held_l; }
bool rightHeld() { return held_r; }
float tiltX() { return tilt_x; }
float tiltY() { return tilt_y; }
uint32_t lastActivityMs() { return sim_ms; }
void markActivity(uint32_t) {}
bool anyStuck() { return false; }
void setRotate180(bool) {}
bool leftRaw() { return false; }
void syncHeld(uint32_t) {}
void setTiltRot(int) {}
}
namespace sound {
void begin() {} void setEnabled(bool) {} bool enabled() { return true; }
void play(const Note *) {} void tone(uint16_t, uint16_t) {} void update(uint32_t) {}
bool busy() { return false; } void stop() {} void prepareSleep() {}
const Note HELLO[1] = {}, HAPPY[1] = {}, PURR[1] = {}, SURPRISE[1] = {}, DIZZY[1] = {}, CLICK[1] = {}, SELECT[1] = {},
           BACK[1] = {}, JUMP[1] = {}, COIN[1] = {}, HIT[1] = {}, GAMEOVER[1] = {}, LEVELUP[1] = {}, SAD[1] = {}, SLEEPY[1] = {};
}
static int bat_mv = 3900;
static bool night = false;
namespace power {
static RtcState st;
RtcState &rtc() { return st; }
uint32_t nowS() { return 100000 + sim_ms / 1000; }
int batteryMv(bool) { return bat_mv; }
int batteryPct() { return bat_mv >= 4150 ? 100 : bat_mv <= 3300 ? 0 : (bat_mv - 3300) * 100 / 850; }
bool batteryLow() { return bat_mv < 3500; }
bool batteryCritical() { return bat_mv < 3300; }
bool clockSet() { return true; }
int minuteOfDay() { return 14 * 60 + 35; }
void setClock(int, int) {}
bool isNight() { return night; }
void noteInteraction() {}
void noteMotionWake() {}
bool motionMuted() { return false; }
void sleep(uint32_t, bool) { throw StopSim(); }
}
namespace store {
Data d = {3, 1, 0, 0, 1, 0, {42, 37, 9, 231, 6}, 128, 512};
void begin() {} void save() {} void resetAll() {}
}
namespace lis3dh {
bool begin() { return true; } bool present() { return true; } void configAwake() {}
void configSleepMotion(bool) {} bool read(Accel &a) { a = {0, 0, 1}; return true; }
uint8_t clickSource() { return 0; } bool motionLatched() { return false; } void powerDown() {}
}

// ---------------- çıktı ----------------
static std::string outdir = ".";
static void dump(const std::string &name)
{
    std::string p = outdir + "/" + name + ".pbm";
    FILE *f = fopen(p.c_str(), "w");
    fprintf(f, "P1\n%d %d\n", LCD_W, LCD_H);
    for (int y = 0; y < LCD_H; y++) {
        for (int x = 0; x < LCD_W; x++) fputc(display::getPixel(x, y) ? '1' : '0', f);
        fputc('\n', f);
    }
    fclose(f);
}

static const char *MOOD_NAMES[] = {"neutral", "happy", "love", "surprised", "dizzy", "bored", "sleepy",
                                   "sleeping", "sad", "wink", "laugh", "angry"};

static void runGame(int id, uint32_t snap_frame, const char *name, std::function<uint32_t(uint32_t)> sc)
{
    script = sc;
    frame_no = 0;
    on_frame = [&](uint32_t n) { if (n == snap_frame) { dump(name); throw StopSim(); } };
    try { games::play(id); } catch (StopSim &) {}
    on_frame = nullptr; script = nullptr;
}

int main(int argc, char **argv)
{
    if (argc > 1) outdir = argv[1];
    display::begin();
    for (int style = 0; style < 2; style++) {
        store::d.style = style;
        const char *sn = style ? "yildiz" : "kedi";
        for (int m = 0; m < face::MOOD_COUNT; m++) {
            display::clear();
            face::draw((face::Mood)m, 0, 0, false, 600);
            dump(std::string(sn) + "_" + MOOD_NAMES[m]);
        }
        display::clear();
        face::draw(face::NEUTRAL, 0.8f, -0.3f, false, 0);
        face::bubble(style ? "Pırıl pırıl!" : "Miyav!");
        dump(std::string(sn) + "_bubble");
        display::clear();
        face::draw(face::HAPPY, 0, 0, false, 0);
        face::bubble("Oyun\noynayalım mı?");
        dump(std::string(sn) + "_bubble2");
        bat_mv = 3450;
        face::drawIdle(face::SAD, false);
        dump(std::string(sn) + "_lowbat");
        bat_mv = 3900;
    }
    store::d.style = 0;

    // menü
    script = [](uint32_t) { return 0u; };
    frame_no = 0;
    on_frame = [](uint32_t n) { if (n == 3) { dump("menu"); throw StopSim(); } };
    try { menu::run(); } catch (StopSim &) {}

    // oyunlar
    runGame(games::ZIPLA, 60 + 150, "oyun_zipla", [](uint32_t now) {
        return (now / 33) % 37 == 0 ? (uint32_t)input::EV_R_DOWN : 0u; });
    held_r = false; tilt_x = 0.3f;
    runGame(games::YAKALA, 60 + 120, "oyun_yakala", [](uint32_t) { return 0u; });
    tilt_x = 0;
    runGame(games::HAFIZA, 60 + 40, "oyun_hafiza", [](uint32_t) { return 0u; });
    runGame(games::TEPKI, 60 + 5, "oyun_tepki", [](uint32_t) { return 0u; });
    runGame(games::DUELLO, 60 + 3, "oyun_duello", [](uint32_t) { return 0u; });
    store::d.style = 1;
    runGame(games::ZIPLA, 60 + 95, "oyun_zipla_yildiz", [](uint32_t now) {
        return (now / 33) % 41 == 0 ? (uint32_t)input::EV_R_DOWN : 0u; });
    printf("tamam\n");
    return 0;
}
