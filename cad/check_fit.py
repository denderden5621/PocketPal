"""Montaj çakışma kontrolü: parçalar ve elektronik bileşenler birbirine giriyor mu?
Kullanım: python3 check_fit.py <stl_klasoru>"""
import sys, os, numpy as np, trimesh
sys.path.insert(0, os.path.dirname(__file__))
import keychain_cad as K
from manifold3d import Manifold, Mesh

STL = sys.argv[1] if len(sys.argv) > 1 else "stl"
A = os.path.join(STL, "_montaj_konumu")

def M(path):
    t = trimesh.load(path); t.merge_vertices()
    return Manifold(Mesh(vert_properties=np.asarray(t.vertices, dtype=np.float32), tri_verts=np.asarray(t.faces, dtype=np.uint32)))

def components():
    B = K.box
    return {
        "pil": B(-15.5, 15.5, K.BAT_CY - 10.25, K.BAT_CY + 10.25, 2.2, 7.5),
        "xiao_kart": B(-K.XIAO_W / 2, K.XIAO_W / 2, K.XIAO_Y0, K.XIAO_Y1, K.XIAO_Z0, K.XIAO_Z0 + K.XIAO_PCB),
        "usb_c": B(-4.5, 4.5, K.XIAO_Y0 - 0.6, K.XIAO_Y0 + 6.8, K.XIAO_Z0 + K.XIAO_PCB, K.XIAO_Z0 + K.XIAO_PCB + 3.2),
        "xiao_kalkan": B(-6, 6, K.XIAO_Y0 + 8, K.XIAO_Y0 + 19, K.XIAO_Z0 + K.XIAO_PCB, K.XIAO_Z0 + K.XIAO_PCB + 2.0),
        "piezo": K.cyl(20.0, 1.25, 1.7, 0, K.BAT_CY),
        "surgu": B(K.SLIDE_CX - 1.8, K.SLIDE_CX + 1.8, K.SLIDE_CY - 4.3, K.SLIDE_CY + 4.3, 4.0, 7.5),
        "fpc_adaptor": B(-14, 14, -17.3, -6.0, K.Z_FLOOR1 + 0.3, K.Z_FLOOR1 + 3.3),
        "lis3dh": B(-12.7, 12.7, -5.8, 12.0, K.Z_FLOOR1 + 0.3, K.Z_FLOOR1 + 2.9),
        "panel": B(-K.PANEL_W / 2, K.PANEL_W / 2, K.PANEL_BOT, K.PANEL_TOP, K.Z_LEDGE, K.Z_LEDGE + K.PANEL_T),
        "koruyucu": B(-K.PANEL_W / 2, K.PANEL_W / 2, K.PANEL_BOT, K.PANEL_TOP, K.Z_LEDGE + K.PANEL_T, K.Z_CHASSIS_TOP),
    }

if __name__ == "__main__":
    cat = M(os.path.join(A, "kedi_on_kabuk.stl")); star = M(os.path.join(A, "yildiz_on_kabuk.stl"))
    cr = M(os.path.join(A, "tasiyici.stl")); bc = M(os.path.join(A, "arka_kapak.stl"))
    iv = lambda a, b: (a ^ b).volume()
    bad = 0
    pairs = [("kedi∩taşıyıcı", cat, cr), ("yıldız∩taşıyıcı", star, cr), ("kedi∩arka", cat, bc), ("taşıyıcı∩arka", cr, bc)]
    for n, a, b in pairs:
        v = iv(a, b); bad += v > 0.01; print(f"{n:18s} {v:7.3f} mm3")
    for n, c in components().items():
        vs = [iv(c, x) for x in (cr, cat, star, bc)]
        bad += any(v > 0.01 for v in vs)
        print(f"{n:12s} taşıyıcı {vs[0]:6.3f}  kedi {vs[1]:6.3f}  yıldız {vs[2]:6.3f}  arka {vs[3]:6.3f}")
    for nm, btns, sh in [("kedi", K.CAT_BTNS, cat), ("yıldız", K.STAR_BTNS, star)]:
        for (x, y) in btns:
            sw = K.box(x - 3, x + 3, y - 3, y + 3, K.SW_BODY_Z0, K.SW_BODY_Z0 + 3.5) + K.cyl(3.5, K.SW_BODY_Z0 + 3.5, K.SW_BODY_Z0 + 5.0, x, y)
            v1, v2 = iv(sw, sh), iv(sw, cr); bad += (v1 > 0.01) + (v2 > 0.01)
            print(f"{nm} düğme {x:+.1f},{y:+.1f}: kabuk {v1:.3f} taşıyıcı {v2:.3f}")
    print("SONUÇ:", "ÇAKIŞMA YOK" if bad == 0 else f"{bad} çakışma")
