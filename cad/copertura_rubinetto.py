"""Copertura provvisoria per il rubinetto doppio esistente (in attesa della fontanella).

    python3 cad/copertura_rubinetto.py   -> stl/print/20_*.stl, stl/assembly/20_*.stl

Il rubinetto esce dalla parete da 25 cm, a 95 mm dall'angolo, e sporge 175 mm dal muro.
La copertura e' un cappuccio in due pezzi:
  - 20_copertura_rubinetto: guscio che si cala DALL'ALTO sul rubinetto e appoggia sul corpo
    cromato con la feritoia frontale. Copre gomito, comando superiore e prima uscita.
  - 21_fondo_copertura: fondo che si spinge DA SOTTO e si aggancia a scatto ai fianchi.
    Ha l'apertura per l'uscita usata (115..145 mm dal muro) dove si infila la bottiglia.
    Una volta montato resta sotto le uscite e impedisce al guscio di sfilarsi.
Il comando frontale (145..175 mm) resta fuori dal guscio, libero da ruotare.

Coordinate locali: x = distanza dal muro, y = laterale (0 = asse del tubo), z = asse del
corpo del rubinetto. Le misure del rubinetto sono stimate dalle foto: verificale prima di stampare.
"""
import math
import os
import sys

import numpy as np
from shapely.geometry import Polygon, box, Point
from manifold3d import Manifold

sys.path.insert(0, os.path.dirname(__file__))
from geom import prism, cyl, cyl_along, union, subtract  # noqa: E402

# --- Rubinetto esistente (stime dalle foto, mm) ------------------------------
TAP = dict(
    pipe_x=30.0, pipe_d=20.0, insul_d=32.0,     # tubo che sale lungo il muro + isolante blu
    elbow_x=(13.0, 46.0), elbow_z=(-40.0, 12.0),  # gomito in ottone con raccordo
    body_d=22.0, body_x=(13.0, 175.0),          # corpo cromato orizzontale
    top_knob_x=88.0, top_knob_d=30.0, top_knob_h=58.0,   # comando superiore (non usato)
    out1_x=88.0, out2_x=128.0, out_d=27.0, out_h=18.0,   # uscite filettate 3/4" verso il basso
    front_knob_x=(145.0, 175.0), front_knob_d=32.0,      # comando frontale (usato)
)

# --- Copertura ---------------------------------------------------------------
X_FRONT = 143.5    # faccia frontale (il comando frontale inizia a 145)
HALF_W = 31.0      # semi-larghezza esterna
Z_TOPC = 66.0      # sommita' esterna (comando superiore alto ~58)
Z_BOT = -23.0      # fondo nella parte anteriore (sotto le uscite, punte a -18)
Z_BACK_BOT = -54.0 # fianchi posteriori piu' lunghi: nascondono gomito e raccordo
X_STEP = 60.0      # inizio della parte anteriore piu' corta
T = 3.0            # spessore pareti
C_TOP = 20.0       # smusso frontale superiore (45 deg: stampabile)
C_FRONT = 7.0      # smussi verticali frontali
R_SIDE = 9.0       # raccordo spigoli superiori laterali
SLOT_W = 26.0      # feritoia frontale per il corpo cromato (d 22)
OPEN_X = (114.0, 160.0)  # apertura bottiglia nel fondo (aperta verso il fronte)
OPEN_W = 32.0
SNAP_X = (80.0, 122.0)   # agganci a scatto fondo -> fianchi
SNAP_Z = -16.0


def _cs(poly):
    from geom import to_cs
    return to_cs(poly)


def side_profile(inset=0.0):
    """Profilo laterale (x, z): smusso frontale alto, fianchi posteriori piu' lunghi."""
    p = Polygon([(0, Z_TOPC), (X_FRONT - C_TOP, Z_TOPC), (X_FRONT, Z_TOPC - C_TOP),
                 (X_FRONT, Z_BOT + 3), (X_FRONT - 3, Z_BOT), (X_STEP, Z_BOT),
                 (X_STEP - (Z_BOT - Z_BACK_BOT), Z_BACK_BOT), (0, Z_BACK_BOT)])
    return p.buffer(-inset, join_style=2) if inset else p


def front_profile(inset=0.0):
    """Profilo frontale (y, z): spigoli superiori raccordati."""
    hw = HALF_W - inset
    r = max(R_SIDE - inset, 1.0)
    top = Z_TOPC - inset
    return box(-hw, Z_BACK_BOT - 50, hw, top - r).union(box(-hw + r, top - 2 * r, hw - r, top)) \
        .union(Point(-hw + r, top - r).buffer(r, quad_segs=16)).union(Point(hw - r, top - r).buffer(r, quad_segs=16))


def plan_profile(inset=0.0):
    """Pianta (x, y): spigoli frontali smussati a 45 deg."""
    hw = HALF_W - inset
    xf = X_FRONT - inset
    c = C_FRONT
    return Polygon([(-10, -hw), (xf - c, -hw), (xf, -hw + c), (xf, hw - c), (xf - c, hw), (-10, hw)])


