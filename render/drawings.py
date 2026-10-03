"""Tavole tecniche 2D ricavate dalla geometria reale (sezioni e proiezioni).

    python3 render/drawings.py      -> docs/img/{pianta,prospetto,sezione,dettaglio_beccuccio}.png
                                       docs/tavola_progetto.png / .pdf
"""
import math
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.patches import Polygon as MPoly, Circle, Rectangle
import trimesh
from shapely.geometry import Polygon, MultiPolygon

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "cad"))
import fontanella as F  # noqa: E402

IMG = os.path.join(ROOT, "docs", "img")
os.makedirs(IMG, exist_ok=True)

COL = {"sabbia": "#cbbca3", "antracite": "#4a4b4d", "grigio": "#a9a9a5", "tubo": "#3f9a4a",
       "ottone": "#b8955a", "nero": "#2a2a2a"}
INK = "#2b2a28"
DIM = "#8a4b2a"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})


def tm_of(m):
    mesh = m.to_mesh()
    return trimesh.Trimesh(np.asarray(mesh.vert_properties)[:, :3], np.asarray(mesh.tri_verts), process=False)


MANI = {}


def load():
    meshes = []
    items = [(name, color, fn()) for name, fn, color, how, qty in F.PARTS]
    items += [("tubo", "tubo", F.tubo_ppr()), ("rompigetto", "ottone", F.rompigetto()),
              ("pompa", "nero", F.pompa()), ("galleggianti", "nero", F.galleggianti())]
    for name, color, m in items:
        MANI[name] = m
        meshes.append((name, color, tm_of(m.simplify(0.03))))
    return meshes


# ---------------------------------------------------------------------------
# helpers di quotatura
# ---------------------------------------------------------------------------
def dim_h(ax, x0, x1, y, text, off=0, fs=9, ext_from=None):
    ax.annotate("", (x0, y), (x1, y), arrowprops=dict(arrowstyle="<|-|>", color=DIM, lw=0.9, shrinkA=0, shrinkB=0,
                                                      mutation_scale=8))
    ax.text((x0 + x1) / 2, y + off, text, ha="center", va="bottom", color=DIM, fontsize=fs,
            bbox=dict(fc="white", ec="none", pad=0.6, alpha=.85))
    if ext_from is not None:
        for x, yy in ((x0, ext_from[0]), (x1, ext_from[1])):
            ax.plot([x, x], [yy, y], color=DIM, lw=0.5, ls="-")


def dim_v(ax, x, y0, y1, text, fs=9, side="left", ext=None):
    ax.annotate("", (x, y0), (x, y1), arrowprops=dict(arrowstyle="<|-|>", color=DIM, lw=0.9, shrinkA=0, shrinkB=0,
                                                      mutation_scale=8))
    ax.text(x + (-3 if side == "left" else 3), (y0 + y1) / 2, text, ha="right" if side == "left" else "left",
            va="center", rotation=90, color=DIM, fontsize=fs, bbox=dict(fc="white", ec="none", pad=0.6, alpha=.85))
    if ext:
        for y, xx in ext:
            ax.plot([xx, x], [y, y], color=DIM, lw=0.5)


def level(ax, x0, x1, z, text, fs=8.5, ha="left"):
    ax.plot([x0, x1], [z, z], color=DIM, lw=0.6, ls=(0, (6, 3)))
    tx = x1 if ha == "left" else x0
    ax.plot([tx], [z], marker="v", color=DIM, ms=5)
    ax.text(tx + (6 if ha == "left" else -6), z, text, color=DIM, fontsize=fs, va="center", ha=ha)


def note(ax, xy, xytext, text, fs=8.5, ha="left"):
    ax.annotate(text, xy, xytext, fontsize=fs, color=INK, ha=ha, va="center",
                arrowprops=dict(arrowstyle="-", color=INK, lw=0.6, shrinkA=2, shrinkB=0),
                bbox=dict(fc="white", ec="none", pad=0.5, alpha=.9))
    ax.plot(*xy, marker="o", ms=2.5, color=INK)


def hatch_rect(ax, x0, y0, x1, y1, label=None):
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc="#e6dccb", ec=INK, lw=0.8, hatch="////"))


