"""
Montaj görselleri: pyvista ile 3D render + matplotlib ile Türkçe etiketler.
Kullanım (depo kökünden): python3 cad/render_images.py stl images images/screens
(önce python3 cad/keychain_cad.py stl çalıştırılmış olmalı: stl/_montaj_konumu/ gerekir)
"""
import sys, os
import numpy as np
import pyvista as pv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
import keychain_cad as K

STL = sys.argv[1] if len(sys.argv) > 1 else "stl"
OUT = sys.argv[2] if len(sys.argv) > 2 else "images"
SCR = sys.argv[3] if len(sys.argv) > 3 else os.path.join(OUT, "screens")
os.makedirs(OUT, exist_ok=True)
ASM = os.path.join(STL, "_montaj_konumu")
pv.OFF_SCREEN = True
W, H = 1400, 1050
TMP = os.path.join(OUT, "_doku")
os.makedirs(TMP, exist_ok=True)

COL = dict(cat="#F2A07B", star="#F7C85A", cradle="#C9CED6", back="#AEB6C2", xiao="#1F3D7A", usb="#B8BCC2",
           shield="#D9DCE0", bat="#7FA7C9", piezo="#C9A24A", ceramic="#F2F2EE", lis="#5B3F8C", adapter="#2E7D4F",
           conn="#E8D9B0", panel="#2B2D31", active="#B9BDB5", fpc="#D88A2D", cover="#DDEEFF", sw="#222222",
           plunger="#3A3A3A", slide="#2C5BA8", lever="#EDEDED", screw="#9AA0A6", cap="#F7B6C8", cap_star="#F29B4B", ink="#151515",
           wire_r="#D93A3A", wire_k="#222222", wire_y="#E8C330", wire_g="#3FA34D", wire_b="#3A6FD9")


def load(name):
    return pv.read(os.path.join(ASM, name + ".stl"))


def bx(x0, x1, y0, y1, z0, z1):
    return pv.Box(bounds=(x0, x1, y0, y1, z0, z1))


def cy(d, z0, z1, x, y, res=48):
    return pv.Cylinder(center=(x, y, (z0 + z1) / 2), direction=(0, 0, 1), radius=d / 2, height=z1 - z0, resolution=res)


def screen_texture(name):
    """Simülatörden çıkan ekran PNG'sinin çerçevesiz hâli (doku olarak)."""
    src = os.path.join(SCR, name + ".png")
    im = Image.open(src)
    b = 12
    im = im.crop((b, b, im.width - b, im.height - b))
    p = os.path.join(TMP, name + ".png")
    im.save(p)
    return pv.read_texture(p)


# ---------------- bileşen modelleri (montaj koordinatları) ----------------
def comp_piezo(dz=0):
    z = K.BACK_T - 0.4 + dz
    return [(cy(20.0, z, z + 0.25, 0, K.BAT_CY), COL["piezo"]), (cy(14.0, z + 0.25, z + 0.45, 0, K.BAT_CY), COL["ceramic"])]


def comp_battery(dz=0):
    return [(bx(-15.5, 15.5, K.BAT_CY - 10.25, K.BAT_CY + 10.25, 2.2 + dz, 7.5 + dz), COL["bat"])]


def comp_xiao(dz=0):
    z0 = K.XIAO_Z0 + dz
    w = K.XIAO_W / 2
    return [(bx(-w, w, K.XIAO_Y0, K.XIAO_Y1, z0, z0 + K.XIAO_PCB), COL["xiao"]),
            (bx(-4.5, 4.5, K.XIAO_Y0 - 0.6, K.XIAO_Y0 + 6.8, z0 + K.XIAO_PCB, z0 + K.XIAO_PCB + 3.2), COL["usb"]),
            (bx(-6.0, 6.0, K.XIAO_Y0 + 8.0, K.XIAO_Y0 + 19.0, z0 + K.XIAO_PCB, z0 + K.XIAO_PCB + 2.0), COL["shield"])]


def comp_slide(dz=0):
    cx, cyy = K.SLIDE_CX, K.SLIDE_CY
    return [(bx(cx - 1.8, cx + 1.8, cyy - 4.3, cyy + 4.3, 4.0 + dz, 7.5 + dz), COL["slide"]),
            (bx(cx - 0.75, cx + 0.75, cyy - 1.5, cyy + 0.5, 0.3 + dz, 4.0 + dz), COL["lever"])]


