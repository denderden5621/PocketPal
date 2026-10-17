"""
Kablolama şemaları (2B, Türkçe). Kullanım: python3 wiring_diagrams.py <cikti_klasoru>
  20_kablolama_semasi.png  tüm bağlantılar
  21_fpc_adaptor.png       ekran adaptörü: köprüler ve iki olası pin sırası
  22_lis3dh_diyot.png      ivmeölçer + diyot yönü
  23_guc_bolucu.png        pil, anahtar, pil ölçüm bölücüsü
"""
import sys, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle, Polygon

OUT = sys.argv[1] if len(sys.argv) > 1 else "images"
os.makedirs(OUT, exist_ok=True)
plt.rcParams["font.family"] = "DejaVu Sans"

C = dict(v3="#D93A3A", gnd="#1E1E1E", sclk="#E8A317", si="#2E9E4F", scs="#2F6FD6", vcom="#9B59B6",
         sda="#16A085", scl="#D35400", wake="#AEB6BA", btn="#5F6A6A", piezo="#B7950B", bat="#E74C3C",
         adc="#8B5A2B", board="#1F3D7A", pad="#E8C870", mod_lis="#5B3F8C", mod_ad="#2E7D4F")


def canvas(w=16, h=11, xl=160, yl=110, title=None, sub=None):
    fig = plt.figure(figsize=(w, h), dpi=110)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, xl); ax.set_ylim(0, yl); ax.axis("off")
    ax.set_aspect("equal")
    if title:
        ax.text(3, yl - 4, title, fontsize=20, fontweight="bold", va="top")
    if sub:
        ax.text(3, yl - 9.5, sub, fontsize=11.5, color="#444", va="top")
    return fig, ax


def box(ax, x, y, w, h, fc, label=None, lc="white", fs=12, r=1.5, ec="#333"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc=fc, ec=ec, lw=1.2, zorder=2))
    if label:
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", color=lc, fontsize=fs, fontweight="bold", zorder=3)


def pad(ax, x, y, name, side, fs=11, col=C["pad"]):
    ax.add_patch(Circle((x, y), 1.05, fc=col, ec="#7a5c00", lw=1, zorder=4))
    if side == "l":
        ax.text(x - 2.0, y, name, ha="right", va="center", fontsize=fs, fontweight="bold", zorder=4)
    elif side == "r":
        ax.text(x + 2.0, y, name, ha="left", va="center", fontsize=fs, fontweight="bold", zorder=4)
    elif side == "in_l":
        ax.text(x + 2.0, y, name, ha="left", va="center", fontsize=fs, fontweight="bold", color="white", zorder=4)
    elif side == "in_r":
        ax.text(x - 2.0, y, name, ha="right", va="center", fontsize=fs, fontweight="bold", color="white", zorder=4)


def wire(ax, pts, col, lw=3.2, label=None, lpos=None, lfs=9.5):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    ax.plot(xs, ys, color="white", lw=lw + 2.4, solid_capstyle="round", solid_joinstyle="round", zorder=5)
    ax.plot(xs, ys, color=col, lw=lw, solid_capstyle="round", solid_joinstyle="round", zorder=6)
    for p in (pts[0], pts[-1]):
        ax.add_patch(Circle(p, 0.55, fc=col, ec="white", lw=0.8, zorder=7))
    if label:
        if lpos is None:
            i = len(pts) // 2
            lpos = ((pts[i - 1][0] + pts[i][0]) / 2, (pts[i - 1][1] + pts[i][1]) / 2)
        ax.text(lpos[0], lpos[1], label, fontsize=lfs, ha="center", va="center", color=col, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=col, lw=0.8), zorder=8)


def diode(ax, x0, y0, x1, y1, label=True):
    """Yatay 1N4148: (x0,y0) anot -> (x1,y1) katot. Siyah bant katotta."""
    xm = (x0 + x1) / 2
    ax.add_patch(FancyBboxPatch((xm - 3.2, y0 - 1.1), 6.4, 2.2, boxstyle="round,pad=0,rounding_size=1.0", fc="#F4A261", ec="#7a3d00", lw=1, zorder=9))
    bx = xm + 1.7 if x1 > x0 else xm - 2.4
    ax.add_patch(Rectangle((bx, y0 - 1.1), 0.7, 2.2, fc="#111", zorder=10))
    if label:
        ax.text(xm, y0 + 2.4, "1N4148", fontsize=9, ha="center", fontweight="bold", zorder=10)
        ax.text(bx + 0.35, y0 - 2.6, "bant", fontsize=8.5, ha="center", zorder=10)


