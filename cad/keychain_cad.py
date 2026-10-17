"""
Pocket Pal anahtarlık - parametrik CAD (manifold3d)
Tüm parçaları STL olarak üretir:
  tasiyici.stl      ortak iç taşıyıcı (kedi ve yıldız için aynı)
  arka_kapak.stl    ortak arka kapak
  kedi_on_kabuk.stl kedi ön kabuğu
  yildiz_on_kabuk.stl puf yıldız ön kabuğu
  dugme_kapagi.stl  düğme kapağı (2 adet bas)
  ekran_kapagi_sablon.svg  şeffaf ekran koruyucu kesim şablonu

Koordinatlar (mm): X sağa, Y yukarı (yüz önden bakılırken), Z öne doğru.
Z=0 arka yüz, Z=TOTAL_H ön yüz. Ön kabuk yüzü aşağı bakacak şekilde basılır.
Kullanım: python3 keychain_cad.py <çıktı_klasörü>
"""
import sys, os, math
import numpy as np
import trimesh
from manifold3d import CrossSection, Manifold, JoinType

OUT = sys.argv[1] if len(sys.argv) > 1 else "stl"
os.makedirs(OUT, exist_ok=True)

# ---------------- ana ölçüler ----------------
SEG = 96                      # daire segmenti
CORE_HALF = 23.4              # kabuk içi çekirdek boşluğu (squircle yarı genişlik)
CORE_N = 4.0                  # squircle üssü
CHASSIS_HALF = CORE_HALF - 0.15

BACK_T = 1.6                  # arka plaka
REAR_H = 6.0                  # arka katman (pil, XIAO, piezo)
FLOOR_T = 1.0                 # şasi tabanı
FRONT_CLR = 4.0               # ön katman (FPC adaptörü, LIS3DH)
PANEL_T = 0.75                # Sharp LS013B7DH03 kalınlığı
COVER_T = 0.7                 # şeffaf koruyucu
WALL_T = 1.6                  # ön duvar

Z_FLOOR0 = BACK_T + REAR_H                 # 7.6
Z_FLOOR1 = Z_FLOOR0 + FLOOR_T              # 8.6
Z_LEDGE = Z_FLOOR1 + FRONT_CLR             # 12.6 panel oturma yüzeyi
Z_CHASSIS_TOP = Z_LEDGE + PANEL_T + COVER_T  # 14.05
Z_FRONT_IN = Z_CHASSIS_TOP
TOTAL_H = Z_FRONT_IN + WALL_T             # 15.65

# Ekran modülü (26.6 x 30.3), aktif alan 23.04 kare, FPC altta
PANEL_W, PANEL_H = 26.6, 30.3
ACTIVE = 23.04
ACT_CY = -2.5                             # aktif alan merkezi Y
ACT_TOP_MARGIN = 1.8
PANEL_TOP = ACT_CY + ACTIVE / 2 + ACT_TOP_MARGIN   # 10.82
PANEL_BOT = PANEL_TOP - PANEL_H                    # -19.48
PANEL_CY = (PANEL_TOP + PANEL_BOT) / 2
LIP_CLR = 0.3
LIP_T = 0.8

# Vida sütunları (kabuktan şasiye), M2 kendinden kılavuzlu
PILLARS = [(-19.5, -3.0), (19.5, -3.0), (-18.5, -13.0), (18.5, -13.0)]
PILLAR_D = 4.6
PILOT_D = 1.7
SCREW_CLR_D = 2.4
SCREW_HEAD_D = 4.2

# Düğme yuvaları (kabuğa göre değişir)
SW = 6.0            # 6x6 tact switch
SW_POCKET_WALL = 0.8
SW_POCKET_IN = SW + 0.3
SW_BODY_Z0 = 9.2
CAT_BTNS = [(-14.0, 16.0), (14.0, 16.0)]
STAR_BTNS = [(-18.7, 6.0), (18.7, 6.0)]
CAP_SHAFT_D = 4.6
CAP_HOLE_D = 5.0
CAP_FLANGE_D = 7.2
CAP_CB_D = 7.8
CAP_CB_DEPTH = 0.75

