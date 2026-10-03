"""Fontanella d'angolo per riempimento bottiglie - generatore parametrico.

Uso:
    python3 cad/fontanella.py          # genera stl/assembly/*.stl e stl/print/*.stl

Ogni pezzo e' modellato in coordinate di assemblato (vedi params.py) e poi
riorientato/appoggiato sul piatto per la stampa.
"""
import math
import os
import sys
import json

import numpy as np
import trimesh
from shapely.geometry import Polygon, LineString, Point, box
from shapely import affinity
from manifold3d import Manifold

sys.path.insert(0, os.path.dirname(__file__))
from params import *  # noqa
from geom import (prism, disc, quadrant, wedge, cyl, cyl_along, sandwich, dist_to,
                  contains, bullnose, union, subtract, polys)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------------------
# Profili 2D
# ---------------------------------------------------------------------------
_t = np.linspace(0, math.pi / 2, ARC_PTS)
_c, _s = np.cos(_t), np.sin(_t)
ARC = np.c_[A * np.sign(_c) * np.abs(_c) ** (2 / ARC_N), B * np.abs(_s) ** (2 / ARC_N)]
ARC_LINE = LineString(ARC)
F = Polygon([(0, 0)] + ARC.tolist())                        # pianta a tre lati
Q = quadrant()
F_IN = F.difference(ARC_LINE.buffer(NOSE_SET, quad_segs=16))  # corpo arretrato
F_IN = max(F_IN.geoms, key=lambda g: g.area) if F_IN.geom_type == "MultiPolygon" else F_IN
# colonnina dello schienale sopra l'uscita del tubo (aperta verso il muro)
COLUMN = box(0, PIPE_Y - COL_HW, RISER[0], PIPE_Y + COL_HW).union(disc(RISER, COL_HW))
CHASE = box(-1, PIPE_Y - CH_HW, RISER[0], PIPE_Y + CH_HW).union(disc(RISER, CH_HW))


def front_arc_of(poly):
    """Bordo di 'poly' che non giace sulle pareti (x=0 o y=0)."""
    walls = LineString([(0, 2000), (0, 0), (2000, 0)]).buffer(0.05)
    return poly.exterior.difference(walls)


# Interno vasca (zona bagnata) ------------------------------------------------
_I = F.difference(ARC_LINE.buffer(RIM_W))
_I = _I.intersection(box(T_W, T_S, 2000, 2000)).difference(COLUMN.buffer(0.01))
_I = _I.buffer(8, join_style=1).buffer(-14, join_style=1).buffer(6, join_style=1)
I_BASIN = max(polys(_I), key=lambda g: g.area)
I_FUNNEL = I_BASIN.buffer(-LEDGE, join_style=1)
DRAIN = SPOUT

# Corpo: interno e anello di centraggio --------------------------------------
CI = F_IN.buffer(-WALL, join_style=2)
DOOR_WEDGE = wedge(DOOR_A1, DOOR_A2)
LIP = CI.buffer(2.5, join_style=2).difference(CI).intersection(F_IN.buffer(-0.01))  # meta' interna della parete
LIP = LIP.difference(DOOR_WEDGE.buffer(1.0))

# Viti corpo -> vasca (4 linguette) ------------------------------------------
def _in_point(angle_deg, inset):
    r = Point(0, 0)
    ray = LineString([(0, 0), (2000 * math.cos(math.radians(angle_deg)),
                                2000 * math.sin(math.radians(angle_deg)))])
    p = ray.intersection(F_IN.exterior)
    p = max(polys_points(p), key=lambda q: q.distance(r))
    k = (p.distance(r) - inset) / p.distance(r)
    return (p.x * k, p.y * k)


def polys_points(g):
    return list(g.geoms) if hasattr(g, "geoms") else [g]


TABS = [  # (centro vite, punto d'attacco alla parete)
    ((80.0, WALL + 9.0), (80.0, 0.0)),
    ((WALL + 9.0, 80.0), (0.0, 80.0)),
    (_in_point(6.0, 14.0), _in_point(6.0, -2.0)),
    (_in_point(85.0, 14.0), _in_point(85.0, -2.0)),
]
Z_TAB = (756.0, 764.0)

# Viti schienale -> vasca ----------------------------------------------------
BS_SCREWS = [(13.5, 38.0), (13.5, 160.0), (13.5, 222.0)]
HEAD_PINS = [(9.0, PIPE_Y - (CH_HW + COL_HW) / 2), (9.0, PIPE_Y + (CH_HW + COL_HW) / 2)]

# Magneti sportello -----------------------------------------------------------
MAG_ANG = [DOOR_A1 + 9.0, DOOR_A2 - 9.0]
MAG_PTS = [_in_point(a, WALL + 6.5) for a in MAG_ANG]