def resistor(ax, x, y, vertical=True, label="1 MΩ"):
    if vertical:
        ax.add_patch(FancyBboxPatch((x - 1.0, y - 3.0), 2.0, 6.0, boxstyle="round,pad=0,rounding_size=0.8", fc="#E9D8A6", ec="#7a6000", lw=1, zorder=9))
        for i, c in enumerate(["#8B4513", "#111", "#2E9E4F"]):
            ax.add_patch(Rectangle((x - 1.0, y + 1.6 - i * 1.2), 2.0, 0.45, fc=c, zorder=10))
        ax.text(x + 1.8, y, label, fontsize=9.5, va="center", fontweight="bold", zorder=10)
    else:
        ax.add_patch(FancyBboxPatch((x - 3.0, y - 1.0), 6.0, 2.0, boxstyle="round,pad=0,rounding_size=0.8", fc="#E9D8A6", ec="#7a6000", lw=1, zorder=9))
        for i, c in enumerate(["#8B4513", "#111", "#2E9E4F"]):
            ax.add_patch(Rectangle((x - 1.6 + i * 1.2, y - 1.0), 0.45, 2.0, fc=c, zorder=10))
        ax.text(x, y + 2.2, label, fontsize=9.5, ha="center", fontweight="bold", zorder=10)


def tact(ax, x, y, name):
    ax.add_patch(Rectangle((x - 3, y - 3), 6, 6, fc="#2b2b2b", ec="#000", zorder=3))
    ax.add_patch(Circle((x, y), 1.6, fc="#555", ec="#000", zorder=4))
    ax.text(x, y + 5.0, name, fontsize=11.5, ha="center", fontweight="bold")


# ---------------------------------------------------------------------------
# XIAO (üstten görünüm, USB-C yukarıda) — Seeed resmi pin sırası
names = {1: "SCLK", 2: "SI", 3: "SCS", 4: "EXTCOMIN", 5: "DISP", 6: "VDDA", 7: "VDD", 8: "EXTMODE", 9: "VSS", 10: "VSSA"}
XL = ["D0", "D1", "D2", "D3", "D4", "D5", "D6"]
XR = ["5V", "GND", "3V3", "D10", "D9", "D8", "D7"]


def xiao(ax, x0, y0, w=26, h=42, label="XIAO ESP32-C6\n(üstten, USB-C yukarıda)", label_y=None):
    box(ax, x0, y0, w, h, C["board"], r=2.0)
    ax.add_patch(FancyBboxPatch((x0 + w / 2 - 4.5, y0 + h - 2.5), 9, 5, boxstyle="round,pad=0,rounding_size=1.2", fc="#C0C4C8", ec="#555", zorder=3))
    ax.text(x0 + w / 2, y0 + h + 3.6, "USB-C", ha="center", fontsize=9.5)
    ly = y0 + h / 2 - 1 if label_y is None else label_y
    ax.text(x0 + w / 2, ly, label, ha="center", va="center", color="white", fontsize=10.5, fontweight="bold", zorder=3)
    pins = {}
    for i, n in enumerate(XL):
        y = y0 + h - 7 - i * 5
        pad(ax, x0 + 1.8, y, n, "in_l", fs=10)
        pins[n] = (x0 + 1.8, y)
    for i, n in enumerate(XR):
        y = y0 + h - 7 - i * 5
        pad(ax, x0 + w - 1.8, y, n, "in_r", fs=10)
        pins[n] = (x0 + w - 1.8, y)
    return pins


# ======================= 20: XIAO bağlantı haritası =======================
fig, ax = canvas(16, 10.4, 160, 104, title="Bağlantı haritası – XIAO ESP32-C6",
                 sub="Renkler öneridir: kırmızı = 3V3 / pil +, siyah = GND, beyaz = D0 hattı. Adaptör pin no.lar A tipi adaptör içindir (B tipinde: 11 − no.).")