# XIAO ESP32-C6 (21 x 17.5), USB-C alt kenarda
XIAO_W, XIAO_L = 17.5, 21.0
XIAO_Y0, XIAO_Y1 = -22.4, -22.4 + XIAO_L
XIAO_Z0 = 3.1                              # kart alt yüzü (alt pedlere kablo payı), bileşenler öne
XIAO_PCB = 1.2
USB_W, USB_H = 9.0, 3.2
USB_CZ = XIAO_Z0 + XIAO_PCB + USB_H / 2    # ~6.2

# Pil 502030 (20.5 x 31 x 5.3), yatay, üst yarıda
BAT_W, BAT_H = 31.5, 21.0
BAT_CX, BAT_CY = 0.0, 10.5

# Sürgülü anahtar (SS12D00), kolu arkaya bakar
SLIDE_CX, SLIDE_CY = -12.8, -6.7


def squircle(ax, ay, n=4.0, cx=0.0, cy=0.0, pts=240):
    t = np.linspace(0, 2 * np.pi, pts, endpoint=False)
    c, s = np.cos(t), np.sin(t)
    x = ax * np.sign(c) * np.abs(c) ** (2.0 / n) + cx
    y = ay * np.sign(s) * np.abs(s) ** (2.0 / n) + cy
    return CrossSection([np.column_stack([x, y])])


def rrect(w, h, r, cx=0.0, cy=0.0):
    r = min(r, w / 2 - 0.01, h / 2 - 0.01)
    cs = CrossSection.square([w - 2 * r, h - 2 * r], center=True).offset(r, JoinType.Round, circular_segments=SEG)
    return cs.translate([cx, cy])


def circle(r, cx=0.0, cy=0.0):
    return CrossSection.circle(r, SEG).translate([cx, cy])


def ext(cs, z0, z1):
    return Manifold.extrude(cs.simplify(0.005), z1 - z0).translate([0, 0, z0])


def cyl(d, z0, z1, cx, cy):
    return Manifold.cylinder(z1 - z0, d / 2, d / 2, SEG).translate([cx, cy, z0])


def box(x0, x1, y0, y1, z0, z1):
    return Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def round_outline(cs, r_convex, r_concave):
    """Dış köşeleri r_convex, iç köşeleri r_concave ile yuvarla."""
    cs = cs.offset(r_concave, JoinType.Round, circular_segments=SEG).offset(-r_concave, JoinType.Round, circular_segments=SEG)
    cs = cs.offset(-r_convex, JoinType.Round, circular_segments=SEG).offset(r_convex, JoinType.Round, circular_segments=SEG)
    return cs


def rounded_body(outline, h, r_front=2.4, r_back=1.0, steps=10):
    """Profil çizgisinden kenarları yuvarlatılmış katı gövde (kademeli fillet)."""
    parts = [ext(outline.offset(-0.0, JoinType.Round), r_back, h - r_front)]
    for i in range(steps):
        a0 = i / steps
        a1 = (i + 1) / steps
        # ön kenar: z = h - r + r*sin(theta)
        z0 = h - r_front + r_front * math.sin(a0 * math.pi / 2)
        z1 = h - r_front + r_front * math.sin(a1 * math.pi / 2)
        inset = r_front - r_front * math.cos(a1 * math.pi / 2)
        parts.append(ext(outline.offset(-inset, JoinType.Round, circular_segments=SEG), z0 - (0.02 if i else 0.0), z1))
        # arka kenar
        b0 = r_back - r_back * math.sin(a1 * math.pi / 2)
        b1 = r_back - r_back * math.sin(a0 * math.pi / 2)
        inset_b = r_back - r_back * math.cos(a1 * math.pi / 2)
        parts.append(ext(outline.offset(-inset_b, JoinType.Round, circular_segments=SEG), b0, b1 + (0.02 if i else 0.02)))
    return Manifold.batch_boolean(parts, __import__("manifold3d").OpType.Add)


