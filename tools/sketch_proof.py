"""Doves italic fork-proof: roman reference vs two italic directions.

Skeletons are swept with a simulated broad-edge nib (rotated rect stamped
along a Catmull-Rom smoothed path, unioned via shapely) so stroke contrast
falls out of real calligraphic geometry rather than generic vector taper.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch, Polygon as MPoly
from matplotlib.path import Path
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
from shapely.geometry import Polygon
from shapely.ops import unary_union

ROMAN = ("/Users/chris/Library/CloudStorage/GoogleDrive-chris@mccaff.us/"
         "Shared drives/McCaffery Ops/IT/Fonts/DovesType_3.117_OTF/DovesType-Regular.otf")

XH = 374
INK = "#1c1a17"
PAPER = "#f7f4ee"


# ---------- nib sweep engine ----------

def catmull(pts, closed=False, subdiv=16):
    """Dense resampling of a point list through a Catmull-Rom spline."""
    P = [np.asarray(p, float) for p in pts]
    n = len(P)
    if n < 2:
        return np.array(P)
    if closed:
        ext = P + P[:3]
        idx = lambda i: i % n
    else:
        ext = [P[0]] + P + [P[-1]]
        idx = None
    out = []
    if closed:
        for i in range(n):
            p0, p1, p2, p3 = ext[i], ext[i + 1], ext[i + 2], ext[i + 3]
            for t in np.linspace(0, 1, subdiv, endpoint=False):
                t2, t3 = t * t, t * t * t
                out.append(0.5 * ((2 * p1) + (-p0 + p2) * t +
                                  (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 +
                                  (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    else:
        for i in range(len(ext) - 3):
            p0, p1, p2, p3 = ext[i], ext[i + 1], ext[i + 2], ext[i + 3]
            for t in np.linspace(0, 1, subdiv, endpoint=False):
                t2, t3 = t * t, t * t * t
                out.append(0.5 * ((2 * p1) + (-p0 + p2) * t +
                                  (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 +
                                  (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
        out.append(P[-1])
    return np.array(out)


def resample_arclen(S, step=3.0):
    """Uniformly resample a dense polyline every `step` units of arc length."""
    d = np.linalg.norm(np.diff(S, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(d)])
    n = max(int(round(s[-1] / step)), 2)
    t = np.linspace(0, s[-1], n)
    return np.column_stack([np.interp(t, s, S[:, 0]),
                            np.interp(t, s, S[:, 1])])


def sweep_glyph(paths, nib_w, nib_th, angle_deg, shear_deg):
    """paths: list of (points, closed). Returns unioned shapely geometry."""
    tan_s = np.tan(np.radians(shear_deg))
    th = np.radians(angle_deg)
    u = np.array([np.cos(th), np.sin(th)])
    v = np.array([-np.sin(th), np.cos(th)])
    h, k = nib_w / 2.0, nib_th / 2.0
    polys = []
    R = np.column_stack([u, v])
    for pts, closed in paths:
        arr = catmull(pts, closed=closed)
        arr[:, 0] += arr[:, 1] * tan_s          # slant shear about y=0
        arr = resample_arclen(arr, step=3.0)    # kill banding on long runs
        for c in arr:
            quad = c + R @ np.array([h, k]), c + R @ np.array([-h, k]), \
                   c + R @ np.array([-h, -k]), c + R @ np.array([h, -k])
            polys.append(Polygon(quad))
    return unary_union(polys).buffer(1.1, join_style=1).simplify(1.3)


# ---------- italic skeleton definitions ----------

CHANCERY = {
    "d": [
        ([(152, 618), (147, 480), (141, 250), (137, 28)], False),
        ([(142, 330), (108, 372), (56, 360), (22, 300), (14, 210),
          (24, 110), (66, 26), (118, 22), (142, 90)], True),
    ],
    "o": [
        ([(10, 175), (26, 295), (78, 366), (150, 380), (218, 350),
          (244, 270), (238, 160), (198, 50), (122, 4), (54, 30),
          (16, 100)], True),
    ],
    "v": [
        ([(8, 352), (46, 214), (82, 62), (100, 12)], False),
        ([(94, 18), (150, 190), (188, 336), (206, 352), (218, 330)], False),
    ],
    "e": [
        ([(22, 222), (150, 250), (166, 296), (128, 358), (66, 366),
          (26, 318), (16, 238), (30, 136), (72, 44), (128, 12),
          (168, 58), (182, 118)], False),
    ],
    "s": [
        ([(198, 316), (156, 354), (102, 362), (58, 332), (50, 282),
          (88, 240), (140, 208), (174, 162), (164, 92), (116, 30),
          (58, 14), (20, 46)], False),
    ],
}

RESTRAINED = {
    "d": [
        ([(150, 616), (146, 470), (142, 250), (140, 28)], False),
        ([(140, 320), (106, 366), (58, 356), (28, 298), (20, 212),
          (30, 112), (70, 28), (116, 24), (140, 86)], True),
    ],
    "o": [
        ([(14, 180), (32, 298), (84, 364), (154, 376), (220, 344),
          (246, 262), (240, 156), (202, 52), (128, 6), (62, 32),
          (22, 102)], True),
    ],
    "v": [
        ([(12, 348), (52, 208), (88, 58), (104, 14)], False),
        ([(100, 18), (156, 194), (192, 334), (210, 350), (222, 328)], False),
    ],
    "e": [
        ([(28, 226), (152, 254), (168, 300), (132, 358), (72, 364),
          (34, 316), (24, 240), (38, 140), (78, 46), (132, 14),
          (172, 58), (186, 116)], False),
    ],
    "s": [
        ([(194, 314), (154, 352), (104, 358), (62, 330), (56, 282),
          (92, 242), (142, 210), (176, 164), (166, 94), (120, 32),
          (64, 16), (26, 48)], False),
    ],
}

DIRS = {
    "A · chancery":   (CHANCERY,   dict(nib_w=64, nib_th=7, angle_deg=20, shear_deg=5)),
    "B · restrained": (RESTRAINED, dict(nib_w=68, nib_th=8, angle_deg=32, shear_deg=10)),
}


# ---------- roman outline extraction ----------

class MplPen(BasePen):
    """BasePen -> matplotlib Path vertices/codes."""
    def __init__(self, glyphSet):
        super().__init__(glyphSet)
        self.v, self.c = [], []

    def _moveTo(self, p):
        self.v.append(p); self.c.append(Path.MOVETO)

    def _lineTo(self, p):
        self.v.append(p); self.c.append(Path.LINETO)

    def _curveToOne(self, a, b, e):
        self.v.extend([a, b, e]); self.c.extend([Path.CURVE4] * 3)

    def _closePath(self):
        if self.c and self.c[-1] != Path.CLOSEPOLY:
            self.v.append(self.v[0]); self.c.append(Path.CLOSEPOLY)


def draw_roman_word(ax, word, x_offset, y_offset):
    f = TTFont(ROMAN)
    gs = f.getGlyphSet()
    cmap = f.getBestCmap()
    x = 0
    for ch in word:
        gn = cmap[ord(ch)]
        adv = gs[gn].width
        pen = MplPen(gs)
        gs[gn].draw(pen)
        verts = [(vx + x + x_offset, vy + y_offset) for vx, vy in pen.v]
        path = Path(verts, pen.c)
        ax.add_patch(PathPatch(path, facecolor=INK, edgecolor=INK, lw=0.4))
        x += adv
    return x


# ---------- italic rendering ----------

def draw_swept(ax, geom, x_offset, y_offset):
    geoms = getattr(geom, "geoms", [geom])
    for g in geoms:
        ext = np.asarray(g.exterior.coords)
        ax.add_patch(MPoly(ext + [x_offset, y_offset], closed=True,
                           facecolor=INK, edgecolor=INK, lw=0.5))
        for hole in g.interiors:
            hx = np.asarray(hole.coords)
            ax.add_patch(MPoly(hx + [x_offset, y_offset], closed=True,
                               facecolor=PAPER, edgecolor=PAPER, lw=0.4))


def word_geometry(defs, params):
    geoms, cursor = {}, 0
    for ch, paths in defs.items():
        g = sweep_glyph(paths, **params)
        xmin, ymin, xmax, ymax = g.bounds
        if cursor > 0:
            cursor -= xmin                      # trim leading sidebearing
        geoms[ch] = (g, cursor)
        cursor += xmax                          # next glyph starts at prev xmax
        cursor += 52                            # fixed letterfit gap
    return geoms, cursor


def build(out="proofs/fork-v1.png"):
    fig, ax = plt.subplots(figsize=(14.5, 9.5), dpi=150)
    fig.patch.set_facecolor(PAPER)
    ax.set_facecolor(PAPER)

    rows = []  # (label, baseline_y)
    y = 0

    # roman reference
    total_r = draw_roman_word(ax, "doves", 40, y)
    rows.append(("your Doves Type roman", y))
    y -= 1150

    ital_xmaxes = []
    for label, (defs, params) in DIRS.items():
        geoms, wmax = word_geometry(defs, params)
        for ch, (g, gx) in geoms.items():
            draw_swept(ax, g, gx + 40, y)
        rows.append((label, y))
        ital_xmaxes.append(wmax + 80)
        y -= 1150

    total = max(total_r + 40, max(ital_xmaxes))

    # guides: baselines solid-faint, x-heights dashed
    for label, base in rows:
        ax.plot([-30, total], [base, base], color="#b9b2a4", lw=0.7, zorder=0)
        ax.plot([-30, total], [base + XH, base + XH], color="#d8d2c4",
                lw=0.7, ls=(0, (4, 3)), zorder=0)
        ax.text(-60, base + XH * 0.42, label, ha="right", va="center",
                fontsize=11.5, color="#6b6456", style="italic")

    ax.set_xlim(-330, total + 60)
    ax.set_ylim(y + 250, 850)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.text(0.5, 0.015,
             "Doves italic · v0.1 structural sketches — nib-swept skeletons, "
             "not final curves",
             ha="center", fontsize=9, color="#8a8272")
    fig.tight_layout()
    fig.savefig(out, facecolor=PAPER, bbox_inches="tight")
    print("wrote", out)


if __name__ == "__main__":
    build()
