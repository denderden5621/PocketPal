#!/bin/sh
# Ekran simülatörünü derle ve çalıştır: ./build.sh <çıktı_klasörü>
set -e
D=$(cd "$(dirname "$0")" && pwd)
M="$D/../../main"
OUT=${1:-$D/out}
mkdir -p "$OUT"
g++ -std=gnu++17 -O1 -w -I"$D/stubs" -I"$M" "$D/sim.cpp" "$M/display.cpp" "$M/face.cpp" "$M/games.cpp" "$M/menu.cpp" -o "$D/sim" -lm
"$D/sim" "$OUT"