# ---------------------------------------------------------------------------
# 01 VASCA (piano con bordo affusolato, sede griglia, imbuto di scarico)
# ---------------------------------------------------------------------------
def funnel_floor(X, Y):
    r = np.hypot(X - DRAIN[0], Y - DRAIN[1])
    return np.minimum(Z_DRAIN + FUNNEL_SLOPE * r, Z_GRID_TOP - GRID_T - 1.5)


def vasca():
    b = (-1, -1, A + 1, B + 1)
    arc = ARC_LINE

    def top(X, Y):
        d = dist_to(arc, X, Y)
        return Z_TOP - bullnose(d, NOSE_R)

    def bot(X, Y):
        d = dist_to(arc, X, Y)
        return (Z_TOP - 14.0) - np.minimum(d, NOSE_SET)

    nose = sandwich(b, 0.6, top, bot) ^ prism(F, Z_TOP - 40, Z_TOP + 1)
    skirt = prism(F_IN, Z_VASCA_BOT, Z_TOP - 14.0 - NOSE_SET + 0.5)
    body = nose + skirt
    # cresta anti-infiltrazione sotto lo schienale
    ridge = union([prism(box(4, 4, A - 30, 7), Z_TOP - 0.5, Z_TOP + 4),
                   prism(box(4, 4, 7, B - 30), Z_TOP - 0.5, Z_TOP + 4)])
    body = body + ridge

    cuts = []
    # sede griglia
    cuts.append(prism(I_BASIN, Z_GRID_TOP - GRID_T, Z_TOP + 10))
    # imbuto
    fb = I_FUNNEL.bounds
    fun = sandwich((fb[0] - 1, fb[1] - 1, fb[2] + 1, fb[3] + 1), 0.8,
                   lambda X, Y: np.full_like(X, Z_GRID_TOP - GRID_T + 0.5), funnel_floor)
    cuts.append(fun ^ prism(I_FUNNEL, 700, 900))
    # tacca per le dita (estrazione griglia)
    fp = I_BASIN.exterior.interpolate(I_BASIN.exterior.project(Point(A * 0.8, B * 0.8)))
    cuts.append(cyl((fp.x, fp.y), 11, Z_GRID_TOP - GRID_T + 2, Z_TOP + 5))
    # scarico
    cuts.append(cyl(DRAIN, DRAIN_D / 2, Z_VASCA_BOT - 5, Z_DRAIN + 2))
    # scanalatura di centraggio sul corpo
    cuts.append(prism(LIP.buffer(0.35, join_style=2), Z_VASCA_BOT - 1, Z_VASCA_BOT + LIP_H + 0.6))
    # inserti M4 viti dal corpo
    for c, _ in TABS:
        cuts.append(cyl(c, INSERT_M4 / 2, Z_VASCA_BOT - 1, Z_VASCA_BOT + 10))
    # viti schienale: foro passante + lamatura dal basso
    for c in BS_SCREWS:
        cuts.append(cyl(c, 2.3, Z_VASCA_BOT - 1, Z_TOP + 1))
        cuts.append(cyl(c, 4.5, Z_VASCA_BOT - 1, Z_TOP - 16))
    # magneti sportello
    for p in MAG_PTS:
        cuts.append(cyl(p, MAG_D / 2, Z_VASCA_BOT - 1, Z_VASCA_BOT + MAG_H))
    body = subtract(body, cuts)
    # piccoli appoggi della griglia nell'imbuto
    posts = []
    for a in (30, 150, 270):
        p = (DRAIN[0] + 48 * math.cos(math.radians(a)), DRAIN[1] + 48 * math.sin(math.radians(a)))
        if I_FUNNEL.buffer(-6).contains(Point(p)):
            posts.append(cyl(p, 4, Z_DRAIN, Z_GRID_TOP - GRID_T - 0.2, 32))
    if posts:
        body = body + union(posts)
    return body


# ---------------------------------------------------------------------------
# 02 GRIGLIA removibile
# ---------------------------------------------------------------------------
def griglia():
    g = I_BASIN.buffer(-0.6, join_style=1)
    z0, z1 = Z_GRID_TOP - GRID_T, Z_GRID_TOP
    plate = prism(g, z0, z1)
    inner = g.buffer(-7, join_style=1)
    # asole perpendicolari alla parete della fontana, passo 9 mm
    from shapely.ops import unary_union
    e = np.array([1.0, 0.0])      # asole perpendicolari alla parete della fontana
    nrm = np.array([0.0, 1.0])
    slots = []
    for k in range(-30, 31):
        p0 = -400 * e + k * 9.0 * nrm
        p1 = 400 * e + k * 9.0 * nrm
        for p in polys(LineString([tuple(p0), tuple(p1)]).buffer(2.0).intersection(inner)):
            if p.area > 30:
                slots.append(p)
    sl = unary_union(slots)
    # due nervature trasversali di irrigidimento
    ribs = unary_union([LineString([tuple(c * e - 400 * nrm), tuple(c * e + 400 * nrm)]).buffer(2.5)
                        for c in (80.0, 135.0)])
    sl = sl.difference(ribs)
    return plate - prism(sl, z0 - 1, z1 + 1)


