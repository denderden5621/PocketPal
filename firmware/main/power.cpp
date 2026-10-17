#include "power.h"
#include "display.h"
#include "sound.h"
#include "lis3dh.h"
#include "esp_sleep.h"
#include "esp_log.h"
#include "esp_attr.h"
#include "driver/gpio.h"
#include "driver/rtc_io.h"
#include "esp_adc/adc_oneshot.h"
#include "esp_adc/adc_cali.h"
#include "esp_adc/adc_cali_scheme.h"
#include "ulp_lp_core.h"
#include <sys/time.h>
#include <string.h>
#include "esp_rom_sys.h"

extern "C" {
#include "ulp_main.h"
}

extern const uint8_t ulp_main_bin_start[] asm("_binary_ulp_main_bin_start");
extern const uint8_t ulp_main_bin_end[]   asm("_binary_ulp_main_bin_end");

static const char *TAG = "guc";

namespace power {

static const uint32_t MAGIC = 0x50414C31;   // "PAL1"
RTC_DATA_ATTR static RtcState st;

RtcState &rtc() { return st; }

uint32_t nowS()
{
    struct timeval tv;
    gettimeofday(&tv, nullptr);
    return (uint32_t)tv.tv_sec;
}

static void startLpCore()
{
    // EXTCOMIN pini LP çekirdeğe ait: LP IO olarak hazırla
    rtc_gpio_init(PIN_EXTCOMIN);
    rtc_gpio_set_direction(PIN_EXTCOMIN, RTC_GPIO_MODE_OUTPUT_ONLY);
    rtc_gpio_set_level(PIN_EXTCOMIN, 0);

    ulp_lp_core_stop();
    ESP_ERROR_CHECK(ulp_lp_core_load_binary(ulp_main_bin_start, ulp_main_bin_end - ulp_main_bin_start));
    ulp_lp_core_cfg_t cfg = {};
    cfg.wakeup_source = ULP_LP_CORE_WAKEUP_SOURCE_LP_TIMER;
    cfg.lp_timer_sleep_duration_us = 500000;     // 0.5 sn'de bir çevir = 1 Hz kare dalga
    ESP_ERROR_CHECK(ulp_lp_core_run(&cfg));
    ESP_LOGI(TAG, "LP çekirdek başladı (EXTCOMIN 1 Hz)");
}

Wake begin()
{
    esp_sleep_wakeup_cause_t c = esp_sleep_get_wakeup_cause();
    bool cold = (st.magic != MAGIC) || (c == ESP_SLEEP_WAKEUP_UNDEFINED);
    if (st.magic != MAGIC) {
        memset(&st, 0, sizeof(st));
        st.magic = MAGIC;
        st.last_interact_s = nowS();
    }
    st.boots++;
    if (cold) startLpCore();

    if (cold) return WAKE_COLD;
    if (c == ESP_SLEEP_WAKEUP_TIMER) return WAKE_TIMER;
    if (c == ESP_SLEEP_WAKEUP_GPIO) {
        gpio_hold_dis(PIN_WAKE_L);
        gpio_set_direction(PIN_WAKE_L, GPIO_MODE_INPUT);
        gpio_pullup_en(PIN_WAKE_L);
        // INT1 kilidini oku+temizle; sonra pin hâlâ düşükse basılı tutulan düğmedir
        bool motion = lis3dh::begin() && lis3dh::motionLatched();
        esp_rom_delay_us(200);
        bool btn = gpio_get_level(PIN_WAKE_L) == 0;
        if (btn || !motion) return WAKE_BUTTON;   // kısa basış da düğme sayılır
        return WAKE_MOTION;
    }
    return WAKE_OTHER;
}

// ---------------- pil ----------------
static adc_oneshot_unit_handle_t adc = nullptr;
static adc_cali_handle_t cali = nullptr;

static int readMv()
{
    if (!adc) {
        adc_oneshot_unit_init_cfg_t u = {};
        u.unit_id = ADC_UNIT_1;
        if (adc_oneshot_new_unit(&u, &adc) != ESP_OK) { adc = nullptr; return 0; }
        adc_oneshot_chan_cfg_t ch = {};
        ch.atten = ADC_ATTEN_DB_12;
        ch.bitwidth = ADC_BITWIDTH_DEFAULT;
        adc_oneshot_config_channel(adc, ADC_CHANNEL_1, &ch);   // GPIO1 = D1
        adc_cali_curve_fitting_config_t cc = {};
        cc.unit_id = ADC_UNIT_1;
        cc.chan = ADC_CHANNEL_1;
        cc.atten = ADC_ATTEN_DB_12;
        cc.bitwidth = ADC_BITWIDTH_DEFAULT;
        if (adc_cali_create_scheme_curve_fitting(&cc, &cali) != ESP_OK) cali = nullptr;
    }
    // 1 MΩ bölücü yüksek empedanslı: ilk okumayı at, kalanların ortalamasını al
    int sum = 0, n = 0, raw = 0, mv = 0;
    adc_oneshot_read(adc, ADC_CHANNEL_1, &raw);
    for (int i = 0; i < 16; i++) {
        if (adc_oneshot_read(adc, ADC_CHANNEL_1, &raw) != ESP_OK) continue;
        if (cali) adc_cali_raw_to_voltage(cali, raw, &mv);
        else mv = raw * 3100 / 4095;
        sum += mv; n++;
    }
    if (!n) return 0;
    return (int)((sum / n) * BAT_DIVIDER);
}

int batteryMv(bool fresh)
{
    if (fresh || st.bat_mv == 0) {
        int mv = readMv();
        if (mv > 0) st.bat_mv = (uint16_t)(st.bat_mv ? (st.bat_mv + mv) / 2 : mv);
    }
    return st.bat_mv;
}

int batteryPct()
{
    int mv = batteryMv();
    if (mv < 2500) return -1;          // pil bölücüsü bağlı değil / ölçülemiyor
    // LiPo eğrisine kabaca uyan parçalı doğrusal tablo
    static const int16_t tbl[][2] = {{3300, 0}, {3500, 8}, {3650, 25}, {3750, 45}, {3850, 62},
                                     {3950, 75}, {4050, 88}, {4150, 100}};
    if (mv <= tbl[0][0]) return 0;
    for (int i = 1; i < 8; i++) {
        if (mv <= tbl[i][0]) {
            int x0 = tbl[i - 1][0], y0 = tbl[i - 1][1], x1 = tbl[i][0], y1 = tbl[i][1];
            return y0 + (mv - x0) * (y1 - y0) / (x1 - x0);
        }
    }
    return 100;
}

bool batteryLow()      { int mv = batteryMv(); return mv > 2500 && mv < BAT_LOW_MV; }
bool batteryCritical() { int mv = batteryMv(); return mv > 2500 && mv < BAT_CRIT_MV; }

// ---------------- saat ----------------
bool clockSet() { return st.clock_set; }

int minuteOfDay()
{
    if (!st.clock_set) return -1;
    int64_t s = (int64_t)nowS() + st.clock_offset_s;
    s %= 86400; if (s < 0) s += 86400;
    return (int)(s / 60);
}

void setClock(int h, int m)
{
    int32_t want = (h * 60 + m) * 60;
    st.clock_offset_s = want - (int32_t)(nowS() % 86400);
    st.clock_set = 1;
}

bool isNight()
{
    int m = minuteOfDay();
    if (m < 0) return false;
    int h = m / 60;
    return (NIGHT_START_H > NIGHT_END_H) ? (h >= NIGHT_START_H || h < NIGHT_END_H)
                                         : (h >= NIGHT_START_H && h < NIGHT_END_H);
}

// ---------------- etkileşim / hareket ----------------
void noteInteraction()
{
    st.last_interact_s = nowS();
}

void noteMotionWake()
{
    uint32_t now = nowS();
    st.motion_times[st.motion_idx] = now;
    st.motion_idx = (st.motion_idx + 1) % MOTION_STORM_COUNT;
    // halkadaki en eski kayıt pencere içindeyse = fırtına (örn. çanta yürürken sallanıyor)
    uint32_t oldest = st.motion_times[st.motion_idx];
    if (oldest != 0 && now - oldest < MOTION_STORM_WINDOW_S) {
        // örn. çanta yürürken sallanıyor: hareketle uyanmayı bir süre kapat,
        // fırtınalar sürerse süreyi katla (5, 10, 20, 40, 80 dk)
        if (now - st.last_storm_s > 3600) st.storm_level = 0;
        uint32_t mute = (uint32_t)MOTION_MUTE_S << (st.storm_level < 4 ? st.storm_level : 4);
        if (st.storm_level < 4) st.storm_level++;
        st.last_storm_s = now;
        st.motion_mute_until_s = now + mute;
        for (int i = 0; i < MOTION_STORM_COUNT; i++) st.motion_times[i] = 0;
        ESP_LOGI(TAG, "hareket fırtınası: %lu sn hareketle uyanma kapalı", (unsigned long)mute);
    }
}

bool motionMuted() { return nowS() < st.motion_mute_until_s; }

// ---------------- uyku ----------------
void sleep(uint32_t timer_s, bool motion)
{
    bool mute = motionMuted();
    if (mute) {
        uint32_t left = st.motion_mute_until_s - nowS() + 1;
        if (timer_s == 0 || left < timer_s) timer_s = left;    // susturma bitince yeniden kur
    }

    sound::prepareSleep();
    display::prepareSleep();

    if (lis3dh::present()) {
        if (motion && !mute) lis3dh::configSleepMotion(true);   // 10 Hz düşük güç + hareket kesmesi
        else lis3dh::powerDown();                                // hareketle uyanma yoksa tamamen kapat
    }

    // Sol düğme (veya INT1) şu an düşükse GPIO uyandırması hemen tetiklenir:
    // sıkışmış düğmede pili bitirmemek için yalnızca zamanlayıcıyla uyan.
    gpio_set_direction(PIN_WAKE_L, GPIO_MODE_INPUT);
    gpio_pullup_en(PIN_WAKE_L);
    bool low_now = gpio_get_level(PIN_WAKE_L) == 0;
    if (low_now && lis3dh::present() && lis3dh::motionLatched()) low_now = gpio_get_level(PIN_WAKE_L) == 0;
    if (!low_now) {
        esp_deep_sleep_enable_gpio_wakeup(1ULL << PIN_WAKE_L, ESP_GPIO_WAKEUP_GPIO_LOW);
    } else {
        ESP_LOGW(TAG, "sol düğme basılı kalmış: yalnızca zamanlayıcı");
        if (timer_s == 0 || timer_s > 60) timer_s = 60;
    }
    if (timer_s) esp_sleep_enable_timer_wakeup((uint64_t)timer_s * 1000000ULL);
    else esp_sleep_disable_wakeup_source(ESP_SLEEP_WAKEUP_TIMER);   // hafif uykudan kalan zamanlayıcıyı temizle

    ESP_LOGI(TAG, "derin uyku (zamanlayıcı %lu sn, hareket %d)", (unsigned long)timer_s, motion && !mute);
    esp_deep_sleep_start();
}

} // namespace power