P = xiao(ax, 67, 25, w=26, h=51, label="XIAO ESP32-C6 · üstten\nmetal kalkan size bakar", label_y=29)
LT = {"D0": ("Sol düğme  +  diyot anodu (beyaz)", "#7D8A8F"),
      "D1": ("Pil bölücü orta noktası (kahverengi)", C["adc"]),
      "D2": ("Adaptör pin 4  (EXTCOMIN)", C["vcom"]),
      "D3": ("Sağ düğme (gri)", C["btn"]),
      "D4": ("LIS3DH  SDA", C["sda"]),
      "D5": ("LIS3DH  SCL", C["scl"]),
      "D6": ("BOŞ  (TX – bağlamayın)", "#999999")}
RT = {"5V": ("BOŞ", "#999999"),
      "GND": ("Adaptör pin 9  ·  düğme ortak  ·  piezo siyah", C["gnd"]),
      "3V3": ("Adaptör pin 7", C["v3"]),
      "D10": ("Adaptör pin 2  (SI)", C["si"]),
      "D9": ("Adaptör pin 3  (SCS)", C["scs"]),
      "D8": ("Adaptör pin 1  (SCLK)", C["sclk"]),
      "D7": ("Piezo kırmızı", C["piezo"])}
for n, (txt, col) in LT.items():
    x, y = P[n]
    ax.plot([x, 52], [y, y], color=col, lw=3.4, solid_capstyle="round", zorder=5)
    ax.text(51, y, txt, ha="right", va="center", fontsize=11.5, color=col if col != "#999999" else "#777", fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=col, lw=1.0))
for n, (txt, col) in RT.items():
    x, y = P[n]
    ax.plot([x, 108], [y, y], color=col, lw=3.4, solid_capstyle="round", zorder=5)
    ax.text(109, y, txt, ha="left", va="center", fontsize=11.5, color=col if col != "#999999" else "#777", fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=col, lw=1.0))
# arka yüz pedleri
box(ax, 67, 5, 26, 15, "#123060", r=1.5)
ax.text(80, 17.5, "ARKA YÜZ", ha="center", color="white", fontsize=10, fontweight="bold", zorder=4)
pad(ax, 74, 11, "", "r"); pad(ax, 86, 11, "", "r")
ax.text(74, 14.2, "BAT+", ha="center", color="white", fontsize=10, fontweight="bold", zorder=5)
ax.text(86, 14.2, "BAT−", ha="center", color="white", fontsize=10, fontweight="bold", zorder=5)
ax.plot([74, 74, 52], [11, 9, 9], color=C["bat"], lw=3.4, zorder=5)
ax.text(51, 9, "Anahtarın kenar bacağı  +  R1 (1 MΩ)", ha="right", va="center", fontsize=11.5, color=C["bat"], fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=C["bat"], lw=1.0))
ax.plot([86, 86, 108], [11, 9, 9], color=C["gnd"], lw=3.4, zorder=5)
ax.text(109, 9, "Pil siyah  +  R2 (1 MΩ)", ha="left", va="center", fontsize=11.5, color=C["gnd"], fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=C["gnd"], lw=1.0))
ax.text(80, 2.2, "Pedlerin yeri kartın arka yüzünde yazılıdır. Pil kablolarını kartı taşıyıcıya takmadan ÖNCE lehimleyin.",
        ha="center", fontsize=10, color="#333")
# küçük not kutusu
ax.text(3, 86, "Bir pine iki kablo girerse:", fontsize=10.5, fontweight="bold", color="#333")
ax.text(3, 82.5, "uçları 3 mm soyun, birbirine bükün,\nbirlikte deliğe sokup lehimleyin.", fontsize=10, color="#333", va="top")
ax.text(118, 86, "Toplam: 17 kablo + 1 diyot + 2 direnç", fontsize=10.5, fontweight="bold", color="#333")
ax.text(118, 82.5, "Ayrıntılar: ekran adaptörü, ivmeölçer\nve güç şemaları (sonraki sayfalar).", fontsize=10, color="#333", va="top")
fig.savefig(os.path.join(OUT, "20_kablolama_semasi.png"), dpi=110)
plt.close(fig)
print("yazıldı 20_kablolama_semasi")

