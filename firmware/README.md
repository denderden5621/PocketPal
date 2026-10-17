# Pocket Pal yazılımı (ESP-IDF v5.5, ESP32-C6)

Seeed XIAO ESP32-C6 için kedi / puf yıldız anahtarlık yazılımı. Sharp LS013B7DH03 bellek LCD'yi sürer,
LIS3DH ivmeölçerden vuruş/sallama/eğim okur, piezo ile ses çıkarır ve zamanının neredeyse tamamını
derin uykuda geçirir. Uykudayken ekranın 1 Hz EXTCOMIN darbesini çipin düşük güç (LP) RISC-V çekirdeği üretir;
bu yüzden yüz ekranda kalırken ana işlemci tamamen kapalıdır.

## Hızlı yükleme (derlemeden)

Hazır dosya: `prebuilt/pocketpal_tam.bin` (bootloader + bölüm tablosu + uygulama, tek dosya).

* Tarayıcı: Chrome/Edge ile https://espressif.github.io/esptool-js/ → Connect → adres `0x0` → dosya → Program.
* Komut satırı: `python -m esptool --chip esp32c6 write_flash 0x0 pocketpal_tam.bin`

Kart görünmüyorsa XIAO'daki **B (BOOT)** düğmesini basılı tutarak USB'yi takın.

## Derleme

```
# ESP-IDF v5.5 kurulu ve ortamı etkin olmalı (export.sh / ESP-IDF komut istemi)
idf.py set-target esp32c6
idf.py build
idf.py -p <PORT> flash monitor
idf.py merge-bin -o pocketpal_tam.bin      # tek dosyalık ikili (build/ içinde) → prebuilt/ klasörüne kopyalayın
```

Arduino IDE / PlatformIO-Arduino kullanılmaz: Arduino'nun hazır ESP32-C6 kütüphaneleri LP çekirdeği
etkinleştirmez (`CONFIG_ULP_COPROC_TYPE_LP_CORE`).

## Dosyalar

| Dosya | Görev |
|---|---|
| `main/config.h` | **Tüm ayarlar**: pinler, zaman aşımları, gece saatleri, pil eşikleri, ekran yönü |
| `main/main.cpp` | Uyanma nedenine göre akış (soğuk açılış / zamanlayıcı / hareket / düğme) |
| `main/power.cpp` | LP çekirdeği yükleme, derin uyku, uyandırma kaynakları, hareket fırtınası koruması, pil ADC, saat |
| `main/ulp/lp_vcom.c` | LP çekirdek programı: 0,5 sn'de bir EXTCOMIN'i çevirir |
| `main/display.cpp` | Sharp bellek LCD sürücüsü (yalnızca değişen satırlar), çizim, Türkçe 5×7 yazı tipi |
| `main/face.cpp` | 12 ifade, kedi ve yıldız stilleri, konuşma balonları, etkileşimli yüz |
| `main/games.cpp` | Zıpla, Yakala, Hafıza, Tepki, Düello |
| `main/menu.cpp` | Menü, saat ayarı, durum ve rekorlar |
| `main/input.cpp` | Düğmeler (sıçrama önleme, uzun basış, ikili basış), ivmeölçer olayları, eğim yönü (menüden 4 seçenek) |
| `main/lis3dh.cpp` | LIS3DH: uyanıkken 400 Hz + tıklama algılama, uykuda 10 Hz + hareket kesmesi |
| `main/sound.cpp` | Piezo melodileri (LEDC PWM) |
| `main/store.cpp` | Kalıcı ayarlar ve rekorlar (NVS) |
| `tools/make_font.py` | 5×7 yazı tipini (Türkçe harflerle) üretir |
| `tools/host_sim/` | Ekranı bilgisayarda PNG'ye çizen simülatör: `tools/host_sim/build.sh /tmp/sim` sonra `python3 tools/host_sim/to_png.py /tmp/sim ../images/screens` |

## Pin haritası (XIAO ESP32-C6)

| Pin | GPIO | Bağlantı |
|---|---|---|
| D0 | 0 (LP) | Sol düğme + LIS3DH INT1 (1N4148 üzerinden) — derin uyku uyandırma |
| D1 | 1 | Pil bölücü (2 × 1 MΩ) orta noktası |
| D2 | 2 (LP) | Ekran EXTCOMIN (LP çekirdek sürer) |
| D3 | 21 | Sağ düğme |
| D4 / D5 | 22 / 23 | LIS3DH SDA / SCL |
| D6 | 16 | **Boş** (UART TX, açılışta veri basar) |
| D7 | 17 | Piezo |
| D8 / D9 / D10 | 19 / 20 / 18 | Ekran SCLK / SCS / SI |

## Güç davranışı

* Uyanık oturum 20 sn dokunulmazsa biter (`AWAKE_TIMEOUT_MS`).
* Gündüz 2–5 dakikada bir kısa uyanıp göz kırpar (animasyon beklemeleri hafif uykuda); gece (saat ayarlıysa 23–07) saatte bir kontrol eder.
* Hareketle uyanış yalnızca 1,4 sn'lik bir "bakış"tır; düğme ya da çift vuruş gelirse tam uyanır.
* 10 dakikada 6 hareket uyanışı olursa (çanta yürürken sallanıyor) hareketle uyanma 5 dk kapanır;
  fırtınalar sürerse süre 10, 20, 40, 80 dakikaya katlanır.
* Sol düğme 5 sn'den uzun basılı kalırsa (çantada sıkışma) uyandırma yalnızca zamanlayıcıya düşer.
* Pil ~3,3 V altına inince yalnızca sol düğme uyandırır.
* Uykuda düşük tutulan pinlerin (ekran SPI, piezo) iç pull-up'ları kapatılır; açık kalsa pin başına ~70 µA boşa giderdi.
* Hareketle uyanma kapalıyken (menü) LIS3DH tamamen kapatılır.
* Wi-Fi / Bluetooth hiç başlatılmaz. Görev bekçisi (watchdog) donmada yeniden başlatır.

## Doğrulama durumu

Kod ESP-IDF v5.5.6 ile uyarısız derlenir ve ekran çizimleri ana bilgisayar simülatöründe denenmiştir.
Gerçek donanımda ilk kez denerken seri konsolu (`idf.py monitor`) açık tutun: `ekran hazır`, `LIS3DH bulundu`,
`LP çekirdek başladı` satırlarını görmelisiniz.
