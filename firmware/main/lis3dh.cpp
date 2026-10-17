#include "lis3dh.h"
#include "config.h"
#include "driver/i2c_master.h"
#include "esp_log.h"

static const char *TAG = "lis3dh";

namespace lis3dh {

enum : uint8_t {
    WHO_AM_I = 0x0F, CTRL_REG1 = 0x20, CTRL_REG2 = 0x21, CTRL_REG3 = 0x22, CTRL_REG4 = 0x23,
    CTRL_REG5 = 0x24, CTRL_REG6 = 0x25, REFERENCE = 0x26, OUT_X_L = 0x28, INT1_CFG = 0x30,
    INT1_SRC = 0x31, INT1_THS = 0x32, INT1_DURATION = 0x33, CLICK_CFG = 0x38, CLICK_SRC = 0x39,
    CLICK_THS = 0x3A, TIME_LIMIT = 0x3B, TIME_LATENCY = 0x3C, TIME_WINDOW = 0x3D,
};

static i2c_master_bus_handle_t bus = nullptr;
static i2c_master_dev_handle_t dev = nullptr;
static bool ok = false;

static esp_err_t wr(uint8_t reg, uint8_t val)
{
    uint8_t b[2] = {reg, val};
    return i2c_master_transmit(dev, b, 2, 50);
}

static esp_err_t rd(uint8_t reg, uint8_t *dst, size_t n)
{
    if (n > 1) reg |= 0x80;  // otomatik artırma
    return i2c_master_transmit_receive(dev, &reg, 1, dst, n, 50);
}

bool begin()
{
    if (ok) return true;
    if (!bus) {
        i2c_master_bus_config_t bc = {};
        bc.i2c_port = I2C_NUM_0;
        bc.sda_io_num = PIN_I2C_SDA;
        bc.scl_io_num = PIN_I2C_SCL;
        bc.clk_source = I2C_CLK_SRC_DEFAULT;
        bc.glitch_ignore_cnt = 7;
        bc.flags.enable_internal_pullup = true;   // modülde direnç yoksa yedek
        if (i2c_new_master_bus(&bc, &bus) != ESP_OK) return false;
    }
    static const uint8_t ADDRS[2] = {0x18, 0x19};   // SDO pinine göre iki olası adres
    for (uint8_t addr : ADDRS) {
        if (i2c_master_probe(bus, addr, 50) != ESP_OK) continue;
        i2c_device_config_t dc = {};
        dc.dev_addr_length = I2C_ADDR_BIT_LEN_7;
        dc.device_address = addr;
        dc.scl_speed_hz = 400000;
        if (i2c_master_bus_add_device(bus, &dc, &dev) != ESP_OK) continue;
        uint8_t who = 0;
        if (rd(WHO_AM_I, &who, 1) == ESP_OK && who == 0x33) {
            ok = true;
            ESP_LOGI(TAG, "bulundu, adres 0x%02X", addr);
            return true;
        }
        i2c_master_bus_rm_device(dev);
        dev = nullptr;
    }
    ESP_LOGW(TAG, "LIS3DH bulunamadı - hareket özellikleri kapalı");
    return false;
}

bool present() { return ok; }

void configAwake()
{
    if (!ok) return;
    wr(CTRL_REG1, 0x77);   // 400 Hz, normal mod, XYZ
    wr(CTRL_REG2, 0x00);
    wr(CTRL_REG3, 0x00);   // INT1'e hiçbir şey yönlendirme (D0 sol düğmeye kalsın)
    wr(CTRL_REG4, 0x80);   // BDU, ±2 g
    wr(CTRL_REG5, 0x00);
    wr(CTRL_REG6, 0x02);   // INT aktif düşük
    wr(CLICK_CFG, 0x30);   // Z ekseni tek + çift tıklama (yüze vurmak)
    wr(CLICK_THS, 0x80 | 0x28);  // kilitli, ~640 mg
    wr(TIME_LIMIT, 0x0C);
    wr(TIME_LATENCY, 0x18);
    wr(TIME_WINDOW, 0x60);
    uint8_t dummy; rd(CLICK_SRC, &dummy, 1); rd(INT1_SRC, &dummy, 1);
}

void configSleepMotion(bool enable_int)
{
    if (!ok) return;
    wr(CTRL_REG1, 0x2F);   // 10 Hz, düşük güç, XYZ
    wr(CTRL_REG2, 0x01);   // yüksek geçiren filtre IA1 için (yerçekimini yok say)
    wr(CTRL_REG4, 0x80);
    wr(CTRL_REG5, 0x08);   // INT1 kilitli
    wr(CTRL_REG6, 0x02);   // aktif düşük
    wr(INT1_THS, 0x0A);    // ~160 mg (2 g ölçekte 16 mg/LSB)
    wr(INT1_DURATION, 0x01);
    wr(CLICK_CFG, 0x00);
    uint8_t dummy; rd(REFERENCE, &dummy, 1);  // filtreyi sıfırla
    wr(INT1_CFG, 0x2A);    // X/Y/Z yüksek olayları VEYA
    rd(INT1_SRC, &dummy, 1);
    wr(CTRL_REG3, enable_int ? 0x40 : 0x00);  // I1_IA1
}

bool read(Accel &a)
{
    if (!ok) { a = {0, 0, 1}; return false; }
    uint8_t b[6];
    if (rd(OUT_X_L, b, 6) != ESP_OK) return false;
    auto conv = [](uint8_t lo, uint8_t hi) { return (float)(int16_t)((hi << 8) | lo) / 16384.0f; };
    a.x = conv(b[0], b[1]); a.y = conv(b[2], b[3]); a.z = conv(b[4], b[5]);
    return true;
}

uint8_t clickSource()
{
    if (!ok) return 0;
    uint8_t v = 0; rd(CLICK_SRC, &v, 1); return v;
}

bool motionLatched()
{
    if (!ok) return false;
    uint8_t v = 0; rd(INT1_SRC, &v, 1); return v & 0x40;
}

void powerDown()
{
    if (!ok) return;
    wr(CTRL_REG3, 0x00);
    wr(CTRL_REG1, 0x08);   // ODR 0 = kapalı
}

} // namespace lis3dh