# ======================= 21: FPC adaptörü yakın plan =======================
fig, ax = canvas(14, 8.6, 140, 86, title="Ekran adaptörü – köprüler ve pin sırası",
                 sub="Adaptör kartındaki numaralara göre. Önce şerit kablonun ucundaki 1 / 10 işaretini kontrol edin.")
for col_i, (title, order) in enumerate([("A) Şeridin 1 numaralı ucu adaptörün 1. pininde", list(range(1, 11))),
                                         ("B) Ters (1 ↔ 10): şeridin 1 numaralı ucu adaptörün 10. pininde", list(range(10, 0, -1)))]):
    x0 = 6 + col_i * 68
    ax.text(x0, 70, title, fontsize=11, fontweight="bold")
    box(ax, x0 + 2, 8, 14, 56, C["mod_ad"], r=1.2)
    conn = {}
    for i in range(10):
        adapter_pin = i + 1
        panel_pin = order[i]
        y = 60 - i * 5.3
        pad(ax, x0 + 4, y, f"{adapter_pin}", "in_l", fs=10)
        conn[adapter_pin] = (x0 + 4, y)
        nm = names[panel_pin]
        if panel_pin in (5, 6, 7, 8):
            dest, col = {5: "3V3 köprü", 6: "3V3 köprü", 7: "3V3 köprü + XIAO 3V3", 8: "3V3 köprü + LIS3DH VIN"}[panel_pin], C["v3"]
        elif panel_pin in (9, 10):
            dest, col = {9: "GND köprü + XIAO GND", 10: "GND köprü + LIS3DH GND"}[panel_pin], C["gnd"]
        else:
            dest, col = {1: ("XIAO D8", C["sclk"]), 2: ("XIAO D10", C["si"]), 3: ("XIAO D9", C["scs"]), 4: ("XIAO D2", C["vcom"])}[panel_pin]
        ax.text(x0 + 18.5, y, f"ekran {panel_pin}: {nm}", fontsize=10, va="center")
        ax.text(x0 + 42, y, "→ " + dest, fontsize=10, va="center", color=col, fontweight="bold")
    # köprüleri çiz
    groups = {}
    for i in range(10):
        pp = order[i]
        g = "v" if pp in (5, 6, 7, 8) else ("g" if pp in (9, 10) else None)
        if g: groups.setdefault(g, []).append(i + 1)
    for g, pins in groups.items():
        col = C["v3"] if g == "v" else C["gnd"]
        ys = [conn[p][1] for p in pins]
        ax.plot([x0 + 13.5, x0 + 13.5], [min(ys), max(ys)], color=col, lw=4, zorder=6, solid_capstyle="round")
        for p in pins:
            ax.plot([conn[p][0] + 4.6, x0 + 13.5], [conn[p][1], conn[p][1]], color=col, lw=2.2, zorder=6)
    ax.text(x0 + 2, 3.5, "Köprü: komşu pinleri tek kabloyla ya da lehim damlasıyla birleştirin.", fontsize=9, color="#333")
fig.savefig(os.path.join(OUT, "21_fpc_adaptor.png"), dpi=110)
plt.close(fig)
print("yazıldı 21_fpc_adaptor")

# ======================= 22: LIS3DH + diyot =======================
fig, ax = canvas(14, 8.2, 140, 82, title="İvmeölçer ve uyandırma diyotu",
                 sub="Sol düğme ve INT1 aynı uyandırma pinini (D0) paylaşır; diyot ikisini ayırır. Adaptör pin no.lar A tipi içindir (B tipinde 8 → 3, 10 → 1).")
box(ax, 6, 10, 26, 50, C["mod_lis"], r=1.5)
ax.text(19, 62.5, "LIS3DH modülü", ha="center", fontsize=12, fontweight="bold")
LP = {}
for i, n in enumerate(["VIN", "GND", "SCL", "SDA", "SDO", "CS", "INT1"]):
    y = 54 - i * 6.5
    pad(ax, 29, y, n, "in_r", fs=10.5)
    LP[n] = (29, y)
