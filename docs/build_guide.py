# -*- coding: utf-8 -*-
"""Pocket Pal Türkçe yapım kılavuzu (PDF).
Kullanım (depo kökünden): python3 docs/build_guide.py . docs/Pocket_Pal_Yapim_Kilavuzu.pdf"""
import sys, os, csv
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Image, Table, TableStyle,
                                PageBreak, KeepTogether, CondPageBreak)
from reportlab.platypus.tableofcontents import TableOfContents
from PIL import Image as PILImage

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "docs", "Pocket_Pal_Yapim_Kilavuzu.pdf")
IMG = os.path.join(ROOT, "images")
SCR = os.path.join(IMG, "screens")

F = "/usr/share/fonts/truetype/dejavu/"
pdfmetrics.registerFont(TTFont("DV", F + "DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DVB", F + "DejaVuSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("DVI", F + "DejaVuSans-Oblique.ttf"))
pdfmetrics.registerFont(TTFont("DVM", F + "DejaVuSansMono.ttf"))
from reportlab.pdfbase.pdfmetrics import registerFontFamily
registerFontFamily("DV", normal="DV", bold="DVB", italic="DVI", boldItalic="DVB")

INK = colors.HexColor("#1F2328")
ACC = colors.HexColor("#E07A5F")
ACC2 = colors.HexColor("#3D5A80")
SOFT = colors.HexColor("#FFF6E8")
LINE = colors.HexColor("#E2D6C2")
WARN = colors.HexColor("#FDECEA")
WARN_E = colors.HexColor("#C0392B")
TIP = colors.HexColor("#EAF4EC")
TIP_E = colors.HexColor("#2E7D4F")

S = {}
S["body"] = ParagraphStyle("body", fontName="DV", fontSize=9.6, leading=13.6, textColor=INK, spaceAfter=5)
S["small"] = ParagraphStyle("small", parent=S["body"], fontSize=8.4, leading=11.2, spaceAfter=2)
S["cell"] = ParagraphStyle("cell", parent=S["body"], fontSize=8.4, leading=10.8, spaceAfter=0)
S["cellb"] = ParagraphStyle("cellb", parent=S["cell"], fontName="DVB")
S["h1"] = ParagraphStyle("h1", fontName="DVB", fontSize=19, leading=24, textColor=ACC2, spaceBefore=4, spaceAfter=10)
S["h2"] = ParagraphStyle("h2", fontName="DVB", fontSize=13, leading=17, textColor=INK, spaceBefore=10, spaceAfter=6)
S["h3"] = ParagraphStyle("h3", fontName="DVB", fontSize=10.6, leading=14, textColor=ACC, spaceBefore=6, spaceAfter=3)
S["cap"] = ParagraphStyle("cap", parent=S["body"], fontName="DVI", fontSize=8.2, leading=10.5, textColor=colors.HexColor("#555"), alignment=TA_CENTER, spaceAfter=8)
S["mono"] = ParagraphStyle("mono", fontName="DVM", fontSize=8.2, leading=11, textColor=INK, backColor=colors.HexColor("#F4F4F2"),
                           borderPadding=(5, 6, 5, 6), spaceBefore=3, spaceAfter=8)
S["title"] = ParagraphStyle("title", fontName="DVB", fontSize=30, leading=36, textColor=ACC2, alignment=TA_CENTER)
S["subtitle"] = ParagraphStyle("subtitle", fontName="DV", fontSize=13, leading=18, textColor=INK, alignment=TA_CENTER)
S["toc1"] = ParagraphStyle("toc1", fontName="DV", fontSize=10, leading=13.5, leftIndent=6)
S["toc2"] = ParagraphStyle("toc2", fontName="DV", fontSize=8.6, leading=11, leftIndent=22, textColor=colors.HexColor("#444"))

W_FULL = 174 * mm


class Doc(BaseDocTemplate):
    def __init__(self, fn):
        super().__init__(fn, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=17 * mm, bottomMargin=17 * mm,
                         title="Pocket Pal – Yapım Kılavuzu", author="Pocket Pal", subject="Kedi ve yıldız ESP32 anahtarlık")
        fr = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="f")
        self.addPageTemplates([PageTemplate(id="p", frames=[fr], onPage=self.deco)])

    def deco(self, c, doc):
        if doc.page == 1:
            return
        c.saveState()
        c.setFont("DV", 7.8)
        c.setFillColor(colors.HexColor("#888"))
        c.drawString(18 * mm, 10 * mm, "Pocket Pal – Kedi & Yıldız Anahtarlık · Yapım Kılavuzu")
        c.drawRightString(A4[0] - 18 * mm, 10 * mm, f"{doc.page}")
        c.setStrokeColor(LINE); c.setLineWidth(0.6)
        c.line(18 * mm, 13 * mm, A4[0] - 18 * mm, 13 * mm)
        c.restoreState()

    def afterFlowable(self, f):
        items = getattr(f, "_content", None) if isinstance(f, KeepTogether) else [f]
        for x in items or []:
            if isinstance(x, Paragraph) and x.style.name in ("h1", "h2"):
                lvl = 0 if x.style.name == "h1" else 1
                txt = x.getPlainText()
                key = "k%d" % id(x)
                self.canv.bookmarkPage(key)
                self.canv.addOutlineEntry(txt, key, level=lvl, closed=False)
                self.notify("TOCEntry", (lvl, txt, self.page, key))


story = []
P = lambda t, st="body": story.append(Paragraph(t, S[st]))


def H1(t):
    story.append(CondPageBreak(60 * mm))
    P(t, "h1")


def H2(t):
    story.append(CondPageBreak(40 * mm))
    P(t, "h2")


CROP_TOP = {"03": 0.075, "05": 0.075, "06": 0.075, "10": 0.075, "11": 0.075, "12": 0.075, "13": 0.075, "14": 0.075,
            "15": 0.075, "16": 0.075, "17": 0.075, "20": 0.08, "21": 0.10, "22": 0.10, "23": 0.10}
CROP_DIR = os.path.join(os.path.dirname(os.path.abspath(OUT)), "_kirpik")


def cropped(path):
    key = os.path.basename(path)[:2]
    if key not in CROP_TOP:
        return path
    os.makedirs(CROP_DIR, exist_ok=True)
    im = PILImage.open(path)
    top = int(im.height * CROP_TOP[key])
    out = os.path.join(CROP_DIR, os.path.basename(path))
    im.crop((0, top, im.width, im.height)).save(out)
    return out


def img(name, width=W_FULL, cap=None, folder=IMG):
    path = cropped(os.path.join(folder, name))
    w, h = PILImage.open(path).size
    im = Image(path, width=width, height=width * h / w)
    items = [im]
    if cap:
        items.append(Paragraph(cap, S["cap"]))
    return KeepTogether(items)


def box(text, kind="tip"):
    bg, edge, label = {"tip": (TIP, TIP_E, "İPUCU"), "warn": (WARN, WARN_E, "DİKKAT"), "note": (SOFT, ACC, "NOT")}[kind]
    t = Table([[Paragraph(f"<font name='DVB' color='{edge.hexval()}'>{label}</font>  " + text, S["body"])]], colWidths=[W_FULL])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), bg), ("LINEBEFORE", (0, 0), (0, -1), 3, edge),
                           ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                           ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
    story.append(t)
    story.append(Spacer(1, 6))


def table(rows, widths, header=True, zebra=True, font=8.4):
    data = []
    for i, r in enumerate(rows):
        st = S["cellb"] if (header and i == 0) else S["cell"]
        data.append([c if not isinstance(c, str) else Paragraph(c, st) for c in r])
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    ts = [("GRID", (0, 0), (-1, -1), 0.4, LINE), ("VALIGN", (0, 0), (-1, -1), "TOP"),
          ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
          ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
    if header:
        ts.append(("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F3E9DA")))
    if zebra:
        for i in range(1 + header, len(rows), 2):
            ts.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#FBF8F3")))
    t.setStyle(TableStyle(ts))
    story.append(t)
    story.append(Spacer(1, 8))