# ---------------- dış hatlar ----------------
def cat_outline():
    head = squircle(27.0, 26.0, n=3.5)
    ears = []
    for sx in (-1, 1):
        tri = CrossSection([np.array([[sx * 6.0, 21.0], [sx * 25.5, 15.0], [sx * 20.5, 35.0]])[:: (1 if sx > 0 else -1)]])
        ears.append(tri.offset(-2.5, JoinType.Round, circular_segments=SEG).offset(2.5, JoinType.Round, circular_segments=SEG))
    tab = circle(5.2, 0, 27.0)
    out = head + ears[0] + ears[1] + tab
    return round_outline(out, 1.2, 3.0).simplify(0.02)


def star_outline():
    # Puf yıldız: iç yarıçap, ortak elektronik çekirdeğini (46.8 mm squircle) duvarıyla
    # birlikte saracak kadar büyük olmalı; aksi hâlde yıldız "yuvarlak kare"ye dönüşür.
    R, r = 42.0, 29.0
    pts = []
    for k in range(10):
        ang = math.pi / 2 + k * math.pi / 5
        rad = R if k % 2 == 0 else r
        pts.append([rad * math.cos(ang), rad * math.sin(ang)])
    star = CrossSection([np.array(pts)])
    return round_outline(star, 8.5, 3.5).simplify(0.02)


def star_top():
    b = star_outline().bounds()
    return b[3]


# ---------------- ön kabuk ----------------
def front_shell(outline, btns, name, keyhole_xy, ear_recess=None):
    h = TOTAL_H
    body = rounded_body(outline, h)
    # çekirdek boşluğu (arkadan açık)
    core = ext(squircle(CORE_HALF, CORE_HALF, CORE_N), -1, Z_FRONT_IN)
    body = body - core
    # ekran penceresi + dışa doğru pah
    win = ext(rrect(ACTIVE + 0.4, ACTIVE + 0.4, 1.5, 0, ACT_CY), Z_FRONT_IN - 0.1, h + 1)
    ch = Manifold.batch_boolean([
        ext(rrect(ACTIVE + 0.4 + 2 * d, ACTIVE + 0.4 + 2 * d, 1.5 + d, 0, ACT_CY), h - 0.8 + d - 0.001, h - 0.8 + d + 0.08)
        for d in np.linspace(0, 0.8, 9)], __import__("manifold3d").OpType.Add)
    body = body - win - ch
    # vida sütunları (çekirdek içinde, ön duvardan arka plakaya)
    for (x, y) in PILLARS:
        body = body + cyl(PILLAR_D, BACK_T + 0.05, Z_FRONT_IN + 0.01, x, y)
        body = body - cyl(PILOT_D, BACK_T - 0.5, Z_FRONT_IN - 0.6, x, y)
    # düğme yuvaları
    for (x, y) in btns:
        o = SW_POCKET_IN + 2 * SW_POCKET_WALL
        pocket = ext(rrect(o, o, 0.8, x, y), SW_BODY_Z0 + 0.4, Z_FRONT_IN + 0.01)
        cavity = ext(rrect(SW_POCKET_IN, SW_POCKET_IN, 0.4, x, y), SW_BODY_Z0 - 2, Z_FRONT_IN + 0.01)
        body = body + pocket - cavity
        # kablo çıkış çentiği (yuva tabanında, merkeze doğru)
        body = body - box(x - 1.5, x + 1.5, y - 4.5, y + 4.5, SW_BODY_Z0 - 2, SW_BODY_Z0 + 2.0) if abs(y) > 10 else body - box(x - 4.5, x + 4.5, y - 1.5, y + 1.5, SW_BODY_Z0 - 2, SW_BODY_Z0 + 2.0)
        # kapak havşası + delik
        body = body - cyl(CAP_CB_D, Z_FRONT_IN - 0.01, Z_FRONT_IN + CAP_CB_DEPTH, x, y)
        body = body - cyl(CAP_HOLE_D, Z_FRONT_IN, h + 1, x, y)
    # USB-C ağzı (alt kenar)
    usb = Manifold.extrude(rrect(13.0, 7.6, 2.6, 0, USB_CZ), 20).rotate([90, 0, 0]).translate([0, -CORE_HALF + 2.0, 0])
    body = body - usb
    # anahtarlık deliği
    kx, ky = keyhole_xy
    body = body - cyl(3.6, -1, h + 1, kx, ky)
    # kedi kulak içi süs girintisi
    if ear_recess is not None:
        body = body - ext(ear_recess, h - 0.6, h + 1)
    return body


