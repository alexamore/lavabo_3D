"""Visualizzatore 3D della copertura provvisoria del rubinetto (docs/copertura_viewer.html)."""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "cad"))
sys.path.insert(0, os.path.join(ROOT, "render"))
import copertura_rubinetto as C  # noqa: E402
from build_viewer import pack, CDN  # noqa: E402
from geom import cyl  # noqa: E402
from manifold3d import Manifold  # noqa: E402

Y0 = 95.0      # asse del tubo dall'angolo, lungo la parete da 25 cm
Z_TAP = 1000.0 # quota indicativa dell'asse del rubinetto (solo per il rendering)


def place(m):
    return m.translate([0, Y0, Z_TAP])


VIEWS = {
    "ambient": {"label": "Vista ambientata", "pos": [720, 470, 1230], "tgt": [80, 95, 985], "fov": 30},
    "front": {"label": "Fronte", "pos": [1100, 95, 1000], "tgt": [0, 95, 990], "fov": 14},
    "spout": {"label": "Lato", "pos": [90, 900, 990], "tgt": [80, 95, 990], "fov": 16},
    "section": {"label": "Sezione", "pos": [380, -520, 1080], "tgt": [80, 95, 990], "fov": 26, "section": True},
    "exploded": {"label": "Esploso", "pos": [760, 560, 1180], "tgt": [80, 95, 1000], "fov": 34, "explode": True},
    "top": {"label": "Pianta", "ortho": True, "pos": [90, 95, 3000], "tgt": [90, 95, 0], "half": 120},
}


def build(local_dir=None):
    parts = []
    for name, fn, color, how in C.PARTS:
        p = pack(place(fn()), name, color, {"20_copertura_rubinetto": "Guscio", "21_fondo_copertura": "Fondo"}[name],
                 simplify=0.01)
        p["explode"] = [0, 0, 130] if name.startswith("20") else [0, 0, -90]
        parts.append(p)
    parts.append(pack(place(C.rubinetto()), "rubinetto", "cromo", "Rubinetto esistente", ref=True, clip=False))
    ins = cyl((C.TAP["pipe_x"], 0), C.TAP["insul_d"] / 2 + 0.5, -400, -48, 48)
    parts.append(pack(place(ins), "isolante", "blu", "Isolante", ref=True, clip=False))
    bx, bz = C.TAP["out2_x"], -C.TAP["out_h"] - 6
    bottle = cyl((bx, 0), 14, bz - 22, bz, 32) + Manifold.cylinder(45, 44, 14, 64).translate([bx, 0, bz - 67]) + \
        cyl((bx, 0), 44, bz - 300, bz - 67, 64)
    parts.append(pack(place(bottle), "bottiglia", "vetro", "Bottiglia", ref=True, clip=False))
    data = dict(parts=parts, views=VIEWS, title="Copertura rubinetto",
                subtitle="Cappuccio provvisorio in ASA sul rubinetto doppio esistente: comando frontale libero, "
                         "uscita per la bottiglia da 11,5 a 14,5 cm dal muro.")
    tpl = open(os.path.join(ROOT, "render", "viewer_template.html")).read()
    out = tpl.replace("__DATA__", json.dumps(data, separators=(",", ":")))
    with open(os.path.join(ROOT, "docs", "copertura_viewer.html"), "w") as f:
        f.write(out.replace("__THREE__", CDN))
    if local_dir:
        with open(os.path.join(local_dir, "copertura_local.html"), "w") as f:
            f.write(out.replace("__THREE__", "/node_modules/three"))


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else None)
