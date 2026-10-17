# Pocket Pal – Kedi & Puf Yıldız Anahtarlık

Çantaya takılan, yüzü her zaman ekranda duran ESP32-C6 anahtarlık. Burada bir tane (ya da arkadaşlarla
birkaç tane) yapmak için gereken her şey var.

**Buradan başlayın:** `Pocket_Pal_Yapim_Kilavuzu.pdf` (GitHub deposunda `docs/` klasöründe)

| Zip pakette | GitHub deposunda | İçerik |
|---|---|---|
| `Pocket_Pal_Yapim_Kilavuzu.pdf` | `docs/` | Adım adım görselli yapım kılavuzu (malzeme, baskı, yazılım, kablolama, test, montaj, kullanım) |
| `malzeme_listesi.csv` | `docs/` | Malzeme listesi, fiyatlar ve Türkiye'deki satıcılar (Excel'de açılır) |
| `stl/` | `stl/` | Baskıya hazır STL'ler (doğru yönde) ve ekran koruyucu kesim şablonu |
| `yazilim/hazir/` | `firmware/prebuilt/` | Hazır yazılım: `pocketpal_tam.bin` → tarayıcıdan 0x0 adresine yükleyin |
| `yazilim/pocketpal/` | `firmware/` | Tam kaynak kodu (ESP-IDF v5.5 projesi) ve README |
| `cad/` | `cad/` | Parametrik CAD ve görsel üretim betikleri (Python) |
| `gorseller/` | `images/` | Kılavuzdaki görseller ve ekran görüntüleri |

## Kısa yol

1. Parçaları sipariş edin (ekranın gelmesi 7–10 iş günü sürer; önce onu sipariş edin).
2. `stl/` içindeki 5 dosyayı PLA ile basın (destek gerekmez).
3. XIAO'ya `pocketpal_tam.bin` dosyasını yükleyin.
4. Kılavuzun 5. bölümündeki tabloya göre kablolayın (pil en son), 6. bölümdeki testleri yapın.
5. 7. bölüme göre kasaya yerleştirin, 4 vidayı takın.

Ölçüler: kedi 54 × 59 × 15,7 mm · yıldız 73 × 70 × 15,7 mm · parça maliyeti ≈ 1.870–2.100 TL (ekran 10+ adet alınırsa ≈ 1.660–1.890 TL).

Paketi yeniden üretmek için depo kökünde: `tools/make_package.sh` → `dist/PocketPal_Paket.zip`.