# ---------------------------------------------------------------------------
# 03 SCHIENALE (ali aderenti alle pareti + colonna d'angolo cava)
# ---------------------------------------------------------------------------
def bs_footprint():
    """Schienale sulla parete B (lunga) con colonnina sul tubo + alzatina sulla parete A."""
    g = union_geo([box(0, 0, T_W, B), box(0, 0, A, T_S), COLUMN])
    g = g.buffer(10, join_style=1).buffer(-10, join_style=1).intersection(Q)  # raccordi concavi
    lim = F.difference(ARC_LINE.buffer(NOSE_R + 2))
    return g.intersection(lim)


def union_geo(gs):
    from shapely.ops import unary_union
    return unary_union(gs)


def bs_height(X, Y):
    """Profilo a onda: massimo sulla colonnina del tubo, scende verso l'angolo e verso
    l'estremita' della parete B; alzatina costante sulla parete A."""
    s = np.abs(Y - PIPE_Y)
    far = Y > PIPE_Y
    L = np.where(far, (B - NOSE_R - 2) - PIPE_Y, PIPE_Y)
    tail = np.where(far, BS_TAIL_H, UPSTAND_H)
    q = np.clip((s - COL_HW) / (L - COL_HW), 0, 1)
    f = (1 - q) ** 2.6
    hB = Z_TOP + tail + (Z_BS_TOP - Z_TOP - tail) * f
    return np.where(X <= COLUMN.bounds[2] + 2, hB, Z_TOP + UPSTAND_H)


def schienale():
    fp = bs_footprint()
    free = front_arc_of(fp)
    b = fp.bounds

    def top(X, Y):
        h = bs_height(X, Y)
        d = dist_to(free, X, Y)
        s = np.where(X <= COLUMN.bounds[2] + 2, np.abs(Y - PIPE_Y), 999.0)
        w = np.clip((s - COL_HW) / 20.0, 0, 1)
        w = w * w * (3 - 2 * w)
        return h - w * bullnose(d, 9.0)

    body = sandwich((b[0] - 1, b[1] - 1, b[2] + 1, b[3] + 1), 0.5, top,
                    lambda X, Y: np.full_like(X, Z_TOP)) ^ prism(fp, Z_TOP - 1, Z_BS_TOP + 5)
    cuts = [prism(CHASE, Z_TOP + 3, Z_BS_TOP + 5)]   # cavedio del tubo, aperto verso il muro
    # scanalatura per la cresta della vasca
    cuts.append(union([prism(box(3.6, 3.6, A - 29.6, 7.4), Z_TOP - 1, Z_TOP + 4.5),
                       prism(box(3.6, 3.6, 7.4, B - 29.6), Z_TOP - 1, Z_TOP + 4.5)]))
    for c in BS_SCREWS:
        cuts.append(cyl(c, INSERT_M4 / 2, Z_TOP - 1, Z_TOP + 9))
    for p in HEAD_PINS:
        cuts.append(cyl(p, 2.1, Z_BS_TOP - 10, Z_BS_TOP + 1, 32))
    return subtract(body, cuts)


# ---------------------------------------------------------------------------
# 04 TESTA con beccuccio (stampa capovolta, senza supporti)
# ---------------------------------------------------------------------------
ARM_P0 = np.array(RISER)
ARM_P1 = np.array(SPOUT)


def _stadium(p0, p1, r):
    return LineString([tuple(p0), tuple(p1)]).buffer(r, quad_segs=24)


