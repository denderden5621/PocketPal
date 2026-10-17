#include "games.h"
#include "display.h"
#include "input.h"
#include "sound.h"
#include "face.h"
#include "power.h"
#include "store.h"
#include "lis3dh.h"
#include "config.h"
#include "esp_timer.h"
#include "esp_random.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include <stdio.h>
#include <math.h>

using namespace display;

namespace games {

const char *const NAMES[COUNT] = {"Zıpla", "Yakala", "Hafıza", "Tepki", "Düello"};

static uint32_t ms() { return (uint32_t)(esp_timer_get_time() / 1000); }
static uint32_t rnd(uint32_t n) { return n ? esp_random() % n : 0; }
static bool cat() { return store::d.style == store::STYLE_CAT; }

enum Status { RUNNING, OVER, QUIT, TIMEOUT };

struct Frame { uint32_t now; uint32_t ev; };

// Kare zamanlayıcı: GAME_FPS hızında bekler, girişleri ve sesi günceller
static Status frame(Frame &f, uint32_t timeout_ms = AWAKE_TIMEOUT_MS + 10000)
{
    static uint32_t next = 0;
    uint32_t now = ms();
    if ((int32_t)(next - now) > 0) vTaskDelay(pdMS_TO_TICKS(next - now));
    else vTaskDelay(1);
    now = ms();
    next = now + 1000 / GAME_FPS;
    f.now = now;
    f.ev = input::poll(now);
    sound::update(now);
    if (f.ev & input::EV_L_LONG) return QUIT;
    if (now - input::lastActivityMs() > timeout_ms) return TIMEOUT;
    return RUNNING;
}

static void hud(int score)
{
    char b[12];
    snprintf(b, sizeof b, "%d", score);
    text(LCD_W - 8 - textWidth(b, 1), 6, b, 1);
}

// ======================= 1) ZIPLA =======================
static Status zipla(int &score)
{
    const int GROUND = 112, PX = 18;
    float py = GROUND - 12, vy = 0;
    struct Obs { float x; int w, h; bool counted; } obs[3];
    for (int i = 0; i < 3; i++) obs[i] = {200.0f + i * 70.0f, 8, 12, false};
    float speed = 2.2f, scroll = 0;
    score = 0;
    Frame f;
    uint32_t start = ms();
    while (true) {
        Status s = frame(f);
        if (s != RUNNING) return s;
        bool ground = py >= GROUND - 12;
        if ((f.ev & (input::EV_L_DOWN | input::EV_R_DOWN | input::EV_TAP)) && ground) {
            vy = -5.4f; sound::play(sound::JUMP);
        }
        vy += 0.36f; py += vy;
        if (py > GROUND - 12) { py = GROUND - 12; vy = 0; }
        scroll += speed;
        float maxx = 0;
        for (auto &o : obs) if (o.x > maxx) maxx = o.x;
        for (auto &o : obs) {
            o.x -= speed;
            if (o.x + o.w < 0) {
                o.x = (maxx < LCD_W ? LCD_W : maxx) + 55 + rnd(70) + speed * 8;
                o.w = 7 + rnd(6); o.h = 10 + rnd(9); o.counted = false;
                maxx = o.x;
            }
            if (!o.counted && o.x + o.w < PX) {
                o.counted = true; score++;
                if (score % 5 == 0) { speed += 0.25f; if (speed > 5.0f) speed = 5.0f; sound::play(sound::COIN); }
            }
            // çarpışma (biraz affedici)
            if (PX + 10 > o.x + 1 && PX + 2 < o.x + o.w - 1 && py + 11 > GROUND - o.h + 2) {
                sound::play(sound::HIT);
                return OVER;
            }
        }
        // çizim
        clear();
        hline(0, GROUND, LCD_W);
        for (int x = -((int)scroll % 16); x < LCD_W; x += 16) hline(x, GROUND + 4, 5);
        for (int x = -((int)(scroll / 4) % 64); x < LCD_W; x += 64) {   // bulut/yıldız arka plan
            if (cat()) { ellipse(x + 20, 30, 10, 4, false); ellipse(x + 28, 27, 7, 4, false); }
            else { pixel(x + 10, 20); pixel(x + 40, 34); pixel(x + 25, 46); circle(x + 52, 18, 1, true); }
        }
        for (auto &o : obs) {
            int x = (int)o.x;
            if (cat()) {   // karton kutu
                rect(x, GROUND - o.h, o.w, o.h, false);
                line(x, GROUND - o.h, x + o.w - 1, GROUND - 1);
            } else {       // meteor
                rect(x, GROUND - o.h, o.w, o.h, true);
                pixel(x + 2, GROUND - o.h + 2, false); pixel(x + o.w - 3, GROUND - 4, false);
            }
        }
        face::smallSprite(PX, (int)py);
        hud(score);
        if (f.now - start < 1500) textCentered(56, "Zıpla!", 2);
        flush();
    }
}

// ======================= 2) YAKALA =======================
static void fish(int x, int y)
{
    ellipse(x, y, 5, 3, true);
    line(x + 5, y, x + 8, y - 3); line(x + 5, y, x + 8, y + 3); vline(x + 8, y - 3, 7);
    pixel(x - 3, y - 1, false);
}

static void bomb(int x, int y)
{
    circle(x, y, 5, true);
    pixel(x - 2, y - 2, false);
    line(x + 3, y - 4, x + 6, y - 7);
    pixel(x + 7, y - 8); pixel(x + 5, y - 9);
}

static void starItem(int x, int y)
{
    line(x - 5, y, x + 5, y, true, 2); line(x, y - 5, x, y + 5, true, 2);
    line(x - 3, y - 3, x + 3, y + 3); line(x - 3, y + 3, x + 3, y - 3);
}

static Status yakala(int &score)
{
    float px = 58;
    struct Item { float x, y, v; bool bad, alive; } it[6] = {};
    int lives = 3;
    score = 0;
    uint32_t next_spawn = ms() + 800;
    float fall = 1.2f;
    Frame f;
    uint32_t start = ms();
    bool tilt = lis3dh::present();
    while (true) {
        Status s = frame(f);
        if (s != RUNNING) return s;
        if (tilt) {
            float tx = input::tiltX();
            px += tx * 7.0f;
            if (fabsf(tx) > 0.2f) input::markActivity(f.now);
        }
        if (input::leftHeld())  px -= 3.5f;
        if (input::rightHeld()) px += 3.5f;
        if (px < 0) px = 0;
        if (px > LCD_W - 18) px = LCD_W - 18;

        if ((int32_t)(f.now - next_spawn) >= 0) {
            for (auto &i : it) if (!i.alive) {
                i = {(float)(10 + rnd(LCD_W - 20)), 14.0f, fall + rnd(10) * 0.05f, rnd(100) < 28, true};
                break;
            }
            uint32_t gap = 900 - (score * 12 > 550 ? 550 : score * 12);
            next_spawn = f.now + gap + rnd(300);
        }
        for (auto &i : it) {
            if (!i.alive) continue;
            i.y += i.v;
            if (i.y > 104 && i.y < 116 && i.x > px - 4 && i.x < px + 22) {
                i.alive = false;
                if (i.bad) { lives--; sound::play(sound::HIT); }
                else {
                    score++; sound::play(sound::COIN);
                    if (score % 8 == 0) fall += 0.25f;
                }
            } else if (i.y > LCD_H + 6) {
                i.alive = false;
                if (!i.bad) { lives--; sound::play(sound::SAD); }
            }
        }
        if (lives <= 0) return OVER;

        clear();
        for (int l = 0; l < 3; l++) {               // can kalpleri (boş = kaybedilen)
            face::heart(8 + l * 12, 9, 6, true);
            if (l >= lives) face::heart(8 + l * 12, 9, 4, false);
        }
        hud(score);
        for (auto &i : it) {
            if (!i.alive) continue;
            if (i.bad) bomb((int)i.x, (int)i.y);
            else if (cat()) fish((int)i.x, (int)i.y);
            else starItem((int)i.x, (int)i.y);
        }
        // sepet + kahraman
        int x = (int)px;
        roundRect(x, 112, 18, 9, 3, true);
        face::smallSprite(x + 3, 100);
        if (f.now - start < 1800) textCentered(50, tilt ? "Eğerek yakala!" : "Basılı tut!", 1);
        flush();
    }
}

// ======================= 3) HAFIZA =======================
static void pads(int lit, const char *msg, int level)
{
    clear();
    // sol ve sağ yastık
    roundRect(6, 30, 54, 70, 10, lit == 0, true);
    roundRect(68, 30, 54, 70, 10, lit == 1, true);
    if (lit != 0) roundRect(7, 31, 52, 68, 9, false, true);
    if (lit != 1) roundRect(69, 31, 52, 68, 9, false, true);
    // oklar
    bool on0 = lit != 0, on1 = lit != 1;
    for (int i = 0; i < 14; i++) { vline(26 + i, 65 - i, 2 * i + 1, on0); }
    for (int i = 0; i < 14; i++) { vline(102 - i, 65 - i, 2 * i + 1, on1); }
    char b[24];
    snprintf(b, sizeof b, "Seviye %d", level);
    textCentered(10, b, 1);
    textCentered(110, msg, 1);
}

static Status hafiza(int &score)
{
    uint8_t seq[64];
    int len = 0;
    score = 0;
    Frame f;
    while (true) {
        seq[len++] = (uint8_t)rnd(2);
        // göster
        int on_ms = 420 - (len * 12 > 220 ? 220 : len * 12);
        pads(-1, "İzle...", len); flush();
        uint32_t t0 = ms();
        while (ms() - t0 < 600) { Status s = frame(f); if (s == QUIT) return s; }
        for (int i = 0; i < len; i++) {
            pads(seq[i], "İzle...", len); flush();
            sound::tone(seq[i] ? 1047 : 659, on_ms);
            t0 = ms();
            while (ms() - t0 < (uint32_t)on_ms) { Status s = frame(f); if (s == QUIT) return s; }
            pads(-1, "İzle...", len); flush();
            t0 = ms();
            while (ms() - t0 < 160) { Status s = frame(f); if (s == QUIT) return s; }
        }
        input::markActivity(ms());
        // oyuncu tekrarlar
        for (int i = 0; i < len; i++) {
            pads(-1, "Senin sıran!", len); flush();
            int got = -1;
            while (got < 0) {
                Status s = frame(f, 8000);
                if (s != RUNNING) return s == TIMEOUT ? OVER : s;
                if (f.ev & input::EV_L_DOWN) got = 0;
                else if (f.ev & input::EV_R_DOWN) got = 1;
            }
            pads(got, "Senin sıran!", len); flush();
            if (got != seq[i]) { sound::play(sound::HIT); vTaskDelay(pdMS_TO_TICKS(400)); return OVER; }
            sound::tone(got ? 1047 : 659, 150);
            t0 = ms();
            while (ms() - t0 < 180) frame(f);
        }
        score = len;
        sound::play(sound::LEVELUP);
        t0 = ms();
        while (ms() - t0 < 500) frame(f);
        if (len >= 64) return OVER;
    }
}

// ======================= 4) TEPKİ =======================
static Status tepki(int &score)
{
    const int ROUNDS = 5;
    int best = 9999, sum = 0, valid = 0;
    Frame f;
    for (int r = 0; r < ROUNDS; r++) {
        // bekle
        clear();
        face::draw(face::NEUTRAL, 0, 0, false, 0);
        char b[40];
        snprintf(b, sizeof b, "Tur %d/%d  Bekle...", r + 1, ROUNDS);
        textCentered(112, b, 1);
        flush();
        uint32_t wait = 1500 + rnd(3000), t0 = ms();
        bool early = false;
        while (ms() - t0 < wait) {
            Status s = frame(f);
            if (s != RUNNING) return s;
            if (f.ev & (input::EV_L_DOWN | input::EV_R_DOWN | input::EV_TAP)) { early = true; break; }
        }
        if (early) {
            clear(); face::draw(face::ANGRY, 0, 0, false, 0); textCentered(112, "Erken! Tekrar", 1); flush();
            sound::play(sound::HIT);
            t0 = ms(); while (ms() - t0 < 1200) frame(f);
            r--;   // turu tekrarla
            continue;
        }
        // ŞİMDİ!
        clear(true);
        textCentered(52, "ŞİMDİ!", 3, false);
        flush();
        sound::tone(1568, 120);
        uint32_t go = ms();
        uint32_t rt = 0;
        while (true) {
            Status s = frame(f, 6000);
            if (s == QUIT) return s;
            if (s == TIMEOUT) return OVER;
            if (f.ev & (input::EV_L_DOWN | input::EV_R_DOWN | input::EV_TAP)) { rt = f.now - go; break; }
        }
        if (rt < (uint32_t)best) best = rt;
        sum += rt; valid++;
        clear();
        face::draw(rt < 300 ? face::HAPPY : face::NEUTRAL, 0, 0, false, 0);
        snprintf(b, sizeof b, "%lu ms", (unsigned long)rt);
        textCentered(108, b, 2);
        flush();
        sound::play(rt < 300 ? sound::COIN : sound::CLICK);
        t0 = ms(); while (ms() - t0 < 1200) frame(f);
    }
    score = valid ? best : 0;
    return OVER;
}


// ======================= 5) DÜELLO (iki kişi) =======================
// Biri sol, biri sağ düğmeyi tutar. "ŞİMDİ!" yazınca ilk basan turu alır,
// erken basan turu rakibine verir. 3 tur alan kazanır.
static void duelScreen(int sl, int sr, const char *msg, int arrow)
{
    clear();
    vline(64, 12, 84);
    textCentered(2, "Düello", 1);
    text(14, 16, "SOL", 2); text(80, 16, "SAĞ", 2);
    char b[16];
    snprintf(b, sizeof b, "%d", sl); text(32 - textWidth(b, 4) / 2, 40, b, 4);
    snprintf(b, sizeof b, "%d", sr); text(96 - textWidth(b, 4) / 2, 40, b, 4);
    if (arrow < 0) { face::triFill(4, 84, 16, 78, 16, 90, true); }
    if (arrow > 0) { face::triFill(124, 84, 112, 78, 112, 90, true); }
    hline(0, 96, LCD_W);
    textCentered(106, msg, msg[0] && textWidth(msg, 2) <= 124 ? 2 : 1);
    flush();
}

static Status duello(int &score)
{
    int sl = 0, sr = 0;
    Frame f;
    score = 0;
    while (sl < 3 && sr < 3) {
        duelScreen(sl, sr, "Hazır...", 0);
        uint32_t wait = 1500 + rnd(3000), t0 = ms();
        int early = 0;
        while (ms() - t0 < wait) {
            Status s = frame(f, 60000);
            if (s != RUNNING) return s;
            if (f.ev & input::EV_L_DOWN) { early = -1; break; }
            if (f.ev & input::EV_R_DOWN) { early = 1; break; }
        }
        int winner = 0;
        const char *msg;
        if (early) {
            winner = -early;
            msg = early < 0 ? "Sol erken bastı!" : "Sağ erken bastı!";
            sound::play(sound::HIT);
        } else {
            clear(true);
            textCentered(52, "ŞİMDİ!", 3, false);
            flush();
            sound::tone(1568, 120);
            while (!winner) {
                Status s = frame(f, 15000);
                if (s == QUIT) return s;
                if (s == TIMEOUT) return OVER;
                bool l = f.ev & input::EV_L_DOWN, r = f.ev & input::EV_R_DOWN;
                if (l && r) winner = 2;          // aynı karede: berabere
                else if (l) winner = -1;
                else if (r) winner = 1;
            }
            msg = winner == 2 ? "Berabere!" : (winner < 0 ? "Sol aldı!" : "Sağ aldı!");
            sound::play(winner == 2 ? sound::CLICK : sound::COIN);
        }
        if (winner == -1) sl++;
        if (winner == 1) sr++;
        duelScreen(sl, sr, msg, winner == 2 ? 0 : winner);
        t0 = ms();
        while (ms() - t0 < 1500) frame(f, 60000);
    }
    score = sl > sr ? 1 : 2;
    return OVER;
}

// ======================= ortak =======================
static bool better(int id, int score)
{
    uint16_t &b = store::d.best[id];
    if (id == DUELLO) { b++; return false; }   // düelloda rekor yok: oynanan maç sayısı
    if (id == TEPKI) { if (score > 0 && (b == 0 || score < b)) { b = (uint16_t)score; return true; } return false; }
    if (score > b) { b = (uint16_t)score; return true; }
    return false;
}

static void intro(int id)
{
    static const char *const HELP[COUNT] = {
        "Düğme ya da vuruş:\nzıpla",
        "Eğ ya da basılı tut:\nkaç ve yakala",
        "Sırayı izle,\nsol/sağ ile tekrarla",
        "ŞİMDİ yazınca\nhemen bas!",
        "İki kişi: biri sol\nbiri sağ. İlk basan!",
    };
    clear();
    textCentered(14, NAMES[id], 2);
    face::smallSprite(58, 38);
    const char *h = HELP[id];
    char l1[32] = {0}; const char *nl = h; int n = 0;
    while (*nl && *nl != '\n' && n < 31) l1[n++] = *nl++;
    textCentered(62, l1, 1);
    if (*nl == '\n') textCentered(74, nl + 1, 1);
    textCentered(104, "Uzun sol: çıkış", 1);
    flush();
    Frame f;
    uint32_t t0 = ms();
    while (ms() - t0 < 1600) frame(f);
}

bool play(int id)
{
    while (true) {
        intro(id);
        int score = 0;
        Status s = RUNNING;
        switch (id) {
        case ZIPLA:  s = zipla(score); break;
        case YAKALA: s = yakala(score); break;
        case HAFIZA: s = hafiza(score); break;
        case TEPKI:  s = tepki(score); break;
        default:     s = duello(score); break;
        }
        if (s == TIMEOUT) return true;
        if (s == QUIT) { sound::play(sound::BACK); return false; }

        store::d.games_played++;
        bool rec = better(id, score);
        store::save();
        auto &st = power::rtc();
        st.joy_until_s = power::nowS() + 45 * 60;
        power::noteInteraction();

        // sonuç ekranı
        sound::play(rec ? sound::LEVELUP : sound::GAMEOVER);
        Frame f;
        uint32_t t0 = ms();
        while (true) {
            clear();
            face::draw(rec || id == DUELLO ? face::LOVE : (score > 0 ? face::HAPPY : face::SAD), 0, 0, false, f.now);
            char b[32];
            if (id == DUELLO) {
                face::bubble(score == 1 ? "SOL kazandı!" : "SAĞ kazandı!");
                snprintf(b, sizeof b, "Maç %d", store::d.best[id]);
            } else {
                if (id == TEPKI) snprintf(b, sizeof b, "En iyi %d ms", score);
                else snprintf(b, sizeof b, "Skor %d", score);
                face::bubble(rec ? "YENİ REKOR!" : b);
                if (rec) {
                    if (id == TEPKI) snprintf(b, sizeof b, "%d ms", score); else snprintf(b, sizeof b, "Skor %d", score);
                } else {
                    if (id == TEPKI) snprintf(b, sizeof b, "Rekor %d ms", store::d.best[id]);
                    else snprintf(b, sizeof b, "Rekor %d", store::d.best[id]);
                }
            }
            rect(0, 100, LCD_W, 28, true, false);
            textCentered(102, b, 1);
            textCentered(116, "Sol:çık  Sağ:tekrar", 1);
            flush();
            Status fs = frame(f);
            if (fs == TIMEOUT) return true;
            if (ms() - t0 < 500) continue;            // yanlışlıkla basmayı önle
            if (f.ev & input::EV_R) { sound::play(sound::SELECT); break; }
            if (f.ev & input::EV_L || fs == QUIT) { sound::play(sound::BACK); return false; }
        }
    }
}

} // namespace games