def comp_adapter(dz=0):
    z0 = K.Z_FLOOR1 + 0.3 + dz
    return [(bx(-14.0, 14.0, -17.3, -6.0, z0, z0 + 1.6), COL["adapter"]),
            (bx(-4.5, 4.5, -17.3, -13.0, z0 + 1.6, z0 + 3.0), COL["conn"])]


def comp_lis(dz=0):
    z0 = K.Z_FLOOR1 + 0.3 + dz
    return [(bx(-12.7, 12.7, -5.8, 12.0, z0, z0 + 1.6), COL["lis"]), (bx(-1.5, 1.5, 2.0, 5.0, z0 + 1.6, z0 + 2.6), COL["ink"])]


def comp_panel(dz=0, tex=None):
    z0 = K.Z_LEDGE + dz
    out = [(bx(-K.PANEL_W / 2, K.PANEL_W / 2, K.PANEL_BOT, K.PANEL_TOP, z0, z0 + K.PANEL_T), COL["panel"]),
           (bx(-4.0, 4.0, K.PANEL_BOT - 3.5, K.PANEL_BOT + 0.2, z0 + 0.1, z0 + 0.25), COL["fpc"])]
    act = pv.Plane(center=(0, K.ACT_CY, z0 + K.PANEL_T + 0.02), direction=(0, 0, 1), i_size=K.ACTIVE, j_size=K.ACTIVE)
    out.append((act, ("tex", tex) if tex is not None else COL["active"]))
    return out


def comp_cover(dz=0):
    z0 = K.Z_LEDGE + K.PANEL_T + dz
    return [(bx(-K.PANEL_W / 2, K.PANEL_W / 2, K.PANEL_BOT, K.PANEL_TOP, z0, z0 + K.COVER_T), COL["cover"])]


def comp_switches(btns, dz=0):
    out = []
    for (x, y) in btns:
        z0 = K.SW_BODY_Z0 + dz
        out.append((bx(x - 3, x + 3, y - 3, y + 3, z0, z0 + 3.5), COL["sw"]))
        out.append((cy(3.5, z0 + 3.5, z0 + 5.0, x, y, 24), COL["plunger"]))
        for sx in (-1, 1):   # bacaklar arkaya bakar
            for sy in (-1, 1):
                out.append((bx(x + sx * 3.2 - 0.3, x + sx * 3.2 + 0.3, y + sy * 2.25 - 0.4, y + sy * 2.25 + 0.4, z0 - 2.0, z0 + 1.0), COL["screw"]))
    return out


def comp_caps(btns, dz=0, color=None):
    out = []
    color = color or COL["cap"]
    for (x, y) in btns:
        z0 = K.Z_FRONT_IN - 0.6 + dz
        out.append((cy(K.CAP_FLANGE_D, z0, z0 + 0.6, x, y), color))
        out.append((cy(K.CAP_SHAFT_D, z0, z0 + 2.6, x, y), color))
    return out


def comp_screws(dz=0):
    out = []
    for (x, y) in K.PILLARS:
        out.append((cy(3.8, 0.0 + dz, 0.9 + dz, x, y, 24), COL["screw"]))
        out.append((cy(2.0, 0.9 + dz, 10.0 + dz, x, y, 16), COL["screw"]))
    return out


def wire(points, color, r=0.35):
    sp = pv.Spline(np.array(points, dtype=float), 40)
    return (sp.tube(radius=r, n_sides=10), color)


# ---------------- çizim altyapısı ----------------
def plotter():
    p = pv.Plotter(off_screen=True, window_size=(W, H))
    p.set_background("white")
    p.enable_anti_aliasing("ssaa")
    p.add_light(pv.Light(position=(80, 60, 200), focal_point=(0, 0, 0), intensity=0.45))
    p.add_light(pv.Light(position=(-60, -40, -200), focal_point=(0, 0, 0), intensity=0.35))
    return p


def add(p, items, opacity=1.0, smooth=False):
    for mesh, c in items:
        if isinstance(c, tuple) and c[0] == "tex":
            p.add_mesh(mesh, texture=c[1], ambient=0.45, diffuse=0.7)
            continue
        op = 0.3 if c == COL["cover"] else opacity
        p.add_mesh(mesh, color=c, opacity=op, smooth_shading=smooth, specular=0.15, specular_power=12,
                   ambient=0.25, diffuse=0.8)