def add_geom(ax, g, **kw):
    gs = [g] if isinstance(g, Polygon) else list(getattr(g, "geoms", []))
    for p in gs:
        if not isinstance(p, Polygon) or p.is_empty:
            continue
        ax.add_patch(MPoly(np.asarray(p.exterior.coords), closed=True, **kw))
        for h in p.interiors:
            ax.add_patch(MPoly(np.asarray(h.coords), closed=True, fc="white", ec=kw.get("ec", INK),
                               lw=kw.get("lw", 0.6)))


# ---------------------------------------------------------------------------
# PIANTA
# ---------------------------------------------------------------------------
def pianta(ax):
    from shapely.geometry import box
    ax.set_aspect("equal")
    hatch_rect(ax, -35, -35, 0, 290)
    hatch_rect(ax, 0, -35, 330, 0)
    ax.text(300, -18, "PARETE A", ha="right", va="center", fontsize=8, color=INK, fontweight="bold")
    ax.text(-18, 270, "PARETE B", ha="center", va="top", rotation=90, fontsize=8, color=INK, fontweight="bold")
    add_geom(ax, F.F, fc="#efe7d8", ec=INK, lw=1.6)
    add_geom(ax, F.F_IN, fc="none", ec="#9a8c74", lw=0.6, ls="--")
    add_geom(ax, F.bs_footprint(), fc=COL["sabbia"], ec=INK, lw=0.9)
    add_geom(ax, F.CHASE, fc="#f7f3ec", ec=INK, lw=0.6, ls=":")
    add_geom(ax, F.I_BASIN, fc="#d9d4cb", ec=INK, lw=0.7)
    # asole griglia (indicative)
    for k in range(-24, 25):
        e = np.array([1, 1]) / math.sqrt(2); n = np.array([1, -1]) / math.sqrt(2)
        from shapely.geometry import LineString
        ln = LineString([tuple(-400 * e + k * 9 * n), tuple(400 * e + k * 9 * n)]).intersection(F.I_BASIN.buffer(-8))
        for seg in getattr(ln, "geoms", [ln]):
            if not seg.is_empty:
                xs, ys = seg.xy
                ax.plot(xs, ys, color="#8f8a80", lw=0.5)
    ax.add_patch(Circle(F.DRAIN, F.DRAIN_D / 2, fc="white", ec=INK, lw=0.7, ls="--"))
    ax.add_patch(Circle(F.SPOUT, F.SPOUT_R, fc="none", ec="#1f5fa8", lw=1.0, ls="--"))
    ax.add_patch(Circle(F.SPOUT, 44, fc="none", ec="#1f5fa8", lw=0.6, ls=":"))
    ax.add_patch(Circle(F.RISER, 10, fc=COL["tubo"], ec=INK, lw=0.6))
    arm = F._stadium(F.ARM_P0, F.ARM_P1, F.ARM_R)
    add_geom(ax, arm, fc="none", ec="#1f5fa8", lw=0.8, ls="--")
    # quote principali
    dim_h(ax, 0, F.A, -60, "250", fs=11)
    ax.plot([0, 0], [-35, -66], color=DIM, lw=0.5); ax.plot([F.A, F.A], [0, -66], color=DIM, lw=0.5)
    dim_v(ax, -60, 0, F.B, "200", fs=11)
    ax.plot([-35, -66], [0, 0], color=DIM, lw=0.5); ax.plot([0, -66], [F.B, F.B], color=DIM, lw=0.5)
    dim_h(ax, 0, F.SPOUT[0], F.SPOUT[1] + 58, "95", fs=8)
    dim_v(ax, F.SPOUT[0] + 58, 0, F.SPOUT[1], "95", fs=8, side="right")
    dim_v(ax, 238, 0, F.T_W, "", fs=7, side="right")
    ax.text(246, 10, "20", fontsize=7, color=DIM, va="center")
    note(ax, (180, 120), (285, 175), "griglia removibile\n(piano bottiglia +83,6)")
    note(ax, F.SPOUT, (150, 250), "asse beccuccio\n(bottiglia Ø 88)")
    note(ax, F.RISER, (55, -110), "salita PPR DN20\nnel cavedio d'angolo")
    note(ax, (160, 10), (190, -110), "ali schienale sp. 20 aderenti alle pareti")
    note(ax, (238 * math.cos(0.5), 188 * math.sin(0.5)), (300, 70), "bordo frontale curvo\naffusolato")
    ax.text(125, 315, "PIANTA  (scala 1:5)", ha="center", fontsize=12, fontweight="bold", color=INK)
    ax.text(125, 300, "pianta a tre lati: 250 lungo parete A + 200 lungo parete B + bordo curvo", ha="center",
            fontsize=8.5, color="#5d574d")
    ax.set_xlim(-90, 380); ax.set_ylim(-130, 325)
    ax.axis("off")


