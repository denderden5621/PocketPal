#!/bin/bash
# Tüm üretilen dosyaları yeniden oluşturur ve dist/PocketPal_Paket.zip paketini hazırlar.
# Kullanım (depo kökünden):  tools/make_package.sh            # her şeyi yeniden üret + paketle
#                            tools/make_package.sh --zip-only # yalnızca paketle
# Gerekenler: python3 + pip install manifold3d trimesh numpy pyvista matplotlib pillow reportlab pypdf, g++ (simülatör), zip
# Yazılımın kendisi ESP-IDF ile ayrıca derlenir (firmware/README.md); paket firmware/prebuilt/ içindeki ikilileri kullanır.
set -euo pipefail
R=$(cd "$(dirname "$0")/.." && pwd)
cd "$R"
if [ "${1:-}" != "--zip-only" ]; then
  echo "== CAD / STL";            python3 cad/keychain_cad.py stl
  echo "== çakışma kontrolü";     python3 cad/check_fit.py stl | tail -1
  echo "== ekran simülatörü";     SIM=$(mktemp -d); firmware/tools/host_sim/build.sh "$SIM"; python3 firmware/tools/host_sim/to_png.py "$SIM" images/screens
  echo "== kablolama şemaları";   python3 cad/wiring_diagrams.py images
  echo "== 3B görseller";         python3 cad/render_images.py stl images images/screens
  echo "== PDF kılavuz";          python3 docs/build_guide.py . docs/Pocket_Pal_Yapim_Kilavuzu.pdf
fi
P=dist/PocketPal_Paket
rm -rf dist && mkdir -p $P/{stl,yazilim/hazir,yazilim/pocketpal,cad,gorseller/ekran}
cp docs/Pocket_Pal_Yapim_Kilavuzu.pdf docs/malzeme_listesi.csv BENIOKU.md LICENSE $P/
cp stl/*.stl stl/ekran_kapagi_sablon.svg $P/stl/
cp firmware/prebuilt/* $P/yazilim/hazir/
cp -r firmware/CMakeLists.txt firmware/README.md firmware/sdkconfig.defaults firmware/main firmware/tools $P/yazilim/pocketpal/
rm -f $P/yazilim/pocketpal/tools/host_sim/sim
cp cad/*.py cad/README.md $P/cad/ && cp docs/build_guide.py $P/cad/kilavuz_uret.py
cp images/*.png $P/gorseller/ && cp images/screens/*.png $P/gorseller/ekran/
find $P -name __pycache__ -prune -exec rm -rf {} +
(cd dist && zip -qr PocketPal_Paket.zip PocketPal_Paket)
ls -la dist/PocketPal_Paket.zip
