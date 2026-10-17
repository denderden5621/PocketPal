"""Adafruit GFX 'classic' 5x7 font (BSD) -> font5x7.h, Türkçe harfler eklenir.
Kullanım: python3 make_font.py glcdfont.c ../main/font5x7.h"""
import re, sys
src = open(sys.argv[1]).read()
body = src[src.index("font[]"):]
vals = [int(v, 16) for v in re.findall(r"0x([0-9A-Fa-f]{2})", body)]
assert len(vals) >= 256 * 5
g = {c: vals[c * 5:c * 5 + 5] for c in range(256)}
def mod(base, adds):
    v = list(g[ord(base)])
    for col, bits in adds: v[col] |= bits
    return v
tr = {
    "ç": mod("c", [(2, 0x80)]), "Ç": mod("C", [(2, 0x80)]),
    "ş": mod("s", [(2, 0x80)]), "Ş": mod("S", [(2, 0x80)]),
    "ı": [0x00, 0x44, 0x7C, 0x40, 0x00], "İ": [0x00, 0x44, 0x7D, 0x44, 0x00],
    "ö": mod("o", [(1, 0x02), (3, 0x02)]), "Ö": [0x38, 0x45, 0x44, 0x45, 0x38],
    "ü": mod("u", [(1, 0x01), (3, 0x01)]), "Ü": [0x3C, 0x41, 0x40, 0x41, 0x3C],
    "ğ": mod("g", [(1, 0x01), (2, 0x02), (3, 0x01)]), "Ğ": [0x38, 0x45, 0x45, 0x55, 0x74],
}
out = ["// Otomatik üretildi: tools/make_font.py", "// 5x7 yazı tipi: Adafruit GFX 'classic' font (BSD lisansı, FONT_LICENSE_Adafruit_BSD.txt)",
       "#pragma once", "#include <stdint.h>", "", "// ASCII 32..126 (95 karakter) + Türkçe harfler, karakter başına 5 sütun, bit0 = üst satır",
       "static const uint8_t FONT5X7[][5] = {"]
for c in range(32, 127):
    out.append("    {" + ", ".join(f"0x{b:02X}" for b in g[c]) + "}," + f" // '{chr(c) if chr(c) not in chr(92)+chr(39) else ' '}'")
keys = list(tr.keys())
for k in keys:
    out.append("    {" + ", ".join(f"0x{b:02X}" for b in tr[k]) + "}," + f" // {k}")
out.append("};")
out.append("")
out.append("// UTF-8 kod noktası -> FONT5X7 indeksi (Türkçe harfler)")
out.append("static const struct { uint16_t cp; uint8_t idx; } FONT_TR_MAP[] = {")
for i, k in enumerate(keys):
    out.append(f"    {{0x{ord(k):04X}, {95 + i}}}, // {k}")
out.append("};")
out.append(f"static const int FONT_TR_COUNT = {len(keys)};")
open(sys.argv[2], "w").write("\n".join(out) + "\n")
print("ok", len(keys), "türkçe glif")
