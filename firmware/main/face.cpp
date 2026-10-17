#include "face.h"
#include "display.h"
#include "input.h"
#include "sound.h"
#include "power.h"
#include "store.h"
#include "lis3dh.h"
#include "config.h"
#include "esp_random.h"
#include <math.h>
#include <stdio.h>
#include <string.h>

using namespace display;

namespace face {

// ---------------- yerleşim ----------------
static const int EYE_Y = 58;
static const int EYE_LX = 38, EYE_RX = 90;
static const int MOUTH_Y = 90;

static inline bool cat() { return store::d.style == store::STYLE_CAT; }
static uint32_t rnd(uint32_t n) { return n ? esp_random() % n : 0; }

// ---------------- yardımcı çizimler ----------------
void triFill(int x0, int y0, int x1, int y1, int x2, int y2, bool on)
{
    // y'ye göre sırala, yatay taramayla doldur
    if (y0 > y1) { int t; t = y0; y0 = y1; y1 = t; t = x0; x0 = x1; x1 = t; }
    if (y1 > y2) { int t; t = y1; y1 = y2; y2 = t; t = x1; x1 = x2; x2 = t; }
    if (y0 > y1) { int t; t = y0; y0 = y1; y1 = t; t = x0; x0 = x1; x1 = t; }
    for (int y = y0; y <= y2; y++) {
        float xa = (y2 == y0) ? x0 : x0 + (float)(x2 - x0) * (y - y0) / (y2 - y0);
        float xb;
        if (y < y1) xb = (y1 == y0) ? x0 : x0 + (float)(x1 - x0) * (y - y0) / (y1 - y0);
        else        xb = (y2 == y1) ? x1 : x1 + (float)(x2 - x1) * (y - y1) / (y2 - y1);
        if (xa > xb) { float t = xa; xa = xb; xb = t; }
        hline((int)lroundf(xa), y, (int)lroundf(xb) - (int)lroundf(xa) + 1, on);
    }
}

static void ditherEllipse(int cx, int cy, int rx, int ry)
{
    for (int dy = -ry; dy <= ry; dy++)
        for (int dx = -rx; dx <= rx; dx++)
            if ((float)(dx * dx) / (rx * rx) + (float)(dy * dy) / (ry * ry) <= 1.0f && ((cx + dx + cy + dy) & 1) == 0)
                pixel(cx + dx, cy + dy, true);
}

void heart(int cx, int cy, int s, bool on)
{
    int r = s / 2;
    circle(cx - r + 1, cy - r / 2, r, true, on);
    circle(cx + r - 1, cy - r / 2, r, true, on);
    triFill(cx - 2 * r + 1, cy - r / 4, cx + 2 * r - 1, cy - r / 4, cx, cy + s, on);
}

static void sparkle(int cx, int cy, int r, bool on)
{
    // 4 köşeli parıltı
    triFill(cx - r, cy, cx, cy - 1, cx, cy + 1, on);
    triFill(cx + r, cy, cx, cy - 1, cx, cy + 1, on);
    triFill(cx, cy - r, cx - 1, cy, cx + 1, cy, on);
    triFill(cx, cy + r, cx - 1, cy, cx + 1, cy, on);
    rect(cx - 1, cy - 1, 3, 3, true, on);
}

void batteryIcon(int x, int y, int pct)
{
    rect(x, y, 15, 8, false);
    rect(x + 15, y + 2, 2, 4, true);
    int w = pct < 0 ? 0 : (pct * 11 + 50) / 100;
    if (w) rect(x + 2, y + 2, w, 4, true);
}

void smallSprite(int x, int y, bool on)
{
    // 12x12 kahraman: kedi başı ya da yıldız
    static const uint8_t CAT[12 * 2] = {
        0x40, 0x20, 0x60, 0x60, 0x7F, 0xE0, 0x7F, 0xE0, 0xFF, 0xF0, 0xCF, 0x30,
        0xCF, 0x30, 0xFF, 0xF0, 0xF9, 0xF0, 0x7F, 0xE0, 0x3F, 0xC0, 0x00, 0x00};
    static const uint8_t STAR[12 * 2] = {
        0x06, 0x00, 0x06, 0x00, 0x0F, 0x00, 0xFF, 0xF0, 0x7F, 0xE0, 0x36, 0xC0,
        0x3F, 0xC0, 0x3F, 0xC0, 0x79, 0xE0, 0x70, 0xE0, 0x60, 0x60, 0x00, 0x00};
    bitmap(x, y, 12, 12, cat() ? CAT : STAR, on);
}

// ---------------- gözler ----------------
static void eyeOpen(int ex, int ey, int rx, int ry, float lid, int side, bool sad, bool angry)
{
    ellipse(ex, ey, rx, ry, true);
    // parlama
    if (cat()) {
        circle(ex - rx / 3, ey - ry / 3, 4, true, false);
        circle(ex + rx / 3, ey + ry / 3, 2, true, false);
    } else {
        sparkle(ex - rx / 3, ey - ry / 3, 6, false);
        circle(ex + rx / 3, ey + ry / 3, 2, true, false);
    }
    // göz kapağı
    if (lid > 0.02f) {
        int top = ey - ry - 1;
        int h = (int)(lid * (2 * ry + 2));
        rect(ex - rx - 1, top, 2 * rx + 3, h, true, false);
        hline(ex - rx + 1, top + h, 2 * rx - 1, true);
        hline(ex - rx + 2, top + h + 1, 2 * rx - 3, true);
    }
    // eğik kaşlar (üzgün: dış köşe aşağı, kızgın: iç köşe aşağı)
    if (sad || angry) {
        bool outer_left = (side < 0);           // sol gözün dışı solda
        bool cover_left = sad ? outer_left : !outer_left;
        int x0 = ex - rx - 2, x1 = ex + rx + 2, yt = ey - ry - 2;
        if (cover_left) triFill(x0, yt, x1, yt, x0, ey + 1, false);
        else            triFill(x0, yt, x1, yt, x1, ey + 1, false);
        if (cover_left) line(x0 + 2, ey - 1, x1 - 1, yt + 2, true, 2);
        else            line(x0 + 1, yt + 2, x1 - 2, ey - 1, true, 2);
    }
}

static void eye(int side, Mood m, float lx, float ly, bool blink, uint32_t t)
{
    int cx = side < 0 ? EYE_LX : EYE_RX;
    int ex = cx + (int)lroundf(lx * 6.0f);
    int ey = EYE_Y + (int)lroundf(ly * 5.0f);
    int rx = cat() ? 12 : 13, ry = cat() ? 16 : 15;

    if (blink && m != SLEEPING && m != HAPPY && m != LAUGH && m != DIZZY && m != LOVE) {
        line(ex - rx, ey + 2, ex + rx, ey + 2, true, 3);
        return;
    }
    switch (m) {
    case HAPPY:
        arc(cx, EYE_Y + 6, 11, 200, 340, true, 4);
        break;
    case WINK:
        if (side > 0) arc(cx, EYE_Y + 6, 11, 200, 340, true, 4);
        else eyeOpen(ex, ey, rx, ry, 0, side, false, false);
        break;
    case LAUGH:
        if (side < 0) { line(cx - 9, EYE_Y - 8, cx + 7, EYE_Y, true, 4); line(cx + 7, EYE_Y, cx - 9, EYE_Y + 8, true, 4); }
        else          { line(cx + 9, EYE_Y - 8, cx - 7, EYE_Y, true, 4); line(cx - 7, EYE_Y, cx + 9, EYE_Y + 8, true, 4); }
        break;
    case SLEEPING:
        arc(cx, EYE_Y - 2, 11, 20, 160, true, 3);
        break;
    case SURPRISED:
        circle(cx, EYE_Y, 16, true);
        circle(cx, EYE_Y, 12, true, false);
        circle(cx + (int)(lx * 5), EYE_Y + (int)(ly * 5), 6, true);
        circle(cx + (int)(lx * 5) - 2, EYE_Y + (int)(ly * 5) - 2, 2, true, false);
        break;
    case LOVE: {
        int s = 14 + (int)(2.0f * sinf(t * 0.012f));   // kalp atışı
        heart(cx, EYE_Y - 2, s);
        break;
    }
    case DIZZY: {
        int a = (int)(t / 4) % 360;
        if (side > 0) a = -a;
        for (int r = 4; r <= 13; r += 4) arc(cx, EYE_Y, r, a + r * 20, a + r * 20 + 270, true, 2);
        break;
    }
    case BORED:   eyeOpen(ex, ey, rx, ry, 0.45f, side, false, false); break;
    case SLEEPY:  eyeOpen(ex, ey, rx, ry, 0.70f, side, false, false); break;
    case SAD:     eyeOpen(ex, ey, rx, ry, 0.0f, side, true, false); break;
    case ANGRY:   eyeOpen(ex, ey, rx, ry, 0.0f, side, false, true); break;
    default:      eyeOpen(ex, ey, rx, ry, 0.0f, side, false, false); break;
    }
}

// ---------------- ağız ----------------
static void catMouthW(int y, int s)
{
    arc(64 - s, y, s, 0, 180, true, 2);
    arc(64 + s, y, s, 0, 180, true, 2);
}

static void openMouth(int y, int rx, int ry, bool tongue)
{
    ellipse(64, y, rx, ry, true);
    rect(64 - rx - 1, y - ry - 1, 2 * rx + 3, ry + 1, true, false);
    hline(64 - rx, y, 2 * rx + 1, true);
    if (tongue) ellipse(64, y + ry - 3, rx / 2, 3, true, false);
}

static void mouth(Mood m, uint32_t t)
{
    int y = MOUTH_Y;
    if (cat()) {
        // bıyıklar
        line(6, y - 10, 24, y - 6, true); line(4, y - 3, 24, y - 3, true); line(6, y + 4, 24, y);
        line(122, y - 10, 104, y - 6, true); line(124, y - 3, 104, y - 3, true); line(122, y + 4, 104, y);
    } else {
        ditherEllipse(24, y - 8, 9, 5);
        ditherEllipse(104, y - 8, 9, 5);
    }
    switch (m) {
    case HAPPY: case LAUGH:
        openMouth(y, 10, 9, true);
        break;
    case LOVE: case WINK:
        if (cat()) catMouthW(y - 2, 5); else arc(64, y - 8, 10, 30, 150, true, 2);
        break;
    case SURPRISED:
        circle(64, y + 2, 6, true); circle(64, y + 2, 3, true, false);
        break;
    case BORED:
        line(57, y + 1, 71, y + 1, true, 2);
        break;
    case SLEEPY:
        if ((t / 2500) % 3 == 2) ellipse(64, y + 2, 4, 6, true);  // esneme
        else line(59, y + 1, 69, y + 1, true, 2);
        break;
    case SLEEPING:
        if (cat()) catMouthW(y - 2, 3); else arc(64, y - 4, 5, 30, 150, true, 2);
        break;
    case SAD: case ANGRY:
        arc(64, y + 8, 9, 215, 325, true, 2);
        break;
    case DIZZY:
        for (int x = 52; x < 76; x++) pixel(x, y + (int)lroundf(2.5f * sinf((x + t / 30) * 0.6f)), true),
                                        pixel(x, y + 1 + (int)lroundf(2.5f * sinf((x + t / 30) * 0.6f)), true);
        break;
    default:
        if (cat()) catMouthW(y - 2, 5); else arc(64, y - 6, 8, 30, 150, true, 2);
        break;
    }
    if (cat()) {
        // burun (ağızdan sonra çizilir ki açık ağız silmesin)
        triFill(60, y - 9, 68, y - 9, 64, y - 5, true);
        if (m != SURPRISED && m != LAUGH && m != HAPPY && m != SAD && m != DIZZY && m != ANGRY)
            line(64, y - 5, 64, y - 2, true, 1);
    }
}

void draw(Mood m, float lx, float ly, bool blink, uint32_t t)
{
    eye(-1, m, lx, ly, blink, t);
    eye(+1, m, lx, ly, blink, t);
    mouth(m, t);
    if (m == SLEEPING) {
        text(92, 16, "z", 1);
        text(102, 6, "Z", 2);
    }
    if (m == ANGRY) {
        // köşede "öfke" işareti
        line(104, 14, 110, 20, true, 2); line(110, 14, 104, 20, true, 2);
    }
}

void bubble(const char *s)
{
    char l1[40] = {0}, l2[40] = {0};
    const char *nl = strchr(s, '\n');
    if (nl) {
        size_t n = (size_t)(nl - s); if (n > 39) n = 39;
        memcpy(l1, s, n); strncpy(l2, nl + 1, 39);
    } else strncpy(l1, s, 39);
    bool two = l2[0] != 0;
    int scale = (!two && textWidth(l1, 2) <= 108) ? 2 : 1;
    int w1 = textWidth(l1, scale), w2 = two ? textWidth(l2, 1) : 0;
    int w = (w1 > w2 ? w1 : w2) + 12;
    if (w > 124) w = 124;
    int h = two ? 24 : (scale == 2 ? 22 : 15);
    int x = (LCD_W - w) / 2, y = 3;
    roundRect(x, y, w, h, 6, true, false);
    roundRect(x, y, w, h, 6, false, true);
    roundRect(x + 1, y + 1, w - 2, h - 2, 5, false, true);
    // kuyruk
    triFill(60, y + h - 1, 70, y + h - 1, 66, y + h + 6, false);
    line(60, y + h - 1, 66, y + h + 6, true); line(70, y + h - 1, 66, y + h + 6, true);
    if (two) { textCentered(y + 4, l1, 1); textCentered(y + 13, l2, 1); }
    else textCentered(y + (scale == 2 ? 4 : 4), l1, scale);
}

// ---------------- uyku yüzü ----------------
Mood idleMood()
{
    auto &st = power::rtc();
    uint32_t now = power::nowS();
    if (power::batteryCritical() || power::isNight()) return SLEEPING;
    if (now < st.joy_until_s) return HAPPY;
    if (power::batteryLow()) return SAD;
    uint32_t since = now - st.last_interact_s;
    if (since > SLEEPY_AFTER_S) return SLEEPY;
    if (since > BORED_AFTER_S) return BORED;
    return NEUTRAL;
}

void drawIdle(Mood m, bool blink, float lx)
{
    clear();
    // Uyku yüzünde mutlu gözler yerine sakin açık göz + gülümseme daha "canlı" durur
    Mood shown = (m == HAPPY) ? WINK : m;
    if (m == HAPPY && !blink) shown = NEUTRAL;
    draw(shown, lx, 0, blink, 0);
    if (m == HAPPY) { heart(112, 14, 8); }
    if (power::batteryLow() || power::batteryCritical()) {
        batteryIcon(104, 112, power::batteryPct());
        if (power::batteryCritical()) text(6, 112, "Şarj et", 1);
    }
}

// ---------------- etkileşimli mod ----------------
static Mood base = NEUTRAL, react = NEUTRAL;
static uint32_t react_until = 0, next_blink = 0, blink_until = 0;
static uint32_t bubble_until = 0, next_look = 0, next_chatter = 0;
static char bubble_txt[48];
static float look_x = 0, look_y = 0, target_x = 0, target_y = 0;
static uint32_t pet_t[6]; static int pet_i = 0;
static uint32_t hearts_until = 0;

static const char *CAT_LINES[] = {
    "Miyav!", "Mrrr...", "Selam!", "Oyun\noynayalım mı?", "Sev beni!", "Balık var mı?",
    "Bugün\nharikasın!", "Patimi\nöptün mü?", "Mır mır", "Uykum yok!", "Hadi oyna!",
};
static const char *STAR_LINES[] = {
    "Pırıl pırıl!", "Selam!", "Parla!", "Oyun?", "Dilek tut!", "Harikasın!",
    "Işık hızında!", "Yıldızın\nbenim!", "Göz kırp!", "Hadi oyna!", "Parıl!",
};

static void say(const char *s, uint32_t now, uint32_t ms)
{
    strncpy(bubble_txt, s, sizeof(bubble_txt) - 1);
    bubble_txt[sizeof(bubble_txt) - 1] = 0;
    bubble_until = now + ms;
}

static void doReact(Mood m, uint32_t now, uint32_t ms) { react = m; react_until = now + ms; }

void enter(uint32_t now, bool cold)
{
    auto &st = power::rtc();
    uint32_t away = power::nowS() - st.last_interact_s;
    base = NEUTRAL;
    next_blink = now + 1500 + rnd(2500);
    next_look = now + 800;
    next_chatter = now + 7000 + rnd(6000);
    bubble_until = 0;
    look_x = look_y = target_x = target_y = 0;

    if (cold) {
        doReact(HAPPY, now, 1800);
        say(cat() ? "Miyav! Selam!" : "Selam!", now, 2200);
        sound::play(sound::HELLO);
    } else if (power::batteryCritical()) {
        doReact(SAD, now, 2500);
        say("Pilim bitti\nşarj et lütfen", now, 3000);
        sound::play(sound::SAD);
    } else if (power::isNight()) {
        doReact(SLEEPY, now, 2500);
        say("Uykum var...", now, 2000);
        sound::play(sound::SLEEPY);
    } else if (away > SLEEPY_AFTER_S) {
        doReact(SURPRISED, now, 900);
        say("Neredeydin?\nÖzledim!", now, 2500);
        sound::play(sound::SURPRISE);
    } else if (away > BORED_AFTER_S) {
        doReact(HAPPY, now, 1500);
        say("Sıkılmıştım!", now, 2000);
        sound::play(sound::HAPPY);
    } else {
        doReact(HAPPY, now, 700);
        sound::play(sound::CLICK);
    }
    power::noteInteraction();
}

Action update(uint32_t ev, uint32_t now)
{
    auto &st = power::rtc();
    if (ev & input::EV_BOTH) { sound::play(sound::SELECT); return ACT_MENU; }
    if (ev & input::EV_R_LONG) { sound::play(sound::SELECT); return ACT_GAMES; }

    if (ev & input::EV_R) {
        // sevme
        pet_t[pet_i] = now; pet_i = (pet_i + 1) % 6;
        uint32_t oldest = pet_t[pet_i];
        store::d.pets++;
        if (oldest && now - oldest < 3000) {
            doReact(ANGRY, now, 1500);
            say("Yeter ama!", now, 1500);
            sound::play(sound::HIT);
        } else {
            doReact(LOVE, now, 1600);
            hearts_until = now + 1600;
            sound::play(sound::PURR);
            if (store::d.pets % 25 == 0) say("Seni çok\nseviyorum!", now, 2200);
        }
        st.joy_until_s = power::nowS() + 20 * 60;
        power::noteInteraction();
    }
    if (ev & input::EV_L) {
        const char **lines = cat() ? CAT_LINES : STAR_LINES;
        int n = 11;
        say(lines[rnd(n)], now, 2400);
        doReact(rnd(3) ? HAPPY : WINK, now, 900);
        sound::play(sound::HAPPY);
        power::noteInteraction();
    }
    if (ev & input::EV_L_LONG) {
        char buf[48];
        int pct = power::batteryPct();
        int mod = power::minuteOfDay();
        if (mod >= 0) snprintf(buf, sizeof buf, "Pil %%%d\nSaat %02d:%02d", pct < 0 ? 0 : pct, mod / 60, mod % 60);
        else snprintf(buf, sizeof buf, "Pil %%%d", pct < 0 ? 0 : pct);
        say(buf, now, 3000);
        sound::play(sound::CLICK);
    }
    if (ev & input::EV_DTAP) {
        // çift vuruş: oyun listesi
        sound::play(sound::SELECT);
        return ACT_GAMES;
    }
    if (ev & input::EV_TAP) {
        doReact(SURPRISED, now, 700);
        sound::play(sound::SURPRISE);
        say("Hihi!", now, 1000);
    }
    if (ev & input::EV_SHAKE) {
        doReact(DIZZY, now, 2500);
        say("Başım\ndöndü!", now, 2000);
        sound::play(sound::DIZZY);
    }

    // temel ruh hâli
    if (power::batteryLow()) base = SAD;
    else if (power::isNight()) base = SLEEPY;
    else if (power::nowS() < st.joy_until_s) base = NEUTRAL;
    else base = NEUTRAL;

    // göz kırpma
    if (now >= next_blink) {
        blink_until = now + 110;
        next_blink = now + 1800 + rnd(3500);
        if (rnd(5) == 0) next_blink = now + 300;   // bazen çift kırpma
    }
    // bakış: ivmeölçer varsa eğime, yoksa rastgele dolaş
    if (lis3dh::present()) {
        target_x = input::tiltX() * 1.6f;
        target_y = input::tiltY() * 1.6f;
    } else if (now >= next_look) {
        target_x = ((int)rnd(5) - 2) * 0.45f;
        target_y = ((int)rnd(3) - 1) * 0.4f;
        next_look = now + 1200 + rnd(2500);
    }
    if (target_x > 1) target_x = 1;
    if (target_x < -1) target_x = -1;
    if (target_y > 1) target_y = 1;
    if (target_y < -1) target_y = -1;
    look_x += (target_x - look_x) * 0.25f;
    look_y += (target_y - look_y) * 0.25f;

    // kendi kendine konuşma (seyrek)
    if (now >= next_chatter) {
        next_chatter = now + 9000 + rnd(9000);
        if (bubble_until < now && rnd(2) == 0) {
            const char **lines = cat() ? CAT_LINES : STAR_LINES;
            say(lines[rnd(11)], now, 2000);
        }
    }
    return ACT_NONE;
}

void render(uint32_t now)
{
    clear();
    Mood m = (now < react_until) ? react : base;
    bool blink = now < blink_until;
    draw(m, look_x, look_y, blink, now);
    if (now < hearts_until) {
        uint32_t k = hearts_until - now;
        int dy = (int)(1600 - k) / 40;
        heart(14, 112 - dy, 7);
        heart(114, 118 - dy * 3 / 2, 6);
        heart(100, 100 - dy, 5);
    }
    if (now < bubble_until) bubble(bubble_txt);
    else if (power::batteryLow()) batteryIcon(104, 112, power::batteryPct());
}

void glanceFrame(uint32_t t_in, float lx, float ly)
{
    clear();
    Mood m = t_in < 350 ? SURPRISED : NEUTRAL;
    draw(m, lx, ly, false, t_in);
}

} // namespace face