def screens(names_caps, per_row=4, w=38 * mm):
    cells, caps = [], []
    rows = []
    for i, (n, c) in enumerate(names_caps):
        cells.append(Image(os.path.join(SCR, n + ".png"), width=w, height=w))
        caps.append(Paragraph(c, S["cap"]))
        if len(cells) == per_row or i == len(names_caps) - 1:
            while len(cells) < per_row:
                cells.append(""); caps.append("")
            rows += [cells, caps]
            cells, caps = [], []
    t = Table(rows, colWidths=[W_FULL / per_row] * per_row)
    t.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("TOPPADDING", (0, 0), (-1, -1), 1), ("BOTTOMPADDING", (0, 0), (-1, -1), 1)]))
    story.append(KeepTogether([t, Spacer(1, 6)]))


def steps(items):
    """Numaralı adım listesi: [(başlık, açıklama), ...]"""
    rows = []
    for i, (t, d) in enumerate(items, 1):
        num = Paragraph(f"<font name='DVB' color='white'>{i}</font>", ParagraphStyle("n", fontName="DVB", fontSize=10, alignment=TA_CENTER, leading=13))
        rows.append([num, Paragraph(f"<b>{t}</b><br/>{d}", S["cell"])])
    t = Table(rows, colWidths=[8 * mm, W_FULL - 8 * mm])
    ts = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (1, 0), (1, -1), 6),
          ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
          ("LINEBELOW", (1, 0), (1, -2), 0.3, LINE)]
    for i in range(len(rows)):
        ts.append(("BACKGROUND", (0, i), (0, i), ACC))
    t.setStyle(TableStyle(ts))
    story.append(t)
    story.append(Spacer(1, 8))


# ============================================================ KAPAK
story.append(Spacer(1, 18 * mm))
P("Pocket Pal", "title")
story.append(Spacer(1, 3 * mm))
P("Kedi &amp; Puf Yıldız anahtarlık · ESP32-C6 · her zaman açık yüz", "subtitle")
story.append(Spacer(1, 2 * mm))
P("Yapım kılavuzu, malzeme listesi, 3D baskı dosyaları ve yazılım", "subtitle")
story.append(Spacer(1, 8 * mm))
t = Table([[Image(os.path.join(IMG, "01_kedi_genel.png"), width=85 * mm, height=85 * mm * 1050 / 1400),
            Image(os.path.join(IMG, "02_yildiz_genel.png"), width=85 * mm, height=85 * mm * 1050 / 1400)]],
          colWidths=[87 * mm, 87 * mm])
story.append(t)
story.append(Spacer(1, 8 * mm))
cover_rows = [["Kedi", "54 × 59 × 15,7 mm"], ["Puf yıldız", "73 × 70 × 15,7 mm"],
              ["Ekran", "1,28\" 128×128 Sharp bellek LCD (arka ışıksız, gün ışığında okunur)"],
              ["Kontroller", "2 düğme + hareket (vuruş, çift vuruş, sallama, eğme)"],
              ["Pil", "250 mAh LiPo · normal kullanımda ~2 ay, az kullanımda ~3 ay"],
              ["Parça maliyeti", "≈ 1.870 – 2.100 TL / adet (ekran 10+ adet alınırsa ≈ 1.660 – 1.890 TL)"],
              ["Zorluk", "Bir akşam · ~40 lehim noktası · XIAO arkasındaki iki pil pedi dışında hepsi 2,54 mm aralıklı"]]
ct = Table([[Paragraph(f"<b>{a}</b>", S["cell"]), Paragraph(b, S["cell"])] for a, b in cover_rows], colWidths=[34 * mm, 120 * mm], hAlign="CENTER")
ct.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -2), 0.3, LINE), ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
story.append(ct)
story.append(PageBreak())

# ============================================================ İÇİNDEKİLER
story.append(Paragraph("İçindekiler", ParagraphStyle("tochead", parent=S["h1"])))
toc = TableOfContents()
toc.levelStyles = [S["toc1"], S["toc2"]]
story.append(toc)
story.append(PageBreak())

# ============================================================ 1 GENEL BAKIŞ
H1("1. Genel bakış")
P("Pocket Pal, çantaya takılan, yüzü <b>her zaman ekranda duran</b> küçük bir dijital arkadaş. Ekranı bir Sharp bellek "
  "LCD'dir: görüntüyü neredeyse hiç güç harcamadan tutar, bu yüzden cihaz uyurken bile yüz görünür. Dokunduğunuzda, "
  "salladığınızda ya da düğmeye bastığınızda uyanır, tepki verir, konuşur ve beş mini oyun oynatır. 20 saniye "
  "dokunulmazsa yeniden uyur; ana işlemci kapanır, ekranı ayakta tutan küçük düşük güç çekirdeği çalışmaya devam eder.")
P("İki kasa seçeneği aynı elektroniği kullanır: <b>kedi</b> (kulaklarda düğmeler) ve <b>puf yıldız</b> (yan kollarda düğmeler). "
  "Yalnızca ön kabuk değişir; iç taşıyıcı, arka kapak, düğme kapakları ve yazılım ortaktır. Kedi mi yıldız mı "
  "çizileceğini menüden seçersiniz.")
H2("Bu pakette ne var?")
table([["Klasör / dosya", "İçerik"],
       ["Pocket_Pal_Yapim_Kilavuzu.pdf", "Bu kılavuz"],
       ["malzeme_listesi.csv", "Malzeme listesi (Excel ile açılır, noktalı virgül ayraçlı)"],
       ["stl/", "Baskıya hazır STL dosyaları (doğru baskı yönünde) + ekran koruyucu kesim şablonu (SVG)"],
       ["yazilim/hazir/pocketpal_tam.bin", "Hazır yazılım: tarayıcıdan tek dosya olarak yüklenir (0x0 adresine)"],
       ["yazilim/pocketpal/", "Tam kaynak kodu (ESP-IDF v5.5 projesi, C++) + LP çekirdek programı + ekran simülatörü"],
       ["cad/", "Parametrik CAD (Python) – ölçüleri değiştirip STL'leri yeniden üretmek için"],
       ["gorseller/", "Kılavuzdaki tüm görseller ve ekran görüntüleri"]],
      [58 * mm, 116 * mm])
P("Aynı dosyalar GitHub deposunda da var: <b>github.com/denderden5621/PocketPal</b>. Depoda klasör adları İngilizcedir: "
  "<font name='DVM'>stl/</font>, <font name='DVM'>firmware/prebuilt/</font> (hazır yazılım), <font name='DVM'>firmware/</font> (kaynak), "
  "<font name='DVM'>cad/</font>, <font name='DVM'>images/</font>, <font name='DVM'>docs/</font> (bu kılavuz ve malzeme listesi).")