def testa():
    z0, z1 = Z_BS_TOP, Z_HEAD_TOP
    col = prism(COLUMN, z0, z1)
    # braccio: parte alta a pianta "stadio" + fondo cilindrico
    arm_top = prism(_stadium(ARM_P0, ARM_P1, ARM_R), Z_ARM, z1)
    arm_bot = cyl_along((*ARM_P0, Z_ARM), (*ARM_P1, Z_ARM), ARM_R)
    spout = cyl(SPOUT, SPOUT_R, Z_OUTLET, z1)
    body = union([col, arm_top, arm_bot, spout])
    # smusso perimetrale sulla faccia superiore
    cuts = []
    # cavedio colonna (aperto sul retro e sotto)
    cuts.append(prism(CHASE, z0 - 5, z1 - 6))
    # canale braccio (aperto sotto: la testa si cala dall'alto sul tubo)
    ch = _stadium(ARM_P0, ARM_P1, CH_W)
    cuts.append(prism(ch, z0 - 5, z1 - 6))   # include la feritoia verticale nella colonna
    cuts.append(cyl(SPOUT, SPOUT_RI, Z_OUTLET - 5, z1 - 6))
    body = subtract(body, cuts)
    # borchie per le viti della copertura inferiore
    u = (ARM_P1 - ARM_P0) / np.linalg.norm(ARM_P1 - ARM_P0)
    n = np.array([-u[1], u[0]])
    bosses = []
    for c in strip_screws():
        blk = Point(*c).buffer(4.0, cap_style=3)
        side = 1.0 if np.dot(np.asarray(c) - ARM_P0, n) > 0 else -1.0
        wall_strip = Point(*(np.asarray(c) + n * side * 3.5)).buffer(0.5, cap_style=3)
        # smusso a 45 deg verso la parete: stampabile anche capovolto
        b = Manifold.batch_hull([prism(blk, Z_ARM - 11, Z_ARM + 1), prism(wall_strip, Z_ARM - 11, Z_ARM + 9)])
        b = b ^ prism(_stadium(ARM_P0, ARM_P1, CH_W + 1), 0, 2000)
        bosses.append(b - cyl(c, INSERT_M3 / 2, Z_ARM - 12, Z_ARM - 4, 24))
    body = body + union(bosses)
    for p in HEAD_PINS:
        body = body - cyl(p, 2.1, z0 - 1, z0 + 10, 32)
    return body


def strip_screws():
    u = (ARM_P1 - ARM_P0) / np.linalg.norm(ARM_P1 - ARM_P0)
    n = np.array([-u[1], u[0]])
    return [tuple(ARM_P0 + u * 33.0 + n * 15.5), tuple(ARM_P0 + u * 47.0 - n * 15.5)]


def copertura_braccio():
    """Listello a L (antracite): chiude la feritoia della colonna e il canale sotto il
    braccio. Trattiene la testa sul tubo PPR."""
    u = (ARM_P1 - ARM_P0) / np.linalg.norm(ARM_P1 - ARM_P0)
    n = np.array([-u[1], u[0]])
    t0 = 0.0
    t1 = np.linalg.norm(ARM_P1 - ARM_P0) - SPOUT_RI - 0.3
    a, b = ARM_P0 + u * t0, ARM_P0 + u * t1
    hw = CH_W - 0.3
    rect = Polygon([tuple(a + n * hw), tuple(b + n * hw), tuple(b - n * hw), tuple(a - n * hw)])
    ztop = Z_ARM - 11.2
    outer = cyl_along((*ARM_P0, Z_ARM), (*ARM_P1, Z_ARM), ARM_R)
    xf = COLUMN.bounds[2]
    horiz = (outer ^ prism(rect, Z_ARM - 30, ztop)) - prism(box(-10, -1000, xf - 3, 1000), 0, 2000)
    ring = COLUMN.difference(CHASE.buffer(0.3)).intersection(rect)
    vert = prism(ring, Z_BS_TOP + 0.4, ztop)
    strip = (horiz + vert) - cyl(SPOUT, SPOUT_RI + 0.3, Z_OUTLET - 5, Z_HEAD_TOP)
    # ribasso sotto il gomito femmina (diametro ~30 mm)
    tc = 52.0
    c0, c1 = ARM_P0 + u * tc, ARM_P0 + u * 200
    endr = Polygon([tuple(c0 + n * 30), tuple(c1 + n * 30), tuple(c1 - n * 30), tuple(c0 - n * 30)])
    strip = strip - prism(endr, Z_ARM - 16.0, Z_ARM)
    zb = Z_ARM - math.sqrt(ARM_R ** 2 - 15.5 ** 2)
    for c in strip_screws():
        strip = strip - cyl(c, 1.7, Z_ARM - 40, Z_ARM, 24)
        strip = strip - Manifold.cylinder(1.7, 3.4, 1.7, 24).translate([c[0], c[1], zb - 0.01])
        strip = strip - cyl(c, 3.4, Z_ARM - 40, zb, 24)
    return strip


# ---------------------------------------------------------------------------
# 05 CORPO / vano tecnico
# ---------------------------------------------------------------------------
def tank_frame(u, v):
    c, s = math.cos(math.radians(TANK_PHI)), math.sin(math.radians(TANK_PHI))
    return (u * c - v * s, u * s + v * c)