ax.add_patch(Rectangle((10, 30), 6, 6, fc="#111", zorder=3))
ax.add_patch(Circle((11, 52), 1.3, fc="#E74C3C", ec="#600", zorder=3))
ax.text(11, 47.5, "LED", fontsize=8.5, ha="center", color="white", zorder=4)
ax.text(4, 5.5, "Modülde güç LED'i varsa sökün (yoksa pil ~10 günde biter).", fontsize=9.5, ha="left", color="#B03A2E", fontweight="bold", zorder=4)
# CS-VIN köprüsü modülün üzerinde
ax.plot([LP["CS"][0] + 1.1, 34, 34, LP["VIN"][0] + 1.1], [LP["CS"][1], LP["CS"][1], LP["VIN"][1], LP["VIN"][1]], color=C["v3"], lw=2.4, ls="--", zorder=6)
ax.text(34.8, LP["SDO"][1] + 3.3, "CS → VIN\nkısa köprü", fontsize=9, color=C["v3"], fontweight="bold", va="center")
ax.text(34.8, LP["SDO"][1] - 0.6, "SDO: boş", fontsize=9, color="#666", va="center")
def tag(y, x0, txt, col, x1=64):
    ax.plot([x0, x1], [y, y], color=col, lw=3.2, zorder=5, solid_capstyle="round")
    ax.text(x1 + 1, y, txt, ha="left", va="center", fontsize=11, color=col, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=col, lw=1.0))
tag(LP["VIN"][1], 30.1, "→ adaptör pin 8 (3V3)", C["v3"], 46)
tag(LP["GND"][1], 30.1, "→ adaptör pin 10 (GND)", C["gnd"], 46)
tag(LP["SCL"][1], 30.1, "→ XIAO D5", C["scl"], 46)
tag(LP["SDA"][1], 30.1, "→ XIAO D4", C["sda"], 46)
# INT1 -> diyot -> D0
y = LP["INT1"][1]
ax.plot([30.1, 72], [y, y], color=C["wake"], lw=3.2, zorder=5)
diode(ax, 82, y, 72, y)
ax.plot([85.2, 98], [y, y], color=C["wake"], lw=3.2, zorder=5)
ax.text(98.8, y, "→ XIAO D0", ha="left", va="center", fontsize=11, color="#7D8A8F", fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=C["wake"], lw=1.0))
ax.text(76.5, y - 5.5, "katot (bant) INT1 tarafında   ·   anot D0 tarafında", fontsize=9.5, ha="center", color="#555")
# düğme
tact(ax, 84, 40, "SOL düğme")
ax.plot([87, 98], [39, 39], color=C["wake"], lw=3.2, zorder=5)
ax.text(98.8, 39, "→ XIAO D0", ha="left", va="center", fontsize=11, color="#7D8A8F", fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=C["wake"], lw=1.0))
ax.plot([81, 76, 76], [41, 41, 34], color=C["gnd"], lw=3.2, zorder=5)
ax.text(76, 31.5, "→ GND", ha="center", va="center", fontsize=10.5, color=C["gnd"], fontweight="bold")
ax.text(110, 60, "D0 deliğine iki şey girer: sol düğmenin kablosu ve diyotun anot bacağı.\nÖnce ikisini birlikte büküp sokun, sonra lehimleyin.\n"
        "Diyot ters takılırsa düğme yine çalışır ama sallayınca/vurunca uyanma çalışmaz.", fontsize=9.5, ha="center", color="#222")
fig.savefig(os.path.join(OUT, "22_lis3dh_diyot.png"), dpi=110)
plt.close(fig)
print("yazıldı 22_lis3dh_diyot")

# ======================= 23: güç + bölücü =======================
fig, ax = canvas(14, 8.2, 140, 82, title="Pil, açma/kapama anahtarı ve pil ölçümü",
                 sub="Pil artısı anahtardan geçer. İki 1 MΩ direnç pil gerilimini yarıya bölüp D1'e verir (sürekli ~2 µA).")
