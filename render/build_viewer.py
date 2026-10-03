"""Genera il visualizzatore 3D interattivo (docs/viewer.html) con la geometria incorporata.

    python3 render/build_viewer.py [cartella_locale_three]

Se si passa una cartella che contiene node_modules/three, scrive anche
<cartella>/viewer_local.html che usa three.js locale (per i render offline).
"""
import base64
import json
import math
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "cad"))
import fontanella as F  # noqa: E402
from geom import cyl  # noqa: E402

CDN = "https://cdn.jsdelivr.net/npm/three@0.160.0"

LABELS = {
    "01_vasca": "Vasca", "02_griglia": "Griglia", "03_schienale": "Schienale",
    "04_testa_beccuccio": "Testa + beccuccio", "05_copertura_braccio": "Listello di chiusura",
    "06_corpo_vano": "Corpo vano tecnico", "07_sportello": "Sportello", "08_serbatoio": "Serbatoio",
    "09_coperchio_serbatoio": "Coperchio serbatoio", "10_box_elettronica": "Box elettronica",
    "11_coperchio_box": "Coperchio box",
}
c50, s50 = math.cos(math.radians(F.TANK_PHI)), math.sin(math.radians(F.TANK_PHI))
dc, ds = math.cos(math.radians(47)), math.sin(math.radians(47))
EXPLODE = {
    "01_vasca": [0, 0, 120], "02_griglia": [0, 0, 220], "03_schienale": [0, 0, 280],
    "04_testa_beccuccio": [0, 0, 400], "05_copertura_braccio": [110, 0, 330],
    "06_corpo_vano": [0, 0, 0], "07_sportello": [dc * 330, ds * 330, 40],
    "08_serbatoio": [c50 * 220, s50 * 220, -150], "09_coperchio_serbatoio": [c50 * 220, s50 * 220, -60],
    "10_box_elettronica": [300, 0, 40], "11_coperchio_box": [370, 0, 40],
    "tubo": [0, 0, 0], "rompigetto": [0, 0, 0],
    "pompa": [c50 * 220, s50 * 220, -150], "galleggianti": [c50 * 220, s50 * 220, -60],
}


def pack(m, name, color, label, ref=False, clip=True, simplify=0.02):
    mesh = m.simplify(simplify).to_mesh()
    v = np.asarray(mesh.vert_properties, dtype=np.float32)[:, :3].copy()
    i = np.asarray(mesh.tri_verts, dtype=np.uint32).ravel().copy()
    return dict(name=name, color=color, label=label, ref=ref, clip=clip,
                explode=EXPLODE.get(name, [0, 0, 0]),
                v=base64.b64encode(v.tobytes()).decode(), i=base64.b64encode(i.tobytes()).decode())


def build(local_dir=None):
    parts = []
    for name, fn, color, how, qty in F.PARTS:
        parts.append(pack(fn(), name, color, LABELS[name]))
    parts.append(pack(F.tubo_ppr(), "tubo", "tubo", "Tubo PPR (nascosto)", ref=True, clip=False))
    parts.append(pack(F.rompigetto(), "rompigetto", "ottone", "Rompigetto", ref=True, clip=False))
    parts.append(pack(F.pompa(), "pompa", "antracite", "Pompa 12 V", ref=True, clip=False))
    parts.append(pack(F.galleggianti(), "galleggianti", "antracite", "Galleggianti", ref=True, clip=False))
    bottle = cyl(F.SPOUT, 44, F.Z_GRID_TOP, F.Z_GRID_TOP + 230, 64) + \
        F.Manifold.cylinder(45, 44, 14, 64).translate([F.SPOUT[0], F.SPOUT[1], F.Z_GRID_TOP + 230]) + \
        cyl(F.SPOUT, 14, F.Z_GRID_TOP + 274, F.Z_GRID_TOP + 296, 32)
    parts.append(pack(bottle, "bottiglia", "vetro", "Bottiglia 1,5 L", ref=True, clip=False))
    data = json.dumps(dict(parts=parts), separators=(",", ":"))
    tpl = open(os.path.join(ROOT, "render", "viewer_template.html")).read()
    out = tpl.replace("__DATA__", data)
    os.makedirs(os.path.join(ROOT, "docs"), exist_ok=True)
    with open(os.path.join(ROOT, "docs", "viewer.html"), "w") as f:
        f.write(out.replace("__THREE__", CDN))
    print("docs/viewer.html", os.path.getsize(os.path.join(ROOT, "docs", "viewer.html")) // 1024, "KB")
    if local_dir:
        with open(os.path.join(local_dir, "viewer_local.html"), "w") as f:
            f.write(out.replace("__THREE__", "/node_modules/three"))


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else None)