# ---------------------------------------------------------------------------
# PROSPETTO frontale (proiezione lungo la bisettrice)
# ---------------------------------------------------------------------------
def project(meshes, view, hdir, exclude=(), light=(0.45, 0.25, 0.85), behind=False):
    view = np.asarray(view, float); view /= np.linalg.norm(view)
    hdir = np.asarray(hdir, float); hdir /= np.linalg.norm(hdir)
    L = np.asarray(light, float); L /= np.linalg.norm(L)
    polys, cols, depth = [], [], []
    for name, color, m in meshes:
        if name in exclude:
            continue
        tri = m.triangles
        n = m.face_normals
        vis = n @ view > 1e-3
        if behind:
            vis &= (m.triangles_center @ view) < 0
        tri = tri[vis]; n = n[vis]
        if not len(tri):
            continue
        h = tri @ hdir
        z = tri[:, :, 2]
        d = (tri @ view).mean(axis=1)
        shade = 0.62 + 0.38 * np.clip(n @ L, 0, 1)
        base = np.array(matplotlib.colors.to_rgb(COL.get(color, "#cccccc")))
        c = np.clip(base[None, :] * shade[:, None], 0, 1)
        polys.append(np.stack([h, z], axis=2)); cols.append(c); depth.append(d)
    P = np.concatenate(polys); C = np.concatenate(cols); D = np.concatenate(depth)
    o = np.argsort(D)
    return P[o], C[o]


def prospetto(ax, meshes):
    ax.set_aspect("equal")
    P, C = project(meshes, view=(1, 1, 0), hdir=(-1, 1, 0), exclude=("pompa", "galleggianti"))
    ax.add_collection(PolyCollection(P, facecolors=C, edgecolors=C, linewidths=0.15))
    # pareti in vista (spigolo d'angolo in asse)
    ax.plot([0, 0], [0, 1400], color="#7d6f58", lw=0.8)
    ax.plot([-260, 260], [0, 0], color=INK, lw=1.4)
    for k in range(-26, 26):
        ax.plot([k * 10, k * 10 - 12], [0, -12], color=INK, lw=0.4)
    for z, t in ((0, "±0,00 pavimento"), (F.Z_CORPO_BOT, "+57,0 fondo vano"), (F.Z_TOP, "+84,0 piano vasca"),
                 (F.Z_OUTLET, "+115,0 uscita beccuccio"), (F.Z_HEAD_TOP, "+121,8 sommità")):
        level(ax, 120, 230, z, t)
    dim_v(ax, 100, F.Z_GRID_TOP, F.Z_OUTLET, f"{F.Z_OUTLET - F.Z_GRID_TOP:.0f} luce utile", fs=8, side="right",
          ext=[(F.Z_GRID_TOP, 60), (F.Z_OUTLET, 10)])
    dim_v(ax, -245, 0, F.Z_TOP, "840", fs=9, ext=[(F.Z_TOP, -160)])
    note(ax, (0, F.Z_OUTLET - 3), (-245, 1265), "beccuccio vicino all'angolo\n(asse a 95 mm da entrambe le pareti)", ha="left")
    note(ax, (60, 880), (-245, 960), "schienale a onda\n(nasconde il tubo PPR)", ha="left")
    note(ax, (-60, 650), (-245, 640), "sportello removibile\n(vano tecnico)", ha="left")
    note(ax, (0, 300), (-245, 300), "copritubo d'angolo\n(opzionale, 3 moduli)", ha="left")
    ax.text(0, 1330, "PROSPETTO FRONTALE  (vista lungo la bisettrice)", ha="center", fontsize=12, fontweight="bold")
    ax.set_xlim(-260, 330); ax.set_ylim(-30, 1360)
    ax.axis("off")


# ---------------------------------------------------------------------------
# SEZIONE sul piano verticale x = y
# ---------------------------------------------------------------------------
def section_paths(name):
    """Sezione esatta con il piano x = y (manifold3d.slice) -> lista di anelli (u, z)."""
    r = 1 / math.sqrt(2)
    M = [[r, r, 0, 0], [0, 0, 1, 0], [r, -r, 0, 0]]  # x'=u, y'=z, z'=distanza dal piano
    cs = MANI[name].transform(M).slice(0.0)
    return [np.asarray(p) for p in cs.to_polygons()]