def project(p, pts):
    ren = p.renderer
    out = []
    for q in pts:
        ren.SetWorldPoint(q[0], q[1], q[2], 1.0)
        ren.WorldToDisplay()
        x, y, _ = ren.GetDisplayPoint()
        out.append((x, H - y))
    return out


def finish(p, cam, name, labels=None, title=None, note=None, zoom=1.0):
    p.camera_position = cam
    p.camera.zoom(zoom)
    img = p.screenshot(return_img=True)
    pts = project(p, [l[0] for l in labels]) if labels else []
    p.close()
    fig = plt.figure(figsize=(W / 150, H / 150), dpi=150)
    ax = fig.add_axes([0, 0, 1, 1]); ax.imshow(img); ax.axis("off")
    if title:
        ax.text(30, 55, title, fontsize=17, fontweight="bold", color="#1A1A1A", family="DejaVu Sans",
                bbox=dict(boxstyle="square,pad=0.3", fc="white", ec="none", alpha=0.85))
    if note:
        ax.text(30, H - 32, note, fontsize=10.5, color="#333333", family="DejaVu Sans",
                bbox=dict(boxstyle="square,pad=0.3", fc="white", ec="none", alpha=0.9))
    for (lab, (px, py)) in zip(labels or [], pts):
        _, text, (ox, oy) = lab
        lines = text.split("\n")
        wpx = max(len(l) for l in lines) * 11.0 + 18
        tx, ty = px + ox, py + oy
        ha = "left" if ox >= 0 else "right"
        if ha == "left" and tx + wpx > W - 12: tx = W - 12 - wpx
        if ha == "right" and tx - wpx < 12: tx = 12 + wpx
        ty = min(max(ty, 95), H - 70)
        ax.annotate(text, xy=(px, py), xytext=(tx, ty), fontsize=10, family="DejaVu Sans", color="#111111",
                    ha=ha, va="center",
                    bbox=dict(boxstyle="round,pad=0.35", fc="#FFFBEA", ec="#C9A227", lw=0.8),
                    arrowprops=dict(arrowstyle="-", color="#C9A227", lw=1.3))
        ax.plot([px], [py], "o", ms=5, color="#C9A227")
    ax.set_xlim(0, W); ax.set_ylim(H, 0)
    fig.savefig(os.path.join(OUT, name + ".png"), dpi=150)
    plt.close(fig)
    print("yazıldı", name)


CAT = load("kedi_on_kabuk"); STAR = load("yildiz_on_kabuk")
CR = load("tasiyici"); BC = load("arka_kapak")
FRONT34 = [(75, -60, 150), (0, 0, 7), (0, 1, 0)]
BACK34 = [(55, -45, -140), (0, -1, 5), (0, 1, 0)]

# ======================= bitmiş görünümler =======================
def hero(shell, color, btns, tex, name, title, kx, capc):
    p = plotter()
    add(p, [(shell, color)])
    add(p, comp_panel(tex=screen_texture(tex)) + comp_cover() + comp_caps(btns, color=capc))
    ring = pv.ParametricTorus(ringradius=9.0, crosssectionradius=0.9).rotate_y(90, inplace=False).translate((0, kx + 8.0, 7.8), inplace=False)
    p.add_mesh(ring, color="#A9AEB4", specular=0.6, specular_power=30, smooth_shading=True)
    finish(p, [(70, -70, 160), (0, 6, 7), (0, 1, 0)], name, title=title, zoom=1.2)

hero(CAT, COL["cat"], K.CAT_BTNS, "kedi_neutral", "01_kedi_genel", "Kedi anahtarlık – bitmiş görünüm", 28.0, COL["cap"])
hero(STAR, COL["star"], K.STAR_BTNS, "yildiz_neutral", "02_yildiz_genel", "Puf yıldız anahtarlık – bitmiş görünüm", K.star_top() - 6.2, COL["cap_star"])