H2("Bu sürümde tasarımda yapılan değişiklikler")
P("Öncelik sırası <b>1) ucuzluk, 2) kolay montaj ve kablolama</b> olarak yeniden gözden geçirildi. Onaylanan tasarım belgesine göre şunlar değişti:")
table([["Değişiklik", "Neden"],
       ["Piezo <b>D6</b> yerine <b>D7</b> pinine", "D6, çipin UART TX pinidir; her açılışta ve her uykudan uyanışta açılış mesajlarını basar. Piezo bu pine bağlı olsaydı her 2–5 dakikada bir cızırdardı. D7 açılışta sessiz kalır."],
       ["Puf yıldız 60 mm yerine <b>73 × 70 mm</b>", "Ortak elektronik çekirdeği 47 mm'lik yuvarlak bir karedir. 60 mm'lik yıldızın iç köşeleri bu çekirdeğin içine düşüyor ve yıldız \"yuvarlak kare\" gibi görünüyordu. Yıldızın iç yarıçapı çekirdeği saracak kadar büyütüldü; kedi ölçüsü değişmedi."],
       ["Vidalar <b>M2×10</b> (M2×6 değil)", "Vidalar arka kapaktan geçip ön kabuktaki sütunlara girer; 6 mm vida yeterince tutmazdı."],
       ["LIS3DH'de <b>CS → VIN</b> köprüsü", "Ucuz modüllerin bir kısmında CS pini boşta bırakılmıştır; boşta kalırsa I2C çalışmayabilir. Tek damla lehimle kesin çözüm."],
       ["Ekran adaptörü için <b>pin sırası kontrolü</b>", "Bazı FPC adaptörlerinde temaslar ters taraftadır (1↔10). Kılavuz iki tipi de veriyor: A tipi (düz) ve B tipi (ters); bağlantı tablosunda B tipi için ayrı sütun var."],
       ["İvmeölçer için <b>Eğim yönü</b> ayarı", "Ucuz LIS3DH modüllerinde eksenlerin yönü farklı olabilir. Menüden 4 yönden biri seçilir; modülü belirli bir yönde yapıştırmak gerekmez."],
       ["Beşinci oyun: <b>Tepki</b>", "Düello (iki kişilik) korunarak tek kişilik bir refleks oyunu eklendi; ek donanım yok."],
       ["Uyku sırasında sızıntıya karşı önlemler", "Uykuda düşük tutulan pinlerin iç pull-up dirençleri kapatılır (pin başına ~70 µA tasarruf); göz kırpma beklemeleri hafif uykuda yapılır; hareketle uyanma kapalıyken ivmeölçer tamamen kapatılır."]],
      [52 * mm, 122 * mm])
box("Pil artısı açma/kapama anahtarından geçtiği için <b>USB ile şarj ederken anahtar AÇIK</b> olmalıdır. Anahtar kapalıyken pil tamamen ayrılır (saklama ve kargo için).", "note")

# ============================================================ 2 MALZEME
H1("2. Malzeme listesi")
P("Fiyatlar KDV dahil, 17 Ekim 2026 itibarıyla. Ekran fiyatı e-komponent'te kontrol edildi; \"tahmini\" yazanları sipariş öncesi "
  "kontrol edin. En pahalı kalem ekrandır (≈ yarısı): arkadaşlarla birlikte 10 adet ve üzeri sipariş edilirse adet fiyatı 729 TL'ye düşer.")
PARTS = [
    ("Ekran", "Sharp LS013B7DH03, 1,28\" 128×128 bellek LCD", "1", "e-komponent", "941 (10+ adet: 729)", "Yurt dışı stoktan 7–10 iş günü. Cam: yalnızca kenarından tutun."),
    ("Ekran adaptörü", "10 pin 0,5 mm FPC → 2,54 mm adaptör, <b>konnektörü lehimli</b>", "1", "yerel elektronikçi / direnc.net", "≈ 40 (tahmini)", "Konnektörü lehimli olanı alın: ince aralıklı lehim gerekmez."),
    ("Kontrolcü", "Seeed Studio XIAO ESP32-C6", "1", "motorobit, Trendyol (Seeed), e-komponent", "≈ 450 (tahmini)", "Üzerinde LiPo şarj devresi var. Pin başlığı LEHİMLENMEMİŞ olanı alın."),
    ("İvmeölçer", "LIS3DH modülü (I2C)", "1", "direnc.net", "≈ 200–400 (tahmini)", "Güç LED'i varsa sökün."),
    ("Pil", "LiPo 502030, 3,7 V ~250 mAh, <b>koruma devreli</b>, kablolu", "1", "n11 / Hepsiburada (\"devreli\"), Robotistan", "≈ 120 (tahmini)", "5 × 20 × 30 mm. İlanda \"devreli\" yazmalı."),
    ("Hoparlör", "20 mm pasif piezo disk, kablolu", "1", "yerel elektronikçi", "≈ 15", "Düz pirinç disk; içinde osilatör olan \"aktif buzzer\" DEĞİL."),
    ("Düğme", "6 × 6 mm tact düğme, 5 mm yükseklik, 4 bacaklı", "2", "yerel", "≈ 5", ""),
    ("Anahtar", "Mini sürgülü anahtar SS12D00 (3 bacak)", "1", "yerel", "≈ 5", ""),
    ("Diyot", "1N4148", "1", "yerel", "≈ 1", "Uyandırma pinini paylaştırır."),
    ("Direnç", "1 MΩ, 1/4 W veya 1/8 W", "2", "yerel", "≈ 1", "Pil ölçümü bölücüsü."),
    ("Kablo", "30 AWG silikon kablo; en az kırmızı, siyah + 2 renk", "~1,5 m", "yerel", "≈ 40", "Silikon kablo ince ve yumuşaktır. Tablodaki renkler öneridir."),
    ("Vida", "M2 × 10 kendinden kılavuzlu (sac/plastik) vida", "4", "hırdavat / elektronikçi", "≈ 10", "Ön kabuğun sütunlarına doğrudan girer, insert gerekmez."),
    ("Halka", "20–25 mm anahtarlık halkası", "1", "kırtasiye / hırdavat", "≈ 5", ""),
    ("Bant", "Kapton bant, ince çift taraflı bant (en fazla 0,5 mm), ısıyla daralan makaron", "az", "yerel", "≈ 30", "Kalın köpük bant KULLANMAYIN: ekranın altında yer yok."),
    ("Ekran koruyucu", "En fazla 0,7 mm şeffaf plastik: ince akrilik/PET levha ya da şeffaf blister ambalaj, 26,6 × 30,3 mm", "1", "hobi dükkânı / geri dönüşüm", "0–20", "Daha kalını camı sıkıştırır. stl/ekran_kapagi_sablon.svg 1:1 kesim şablonu."),
    ("Filament", "PLA; kedi seti ≈ 18 g, yıldız seti ≈ 25 g", "—", "—", "≈ 10–15", "Düğme kapakları farklı renkte basılabilir."),
]
table([["Parça", "Seçilen ürün", "Adet", "Türkiye'de nereden", "Fiyat (TL)", "Not"]] +
      [[a, b, c, d, e, f] for (a, b, c, d, e, f) in PARTS],
      [19 * mm, 42 * mm, 12 * mm, 30 * mm, 23 * mm, 48 * mm])
P("<b>Toplam:</b> ≈ 1.870 – 2.100 TL / adet. Elinizde zaten olan kablo, bant ve filament düşülürse ≈ 1.790 – 2.010 TL; ekran 10+ adet alınırsa ≈ 1.660 – 1.890 TL.")
H2("Gereken aletler")
table([["Alet", "Not"],
       ["Havya (ince uçlu, 300–350 °C) + 0,5–0,8 mm lehim teli + flux", "XIAO arkasındaki iki pil pedi dışında tüm lehimler 2,54 mm aralıklıdır."],
       ["Kablo sıyırıcı, yan keski, cımbız", ""],
       ["Küçük yıldız tornavida (PH0)", "M2 vidalar için."],
       ["Multimetre (µA kademeli olursa daha iyi)", "Süreklilik testi ve isteğe bağlı uyku akımı ölçümü."],
       ["3D yazıcı (FDM, 0,4 mm nozül) ve PLA", ""],
       ["USB-C <b>veri</b> kablosu ve Chrome/Edge yüklü bilgisayar", "Sadece şarj kablosuyla yazılım yüklenmez."],
       ["Süper yapıştırıcı ya da ince çift taraflı bant", "Piezo diski kapağa tutturmak için."]],
      [80 * mm, 94 * mm])

