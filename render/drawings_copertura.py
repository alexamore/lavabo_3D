"""Tavola quotata della copertura provvisoria del rubinetto -> docs/tavola_copertura_rubinetto.png/.pdf"""
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import PathPatch, Rectangle

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "cad"))
sys.path.insert(0, os.path.join(ROOT, "render"))
import copertura_rubinetto as C  # noqa: E402
from drawings import dim_h, dim_v, note, INK, DIM, COL  # noqa: E402

IMG = os.path.join(ROOT, "docs", "img", "copertura")


def rings_to_patch(rings, **kw):
    verts, codes = [], []
    for r in rings:
        verts += r.tolist() + [r[0].tolist()]
        codes += [Path.MOVETO] + [Path.LINETO] * (len(r) - 1) + [Path.CLOSEPOLY]
    return PathPatch(Path(verts, codes), **kw)


def cut(m, M):
    return [np.asarray(p) for p in m.transform(M).slice(0.0).to_polygons()]


SIDE = [[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0]]      # piano y = 0 -> (x, z)
FRONT = [[0, 1, 0, 0], [0, 0, 1, 0], [1, 0, 0, -C.X_FRONT + 1.5]]  # piano x = fronte -> (y, z)
PLAN = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, -(C.Z_BOT + 1.5)]]      # piano z = fondo -> (x, y)


def draw(ax, parts, M):
    for m, fc, hatch in parts:
        rings = cut(m, M)
        if rings:
            ax.add_patch(rings_to_patch(rings, fc=fc, ec=INK, lw=0.8, hatch=hatch))


def main():
    cov, fon, tap = C.copertura(), C.fondo(), C.rubinetto()
    parts = [(cov, COL["sabbia"], "///"), (fon, "#b9a98d", "\\\\\\"), (tap, "#d8dbde", None)]
    fig = plt.figure(figsize=(23.4, 16.5), dpi=120)  # A2
    gs = fig.add_gridspec(2, 3, left=0.02, right=0.98, top=0.93, bottom=0.04, wspace=0.08, hspace=0.12)
    fig.suptitle("COPERTURA PROVVISORIA DEL RUBINETTO DOPPIO  ·  ASA, 2 pezzi, Bambu Lab P2S", fontsize=20,
                 fontweight="bold", color=INK)

    # sezione laterale
    ax = fig.add_subplot(gs[0, 0:2]); ax.set_aspect("equal")
    ax.add_patch(Rectangle((-25, -120), 25, 220, fc="#e6dccb", ec=INK, hatch="////"))
    ax.text(-12, 92, "muro\n(25 cm)", ha="center", va="top", fontsize=8, rotation=90)
    draw(ax, parts, SIDE)
    for x0, x1, z, t in ((0, C.X_FRONT, 85, f"{C.X_FRONT:.1f}"), (0, 175, 100, "175 sporgenza rubinetto"),
                         (C.OPEN_X[0], 145, -48, "uscita bottiglia 114–145"),
                         (145, 175, -32, "comando frontale libero")):
        dim_h(ax, x0, x1, z, t, fs=9)
    dim_v(ax, 195, C.Z_BOT, C.Z_TOPC, f"{C.Z_TOPC - C.Z_BOT:.0f}", side="right")
    dim_v(ax, 215, C.Z_BACK_BOT, C.Z_TOPC, f"{C.Z_TOPC - C.Z_BACK_BOT:.0f}", side="right")
    note(ax, (C.TAP["top_knob_x"], 40), (230, 55), "comando superiore (coperto, non usato)")
    note(ax, (C.TAP["out1_x"], -10), (230, 20), "uscita 1 (coperta)")
    note(ax, (C.TAP["out2_x"], -12), (230, -5), "uscita 2 → bottiglia")
    note(ax, (100, C.Z_BOT + 1.5), (230, -60), "fondo a scatto (si monta da sotto,\nresta sotto le uscite: blocca il guscio)")
    note(ax, (30, -40), (230, -95), "gomito, raccordo e tubo isolato:\nescono dal fondo aperto posteriore")
    ax.set_title("SEZIONE SULL'ASSE DEL RUBINETTO", fontsize=13, fontweight="bold")
    ax.set_xlim(-40, 420); ax.set_ylim(-125, 110); ax.axis("off")

    # fronte
    ax = fig.add_subplot(gs[0, 2]); ax.set_aspect("equal")
    draw(ax, parts, FRONT)
    dim_h(ax, -C.HALF_W, C.HALF_W, C.Z_TOPC + 12, f"{2 * C.HALF_W:.0f}")
    dim_h(ax, -C.SLOT_W / 2, C.SLOT_W / 2, C.Z_BOT - 12, f"feritoia {C.SLOT_W:.0f}")
    ax.set_title("SEZIONE FRONTALE (vista dal fronte)", fontsize=13, fontweight="bold")
    ax.set_xlim(-60, 60); ax.set_ylim(-45, 90); ax.axis("off")

    # pianta del fondo
    ax = fig.add_subplot(gs[1, 0]); ax.set_aspect("equal")
    ax.add_patch(Rectangle((-25, -45), 25, 90, fc="#e6dccb", ec=INK, hatch="////"))
    draw(ax, parts, PLAN)
    dim_h(ax, C.OPEN_X[0], C.X_FRONT, 25, "apertura 114 → fronte", fs=8)
    dim_v(ax, 150, -C.OPEN_W / 2, C.OPEN_W / 2, f"{C.OPEN_W:.0f}", side="right")
    ax.set_title("SEZIONE ORIZZONTALE AL FONDO", fontsize=13, fontweight="bold")
    ax.set_xlim(-30, 190); ax.set_ylim(-50, 45); ax.axis("off")

    for i, (img, t) in enumerate((("ambient.png", "Vista"), ("exploded.png", "Montaggio: guscio dall'alto, fondo da sotto"))):
        ax = fig.add_subplot(gs[1, 1 + i])
        ax.imshow(plt.imread(os.path.join(IMG, img)))
        ax.set_title(t, fontsize=13, fontweight="bold"); ax.axis("off")
    fig.text(0.98, 0.012, "quote in mm dal muro · misure del rubinetto stimate dalle foto: verificarle prima della stampa",
             ha="right", fontsize=11, color="#5d574d")
    fig.savefig(os.path.join(ROOT, "docs", "tavola_copertura_rubinetto.png"), facecolor="white")
    fig.savefig(os.path.join(ROOT, "docs", "tavola_copertura_rubinetto.pdf"), facecolor="white")
    print("ok")


if __name__ == "__main__":
    main()