def tank_poly(inset=0.0, r=12.0):
    u0, u1 = TANK_U0 + inset, TANK_U0 + TANK_L - inset
    v0, v1 = TANK_VOFF - TANK_W / 2 + inset, TANK_VOFF + TANK_W / 2 - inset
    rr = max(r - inset, 0.5)
    p = box(u0 + rr, v0 + rr, u1 - rr, v1 - rr).buffer(rr, quad_segs=12)
    return affinity.rotate(p, TANK_PHI, origin=(0, 0))


SERVICE_HOLES = [((22.0, 40.0), 15.0), ((22.0, 70.0), 12.0)]  # nel fondo: mandata pompa, cavo 12 V
WALL_SCREWS_A = [(60.0, 605.0), (60.0, 735.0), (160.0, 605.0)]   # (x, z) sulla parete A
WALL_SCREWS_B = [(60.0, 605.0), (60.0, 735.0), (225.0, 605.0)]   # (y, z) sulla parete B
BOX_SCREWS = [(135.0, 736.0), (185.0, 736.0)]                    # (y, z) box -> parete B


def corpo():
    z0, z1 = Z_CORPO_BOT, Z_VASCA_BOT
    outer = prism(F_IN, z0, z1)
    cuts = [prism(CI, z0 + FLOOR, z1 + 1)]
    # apertura sportello (aperta in alto: chiusa dalla vasca)
    band = front_arc_of(F_IN).buffer(WALL + 3)
    cuts.append(prism(band.intersection(DOOR_WEDGE), Z_DOOR_BOT, z1 + 1))
    # fori di scarico del fondo
    for (x, y) in [(60, 30), (95, 60), (130, 40), (60, 130), (100, 160), (45, 200)]:
        cuts.append(cyl((x, y), 3.5, z0 - 1, z0 + FLOOR + 1, 24))
    # passaggi servizi nel fondo, vicino all'angolo (mandata pompa, cavo 12 V)
    for c, dd in SERVICE_HOLES:
        cuts.append(cyl(c, dd / 2, z0 - 1, z0 + FLOOR + 1, 32))
    # viti a muro (svasate, testa interna)
    for x, z in WALL_SCREWS_A:
        cuts.append(cyl_along((x, -1, z), (x, WALL + 1, z), 3.25, 32))
        cuts.append(Manifold.cylinder(3.5, 3.25, 6.6, 32).rotate([-90, 0, 0]).translate([x, WALL - 3.5, z]))
    for y, z in BOX_SCREWS:
        cuts.append(cyl_along((-1, y, z), (WALL + 1, y, z), 2.6, 32))
    for y, z in WALL_SCREWS_B:
        cuts.append(cyl_along((-1, y, z), (WALL + 1, y, z), 3.25, 32))
        cuts.append(Manifold.cylinder(3.5, 3.25, 6.6, 32).rotate([0, 90, 0]).translate([WALL - 3.5, y, z]))
    body = subtract(outer, cuts)
    # pareti del cavedio sono gia' parte di outer-CI. Linguette viti verso la vasca
    adds = []
    for c, w in TABS:
        top = disc(c, 8).union(disc(w, 8)).convex_hull.intersection(F_IN)
        slab = prism(top, Z_TAB[0], Z_TAB[1])
        foot = prism(disc(w, 8).intersection(F_IN), Z_TAB[0] - 18, Z_TAB[1])
        tab = Manifold.batch_hull([slab, foot]) ^ prism(F_IN, 0, 2000)
        adds.append(tab - cyl(c, 2.25, Z_TAB[0] - 30, Z_TAB[1] + 1, 32))
    # anello di centraggio
    adds.append(prism(LIP, z1 - 0.01, z1 + LIP_H))
    # binari di appoggio del serbatoio
    for dv in (-40, 40):
        a = tank_frame(TANK_U0 + 8, TANK_VOFF + dv)
        bpt = tank_frame(TANK_U0 + TANK_L + 30, TANK_VOFF + dv)
        rail = LineString([a, bpt]).buffer(2.0).intersection(CI.difference(front_band(0, WALL + 4)))
        adds.append(prism(rail, z0 + FLOOR - 0.01, TANK_Z0))
    body = body + union(adds)
    # i fori nelle linguette ripassati
    return body


# ---------------------------------------------------------------------------
# 06 SPORTELLO frontale curvo (griglia di ventilazione verticale)
# ---------------------------------------------------------------------------
def front_band(i0, i1):
    """Fascia della pianta del corpo tra le distanze i0..i1 dal bordo frontale."""
    arc = front_arc_of(F_IN)
    g = F_IN.intersection(arc.buffer(i1, quad_segs=16))
    return g.difference(arc.buffer(i0, quad_segs=16)) if i0 > 0 else g