# ============================================================ 3 BASKI
H1("3. 3D baskı")
story.append(img("05_baski_yonleri.png", cap="STL dosyaları doğru baskı yönünde kaydedildi: dilimleyiciye sürükleyip bırakmanız yeterli."))
table([["Dosya", "Adet", "Yön", "Not"],
       ["kedi_on_kabuk.stl <i>veya</i> yildiz_on_kabuk.stl", "1", "Yüzü tablada", "Pencere ve düğme delikleri destek istemez. İlk katmanlardaki hafif sarkma normaldir."],
       ["tasiyici.stl", "1", "Arka uçları tablada", "Taban, en fazla ~21 mm'lik kısa köprülerle basılır; varsayılan köprü ayarı ve fan %100 yeterli."],
       ["arka_kapak.stl", "1", "Düz yüzü tablada", ""],
       ["dugme_kapagi.stl", "2", "Flanş tablada", "Küçük parça: \"minimum katman süresi\" 8–10 sn olsun. İsterseniz başka renk."]],
      [52 * mm, 12 * mm, 30 * mm, 80 * mm])
P("<b>Ayarlar:</b> PLA · 0,2 mm katman · 4 çevre duvarı (1,6 mm) · 4 üst / 4 alt katman · %20 dolgu · destek yok · tabla 60 °C. "
  "Baskıdan sonra taşıyıcının vida sütunu boşluklarına ve düğme yuvalarına göz atın; varsa ince ipleri bıçakla temizleyin.")
box("Bir set (ön kabuk + taşıyıcı + kapak + 2 düğme kapağı) yazıcıya göre yaklaşık 3–5 saat sürer; hepsi tek tablaya sığar. PLA 55–60 °C'de yumuşar: "
    "anahtarlığı sıcak arabada bırakmayın. Aynı dosyalar PETG ile de değişiklik yapmadan basılabilir.", "tip")

# ============================================================ 4 YAZILIM
H1("4. Yazılımı yükleyin (önce bunu yapın)")
P("Yazılımı XIAO'ya <b>hiçbir şey lehimlemeden önce</b> yüklemek en kolayıdır: kart çıplakken USB sorunlarını ayırt etmek basittir. "
  "Yazılım daha sonra da aynı USB-C girişinden güncellenebilir.")
H2("Yöntem A – Tarayıcıdan (önerilen, kurulum gerektirmez)")
steps([("Chrome ya da Edge açın", "Adres: <b>https://espressif.github.io/esptool-js/</b> (Espressif'in resmi web yükleyicisi)."),
       ("XIAO'yu USB-C veri kablosuyla takın", "\"Connect\"e basın ve listeden <i>USB JTAG/serial debug unit</i> girişini seçin. Görünmüyorsa: XIAO üzerindeki <b>B (BOOT)</b> düğmesini basılı tutarak USB'yi takın, sonra bırakın."),
       ("Dosyayı seçin", "Flash Address: <b>0x0</b> · File: <b>pocketpal_tam.bin</b> (pakette <font name='DVM'>yazilim/hazir/</font>, GitHub deposunda <font name='DVM'>firmware/prebuilt/</font>)"),
       ("\"Program\"a basın", "Yaklaşık 20 saniye sürer. Bitince XIAO üzerindeki <b>R (RESET)</b> düğmesine basın ya da USB'yi çekip takın."),
       ("Kontrol", "Ekran henüz bağlı olmadığı için görünür bir şey olmaz; bu normaldir. İsterseniz \"Console\" sekmesinde <i>ekran hazır</i> ve <i>LIS3DH bulunamadı</i> satırlarını görürsünüz.")])
H2("Yöntem B – Kaynaktan derleme (kodu değiştirmek isteyenler için)")
P("ESP-IDF <b>v5.5</b> kurun (Windows için \"ESP-IDF Tools Installer\", ya da VS Code ESP-IDF eklentisi). Sonra:")
story.append(Paragraph("cd yazilim/pocketpal      (GitHub deposunda: cd firmware)<br/>idf.py set-target esp32c6<br/>idf.py build<br/>idf.py -p COM5 flash monitor   (Linux/Mac: -p /dev/ttyACM0)", S["mono"]))
P("Pinler, zaman aşımları, gece saatleri ve pil eşikleri tek bir dosyada toplanmıştır: <b>main/config.h</b>. "
  "Arduino IDE kullanılmaz: Arduino'nun hazır ESP32-C6 kütüphaneleri, uykuda ekranı canlı tutan düşük güç (LP) çekirdeğini desteklemiyor.")

# ============================================================ 5 KABLOLAMA
H1("5. Kablolama")
P("Önce her şeyi masada, kasa olmadan kablolayıp test edeceksiniz (bölüm 6). Kablolar, parçalar kasaya yerleştikten sonra da yetecek "
  "uzunlukta kesilir. Sıra: ekran adaptörü → ivmeölçer → düğmeler ve piezo → <b>en son</b> güç (pil ve anahtar).")
box("Pil, bölüm 5.4'e kadar hiçbir yere bağlı olmamalı. Pil kablolarını en son ve anahtar KAPALI konumdayken lehimleyin. LiPo uçlarını asla birbirine değdirmeyin.", "warn")
story.append(img("20_kablolama_semasi.png", cap="XIAO'nun her pininin nereye gittiği. Kartı metal kalkanı size bakacak, USB-C yukarıda olacak şekilde tutun."))
H2("Bağlantı tablosu (lehimledikçe işaretleyin)")
P("Adaptör pin numaraları <b>A tipi</b> adaptör içindir. Adaptörünüz <b>B tipi</b> (ters) çıkarsa (bkz. 5.1) son sütundaki numarayı kullanın: "
  "B tipinde adaptör pin no. = 11 − A tipindeki no. Renkler öneridir; kırmızı (3V3 ve pil +) ve siyah (GND) dışında elinizdeki renkleri kullanıp kablo uçlarını etiketleyebilirsiniz.")
CONN = [
    ["", "Nereden", "Nereye", "Renk", "Uzunluk", "B tipi adaptörde"],
    ["S1", "XIAO D8", "Adaptör pin 1 (SCLK)", "sarı", "6 cm", "pin 10"],
    ["S2", "XIAO D10", "Adaptör pin 2 (SI)", "yeşil", "6 cm", "pin 9"],
    ["S3", "XIAO D9", "Adaptör pin 3 (SCS)", "mavi", "6 cm", "pin 8"],
    ["S4", "XIAO D2", "Adaptör pin 4 (EXTCOMIN)", "mor", "6 cm", "pin 7"],
    ["S5", "XIAO 3V3", "Adaptör pin 7 (VDD)", "kırmızı", "6 cm", "pin 4"],
    ["S6", "XIAO GND", "Adaptör pin 9 (VSS)", "siyah", "6 cm", "pin 2"],
    ["—", "Adaptör 5-6-7-8", "birbirine köprü (3V3)", "kırmızı", "1,5 cm", "pin 3-4-5-6"],
    ["—", "Adaptör 9-10", "birbirine köprü (GND)", "siyah", "1 cm", "pin 1-2"],
    ["L1", "Adaptör pin 8", "LIS3DH VIN", "kırmızı", "4 cm", "pin 3"],
    ["L2", "Adaptör pin 10", "LIS3DH GND", "siyah", "4 cm", "pin 1"],
    ["L3", "XIAO D4", "LIS3DH SDA", "turkuaz", "7 cm", ""],
    ["L4", "XIAO D5", "LIS3DH SCL", "turuncu", "7 cm", ""],
    ["L5", "LIS3DH INT1", "1N4148 katot (bant); diyotun anot bacağı XIAO D0'a", "beyaz", "7 cm", ""],
    ["—", "LIS3DH CS", "LIS3DH VIN (modül üzerinde kısa köprü)", "kırmızı", "1 cm", ""],
    ["T1", "XIAO D0", "Sol düğmenin herhangi bir bacağı (bacak a)", "beyaz", "10 cm", ""],
    ["T2", "XIAO D3", "Sağ düğmenin herhangi bir bacağı (bacak a)", "gri", "10 cm", ""],
    ["T3", "Sol düğme, a'ya çapraz bacak", "Sağ düğme, a'ya çapraz bacak (ortak GND)", "siyah", "8 cm", ""],
    ["T4", "Sağ düğme, a'ya çapraz bacak", "XIAO GND", "siyah", "10 cm", ""],
    ["P1", "Piezo kırmızı", "XIAO D7", "(piezonun kablosu)", "8 cm", ""],
    ["P2", "Piezo siyah", "XIAO GND", "(piezonun kablosu)", "8 cm", ""],
    ["G1", "Anahtarın kenar bacağı", "XIAO arka yüz BAT+", "kırmızı", "4 cm", ""],
    ["—", "R1 (1 MΩ)", "anahtarın aynı kenar bacağı ↔ orta nokta", "direnç bacağı", "—", ""],
    ["—", "R2 (1 MΩ)", "orta nokta ↔ XIAO BAT−", "direnç bacağı", "—", ""],
    ["G2", "R1/R2 orta noktası", "XIAO D1", "kahverengi", "5 cm", ""],
    ["G3", "Pil kırmızı", "Anahtarın orta bacağı (anahtar KAPALI)", "(pilin kablosu)", "kısaltın: 4 cm", ""],
    ["G4", "Pil siyah", "XIAO arka yüz BAT− (en son)", "(pilin kablosu)", "kısaltın: 5 cm", ""],
]
table([[("☐ " + r[0]) if i and r[0] != "—" else r[0]] + r[1:] for i, r in enumerate(CONN)],
      [12 * mm, 38 * mm, 60 * mm, 22 * mm, 19 * mm, 23 * mm])