# ======================= patlatılmış görünüm =======================
p = plotter()
E = 17.0
add(p, [(BC.translate((0, 0, -3.2 * E), inplace=False), COL["back"])])
add(p, comp_screws(-4.4 * E) + comp_piezo(-3.2 * E))
add(p, comp_battery(-1.6 * E) + comp_xiao(-1.6 * E) + comp_slide(-1.6 * E))
add(p, [(CR, COL["cradle"])])
add(p, comp_adapter(1.0 * E) + comp_lis(1.0 * E))
add(p, comp_panel(2.0 * E, tex=screen_texture("kedi_happy")) + comp_cover(2.6 * E))
add(p, [(CAT.translate((0, 0, 4.0 * E), inplace=False), COL["cat"])])
add(p, comp_switches(K.CAT_BTNS, 3.4 * E) + comp_caps(K.CAT_BTNS, 4.9 * E))
cam = [(175, -235, 150), (0, 0, 10), (0, 0, 1)]
labs = [((-20, 20, 4.0 * E + 12), "Ön kabuk (kedi veya yıldız)", (-60, -20)),
        ((14, 16, 4.9 * E + 15), "2 × düğme kapağı", (70, -20)),
        ((14, 16, 3.4 * E + 11), "2 × 6×6 düğme", (90, 10)),
        ((13, 5, 2.6 * E + 14), "Şeffaf koruyucu", (80, 0)),
        ((13, -8, 2.0 * E + 13), "Sharp ekran", (90, 10)),
        ((12, 8, 1.0 * E + 10.5), "LIS3DH ivmeölçer", (90, -5)),
        ((13, -12, 1.0 * E + 10), "FPC adaptörü", (90, 15)),
        ((21, 5, 9), "Taşıyıcı (ortak)", (80, 0)),
        ((15, 12, -1.6 * E + 6), "Pil 502030", (80, 0)),
        ((8, -15, -1.6 * E + 5), "XIAO ESP32-C6", (90, 10)),
        ((-12.8, -6.7, -1.6 * E + 6), "Sürgülü anahtar", (-80, 0)),
        ((-10, 10.5, -3.2 * E + 1.5), "Piezo (arka kapağa yapışık)", (-90, -30)),
        ((-21, -5, -3.2 * E + 1), "Arka kapak (ortak)", (-90, 25)),
        ((-18.5, -13, -4.4 * E + 2), "4 × M2×10 vida", (-80, 0))]
finish(p, cam, "03_patlatilmis", labels=labs, title="Patlatılmış görünüm – parçalar ve sıra", zoom=0.86)

# ======================= adımlar (mekanik montaj) =======================
# A1: ön katman – adaptör ve ivmeölçer taşıyıcının ön yüzünde
p = plotter()
add(p, [(CR, COL["cradle"])])
add(p, comp_adapter() + comp_lis())
labs = [((-10, -12, K.Z_FLOOR1 + 1.9), "FPC adaptörü: konnektör ÖNE (ekrana)\nve aşağı kenara bakar", (-140, 90)),
        ((8, 6, K.Z_FLOOR1 + 1.9), "LIS3DH: ince çift taraflı bantla", (160, -60)),
        ((-14, 16, K.Z_FLOOR1), "Kedi düğme\nboşlukları", (-110, -60)),
        ((18.7, 6, K.Z_FLOOR1), "Yıldız düğme\nboşlukları", (90, -110))]
finish(p, FRONT34, "10_montaj_on_katman", labels=labs, title="Montaj 1 – Ön katman: adaptör ve ivmeölçer",
       note="Adaptör ve LIS3DH, kabloları XIAO'ya lehimli hâlde, büyük pencereden yan çevrilerek öne geçirilir.", zoom=1.25)

# A2: ekran
p = plotter()
add(p, [(CR, COL["cradle"])])
add(p, comp_adapter() + comp_lis() + comp_panel(tex=screen_texture("kedi_neutral")) + comp_cover(2.0))
fx = [(0, K.PANEL_BOT + 0.1, K.Z_LEDGE + 0.15), (0, K.PANEL_BOT - 2.2, K.Z_LEDGE - 0.6), (0, K.PANEL_BOT - 1.8, K.Z_FLOOR1 + 3.5), (0, -15.2, K.Z_FLOOR1 + 3.3)]
add(p, [wire(fx, COL["fpc"], r=0.25)])
labs = [((0, K.PANEL_BOT - 2.0, K.Z_LEDGE - 1.0), "Şerit kablo tek yumuşak kıvrımla adaptöre girer.\nCamın dibinden ASLA keskin bükmeyin.", (190, 70)),
        ((-11, 8, K.Z_LEDGE + 2.8), "Şeffaf koruyucu panelin üstüne", (-120, -70)),
        ((12, 0, K.Z_LEDGE + 0.6), "Ekran dudağın içine oturur", (150, -40))]
