#pragma once
// ======================================================================
//  Pocket Pal - donanım ve davranış ayarları (tek yerden değiştirin)
// ======================================================================
#include "driver/gpio.h"

// ---- Pin haritası: Seeed XIAO ESP32-C6 ----
#define PIN_WAKE_L      GPIO_NUM_0    // D0: sol düğme + LIS3DH INT1 (1N4148 ile), derin uyku uyandırma
#define PIN_BAT_ADC     GPIO_NUM_1    // D1: pil bölücü orta noktası (1M/1M)
#define PIN_EXTCOMIN    GPIO_NUM_2    // D2: ekran EXTCOMIN (LP çekirdek sürer)
#define PIN_BTN_R       GPIO_NUM_21   // D3: sağ düğme
#define PIN_I2C_SDA     GPIO_NUM_22   // D4
#define PIN_I2C_SCL     GPIO_NUM_23   // D5
#define PIN_PIEZO       GPIO_NUM_17   // D7 (D6=TX açılışta veri basar -> piezo cızırdardı, boş bırakın)
#define PIN_LCD_SCLK    GPIO_NUM_19   // D8
#define PIN_LCD_SCS     GPIO_NUM_20   // D9 (aktif yüksek)
#define PIN_LCD_SI      GPIO_NUM_18   // D10

// ---- Ekran: Sharp LS013B7DH03, 128x128 ----
#define LCD_W           128
#define LCD_H           128
#define LCD_SPI_HZ      1000000       // veri sayfası üst sınırı 1.1 MHz
#define LCD_ROTATE_180  0             // görüntü ters çıkarsa 1 yapın
#define LCD_MIRROR_X    0             // ayna görüntü çıkarsa 1 yapın

// ---- Zamanlar ----
#define AWAKE_TIMEOUT_MS        20000   // dokunulmazsa uykuya geçiş
#define IDLE_WAKE_MIN_S         120     // gündüz göz kırpma uyanışları arası (rastgele)
#define IDLE_WAKE_MAX_S         300
#define NIGHT_CHECK_S           3600    // gece: saatte bir kontrol
#define BORED_AFTER_S           (2 * 3600)
#define SLEEPY_AFTER_S          (6 * 3600)
#define NIGHT_START_H           23
#define NIGHT_END_H             7
#define BUTTON_STUCK_MS         5000
#define MOTION_STORM_COUNT      6       // 10 dk içinde bu kadar hareket uyanışı -> hareketle uyanma 5 dk kapalı
#define MOTION_STORM_WINDOW_S   600
#define MOTION_MUTE_S           300

// ---- Pil ----
#define BAT_DIVIDER             2.0f    // 1M/1M
#define BAT_LOW_MV              3500
#define BAT_CRIT_MV             3300
#define BAT_FULL_MV             4150
#define BAT_EMPTY_MV            3300

// ---- Oyun ----
#define GAME_FPS                30