box("Bazı deliklere birden fazla iletken girer: <b>D0</b> (T1 + diyotun anot bacağı) ve <b>GND</b> (S6 + T4 + P2, üç kablo). Uçları 3 mm soyun, birbirine bükün, birlikte deliğe sokup tek seferde lehimleyin.", "tip")

H2("5.1 Ekran adaptörü")
story.append(img("21_fpc_adaptor.png", cap="Adaptör kartındaki numaralara göre iki olası sıra. Hangisinin geçerli olduğunu şerit kablonun ucundaki numaralardan anlarsınız."))
steps([("Adaptör tipini belirleyin", "Ekran şeridinin uç kısmındaki 1 ve 10 işaretlerine bakın, şeridi konnektöre takılacağı gibi tutun. Şeridin 1. teması adaptörün 1. pinine denk geliyorsa <b>A tipi</b>, 10. pinine denk geliyorsa <b>B tipi</b>. Tipi adaptörün üzerine kalemle yazın."),
       ("Köprüleri yapın", "A tipi: pin 5-6-7-8 birbirine (3V3), pin 9-10 birbirine (GND). B tipi: pin 3-4-5-6 ve pin 1-2. Komşu pinleri kısa bir tel ya da lehim damlasıyla birleştirin."),
       ("Altı kabloyu lehimleyin", "S1…S6. B tipi adaptörde bağlantı tablosunun son sütunundaki pin numaralarını kullanın."),
       ("Şeridi henüz takmayın", "Ekran testte takılır, testten sonra çıkarılır ve montajda (Montaj 2) yeniden takılır. Konnektörün kilit kapağını her seferinde nazikçe açın.")])
box("Ekranı adaptöre takmadan önce multimetreyle kontrol edin: XIAO 3V3 ile GND arasında kısa devre olmamalı. Yanlış sırayla bağlanan ekran çalışmaz ve zarar görebilir; ilk açılışta ekranda 2 saniye içinde yüz çıkmazsa USB'yi hemen çekin.", "warn")

H2("5.2 İvmeölçer ve uyandırma diyotu")
story.append(img("22_lis3dh_diyot.png", cap="INT1 → diyot → D0. Diyotun siyah bandı INT1 tarafında."))
steps([("Modülü inceleyin", "Üzerinde güç LED'i varsa havyayla sökün ya da yolunu kesin. LED açık kalırsa pil ~10 günde biter."),
       ("CS → VIN köprüsü", "Modülün CS pinini VIN pinine kısa bir telle bağlayın. SDO boş kalır (yazılım iki adresi de dener)."),
       ("Dört kablo", "L1 ve L2 adaptörden gelir (3V3 ve GND), L3 ve L4 XIAO'ya gider."),
       ("Diyot", "1N4148'in bantlı (katot) bacağına INT1'den gelen kabloyu (L5) lehimleyin. Bantsız (anot) bacağını sol düğme kablosuyla (T1) birlikte D0 deliğine sokup lehimleyin. Diyotu makaronla sarın.")])

H2("5.3 Düğmeler ve piezo")
P("Her 6×6 düğmenin dört bacağı ikişer ikişer içeriden bağlıdır; herhangi bir bacağı (\"bacak a\") ve ona <b>çapraz</b> olan bacağı kullanırsanız her zaman doğru çalışır. "
  "Düğme kabloları kabuktaki yuvalara gideceği için 10 cm bırakın; kabuk açılıp kapanabilsin. T3 ortak toprak kablosu iki düğmeyi birbirine, "
  "T4 de sağ düğmeyi XIAO GND'ye bağlar. Piezonun kendi kabloları D7 (kırmızı) ve GND'ye (siyah) gider; piezo arka kapağa yapışacağı için 8 cm yeterlidir.")

H2("5.4 Güç: pil, anahtar ve pil ölçümü (en son)")
story.append(img("23_guc_bolucu.png", cap="Pil artısı anahtardan geçer; 2 × 1 MΩ bölücü pil gerilimini ölçmek için D1'e gider."))
steps([("Anahtarı hazırlayın (pil yok)", "Kenar bacaklardan birine 4 cm kırmızı kablo (G1) ve R1'in bir bacağını birlikte lehimleyin. Bu bacağı <b>kullanılan kenar bacak</b> olarak işaretleyin; diğer kenar bacak boş kalır."),
       ("Bölücü", "R1'in boş bacağını R2'nin bir bacağıyla uç uca lehimleyin (orta nokta). Orta noktaya kahverengi kabloyu (G2) ekleyin. Makaronla sarın."),
       ("XIAO arka yüz", "G1'i <b>BAT+</b> pedine, R2'nin boş bacağını <b>BAT−</b> pedine, G2'yi D1'e lehimleyin."),
       ("KAPALI konumu bulun", "Multimetreyi süreklilik (bip) konumuna alın. Sürgüyü orta bacak ile kullanılan kenar bacak arasında <b>bip sesi gelmeyecek</b> konuma getirin: bu KAPALI'dır. Hangi tarafın KAPALI olduğunu not edin; montajdan sonra kasanın arkasına işaretleyeceksiniz."),
       ("Pili bağlayın", "Anahtar KAPALI iken: pil kablolarını tek tek kesin (ikisini birden kesmek kısa devre yapar), kırmızıyı ~4 cm bırakıp anahtarın <b>orta</b> bacağına (G3), en son siyahı ~5 cm bırakıp <b>BAT−</b> pedine (G4) lehimleyin. Pedlerin üzerine Kapton bant yapıştırın.")])

# ============================================================ 6 TEST
H1("6. Masada test")
P("Her şey kasa dışındayken, <b>pil anahtarı KAPALI</b> ve XIAO USB'ye takılıyken yapın. Ekran şeridini adaptöre takın (temas yüzü konnektörün temaslarına bakacak şekilde, kilit kapağını kapatın).")
screens([("kedi_bubble", "1 · Açılış: 1–2 sn içinde \"Miyav!\""), ("kedi_love", "2 · Sağ düğme: kalp gözler"),
         ("kedi_bubble2", "3 · Sol düğme: konuşur"), ("menu", "4 · İki düğme birlikte: menü")])
