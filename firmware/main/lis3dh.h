#pragma once
#include <stdint.h>
#include <stdbool.h>

// LIS3DH ivmeölçer (I2C). Uyanıkken 400 Hz + çift/tek dokunma algılama,
// uykuda 10 Hz düşük güç + hareketle INT1 (aktif düşük, kilitli).
namespace lis3dh {

struct Accel { float x, y, z; };   // g cinsinden

bool begin();                       // false: modül bulunamadı
bool present();
void configAwake();                 // 400 Hz, tıklama algılama, INT1 kapalı
void configSleepMotion(bool enable_int);  // 10 Hz düşük güç, hareket kesmesi INT1 (aktif düşük)
bool read(Accel &a);
uint8_t clickSource();              // CLICK_SRC (okuyunca temizlenir). bit4 tek, bit5 çift
bool motionLatched();               // INT1_SRC IA biti (okuyunca temizlenir)
void powerDown();

} // namespace lis3dh