def _solid(sp, fp, pp):
    # profili estrusi lungo i tre assi e intersecati
    a = Manifold.extrude(_cs(sp), 400).translate([0, 0, -200])          # (x,z) come (x,y) -> poi ruoto
    a = a.rotate([90, 0, 0])                                             # y_locale -> z
    b = Manifold.extrude(_cs(fp), 400).translate([0, 0, -200]).rotate([90, 0, 0]).rotate([0, 0, 90])
    c = Manifold.extrude(_cs(pp), 400).translate([0, 0, -200])
    return a ^ b ^ c


def copertura():
    outer = _solid(side_profile(), front_profile(), plan_profile()) ^ Manifold.cube([X_FRONT + 1, 400, 400]).translate([0, -200, -200])
    cav_side = side_profile(T).union(box(-5, -200, X_FRONT - T, Z_BOT + T)).union(box(-5, Z_BACK_BOT - 10, T + 0.5, Z_TOPC - T))
    cav = _solid(cav_side, front_profile(T), plan_profile(T))
    m = outer - cav
    # feritoia frontale per il corpo cromato: si cala dall'alto
    slot = box(-SLOT_W / 2, Z_BOT - 10, SLOT_W / 2, 0).union(Point(0, 0).buffer(SLOT_W / 2, quad_segs=24))
    m = m - _solid(box(X_FRONT - 15, -300, X_FRONT + 5, 300), slot, box(-50, -300, 400, 300))
    # fori per gli agganci a scatto del fondo
    for i, x in enumerate(SNAP_X):
        for s in (-1, 1):
            m = m - cyl_along((x, s * (HALF_W - T - 1), SNAP_Z), (x, s * (HALF_W + 1), SNAP_Z), 1.6, 24)
    return m


def fondo():
    pp = plan_profile(T + 0.25)
    plate2d = pp.intersection(box(X_STEP + 0.5, -100, 400, 100))
    opening = box(OPEN_X[0] + OPEN_W / 2, -OPEN_W / 2, OPEN_X[1], OPEN_W / 2).union(
        Point(OPEN_X[0] + OPEN_W / 2, 0).buffer(OPEN_W / 2, quad_segs=24))
    plate = prism(plate2d.difference(opening), Z_BOT, Z_BOT + 3)
    # bordo rialzato sui fianchi e sul retro (davanti no: l'uscita usata e' vicina al fronte)
    rim2d = plate2d.difference(plate2d.buffer(-2.4, join_style=2)).intersection(box(0, -100, X_FRONT - 12, 100))
    rim = prism(rim2d.difference(opening), Z_BOT + 2.99, Z_BOT + 11)
    m = plate + rim
    # dentini a scatto
    yi = HALF_W - T - 0.25
    for x in SNAP_X:
        for s in (-1, 1):
            m = m + (Manifold.sphere(1.3, 24).scale([1, 1, 1]).translate([x, s * yi, SNAP_Z]) ^
                     Manifold.cube([10, 10, 10], True).translate([x, s * (yi + 5), SNAP_Z]))
    return m


def rubinetto():
    """Ingombro indicativo del rubinetto esistente (solo per verifiche e rendering)."""
    t = TAP
    parts = [cyl((t["pipe_x"], 0), t["pipe_d"] / 2, -260, -20, 48),
             cyl((t["pipe_x"], 0), t["insul_d"] / 2, -260, -48, 48),
             Manifold.cube([t["elbow_x"][1] - t["elbow_x"][0], 33, t["elbow_z"][1] - t["elbow_z"][0]])
             .translate([t["elbow_x"][0], -16.5, t["elbow_z"][0]]),
             cyl_along((t["body_x"][0], 0, 0), (t["body_x"][1] - 30, 0, 0), t["body_d"] / 2, 48),
             cyl((t["top_knob_x"], 0), t["top_knob_d"] / 2, 0, t["top_knob_h"], 48),
             cyl((t["out1_x"], 0), t["out_d"] / 2, -t["out_h"], 0, 48),
             cyl((t["out2_x"], 0), t["out_d"] / 2, -t["out_h"], 0, 48),
             cyl_along((t["front_knob_x"][0], 0, 0), (t["front_knob_x"][1], 0, 0), t["front_knob_d"] / 2, 48)]
    return union(parts)


PARTS = [
    ("20_copertura_rubinetto", copertura, "sabbia", ("rot", "y", 90)),   # faccia frontale sul piatto
    ("21_fondo_copertura", fondo, "sabbia", "up"),
]


if __name__ == "__main__":
    import fontanella as F
    for name, fn, color, how in PARTS:
        m = fn()
        assert m.status().name == "NoError" and len(m.decompose()) == 1, name
        tm = F.to_trimesh(m.simplify(0.01))
        tm.export(os.path.join(F.ROOT, "stl", "assembly", name + ".stl"))
        pt = F.print_orient(tm, how)
        pt.export(os.path.join(F.ROOT, "stl", "print", name + ".stl"))
        ext = pt.extents
        print(f"{name:26s} {ext[0]:6.1f} x {ext[1]:6.1f} x {ext[2]:6.1f}  vol {tm.volume / 1000:6.1f} cm3  "
              f"watertight={tm.is_watertight}")
    r = rubinetto()
    print("interferenza guscio/rubinetto:", round((copertura() ^ r).volume(), 2),
          " fondo/rubinetto:", round((fondo() ^ r).volume(), 2),
          " guscio/fondo:", round((copertura() ^ fondo()).volume(), 2))