table([["Test", "Ne yapın", "Ne görmelisiniz"],
       ["Ekran", "USB'yi takın", "Mutlu kedi yüzü ve \"Miyav! Selam!\" balonu, kısa bir melodi."],
       ["Düğmeler", "Sol kısa, sağ kısa, ikisi birlikte", "Sol: konuşma balonu · Sağ: kalp gözler + mırlama sesi · İkisi: menü."],
       ["İvmeölçer", "Modüle iki kez hızlıca vurun; LIS3DH'yi sağa yatırın", "Çift vuruşta oyun listesi açılır; sallayınca \"Başım döndü!\". Sağa yatırınca gözler sağa kaymalı; kaymıyorsa menü → <b>Eğim yönü</b>'nü doğru olana kadar değiştirin (4 seçenek). Bunu montajdan sonra kasayla bir kez daha deneyin."],
       ["Ses", "Menü → Ses: Açık", "Her harekette kısa bip/melodi. Ses yoksa piezo kablolarını (D7/GND) kontrol edin."],
       ["Pil ölçümü", "Pil anahtarını AÇIN, menü → Durum", "%… ve ~3,7–4,2 V. \"Pil ölçülemiyor\" yazıyorsa bölücü/D1 bağlantısını kontrol edin."],
       ["Uyku ve uyanma", "USB'yi çekin, 20 sn dokunmayın", "Yüz ekranda kalır (uyku). Sol düğme uyandırır. Sallayınca kısa bir bakış atıp yeniden uyur."]],
      [24 * mm, 56 * mm, 94 * mm])
box("Görüntü baş aşağıysa: menü → <b>Ekranı çevir</b>. Bu ayar kalıcıdır ve eğim yönünü de birlikte çevirir.", "tip")
box("Testler bitince anahtarı KAPALI konuma alın, USB'yi çekin ve <b>ekran şeridini konnektörden çıkarın</b> (kilit kapağını açarak). Ekran, montajda adaptör yerine yapıştırıldıktan sonra yeniden takılır.", "note")
H2("İsteğe bağlı: uyku akımı ölçümü")
P("Multimetreyi µA kademesine alın. Anahtarı AÇIK konuma getirin, USB'yi çekin ve cihazın uykuya geçmesini bekleyin (20 sn). Probları anahtarın "
  "<b>orta</b> bacağına ve <b>kullanılan kenar</b> bacağına tutun, sonra anahtarı KAPATIN: akım artık ölçüm aletinin içinden geçer. "
  "Cihazı µA kademesinde açmaya çalışmayın; açılış akımı ölçüm aletinin direncinde gerilim düşürüp kartı yeniden başlatabilir. "
  "Uykuda <b>~40–60 µA</b> beklenir (XIAO ~15, ekran ~5–15, LIS3DH ~2–6, bölücü ~2 µA, göz kırpma uyanışlarının ortalaması 10–20 µA; ölçüm anında 2–5 dakikada bir kısa sıçramalar görürsünüz). "
  "1 mA civarı sabit bir değer, LIS3DH üzerinde unutulmuş bir LED'i gösterir.")

# ============================================================ 7 MONTAJ
H1("7. Kasaya montaj")
P("Testler bitince lehimli hiçbir kabloyu sökmeden parçaları yerleştirin (ekran şeridi testten sonra çıkarılmış olmalı). Sıra önemlidir: önce ön katman taşıyıcının içinden öne geçer, sonra arka katman yerine oturur.")
story.append(img("03_patlatilmis.png", cap="Parçaların sırası, önden arkaya."))
H2("Montaj 1 – Ön katman")
story.append(img("10_montaj_on_katman.png", width=150 * mm))
steps([("Adaptörü ve LIS3DH'yi öne geçirin", "Taşıyıcıyı ön yüzü yukarı bakacak şekilde tutun. Ekran şeridi takılı DEĞİLKEN adaptörü ve LIS3DH'yi (kabloları XIAO'ya lehimli hâlde) arkadan, büyük alt pencereden yan çevirerek öne geçirin."),
       ("Adaptör", "Alt bölgeye, konnektörü öne ve aşağı kenara bakacak şekilde ince (en fazla 0,5 mm) çift taraflı bantla yapıştırın."),
       ("LIS3DH", "Adaptörün üstündeki bölgeye aynı ince bantla yapıştırın. Çip öne (ekrana) bakmalı; dönüş yönü önemli değil (menüden Eğim yönü ayarlanır). Kabloları pencereden arkaya inmeli.")])
H2("Montaj 2 – Ekran")
story.append(img("11_montaj_ekran.png", width=150 * mm))
steps([("Şeridi takın", "Konnektörün kilit kapağını açın, şeridi düz şekilde sonuna kadar itin, kapağı kapatın."),
       ("Ekranı oturtun", "Ekranı, şerit tek ve yumuşak bir kıvrım yapacak şekilde çevirip dudağın içine, doğrudan köşe ayaklarının üstüne yatırın (altına bant ya da köpük koymayın: panel + koruyucu yüksekliği kabuğa tam oturacak şekilde hesaplandı)."),
       ("Koruyucu", "Şablona göre kestiğiniz, en fazla 0,7 mm kalınlıktaki şeffaf koruyucuyu ekranın üstüne koyun (koruyucu filmini soyun).")])
box("Şerit kablo camın dibinden keskin bükülürse ekran kalıcı olarak bozulur. Kıvrım, şeridin uzak ucunda ve geniş olmalı.", "warn")
H2("Montaj 3 – Arka katman")
story.append(img("12_montaj_arka_katman.png", width=150 * mm))
steps([("XIAO", "Taşıyıcıyı ters çevirin. XIAO'yu iki rayın arasına, USB-C alt kenarda ve metal kalkan öne (ekrana) bakacak şekilde bastırın."),
       ("Anahtar", "Sürgülü anahtarı yuvasına, kolu arkaya bakacak şekilde yerleştirin."),
       ("Pil", "Pilin taşıyıcıya bakan yüzüne Kapton bant yapıştırın, pili üstteki kaburgaların arasına koyun; kabloları çentikten aşağı insin."),
       ("Kablo düzeni", "Kabloları cep kenarlarındaki kanallara yatırın; hiçbir kablo pilin ya da XIAO'nun üzerinden geçmesin.")])
H2("Montaj 4 – Piezo")
story.append(img("13_montaj_piezo.png", width=150 * mm))
P("Piezo diski arka kapağın iç yüzündeki sığ çukura, pirinç yüzü kapağa gelecek şekilde koyun ve kenarından üç nokta süper yapıştırıcıyla tutturun. "
  "Kapağın tamamı ses tablası gibi çalışır; ses delikleri diskin tam arkasındadır.")
H2("Montaj 5 – Düğmeler")
story.append(img("14_montaj_dugmeler_kedi.png", width=130 * mm, cap="Kedi kabuğu"))
story.append(img("15_montaj_dugmeler_yildiz.png", width=130 * mm, cap="Yıldız kabuğu"))
steps([("Kapaklar", "Kabuğu yüzü aşağı bakacak şekilde tutun. Düğme kapaklarını <b>kabuğun içinden</b>, kubbe dışarı bakacak şekilde deliklerine sokun; geniş flanş içteki havşaya oturur."),
       ("Düğmeler", "Kablolu düğmeleri kabuğun içinden yuvalarına, bacaklar arkaya bakacak şekilde sonuna kadar bastırın. Gevşekse bir damla yapıştırıcı."),
       ("Deneyin", "Kapağa bastığınızda net bir \"tık\" hissetmelisiniz.")])
