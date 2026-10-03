"""Utility geometriche: shapely (2D) -> manifold3d (3D)."""
import math
import numpy as np
import shapely
from shapely.geometry import Polygon, MultiPolygon, LineString, Point, box
from shapely.geometry.polygon import orient
from manifold3d import Manifold, CrossSection, Mesh

SEG = 96  # segmenti per cerchi


def polys(geom):
    if geom.is_empty:
        return []
    if isinstance(geom, Polygon):
        return [geom]
    if isinstance(geom, MultiPolygon):
        return list(geom.geoms)
    return [g for g in getattr(geom, "geoms", []) if isinstance(g, Polygon)]


def to_cs(geom):
    rings = []
    for p in polys(geom):
        p = orient(p, 1.0)
        rings.append(np.asarray(p.exterior.coords)[:-1])
        for h in p.interiors:
            rings.append(np.asarray(h.coords)[:-1])
    return CrossSection(rings)


def prism(geom, z0, z1):
    cs = to_cs(geom)
    if cs.is_empty():
        return Manifold()
    return Manifold.extrude(cs, z1 - z0).translate([0, 0, z0])


def disc(c, r, n=SEG):
    return Point(c).buffer(r, quad_segs=max(8, n // 4))


def quadrant(size=2000):
    return box(0, 0, size, size)


def wedge(a1, a2, r=2000, n=64):
    """Settore polare dall'origine tra gli angoli a1..a2 (gradi)."""
    ts = np.radians(np.linspace(a1, a2, n))
    pts = [(0, 0)] + [(r * math.cos(t), r * math.sin(t)) for t in ts]
    return Polygon(pts)


def cyl(c, r, z0, z1, n=SEG):
    return Manifold.cylinder(z1 - z0, r, r, n).translate([c[0], c[1], z0])


def cyl_along(p0, p1, r, n=SEG):
    """Cilindro tra due punti 3D."""
    p0 = np.asarray(p0, float)
    p1 = np.asarray(p1, float)
    v = p1 - p0
    L = float(np.linalg.norm(v))
    m = Manifold.cylinder(L, r, r, n)
    # z -> direzione v
    yaw = math.degrees(math.atan2(v[1], v[0]))
    pitch = math.degrees(math.acos(v[2] / L))
    return m.rotate([0, pitch, 0]).rotate([0, 0, yaw]).translate(p0.tolist())


def sandwich(bounds, step, top_fn, bot_fn):
    """Solido compreso tra due superfici z=bot(x,y) e z=top(x,y) su una griglia."""
    x0, y0, x1, y1 = bounds
    xs = np.arange(x0, x1 + step, step)
    ys = np.arange(y0, y1 + step, step)
    X, Y = np.meshgrid(xs, ys)
    T = np.asarray(top_fn(X, Y), float)
    Bt = np.asarray(bot_fn(X, Y), float)
    T = np.maximum(T, Bt + 0.05)
    ny, nx = X.shape
    N = nx * ny
    vt = np.c_[X.ravel(), Y.ravel(), T.ravel()]
    vb = np.c_[X.ravel(), Y.ravel(), Bt.ravel()]
    verts = np.vstack([vt, vb]).astype(np.float32)
    idx = np.arange(N).reshape(ny, nx)
    a = idx[:-1, :-1].ravel(); b = idx[:-1, 1:].ravel()
    c = idx[1:, 1:].ravel(); d = idx[1:, :-1].ravel()
    top = np.r_[np.c_[a, b, c], np.c_[a, c, d]]
    bot = np.r_[np.c_[a, c, b], np.c_[a, d, c]] + N
    loop = np.r_[idx[0, :], idx[1:, -1], idx[-1, -2::-1], idx[-2:0:-1, 0]]
    la = loop; lb = np.roll(loop, -1)
    s1 = np.c_[la, la + N, lb + N]
    s2 = np.c_[la, lb + N, lb]
    tris = np.vstack([top, bot, s1, s2]).astype(np.uint32)
    m = Manifold(Mesh(vert_properties=verts, tri_verts=tris))
    assert m.status().name == "NoError", m.status()
    return m


def dist_to(geom, X, Y):
    pts = shapely.points(X.ravel(), Y.ravel())
    return shapely.distance(pts, geom).reshape(X.shape)


def contains(geom, X, Y):
    pts = shapely.points(X.ravel(), Y.ravel())
    return shapely.contains(geom, pts).reshape(X.shape)


def bullnose(d, R):
    """Abbassamento per bordo arrotondato di raggio R a distanza d dallo spigolo."""
    d = np.clip(d, 0, R)
    return R - np.sqrt(np.maximum(R * R - (R - d) ** 2, 0))


def union(ms):
    ms = [m for m in ms if not m.is_empty()]
    return Manifold.batch_boolean(ms, shapely_op_union()) if len(ms) > 1 else ms[0]


def shapely_op_union():
    from manifold3d import OpType
    return OpType.Add


def subtract(m, cuts):
    from manifold3d import OpType
    cuts = [c for c in cuts if not c.is_empty()]
    if not cuts:
        return m
    return Manifold.batch_boolean([m] + cuts, OpType.Subtract)
