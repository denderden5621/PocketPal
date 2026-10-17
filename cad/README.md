# CAD ve görsel betikleri

Parametrik kasa modeli (Python 3 + manifold3d) ve kılavuz görsellerini üreten betikler. Tümü depo kökünden çalıştırılır.

```sh
pip install manifold3d trimesh numpy pyvista matplotlib pillow
python3 cad/keychain_cad.py stl                              # tüm STL'ler + stl/_montaj_konumu/ (render için)
python3 cad/check_fit.py stl                                 # parçalar ve modül zarfları çakışıyor mu
python3 cad/wiring_diagrams.py images                        # kablolama şemaları
python3 cad/render_images.py stl images images/screens       # 3B montaj görselleri
```

Önemli ölçüler `keychain_cad.py` başındadır: `TOTAL_H` (kalınlık), `CORE_HALF` (ortak elektronik çekirdeği),
`CAT_BTNS` / `STAR_BTNS` (düğme konumları), `star_outline()` içindeki `R` / `r` (yıldız boyutu), `PILLARS` (vida sütunları).

| Parça | Baskı yönü |
|---|---|
| `kedi_on_kabuk.stl` / `yildiz_on_kabuk.stl` | yüzü tablada |
| `tasiyici.stl` | arka uçları tablada (taban kısa köprülerle basılır) |
| `arka_kapak.stl` | düz yüzü tablada |
| `dugme_kapagi.stl` (2 adet) | flanş tablada |