H2("Montaj 6 – Taşıyıcıyı kabuğa yerleştirin")
story.append(img("16_montaj_kabuga.png", width=150 * mm))
P("Kabuğu yüzü aşağı bakacak şekilde yumuşak bir bezin üzerine koyun. Taşıyıcıyı, ekran pencereye bakacak ve USB-C alt kenardaki ağza denk gelecek "
  "şekilde vida sütunlarının arasından indirin. Düğme kablolarını taşıyıcıdaki düğme boşluklarından geçirip kenarlara yatırın.")
H2("Montaj 7 – Arka kapak ve vidalar")
story.append(img("17_montaj_kapatma.png", width=150 * mm))
steps([("Kapağı yerleştirin", "Piezo kablolarını sıkıştırmadan arka kapağı, anahtar kolu yarıktan çıkacak şekilde oturtun."),
       ("Vidalayın", "4 × M2×10 vidayı çapraz sırayla takın. Sıkı ama zorlamadan: PLA sütunun dişi sıyrılabilir."),
       ("Son kontrol", "Anahtarı AÇIN, sol düğmeye basın: yüz uyanmalı. Bölüm 5.4'te bulduğunuz AÇIK tarafı arka kapakta sürgünün yanına kalemle işaretleyin. Kasayı sağa yatırıp gözlerin sağa kaydığını kontrol edin (gerekirse menü → Eğim yönü). Halkayı anahtarlık deliğine takın.")])

# ============================================================ 8 KULLANIM
H1("8. Kullanım")
story.append(img("06_kontroller.png", width=150 * mm))
H2("Yüz ve ruh hâli")
P("Pocket Pal'ın ruh hâli ne kadar ilgilendiğinize bağlıdır: oynadıktan ya da sevdikten sonra bir süre mutlu bekler, 2 saatten uzun "
  "dokunulmazsa sıkılır, 6 saatten sonra uykulu görünür. Saat ayarlıysa 23:00–07:00 arası uyur ve uyanınca \"Uykum var...\" der. "
  "Pil azaldığında üzgün yüz ve pil simgesi gösterir.")
screens([("kedi_neutral", "Normal"), ("kedi_happy", "Mutlu"), ("kedi_love", "Sevildi"), ("kedi_surprised", "Şaşkın (vuruş)"),
         ("kedi_dizzy", "Başı dönmüş (salla)"), ("kedi_bored", "Sıkılmış"), ("kedi_sleeping", "Uyuyor (gece)"), ("kedi_lowbat", "Pil azaldı"),
         ("yildiz_neutral", "Yıldız: normal"), ("yildiz_happy", "Yıldız: mutlu"), ("yildiz_wink", "Yıldız: göz kırpar"), ("yildiz_sleeping", "Yıldız: uyuyor")])
H2("Oyunlar")
P("Oyun listesine iki yoldan ulaşılır: kasaya <b>çift vuruş</b> ya da <b>sağ düğmeye uzun basış</b>. Sol düğme listede aşağı iner, sağ düğme seçer. "
  "Oyunun içinde <b>sol düğmeye uzun basmak</b> çıkar. Rekorlar kalıcı olarak saklanır.")
screens([("oyun_zipla", "Zıpla"), ("oyun_yakala", "Yakala"), ("oyun_hafiza", "Hafıza"), ("oyun_tepki", "Tepki"), ("oyun_duello", "Düello")], per_row=5, w=31 * mm)
table([["Oyun", "Nasıl oynanır"],
       ["Zıpla", "Kahraman koşar; düğmeye basın ya da kasaya vurun, kutuların (yıldızda meteorların) üzerinden atlayın. Her 5 engelde hız artar."],
       ["Yakala", "Kasayı sağa-sola eğerek (ya da düğmeleri basılı tutarak) balıkları/yıldızları yakalayın, bombalardan kaçın. 3 can."],
       ["Hafıza", "Sol/sağ ışık ve ses sırasını izleyin, aynı sırayla tekrarlayın. Her turda sıra bir uzar."],
       ["Tepki", "Tek kişilik: ekran kararıp \"ŞİMDİ!\" yazınca basın; 5 turun en iyi tepki süreniz (ms) rekor olur."],
       ["Düello", "İki kişilik: biri sol, biri sağ düğmeyi tutar. \"ŞİMDİ!\" yazınca ilk basan turu alır, erken basan kaybeder. 3 tur alan kazanır."]],
      [24 * mm, 150 * mm])
H2("Menü")
table([["Öğe", "Ne yapar"],
       ["Oyunlar", "Oyun listesi"],
       ["Ses: Açık/Kapalı", "Tüm sesleri açar/kapatır"],
       ["Yüz: Kedi/Yıldız", "Ekrandaki yüz stilini kasaya göre seçin"],
       ["Hareket: Açık/Kapalı", "Uykudayken sallama/vuruşla uyanma. Kapalıyken yalnızca sol düğme uyandırır (en uzun pil ömrü)."],
       ["Eğim yönü: 1/4 … 4/4", "İvmeölçerin montaj yönü. Kasayı sağa yatırınca gözler sağa kaymıyorsa doğru olana kadar değiştirin."],
       ["Saati ayarla", "Sol: saat +1, sağ: dakika +5, uzun sağ: kaydet. Gece uyku modu için gereklidir; anahtar kapatılınca ya da pil bitince sıfırlanır."],
       ["Durum", "Pil yüzdesi ve gerilimi, saat, oynanan oyun ve sevgi sayısı; sol düğmeyle rekorlar sayfası"],
       ["Ekranı çevir", "Görüntüyü 180° döndürür"]],
      [40 * mm, 134 * mm])

# ============================================================ 9 PİL
H1("9. Pil ve şarj")
table([["Günlük kullanım", "Günlük tüketim", "Bir şarjla"],
       ["Az: 2 dk oyun", "≈ 1,8 – 2,4 mAh", "≈ 80 – 110 gün (~3 ay)"],
       ["Normal: 5 dk oyun", "≈ 3,3 – 3,9 mAh", "≈ 50 – 60 gün (~2 ay)"],
       ["Yoğun: 15 dk oyun", "≈ 8,3 – 8,9 mAh", "≈ 22 – 24 gün"]],
      [60 * mm, 50 * mm, 64 * mm])
P("Tahminler 200 mAh kullanılabilir kapasite, ~25–40 µA uyku akımı, ortalama 10–20 µA göz kırpma uyanışı ve oyun sırasında ~30 mA içindir; çanta sürekli sallanıyorsa hareketle uyanmalar biraz daha tüketir "
  "(yazılım bunu algılayıp hareketle uyanmayı 5 dakikadan başlayarak artan sürelerle kapatır).")
steps([("Şarj", "Anahtar <b>AÇIK</b> iken USB-C'yi takın; XIAO üzerindeki şarj devresi pili doldurur (250 mAh pil birkaç saatte dolar). Şarj sırasında cihazı normal kullanabilirsiniz."),
       ("Pil azaldı", "~3,5 V altında üzgün yüz + pil simgesi. Oyunlar çalışmaya devam eder."),
       ("Pil bitmek üzere", "~3,3 V altında \"Şarj et\" yazılı uyku yüzü; zamanlayıcı ve hareketle uyanma kapanır, yalnızca sol düğme uyandırır."),
       ("Saklama", "Uzun süre kullanmayacaksanız pili ~%50 doldurup anahtarı kapatın.")])