def cat_ear_recess():
    rs = []
    for sx in (-1, 1):
        tri = CrossSection([np.array([[sx * 10.5, 23.5], [sx * 21.5, 19.5], [sx * 19.0, 31.0]])[:: (1 if sx > 0 else -1)]])
        rs.append(tri.offset(-1.2, JoinType.Round, circular_segments=SEG).offset(1.2, JoinType.Round, circular_segments=SEG))
    return rs[0] + rs[1]


# ---------------- iç taşıyıcı (ortak) ----------------
REAR_BOTTOM = BACK_T + 0.1   # taşıyıcının arka uçları arka kapağa değer


def cradle():
    """Taban plakası + ön yüzde ekran dudağı + arka yüzde sarkan cepler. Arkadan açık."""
    outline = squircle(CHASSIS_HALF, CHASSIS_HALF, CORE_N)
    floor = ext(outline, Z_FLOOR0, Z_FLOOR1)
    floor = floor - ext(rrect(30.0, 15.0, 2.0, 0, -12.5), Z_FLOOR0 - 1, Z_FLOOR1 + 1)   # FPC adaptörü kabloları
    floor = floor - ext(rrect(22.0, 10.0, 2.0, 0, 4.0), Z_FLOOR0 - 1, Z_FLOOR1 + 1)     # LIS3DH kabloları
    floor = floor - ext(rrect(10.5, 7.0, 1.5, 0, -19.5), Z_FLOOR0 - 1, Z_FLOOR1 + 1)    # USB-C üst boşluğu
    for (x, y) in CAT_BTNS + STAR_BTNS:                                                  # düğme bacakları
        floor = floor - ext(rrect(5.0, 5.0, 1.0, x, y), Z_FLOOR0 - 1, Z_FLOOR1 + 1)
    # arka çevre duvarı (tabandan aşağı sarkar), USB ve kablo için açıklıklı
    ring = ext(outline - outline.offset(-1.0, JoinType.Round, circular_segments=SEG), REAR_BOTTOM, Z_FLOOR0 + 0.03)
    ring = ring - box(-10.5, 10.5, -30, -15, 0, Z_FLOOR0 + 1)
    # pil cebi kaburgaları
    bat_in = rrect(BAT_W + 0.6, BAT_H + 0.6, 1.0, BAT_CX, BAT_CY)
    bat_rib = ext(bat_in.offset(1.0, JoinType.Round) - bat_in, REAR_BOTTOM, Z_FLOOR0 + 0.03) ^ ext(outline, 0, 50)
    bat_rib = bat_rib - box(-3.5, 3.5, BAT_CY - 15, BAT_CY - 9, 0, 50)   # kablo çentiği
    # XIAO rayları (kart iki ray arasına arkadan girer)
    xr = []
    for sx in (-1, 1):
        x0 = sx * (XIAO_W / 2 + 0.25)
        xr.append(box(min(x0, x0 + sx * 1.17), max(x0, x0 + sx * 1.17), XIAO_Y0, XIAO_Y1, REAR_BOTTOM, Z_FLOOR0 + 0.03))
    xr.append(box(-XIAO_W / 2 - 1.45, XIAO_W / 2 + 1.45, XIAO_Y1 + 0.25, XIAO_Y1 + 1.25, REAR_BOTTOM, Z_FLOOR0 + 0.03))
    # sürgülü anahtar yuvası (gövde 8.6 x 3.6, kol arkaya)
    sl = ext(rrect(3.6 + 2.4, 8.6 + 2.4, 0.8, SLIDE_CX, SLIDE_CY) - rrect(3.8, 8.8, 0.3, SLIDE_CX, SLIDE_CY), REAR_BOTTOM, Z_FLOOR0 + 0.03)
    # panel desteği + dudak (ön yüz)
    sup = []
    for sx in (-1, 1):
        # alt köşe ayakları (FPC tarafı) ve üst köşe direkleri; ortası LIS3DH için boş
        sup.append(box(min(sx * (PANEL_W / 2 - 3.0), sx * PANEL_W / 2), max(sx * (PANEL_W / 2 - 3.0), sx * PANEL_W / 2), PANEL_BOT, PANEL_BOT + 1.6, Z_FLOOR1 - 0.03, Z_LEDGE))
        sup.append(box(min(sx * 12.85, sx * PANEL_W / 2), max(sx * 12.85, sx * PANEL_W / 2), PANEL_TOP - 1.6, PANEL_TOP, Z_FLOOR1 - 0.03, Z_LEDGE))
    lip_in = rrect(PANEL_W + 2 * LIP_CLR, PANEL_H + 2 * LIP_CLR, 0.6, 0, PANEL_CY)
    lip = ext(lip_in.offset(LIP_T, JoinType.Round, circular_segments=SEG) - lip_in, Z_LEDGE - 0.6, Z_CHASSIS_TOP)
    lip = lip - box(-7.0, 7.0, PANEL_BOT - 3, PANEL_BOT + 1, 0, 50)   # FPC geçişi
    for sx in (-1, 1):
        for y in (PANEL_TOP - 0.7, PANEL_BOT + 0.8):
            sup.append(box(min(sx * (PANEL_W / 2), sx * (PANEL_W / 2 + LIP_CLR + LIP_T - 0.1)), max(sx * (PANEL_W / 2), sx * (PANEL_W / 2 + LIP_CLR + LIP_T - 0.1)), y - 0.7, y + 0.7, Z_FLOOR1 - 0.03, Z_LEDGE))
    body = Manifold.batch_boolean([floor, ring, bat_rib, sl] + xr + sup + [lip], __import__("manifold3d").OpType.Add)
    for (x, y) in PILLARS:
        body = body - cyl(PILLAR_D + 0.6, 0, 50, x, y)
    for (x, y) in CAT_BTNS + STAR_BTNS:
        o = SW_POCKET_IN + 2 * SW_POCKET_WALL + 0.6
        body = body - ext(rrect(o, o, 1.0, x, y), Z_FLOOR1 + 0.3, 50)
    return body