def sportello():
    w = DOOR_WEDGE.buffer(-0.5, join_style=2)
    door2d = front_band(0, WALL).intersection(w)
    z0, z1 = Z_DOOR_BOT + 0.5, Z_VASCA_BOT - 0.4
    door = prism(door2d, z0, z1)
    hook = prism(front_band(WALL, WALL + 2.5).intersection(w), Z_CORPO_BOT + FLOOR + 1.0, z0 + 4)
    # nervatura superiore con magneti (sotto: smusso 45 deg)
    rib_parts = []
    for a in MAG_ANG:
        seg = front_band(WALL - 0.5, WALL + 13).intersection(wedge(a - 4, a + 4))
        top = prism(seg, z1 - 8, z1)
        foot = prism(front_band(WALL - 0.5, WALL + 0.5).intersection(wedge(a - 4, a + 4)), z1 - 21, z1)
        rib_parts.append(Manifold.batch_hull([top, foot]))
    door = union([door, hook] + rib_parts)
    for p in MAG_PTS:
        door = door - cyl(p, MAG_D / 2, z1 - MAG_H, z1 + 1, 32)
    # asole verticali
    slots = []
    for a in np.arange(DOOR_A1 + 7, DOOR_A2 - 6, 2.2):
        r0 = 50
        ln = LineString([(r0 * math.cos(math.radians(a)), r0 * math.sin(math.radians(a))),
                         (400 * math.cos(math.radians(a)), 400 * math.sin(math.radians(a)))])
        slots.append(prism(ln.buffer(1.5), Z_DOOR_BOT + 18, Z_DOOR_BOT + 62))
    return subtract(door, slots)


# ---------------------------------------------------------------------------
# 07 SERBATOIO estraibile + 08 coperchio
# ---------------------------------------------------------------------------
TANK_WALL = 3.0


def serbatoio():
    z0, z1 = TANK_Z0, TANK_Z0 + TANK_H
    t = prism(tank_poly(), z0, z1) - prism(tank_poly(TANK_WALL), z0 + TANK_WALL, z1 + 1)
    # maniglia: aletta sul fronte con smusso
    a, b = tank_frame(TANK_U0 + TANK_L - 2, TANK_VOFF - 35), tank_frame(TANK_U0 + TANK_L - 2, TANK_VOFF + 35)
    c, d = tank_frame(TANK_U0 + TANK_L + 12, TANK_VOFF + 35), tank_frame(TANK_U0 + TANK_L + 12, TANK_VOFF - 35)
    fin = Polygon([a, b, c, d])
    fin_m = Manifold.batch_hull([prism(fin, z1 - 6, z1),
                                 prism(Polygon([a, b, tank_frame(TANK_U0 + TANK_L, TANK_VOFF + 35),
                                                tank_frame(TANK_U0 + TANK_L, TANK_VOFF - 35)]), z1 - 20, z1)])
    t = t + fin_m
    # troppo pieno sul retro (verso l'angolo) e passaggio cavi/tubo
    o = tank_frame(TANK_U0, TANK_VOFF + 30)
    t = t - prism(Point(o).buffer(10), z1 - 12, z1 + 1)
    return t


def coperchio_serbatoio():
    z0 = TANK_Z0 + TANK_H
    plate = prism(tank_poly(), z0, z0 + 3)
    skirt = prism(tank_poly(TANK_WALL + 0.4).difference(tank_poly(TANK_WALL + 2.6)), z0 - 6, z0 + 0.01)
    lid = plate + skirt
    cuts = [cyl(DRAIN, 30, z0 - 10, z0 + 10)]                               # imbuto ingresso
    for uv in ((TANK_U0 + 20, TANK_VOFF - 45), (TANK_U0 + 20, TANK_VOFF - 22)):
        cuts.append(cyl(tank_frame(*uv), 5.3, z0 - 10, z0 + 10, 32))          # galleggianti M10
    o = tank_frame(TANK_U0, TANK_VOFF + 30)
    cuts.append(prism(Point(o).buffer(11), z0 - 10, z0 + 10))               # tubo/cavi
    # presa
    return subtract(lid, cuts)


# ---------------------------------------------------------------------------
# 09 BOX ELETTRONICA stagno + 10 coperchio
# ---------------------------------------------------------------------------
def _to_wall_b(m):
    """Il box e' modellato come se fosse sulla parete A (y=0) e poi specchiato sulla parete B."""
    return m.mirror([1, -1, 0])