# ============================================================ 10 SORUN GİDERME
H1("10. Sorun giderme")
table([["Belirti", "Olası neden ve çözüm"],
       ["Ekranda hiçbir şey yok", "Şerit ters ya da tam oturmamış (kilit kapağı) · adaptör tipi (A/B) · köprüler eksik · 3V3/GND kablosu. Konsolda \"ekran hazır\" görünüyorsa sorun kablolamadadır."],
       ["Görüntü ters / ayna", "Menü → Ekranı çevir. Ayna ise main/config.h içinde LCD_MIRROR_X 1 yapıp derleyin."],
       ["Görüntü yavaş yavaş soluyor / gri", "EXTCOMIN (S4, D2) ya da DISP/EXTMODE köprüsü eksik."],
       ["Vuruş, sallama, eğim çalışmıyor", "Konsolda \"LIS3DH bulunamadı\": SDA/SCL yer değiştirmiş, CS→VIN köprüsü yok ya da VIN/GND eksik."],
       ["Gözler eğimin ters yönüne kayıyor", "Menü → Eğim yönü: doğru olana kadar 1/4 … 4/4 arasında değiştirin."],
       ["Sallayınca uyanmıyor ama düğme çalışıyor", "Diyot ters (bant INT1 tarafında olmalı) ya da L5 kopuk. Menü → Hareket: Açık mı?"],
       ["Ses yok", "Menü → Ses: Açık · piezo D7 ve GND'de mi · \"aktif buzzer\" değil, pasif disk mi?"],
       ["Pil yüzdesi yanlış / \"ölçülemiyor\"", "Bölücünün orta noktası D1'de mi, R2 BAT−'de mi? Ölçüm ±%5 civarındadır."],
       ["Şarj olmuyor", "Anahtar KAPALI olabilir. Şarj sırasında anahtar AÇIK olmalıdır."],
       ["Ekran camı baskı izi gösteriyor / çatlak", "Koruyucu 0,7 mm'den kalın ya da ekranın altında bant var. Kalın parçayı inceltin, bandı kaldırın."],
       ["Bilgisayar XIAO'yu görmüyor", "Veri kablosu kullanın · B (BOOT) basılıyken USB'yi takın · başka USB portu deneyin."],
       ["Pil birkaç günde bitiyor", "LIS3DH üzerinde LED · sürekli basılı kalan düğme (kapak sıkışmış) · uyku akımını ölçün (bölüm 6)."]],
      [52 * mm, 122 * mm])

# ============================================================ 11 TEKNİK
H1("11. Teknik notlar")
H2("Pin haritası")
table([["XIAO", "GPIO", "Bağlantı", "Neden bu pin"],
       ["D0", "GPIO0 (LP)", "Sol düğme + LIS3DH INT1 (1N4148 ile)", "Derin uykudan uyandırma pini"],
       ["D1", "GPIO1 (ADC)", "Pil bölücü orta noktası", "Pil ölçümü"],
       ["D2", "GPIO2 (LP)", "Ekran EXTCOMIN", "Uykuda LP çekirdek 1 Hz kare dalga üretir"],
       ["D3", "GPIO21", "Sağ düğme", "Uyanıkken okunur"],
       ["D4 / D5", "GPIO22 / 23", "LIS3DH SDA / SCL", "Donanım I2C"],
       ["D6", "GPIO16", "BOŞ", "UART TX: açılışta veri basar"],
       ["D7", "GPIO17", "Piezo", "PWM ses; açılışta sessiz"],
       ["D8 / D9 / D10", "GPIO19 / 20 / 18", "Ekran SCLK / SCS / SI", "SPI, 1 MHz, LSB önce"],
       ["BAT+ / BAT−", "—", "Anahtar → pil", "Kart üstü LiPo şarj devresi"]],
      [24 * mm, 30 * mm, 62 * mm, 58 * mm])
H2("Yazılım yapısı")
table([["Dosya", "Görev"],
       ["main.cpp", "Uyanma nedenine göre akış: soğuk açılış, zamanlayıcı (göz kırpma), hareket (kısa bakış), düğme (tam oturum)"],
       ["power.cpp", "LP çekirdeği başlatma, derin uyku, uyandırma kaynakları, hareket fırtınası koruması, pil ADC, saat"],
       ["ulp/lp_vcom.c", "LP RISC-V çekirdeği: 0,5 sn'de bir EXTCOMIN'i çevirir (ana işlemci kapalıyken de)"],
       ["display.cpp", "Sharp bellek LCD sürücüsü, yalnızca değişen satırları gönderir; çizim fonksiyonları, Türkçe 5×7 yazı tipi"],
       ["face.cpp", "12 ifade, kedi/yıldız stilleri, konuşma balonları, etkileşimli yüz"],
       ["games.cpp, menu.cpp", "5 oyun ve menü"],
       ["input.cpp, lis3dh.cpp", "Düğme sıçrama önleme, uzun/çift basış; vuruş, çift vuruş, sallama, eğim"],
       ["sound.cpp, store.cpp", "Piezo melodileri (LEDC PWM); ayarlar ve rekorlar (NVS flash)"],
       ["tools/host_sim/", "Ekranı bilgisayarda PNG olarak çizen simülatör (bu kılavuzdaki ekran görüntüleri buradan)"]],
      [40 * mm, 134 * mm])
H2("Güç bütçesi (uyku)")
table([["Bileşen", "Akım", "Not"],
       ["XIAO ESP32-C6 derin uyku", "~15 µA", "Seeed verisi"],
       ["Sharp LS013B7DH03, 1 Hz EXTCOMIN", "~5–15 µA", "ölçülmeli"],
       ["LIS3DH 10 Hz düşük güç + kesme", "~2–6 µA", "modül LED'siz; Hareket: Kapalı ise <1 µA"],
       ["Bölücü 2 × 1 MΩ", "~2 µA", "sürekli"],
       ["LP çekirdek", "~1 µA", "tahmin"],
       ["Göz kırpma uyanışları (2–5 dk'da bir; beklemeler hafif uykuda)", "~10–20 µA ort.", "gece kapalı"]],
      [80 * mm, 34 * mm, 60 * mm])
P("Wi-Fi ve Bluetooth hiç başlatılmaz. Yazılım zamanlayıcı bekçisi (watchdog) donmalarda cihazı yeniden başlatır; ayarlar ve rekorlar korunur.")
H2("Ölçüleri değiştirmek")
P("Tüm kasa parçaları <b>cad/keychain_cad.py</b> içinde parametriktir (Python, manifold3d). Örneğin yıldızın boyutu <i>star_outline()</i> içindeki "
  "R ve r değerleriyle, düğme konumları CAT_BTNS / STAR_BTNS ile değişir. Çalıştırma: <font name='DVM'>python3 keychain_cad.py stl</font>; "
  "çakışma kontrolü: <font name='DVM'>python3 check_fit.py stl</font>.")

def glue(items):
    out, i = [], 0
    while i < len(items):
        f = items[i]
        if isinstance(f, Paragraph) and f.style.name in ("h1", "h2"):
            grp = [f]
            j = i + 1
            while j < len(items) and isinstance(items[j], (Paragraph, CondPageBreak)) and getattr(getattr(items[j], "style", None), "name", "") in ("h1", "h2", ""):
                grp.append(items[j]); j += 1
                if not isinstance(items[j - 1], CondPageBreak):
                    break
            if j < len(items):
                grp.append(items[j]); j += 1
            out.append(KeepTogether(grp))
            i = j
        else:
            out.append(f); i += 1
    return out


doc = Doc(OUT)
doc.multiBuild(glue(story))
print("PDF yazıldı:", OUT)

# malzeme listesi CSV (Excel için ; ayraç + BOM)
import re
def plain(s):
    return re.sub(r"<[^>]+>", "", s).replace("&amp;", "&")
csv_path = os.path.join(os.path.dirname(OUT) or ".", "malzeme_listesi.csv")
with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["Parça", "Seçilen ürün", "Adet", "Türkiye'de nereden", "Fiyat (TL, KDV dahil)", "Not"])
    for r in PARTS:
        w.writerow([plain(x) for x in r])
    w.writerow([])
    w.writerow(["Toplam", "", "", "", "≈ 1.870 – 2.100", "17 Ekim 2026; tahmini fiyatları sipariş öncesi kontrol edin"])
print("CSV yazıldı:", csv_path)