finish(p, FRONT34, "11_montaj_ekran", labels=labs, title="Montaj 2 – Ekranı taşıyıcıya oturtun", zoom=1.25)

# A3: arka katman (arkadan bakış)
p = plotter()
add(p, [(CR, COL["cradle"])])
add(p, comp_battery() + comp_xiao() + comp_slide())
labs = [((0, K.BAT_CY + 4, 2.2), "Pil: kaburgaların arasına,\nkablosu çentikten aşağı", (-150, -80)),
        ((0, -12, K.XIAO_Z0), "XIAO: raylara arkadan kaydırın,\nUSB-C alt kenarda, çipler ÖNE bakar", (150, 70)),
        ((K.SLIDE_CX, K.SLIDE_CY, 0.3), "Sürgülü anahtar: kolu arkaya", (170, -20))]
finish(p, BACK34, "12_montaj_arka_katman", labels=labs, title="Montaj 3 – Arka katman: pil, XIAO, anahtar",
       note="Taşıyıcı arkadan gösteriliyor (görüntü önden bakışa göre aynalıdır).", zoom=1.25)

# A4: piezo arka kapağa
p = plotter()
add(p, [(BC, COL["back"])])
add(p, comp_piezo())
labs = [((0, K.BAT_CY, 1.6), "Piezo diski çukura yapıştırın\n(pirinç yüzü kapağa,\nkenardan 3 nokta yapıştırıcı)", (150, -90)),
        ((K.SLIDE_CX, K.SLIDE_CY, 1.6), "Sürgü kolu yarığı", (-150, 40)),
        ((K.PILLARS[2][0], K.PILLARS[2][1], 1.6), "Vida delikleri (havşa dışta)", (-140, 80)),
        ((0, K.XIAO_Y0 + 5, 3.0), "XIAO'yu öne bastıran kaburgalar", (160, 60))]
finish(p, FRONT34, "13_montaj_piezo", labels=labs, title="Montaj 4 – Piezo hoparlör arka kapağın iç yüzüne",
       note="Arka kapağın İÇ yüzü (cihaza bakan taraf) gösteriliyor.", zoom=1.3)

# A5: düğmeler kabuğun içine
def step_buttons(shell, color, btns, name, title, zoom):
    p = plotter()
    add(p, [(shell, color)])
    add(p, comp_switches(btns) + comp_caps(btns, color=COL["cap"] if shell is CAT else COL["cap_star"]))
    labs = [((btns[0][0], btns[0][1], K.SW_BODY_Z0 - 1.5), "6×6 düğme: bacaklar arkaya bakar,\nyuvaya tam oturana kadar bastırın", (160, 200)),
            ((btns[1][0], btns[1][1], K.SW_BODY_Z0), "Kapak önce İÇERİDEN takılır\n(kubbe dışarı, flanş içeride)", (-160, -90)),
            ((K.PILLARS[0][0], K.PILLARS[0][1], 1.7), "Vida sütunu", (-140, 90))]
    finish(p, BACK34, name, labels=labs, title=title,
           note="Kabuğun içi (arkadan) gösteriliyor. Düğme kablolarını 2–3 cm boşluklu bırakın.", zoom=zoom)

step_buttons(CAT, COL["cat"], K.CAT_BTNS, "14_montaj_dugmeler_kedi", "Montaj 5 – Düğmeler (kedi kabuğu)", 0.95)
step_buttons(STAR, COL["star"], K.STAR_BTNS, "15_montaj_dugmeler_yildiz", "Montaj 5 – Düğmeler (yıldız kabuğu)", 0.78)

# A6: taşıyıcıyı kabuğa
p = plotter()
add(p, [(CAT, COL["cat"])])
add(p, comp_switches(K.CAT_BTNS) + comp_caps(K.CAT_BTNS))
add(p, [(CR.translate((0, 0, -18), inplace=False), COL["cradle"])])
add(p, comp_battery(-18) + comp_xiao(-18) + comp_slide(-18) + comp_panel(-18) + comp_adapter(-18) + comp_lis(-18))
labs = [((0, -22, -12), "USB-C kabuktaki ağza denk gelir", (170, 60)),
        ((K.PILLARS[1][0], K.PILLARS[1][1], -12), "Taşıyıcı vida sütunlarının arasından\nkayar, ekran pencereye oturur", (170, -40))]
finish(p, [(60, -90, -150), (0, -2, -4), (0, 1, 0)], "16_montaj_kabuga", labels=labs,
       title="Montaj 6 – Taşıyıcıyı kabuğa yerleştirin", zoom=1.15)