def box_elettronica():
    return _to_wall_b(_box_local())


def _box_local():
    x0, x1 = BOX_ALONG; y0, y1 = BOX_DEPTH; z0, z1 = BOX_Z
    W = 2.5
    outer = Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])
    inner = Manifold.cube([x1 - x0 - 2 * W, y1 - y0 - W + 1, z1 - z0 - 2 * W]).translate([x0 + W, y0 + W, z0 + W])
    b = outer - inner
    # bossoli angolari per inserti M3 (viti coperchio)
    adds = []
    for x in (x0 + W + 4, x1 - W - 4):
        for z in (z0 + W + 4, z1 - W - 4):
            adds.append(cyl_along((x, y0 + W, z), (x, y1, z), 4.5, 32))
    # 4 colonnine per piastra componenti
    for x in (x0 + 20, x1 - 20):
        for z in (z0 + 14, z1 - 14):
            adds.append(cyl_along((x, y0 + W - 0.1, z), (x, y0 + W + 6, z), 3.0, 24))
    b = b + union(adds)
    cuts = []
    for x in (x0 + W + 4, x1 - W - 4):
        for z in (z0 + W + 4, z1 - W - 4):
            cuts.append(cyl_along((x, y1 - 8, z), (x, y1 + 1, z), INSERT_M3 / 2, 24))
    for x in (x0 + 20, x1 - 20):
        for z in (z0 + 14, z1 - 14):
            cuts.append(cyl_along((x, y0 + W, z), (x, y0 + W + 7, z), 1.1, 16))
    # guarnizione: striscia EPDM adesiva 3x6 mm sul coperchio
    # passacavi PG7 sul fondo, fori viti a muro sul retro
    for x in (x0 + 25, x1 - 25):
        cuts.append(cyl((x, (y0 + y1) / 2), 6.3, z0 - 1, z0 + W + 1, 32))
    for x, z in BOX_SCREWS:
        cuts.append(cyl_along((x, y0 - 1, z), (x, y0 + W + 1, z), 2.6, 32))
    return subtract(b, cuts)


def coperchio_box():
    return _to_wall_b(_box_lid_local())


def _box_lid_local():
    x0, x1 = BOX_ALONG; y0, y1 = BOX_DEPTH; z0, z1 = BOX_Z
    W = 2.5
    lid = Manifold.cube([x1 - x0, 3.0, z1 - z0]).translate([x0, y1, z0])
    for x in (x0 + W + 4, x1 - W - 4):
        for z in (z0 + W + 4, z1 - W - 4):
            lid = lid - cyl_along((x, y1 - 1, z), (x, y1 + 4, z), 1.7, 24)
    return lid


# ---------------------------------------------------------------------------
# Elenco pezzi, orientamento di stampa, esportazione
# ---------------------------------------------------------------------------
PARTS = [
    # nome, funzione, colore, orientamento ('up' | 'flip' | ('rot', axis, deg)), quantita'
    ("01_vasca", vasca, "sabbia", "up", 1),
    ("02_griglia", griglia, "antracite", "up", 1),
    ("03_schienale", schienale, "sabbia", "up", 1),
    ("04_testa_beccuccio", testa, "sabbia", "flip", 1),
    ("05_copertura_braccio", copertura_braccio, "sabbia", "flip", 1),
    ("06_corpo_vano", corpo, "sabbia", "up", 1),
    ("07_sportello", sportello, "sabbia", "flip", 1),
    ("08_serbatoio", serbatoio, "grigio", "up", 1),
    ("09_coperchio_serbatoio", coperchio_serbatoio, "grigio", "flip", 1),
    ("10_box_elettronica", box_elettronica, "antracite", ("rot", "x", 90), 1),
    ("11_coperchio_box", coperchio_box, "antracite", ("rot", "x", 90), 1),
]


def to_trimesh(m):
    mesh = m.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3]
    f = np.asarray(mesh.tri_verts)
    return trimesh.Trimesh(v, f, process=False)


def print_orient(tm, how):
    t = tm.copy()
    if how == "flip":
        t.apply_transform(trimesh.transformations.rotation_matrix(math.pi, [1, 0, 0]))
    elif isinstance(how, tuple) and how[0] == "rot":
        ax = {"x": [1, 0, 0], "y": [0, 1, 0], "z": [0, 0, 1]}[how[1]]
        t.apply_transform(trimesh.transformations.rotation_matrix(math.radians(how[2]), ax))
    # per i pezzi piu' larghi del piatto, ruota nel piano per stare nei 250x250
    lo, hi = t.bounds
    t.apply_translation([-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2]])
    return t


