"""Normalize OFL master-drawn italics to Doves roman metrics, render comparison.

Pipeline per candidate: instantiate variable weight -> uniform-scale so
x-height = 374 -> adjust slant to target -> extract 'doves' outlines.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.path import Path
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.basePen import BasePen
from fontTools.misc.transform import Transform

ROMAN = ("/Users/chris/Library/CloudStorage/GoogleDrive-chris@mccaff.us/"
         "Shared drives/McCaffery Ops/IT/Fonts/DovesType_3.117_OTF/DovesType-Regular.otf")

TARGET_XH = 374
INK = "#1c1a17"
PAPER = "#f7f4ee"


class MplPen(BasePen):
    def __init__(self, glyphSet, T=None):
        super().__init__(glyphSet)
        self.v, self.c = [], []
        self.T = T or Transform()

    def _moveTo(self, p):
        self.v.append(self.T.transformPoint(p)); self.c.append(Path.MOVETO)

    def _lineTo(self, p):
        self.v.append(self.T.transformPoint(p)); self.c.append(Path.LINETO)

    def _curveToOne(self, a, b, e):
        self.v.extend(self.T.transformPoint(q) for q in (a, b, e))
        self.c.extend([Path.CURVE4] * 3)

    def _closePath(self):
        if self.c and self.c[-1] != Path.CLOSEPOLY:
            self.v.append(self.v[0]); self.c.append(Path.CLOSEPOLY)


def load_italic(path, wght):
    f = TTFont(path)
    if "fvar" in f:
        instantiateVariableFont(f, {"wght": wght}, inplace=True)
    return f


def font_stats(f):
    xh = f["OS/2"].sxHeight
    slant = f["post"].italicAngle
    return xh, slant


def draw_word(ax, f, word, y_off, scale, extra_skew=0.0):
    gs = f.getGlyphSet()
    cmap = f.getBestCmap()
    x = 0
    for ch in word:
        gn = cmap[ord(ch)]
        pen = MplPen(gs, Transform(1, 0, 0, 1, 0, 0)
                     .translate(x + 40, y_off)
                     .scale(scale)
                     .skew(np.radians(extra_skew), 0))
        gs[gn].draw(pen)
        ax.add_patch(PathPatch(Path(pen.v, pen.c), facecolor=INK,
                               edgecolor=INK, lw=0.4))
        x += gs[gn].width * scale
    return x + 40


def flattened_l_points(f):
    """Flatten 'l' outline to dense points (font units)."""
    from fontTools.pens.recordingPen import RecordingPen
    gs = f.getGlyphSet()
    cmap = f.getBestCmap()
    rp = RecordingPen()
    gs[cmap[ord("l")]].draw(rp)
    pts = []
    cur = None
    for op, args in rp.value:
        if op == "moveTo":
            cur = args[0]
        elif op == "lineTo":
            p0, p1 = cur, args[0]
            for t in np.linspace(0, 1, 20):
                pts.append((p0[0] + t * (p1[0] - p0[0]),
                            p0[1] + t * (p1[1] - p0[1])))
            cur = p1
        elif op == "curveTo":
            p0 = cur
            c1, c2, p3 = args
            for t in np.linspace(0, 1, 24):
                mt = 1 - t
                pts.append((mt**3 * p0[0] + 3 * mt**2 * t * c1[0] +
                            3 * mt * t**2 * c2[0] + t**3 * p3[0],
                            mt**3 * p0[1] + 3 * mt**2 * t * c1[1] +
                            3 * mt * t**2 * c2[1] + t**3 * p3[1]))
            cur = p3
    return pts


def lean_deg(pts, y0=150, y1=450):
    """Rightward lean in degrees: positive = tops pushed right."""
    sel = [(x, yy) for x, yy in pts if y0 < yy < y1]
    ys = np.array([p[1] for p in sel])
    xs = np.array([p[0] for p in sel])
    m, _ = np.polyfit(ys, xs, 1)
    return np.degrees(np.arctan(m))


def calibrated_skew(f, target_lean_deg):
    """Extra right-skew (deg) so 'l' leans target_lean_deg rightward."""
    native = lean_deg(flattened_l_points(f))
    need = np.tan(np.radians(target_lean_deg)) - np.tan(np.radians(native))
    return np.degrees(np.arctan(need)), native


def stem_width(f, y0=150, y1=450):
    pts = flattened_l_points(f)
    xs = [x for x, yy in pts if y0 < yy < y1]
    return (max(xs) - min(xs)) if xs else None


def build(out="proofs/harmonize-v1.png"):
    rows = []

    fig, ax = plt.subplots(figsize=(14.5, 10), dpi=150)
    fig.patch.set_facecolor(PAPER)
    ax.set_facecolor(PAPER)

    # roman reference at native scale (xh already 374)
    f = TTFont(ROMAN)
    gs = f.getGlyphSet()
    cmap = f.getBestCmap()
    x = 0
    for ch in "doves":
        gn = cmap[ord(ch)]
        pen = MplPen(gs, Transform(1, 0, 0, 1, 0, 0).translate(x + 40, 0))
        gs[gn].draw(pen)
        ax.add_patch(PathPatch(Path(pen.v, pen.c), facecolor=INK,
                               edgecolor=INK, lw=0.4))
        x += gs[gn].width
    rows.append(("your Doves Type roman  (xh 374, stem ~71)", 0, x + 40))
    y = -1150

    cands = [
        ("EB Garamond Italic · wght 400", "sources/EBGaramond-Italic-VF.ttf", 400, 7),
        ("EB Garamond Italic · wght 500", "sources/EBGaramond-Italic-VF.ttf", 500, 7),
        ("EB Garamond Italic · wght 600", "sources/EBGaramond-Italic-VF.ttf", 600, 7),
        ("Cormorant Italic · wght 500",   "sources/Cormorant-Italic-VF.ttf", 500, 7),
    ]
    for label, path, wght, target_slant in cands:
        fi = load_italic(path, wght)
        xh, slant = font_stats(fi)
        s = TARGET_XH / xh
        skew, native_lean = calibrated_skew(fi, target_slant)
        # verify: measure lean through the full transform pipeline
        check = lean_deg([(T[0], T[1]) for T in
                          (Transform(1, 0, 0, 1, 0, 0).scale(s)
                           .skew(np.radians(skew), 0).transformPoint(p)
                           for p in flattened_l_points(fi))],
                         y0=150 * s, y1=450 * s)
        xmax = draw_word(ax, fi, "doves", y, s, extra_skew=skew)
        stem = stem_width(fi)
        stem_txt = f"{stem * s:.0f}" if stem else "n/a"
        rows.append((f"{label}  (lean verified {check:.1f}° right, "
                     f"stem→{stem_txt})", y, xmax))
        print(f"  {label}: native lean {native_lean:.1f}°, skew {skew:+.1f}°, "
              f"verified {check:.1f}°")
        y -= 1150

    total = max(r[2] for r in rows)
    for label, base, _ in rows:
        ax.plot([-30, total], [base, base], color="#b9b2a4", lw=0.7, zorder=0)
        ax.plot([-30, total], [base + TARGET_XH, base + TARGET_XH],
                color="#d8d2c4", lw=0.7, ls=(0, (4, 3)), zorder=0)
        ax.text(-60, base + TARGET_XH * 0.42, label, ha="right", va="center",
                fontsize=10.5, color="#6b6456", style="italic")

    ax.set_xlim(-560, total + 60)
    ax.set_ylim(y + 250, 850)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.text(0.5, 0.015,
             "Doves italic · master-cut candidates normalized to Doves metrics — "
             "judge voice and fit, details pending rework",
             ha="center", fontsize=9, color="#8a8272")
    fig.savefig(out, facecolor=PAPER, bbox_inches="tight")
    print("wrote", out)
    for label, _, _ in rows:
        print(" row:", label)


if __name__ == "__main__":
    build()