def back_cover():
    outline = squircle(CHASSIS_HALF, CHASSIS_HALF, CORE_N)
    plate = ext(outline, 0, BACK_T)
    # XIAO'yu öne bastıran iki ince kaburga (kart kenarlarının altında)
    ribs = [box(sx * (XIAO_W / 2 - 1.4) - 0.5, sx * (XIAO_W / 2 - 1.4) + 0.5, XIAO_Y0 + 2.0, XIAO_Y0 + 9.0, BACK_T - 0.03, XIAO_Z0) for sx in (-1, 1)]
    body = Manifold.batch_boolean([plate] + ribs, __import__("manifold3d").OpType.Add)
    for (x, y) in PILLARS:
        body = body - cyl(SCREW_CLR_D, -1, BACK_T + 1, x, y)
        body = body - cyl(SCREW_HEAD_D, -1, 0.9, x, y)
    body = body - ext(rrect(2.0, 5.6, 0.8, SLIDE_CX, SLIDE_CY), -1, BACK_T + 0.5)   # sürgü kolu yarığı
    body = body - cyl(20.6, BACK_T - 0.4, BACK_T + 0.01, 0, BAT_CY)                  # piezo çukuru
    for (dx, dy) in [(0, 0), (4, 0), (-4, 0), (0, 4), (0, -4)]:                       # ses delikleri
        body = body - cyl(1.4, -1, BACK_T, dx, BAT_CY + dy)
    return body