def build(only=None):
    out_a = os.path.join(ROOT, "stl", "assembly")
    out_p = os.path.join(ROOT, "stl", "print")
    os.makedirs(out_a, exist_ok=True)
    os.makedirs(out_p, exist_ok=True)
    report = []
    for name, fn, color, how, qty in PARTS:
        if only and not any(o in name for o in only):
            continue
        m = fn().simplify(0.02)
        tm = to_trimesh(m)
        tm.export(os.path.join(out_a, name + ".stl"))
        pt = print_orient(tm, how)
        pt.export(os.path.join(out_p, name + ".stl"))
        ext = pt.extents
        ok = bool(np.all(ext <= MAX_PRINT + 1e-6))
        info = dict(name=name, color=color, qty=qty, watertight=bool(tm.is_watertight),
                    volume_cm3=round(tm.volume / 1000, 1),
                    print_size_mm=[round(float(e), 1) for e in ext], fits_250=ok)
        report.append(info)
        print(f"{name:28s} {ext[0]:6.1f} x {ext[1]:6.1f} x {ext[2]:6.1f}  "
              f"vol {tm.volume/1000:7.1f} cm3  watertight={tm.is_watertight}  fit={ok}")
    if not only:
        with open(os.path.join(ROOT, "stl", "parts.json"), "w") as f:
            json.dump(report, f, indent=1)
    return report


if __name__ == "__main__":
    build(sys.argv[1:] or None)


# ---------------------------------------------------------------------------
# Riferimenti non stampati (per verifiche e rendering)
# ---------------------------------------------------------------------------
def tubo_ppr():
    """Percorso indicativo PPR DN20: esce dal muro (parete B) a Z_PIPE_IN, gomito in su,
    salita nella colonnina, gomito a 90 deg, braccio, gomito 20 x 1/2" F verso il basso."""
    w0 = (-30.0, PIPE_Y, Z_PIPE_IN)
    wz = (*RISER, Z_PIPE_IN)
    rz = (*RISER, Z_ARM)
    sz = (*SPOUT, Z_ARM)
    u = np.array([1.0, 0.0])
    parts = [cyl_along(w0, wz, 10, 48),                                   # uscita dal muro
             Manifold.sphere(14.5, 48).translate(list(wz)),
             cyl_along((RISER[0] - 16, PIPE_Y, Z_PIPE_IN), wz, 14.5, 48),  # gomito basso
             cyl(RISER, 14.5, Z_PIPE_IN, Z_PIPE_IN + 16, 48),
             cyl(RISER, 10, Z_PIPE_IN, Z_ARM, 48),
             Manifold.sphere(14.5, 48).translate(list(rz)),
             cyl(RISER, 14.5, Z_ARM - 16, Z_ARM, 48),
             cyl_along(rz, (RISER[0] + 16, PIPE_Y, Z_ARM), 14.5, 48),       # gomito alto
             cyl_along(rz, sz, 10, 48),
             Manifold.sphere(15.0, 48).translate(list(sz)),
             cyl_along((SPOUT[0] - 18, PIPE_Y, Z_ARM), sz, 15, 48),         # gomito femmina
             cyl(SPOUT, 15, Z_OUTLET + 4, Z_ARM, 48)]
    return union(parts)


def rompigetto():
    return cyl(SPOUT, 12, Z_OUTLET - 6, Z_OUTLET + 4, 48)


def pompa():
    """Ingombro indicativo pompa sommersa 12 V (circa 45 x 40 x 40 mm) + tubo di mandata."""
    c = tank_frame(TANK_U0 + 30, TANK_VOFF + 25)
    body = Manifold.cube([45, 40, 40], True).rotate([0, 0, TANK_PHI]).translate([c[0], c[1], TANK_Z0 + 3 + 20])
    o = tank_frame(TANK_U0, TANK_VOFF + 30)
    hose = cyl_along((c[0], c[1], TANK_Z0 + 43), (c[0], c[1], TANK_Z0 + TANK_H - 6), 5, 24) + \
        cyl_along((c[0], c[1], TANK_Z0 + TANK_H - 6), (o[0], o[1], TANK_Z0 + TANK_H - 6), 5, 24)
    return body + hose


def galleggianti():
    """Due interruttori a galleggiante verticali (livello alto / basso) appesi al coperchio."""
    out = []
    for uv, L in (((TANK_U0 + 20, TANK_VOFF - 45), 40.0), ((TANK_U0 + 20, TANK_VOFF - 22), 85.0)):
        p = tank_frame(*uv)
        z = TANK_Z0 + TANK_H
        out.append(cyl(p, 4, z - L, z + 8, 24))
        out.append(cyl(p, 12, z - L - 2, z - L + 22, 32))
    return union(out)