box(ax, 4, 30, 28, 20, "#7FA7C9", "LiPo 502030\n3.7 V ~250 mAh\n(koruma devreli)", lc="#0b2a4a", fs=10.5)
# anahtar
box(ax, 42, 44, 15, 8, "#2C5BA8", r=0.8)
ax.add_patch(Rectangle((47.6, 46), 3.8, 4, fc="#EDEDED", zorder=4))
ax.text(49.5, 55, "sürgülü anahtar", ha="center", fontsize=10.5, fontweight="bold")
for xx in (45, 49.5, 54):
    ax.plot([xx, xx], [44, 40.5], color="#888", lw=2.6, zorder=3)
ax.text(45.6, 42.2, "boş", ha="left", fontsize=8.5, color="#666")
ax.text(50.1, 42.2, "orta", ha="left", fontsize=8.5)
ax.text(54.6, 42.2, "kenar", ha="left", fontsize=8.5)
wire(ax, [(32, 45), (37, 45), (37, 34), (49.5, 34), (49.5, 40.5)], C["bat"], label="pil kırmızı", lpos=(39, 30.5))
# BAT+ düğümü
NX = 72
wire(ax, [(54, 40.5), (54, 36), (NX, 36)], C["bat"])
ax.add_patch(Circle((NX, 36), 0.9, fc=C["bat"], zorder=8))
ax.text(NX - 2, 33.2, "BAT+ hattı", ha="right", fontsize=9.5, color=C["bat"], fontweight="bold")
# XIAO arka
box(ax, 100, 14, 34, 40, "#123060", r=1.5)
ax.text(117, 50, "XIAO ARKA YÜZÜ", ha="center", color="white", fontsize=10.5, fontweight="bold", zorder=4)
pad(ax, 108, 36, "", "r"); pad(ax, 108, 22, "", "r")
ax.text(111, 36, "BAT+", color="white", fontsize=10.5, fontweight="bold", va="center", zorder=5)
ax.text(111, 22, "BAT−", color="white", fontsize=10.5, fontweight="bold", va="center", zorder=5)
ax.text(117, 16.5, "(yerleri kartta yazılı)", ha="center", color="#cdd", fontsize=8.5, zorder=5)
wire(ax, [(NX, 36), (108, 36)], C["bat"])
# bölücü: NX'ten yukarı R1, orta nokta, R2 BAT- hattına
wire(ax, [(NX, 36), (NX, 62), (80, 62)], C["bat"], lw=2.6)
resistor(ax, 83, 62, vertical=False, label="R1 1 MΩ")
wire(ax, [(86, 62), (92, 62)], C["adc"], lw=2.6)
ax.add_patch(Circle((92, 62), 0.9, fc=C["adc"], zorder=8))
wire(ax, [(92, 62), (92, 70), (97, 70)], C["adc"], lw=2.6)
ax.text(98, 70, "orta nokta → XIAO D1", ha="left", va="center", fontsize=11, color=C["adc"], fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=C["adc"], lw=1.0))
wire(ax, [(92, 62), (92, 58)], C["adc"], lw=2.6)
resistor(ax, 92, 55, vertical=True, label="R2 1 MΩ")
wire(ax, [(92, 52), (92, 26), (96, 26), (96, 22), (108, 22)], C["gnd"], lw=2.6)
wire(ax, [(32, 34), (34, 34), (34, 22), (96, 22)], C["gnd"], label="pil siyah", lpos=(60, 22))
ax.add_patch(Circle((96, 22), 0.9, fc=C["gnd"], zorder=8))
ax.text(70, 5, "İpucu: R1 ve R2'yi uç uca lehimleyin (orta nokta), makaronla sarın. R1'in boş ucu anahtarın kenar bacağına,\n"
        "R2'nin boş ucu BAT− pedine, orta noktadan D1'e tek kablo. USB ile şarj ederken anahtar AÇIK olmalıdır.",
        fontsize=10, ha="center", color="#222")
fig.savefig(os.path.join(OUT, "23_guc_bolucu.png"), dpi=110)
plt.close(fig)
print("yazıldı 23_guc_bolucu")