def button_cap():
    flange = cyl(CAP_FLANGE_D, 0, 0.6, 0, 0)
    shaft = cyl(CAP_SHAFT_D, 0, 0.6 + (WALL_T - CAP_CB_DEPTH) + 0.8 + 0.15, 0, 0)
    # üstü hafif kubbe
    dome = Manifold.sphere(CAP_SHAFT_D / 2, SEG).scale([1, 1, 0.35]).translate([0, 0, 0.6 + (WALL_T - CAP_CB_DEPTH) + 0.8 + 0.15])
    return flange + shaft + dome


def save(man, name):
    mesh = man.to_mesh()
    tm = trimesh.Trimesh(vertices=np.asarray(mesh.vert_properties)[:, :3], faces=np.asarray(mesh.tri_verts), process=True)
    path = os.path.join(OUT, name)
    tm.export(path)
    b = tm.bounds
    print(f"{name:26s} {b[1][0]-b[0][0]:6.1f} x {b[1][1]-b[0][1]:6.1f} x {b[1][2]-b[0][2]:5.1f} mm  hacim {tm.volume/1000:6.2f} cm3  su-geçirmez={tm.is_watertight}")
    return tm


def flip_for_print(man):
    """Ön kabuğu yüzü tabla üzerine gelecek şekilde çevir."""
    return man.rotate([180, 0, 0]).translate([0, 0, TOTAL_H])


if __name__ == "__main__":
    cat = front_shell(cat_outline(), CAT_BTNS, "kedi", (0.0, 28.0), cat_ear_recess())
    star = front_shell(star_outline(), STAR_BTNS, "yildiz", (0.0, star_top() - 6.2))
    ch = cradle()
    bc = back_cover()
    cap = button_cap()
    # montaj konumunda (render için)
    asm_dir = os.path.join(OUT, "_montaj_konumu")
    os.makedirs(asm_dir, exist_ok=True)
    for m, n in [(cat, "kedi_on_kabuk"), (star, "yildiz_on_kabuk"), (ch, "tasiyici"), (bc, "arka_kapak")]:
        mm = m.to_mesh()
        trimesh.Trimesh(np.asarray(mm.vert_properties)[:, :3], np.asarray(mm.tri_verts)).export(os.path.join(asm_dir, n + ".stl"))
    # baskı yönünde
    save(flip_for_print(cat), "kedi_on_kabuk.stl")
    save(flip_for_print(star), "yildiz_on_kabuk.stl")
    save(ch.translate([0, 0, -REAR_BOTTOM]), "tasiyici.stl")
    save(bc, "arka_kapak.stl")
    save(cap, "dugme_kapagi.stl")
    # şeffaf ekran koruyucu şablonu (1:1 SVG)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="40mm" height="44mm" viewBox="0 0 40 44">
<rect x="{(40-PANEL_W)/2:.2f}" y="{(44-PANEL_H)/2:.2f}" width="{PANEL_W}" height="{PANEL_H}" rx="0.6" fill="none" stroke="black" stroke-width="0.15"/>
<text x="20" y="{(44-PANEL_H)/2 - 1.2:.2f}" font-size="2.2" text-anchor="middle">Ekran koruyucu 26.6 x 30.3 mm (1:1 yazdırın)</text>
</svg>'''
    open(os.path.join(OUT, "ekran_kapagi_sablon.svg"), "w").write(svg)
    print("TOTAL_H", TOTAL_H, "PANEL_TOP", PANEL_TOP, "PANEL_BOT", PANEL_BOT, "USB_CZ", USB_CZ)