# A7: kapatma
p = plotter()
add(p, [(CAT, COL["cat"])])
add(p, comp_battery() + comp_xiao() + comp_slide())
add(p, [(CR, COL["cradle"])])
add(p, [(BC.translate((0, 0, -14), inplace=False), COL["back"])])
add(p, comp_screws(-26))
labs = [((K.PILLARS[2][0], K.PILLARS[2][1], -26), "4 × M2×10 kendinden kılavuzlu vida\n(sıkıca ama zorlamadan)", (-60, 100)),
        ((K.SLIDE_CX, K.SLIDE_CY, -14), "Anahtar kolu yarıktan çıkar", (170, -60)),
        ((0, K.BAT_CY, -14), "Ses delikleri", (170, 0))]
finish(p, [(70, -80, -170), (0, -2, -8), (0, 1, 0)], "17_montaj_kapatma", labels=labs,
       title="Montaj 7 – Arka kapağı vidalayın", zoom=1.15)

# ======================= baskı yönleri =======================
p = plotter()
parts = [("kedi_on_kabuk", COL["cat"], (-38, 34)), ("yildiz_on_kabuk", COL["star"], (40, 34)),
         ("tasiyici", COL["cradle"], (-34, -32)), ("arka_kapak", COL["back"], (22, -32)), ("dugme_kapagi", COL["cap"], (60, -20))]
for fn, c, (x, y) in parts:
    m = pv.read(os.path.join(STL, fn + ".stl"))
    cx, cyy = (m.bounds[0] + m.bounds[1]) / 2, (m.bounds[2] + m.bounds[3]) / 2
    m = m.translate((x - cx, y - cyy, -m.bounds[4]), inplace=False)
    add(p, [(m, c)])
    if fn == "dugme_kapagi":
        add(p, [(m.translate((0, -12, 0), inplace=False), c)])
bed = pv.Plane(center=(5, 0, -0.05), direction=(0, 0, 1), i_size=170, j_size=150, i_resolution=15, j_resolution=14)
p.add_mesh(bed, color="#3B3F45", show_edges=True, edge_color="#5A5F66")
labs = [((-38, 34, 15), "Kedi ön kabuk\n(yüzü tablada)", (-60, -60)),
        ((40, 34, 15), "Yıldız ön kabuk\n(yüzü tablada)", (60, -60)),
        ((-34, -32, 12), "Taşıyıcı\n(arka uçları tablada)", (-80, 60)),
        ((22, -32, 3), "Arka kapak\n(düz yüz tablada)", (40, 100)),
        ((60, -26, 3), "2 × düğme kapağı\n(flanş tablada)", (90, 40))]
finish(p, [(130, -200, 230), (5, 2, 0), (0, 0, 1)], "05_baski_yonleri", labels=labs,
       title="Baskı yönleri – destek gerekmez",
       note="PLA · 0.4 mm nozül · 0.2 mm katman · 4 çevre duvarı · %20 dolgu · destek YOK", zoom=1.0)

# ======================= kontroller (önden) =======================
p = plotter()
add(p, [(CAT, COL["cat"])])
add(p, comp_panel(tex=screen_texture("kedi_bubble")) + comp_cover() + comp_caps(K.CAT_BTNS, color=COL["cap"]))
labs = [((-14, 16, 16), "SOL düğme\n• kısa: konuşur\n• uzun: pil ve saat\n• uykudayken: uyandırır\n• menüde: aşağı", (-170, -60)),
        ((14, 16, 16), "SAĞ düğme\n• kısa: sev (kalpler)\n• uzun: oyun listesi\n• menüde: seç", (170, -60)),
        ((0, -2.5, 15), "İKİSİ BİRLİKTE: menü\nÇİFT VURUŞ: oyunlar\nTEK VURUŞ: şaşırır\nSALLA: başı döner\nEĞ: gözler takip eder", (230, 230)),
        ((0, -24, 6), "Alt kenarda USB-C (şarj ve yazılım)", (-200, 60))]
finish(p, [(0, 2, 190), (0, 2, 7), (0, 1, 0)], "06_kontroller", labels=labs, title="Kontroller", zoom=1.25,
       note="20 saniye dokunulmazsa uykuya geçer; yüz ekranda kalır. Uzun sol basış oyunlardan çıkar.")