def draw_section(ax, meshes):
    from matplotlib.path import Path
    from matplotlib.patches import PathPatch
    for name, color, m in meshes:
        rings = section_paths(name)
        if not rings:
            continue
        verts, codes = [], []
        for r in rings:
            verts += r.tolist() + [r[0].tolist()]
            codes += [Path.MOVETO] + [Path.LINETO] * (len(r) - 1) + [Path.CLOSEPOLY]
        fc = COL.get(color, "#ccc")
        ax.add_patch(PathPatch(Path(verts, codes), fc=fc, ec=INK, lw=0.7,
                               hatch="///" if color == "sabbia" else None))


def sezione(ax, meshes):
    ax.set_aspect("equal")
    # sagome in vista oltre il piano (proiezione tenue)
    P, C = project([mm for mm in meshes if mm[0] not in ("tubo",)], view=(1, -1, 0), hdir=(1, 1, 0), behind=True)
    ax.add_collection(PolyCollection(P, facecolors=np.clip(C * 0.25 + 0.75, 0, 1), edgecolors="none", alpha=1))
    draw_section(ax, meshes)
    # tubo PPR: sempre in evidenza
    ax.add_patch(Rectangle((-40, 0), 40, 1320, fc="#e6dccb", ec=INK, lw=0.8, hatch="////"))
    ax.text(-20, 1280, "angolo\npareti", ha="center", fontsize=7.5, rotation=90, va="top")
    ax.plot([-60, 330], [0, 0], color=INK, lw=1.4)
    u_sp = math.hypot(*F.SPOUT)
    for z, t in ((F.Z_TOP, "+84,0"), (F.Z_OUTLET, "+115,0"), (F.Z_VASCA_BOT, "+77,0"), (F.Z_CORPO_BOT, "+57,0"),
                 (F.Z_BS_TOP, "+104,0")):
        level(ax, 240, 290, z, t)
    note(ax, (math.hypot(*F.RISER), 980), (380, 1000), "tubo PPR DN20 in salita\n(cavedio aperto verso le pareti)")
    note(ax, (math.hypot(*F.RISER) + 30, F.Z_ARM), (380, 1300), "gomito PPR 90°, braccio\norizzontale nel beccuccio")
    note(ax, (u_sp, F.Z_OUTLET - 2), (380, 1190), "gomito PPR 20 × ½\" F\n+ rompigetto (filetto femmina)")
    note(ax, (110, F.Z_GRID_TOP - 4), (380, 880), "griglia removibile sp. 8")
    note(ax, (F.DRAIN[0] * math.sqrt(2) + 30, 800), (380, 815), "imbuto inclinato 12° → scarico Ø28")
    note(ax, (170, 650), (380, 690), "serbatoio estraibile ~1,4 L")
    note(ax, (125, 600), (380, 620), "pompa sommersa 12 V")
    note(ax, (110, 660), (380, 655), "galleggianti livello alto/basso")
    note(ax, (60, 740), (380, 745), "box ESP32 stagno (dietro, in quota)")
    note(ax, (35, 330), (380, 330), "copritubo: passaggio tubo PPR,\nmandata pompa e cavo 12 V")
    note(ax, (190, 600), (380, 580), "sportello con feritoie di ventilazione")
    ax.text(150, 1350, "SEZIONE VERTICALE SULLA BISETTRICE", ha="center", fontsize=12, fontweight="bold")
    ax.set_xlim(-60, 600); ax.set_ylim(-20, 1380)
    ax.axis("off")


