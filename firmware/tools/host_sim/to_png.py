"""PBM ekran dökümlerini bellek-LCD görünümlü PNG'ye çevirir. Kullanım: python3 to_png.py <pbm_klasörü> <png_klasörü>"""
import sys, os, glob
from PIL import Image
src, dst = sys.argv[1], sys.argv[2]
os.makedirs(dst, exist_ok=True)
S = 3
for f in sorted(glob.glob(os.path.join(src, "*.pbm"))):
    im = Image.open(f).convert("L")
    w, h = im.size
    out = Image.new("RGB", (w * S + 24, h * S + 24), (120, 124, 120))
    lcd = Image.new("RGB", (w * S, h * S), (214, 218, 208))
    px = im.load(); lp = lcd.load()
    for y in range(h):
        for x in range(w):
            if px[x, y] < 128:
                for dy in range(S):
                    for dx in range(S):
                        lp[x * S + dx, y * S + dy] = (38, 42, 40)
    out.paste(lcd, (12, 12))
    out.save(os.path.join(dst, os.path.basename(f)[:-4] + ".png"))
print("ok")