def dettaglio(ax, meshes):
    ax.set_aspect("equal")
    sub = [mm for mm in meshes if mm[0] in ("03_schienale", "04_testa_beccuccio", "05_copertura_braccio", "tubo",
                                             "rompigetto", "02_griglia", "01_vasca")]
    P, C = project([mm for mm in sub if mm[0] not in ("tubo",)], view=(1, -1, 0), hdir=(1, 1, 0), behind=True)
    ax.add_collection(PolyCollection(P, facecolors=np.clip(C * 0.25 + 0.75, 0, 1), edgecolors="none"))
    draw_section(ax, sub)
    ax.add_patch(Rectangle((-15, 1000), 15, 260, fc="#e6dccb", ec=INK, lw=0.8, hatch="////"))
    u_sp = math.hypot(*F.SPOUT)
    note(ax, (u_sp, F.Z_OUTLET - 4), (200, 1105), "uscita: rompigetto M24 / anticalcare\nsu raccordo femmina ½\"")
    note(ax, (u_sp + 12, F.Z_ARM - 25), (200, 1150), "canna di uscita Ø46, int. Ø39")
    note(ax, (u_sp - 20, F.Z_ARM), (200, 1195), "gomito PPR 20 × ½\" F (femmina)")
    note(ax, (math.hypot(*F.RISER), F.Z_ARM), (200, 1245), "gomito PPR 20 a 90°")
    note(ax, (85, F.Z_ARM - 14), (200, 1065), "listello di chiusura sotto il braccio\n(2 viti M3, trattiene la testa)")
    note(ax, (62, F.Z_BS_TOP), (200, 1025), "giunto testa/schienale: 2 perni Ø4 inox")
    note(ax, (math.hypot(*F.RISER), 1010), (-5, 990), "PPR DN20", ha="right")
    ax.text(110, 1275, "DETTAGLIO BECCUCCIO", ha="center", fontsize=12, fontweight="bold")
    ax.text(110, 1262, "testa stampata capovolta (piano superiore sul piatto) → nessun supporto",
            ha="center", fontsize=8, color="#5d574d")
    dim_v(ax, u_sp + 40, F.Z_OUTLET, F.Z_HEAD_TOP, f"{F.Z_HEAD_TOP - F.Z_OUTLET:.0f}", fs=8, side="right")
    dim_h(ax, 0, u_sp, F.Z_HEAD_TOP + 12, f"{u_sp:.0f} dall'angolo", fs=8)
    ax.set_xlim(-60, 400); ax.set_ylim(990, 1290)
    ax.axis("off")


def render_panel(ax, path, title):
    im = plt.imread(path)
    ax.imshow(im)
    ax.set_title(title, fontsize=12, fontweight="bold", color=INK, pad=6)
    ax.axis("off")


def main():
    meshes = load()
    for fn, name, size in ((pianta, "pianta", (8, 7.4)), (prospetto, "prospetto", (8, 11)),
                           (sezione, "sezione", (9.5, 11)), (dettaglio, "dettaglio_beccuccio", (9.5, 6.4))):
        fig, ax = plt.subplots(figsize=size, dpi=170)
        fn(ax, meshes) if fn is not pianta else fn(ax)
        fig.tight_layout()
        fig.savefig(os.path.join(IMG, name + ".png"), facecolor="white")
        plt.close(fig)
        print("ok", name)

    # tavola riassuntiva
    fig = plt.figure(figsize=(33.1, 23.4), dpi=110)  # A1 orizzontale
    gs = fig.add_gridspec(2, 3, left=0.01, right=0.99, top=0.95, bottom=0.04, wspace=0.03, hspace=0.06)
    fig.suptitle("FONTANELLA D'ANGOLO PER RIEMPIMENTO BOTTIGLIE  ·  ASA stampato 3D (Bambu Lab P2S, pezzi ≤ 250 mm)",
                 fontsize=22, fontweight="bold", color=INK, y=0.985)
    render_panel(fig.add_subplot(gs[0, 0]), os.path.join(IMG, "ambient.png"), "1 · Vista ambientata")
    render_panel(fig.add_subplot(gs[0, 1]), os.path.join(IMG, "pianta.png"), "2 · Pianta quotata")
    render_panel(fig.add_subplot(gs[0, 2]), os.path.join(IMG, "prospetto.png"), "3 · Prospetto frontale")
    render_panel(fig.add_subplot(gs[1, 0]), os.path.join(IMG, "sezione.png"), "4 · Sezione con tubo PPR e vano tecnico")
    render_panel(fig.add_subplot(gs[1, 1]), os.path.join(IMG, "exploded.png"), "5 · Esploso")
    render_panel(fig.add_subplot(gs[1, 2]), os.path.join(IMG, "dettaglio_beccuccio.png"), "6 · Dettaglio beccuccio")
    fig.text(0.99, 0.012, "Colore: ASA sabbia / beige pietra · dettagli antracite · quote in mm · "
             "z = 0 pavimento · generato da cad/fontanella.py", ha="right", fontsize=12, color="#5d574d")
    fig.savefig(os.path.join(ROOT, "docs", "tavola_progetto.png"), facecolor="white")
    fig.savefig(os.path.join(ROOT, "docs", "tavola_progetto.pdf"), facecolor="white")
    print("ok tavola")


if __name__ == "__main__":
    main()
