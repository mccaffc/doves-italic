"""Doves DNA study: measure distinctive glyphs in the roman vs our trial italic.

Clean-room discipline: we only extract numeric measurements (bbox, thickness
profiles, angles) from the roman — never outlines. Redrawing happens in OUR font.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.path import Path
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
from fontTools.pens.recordingPen import RecordingPen

ROMAN = ("/Users/chris/Library/CloudStorage/GoogleDrive-chris@mccaff.us/"
         "Shared drives/McCaffery Ops/IT/Fonts/DovesType_3.117_OTF/DovesType-Regular.otf")
TRIAL = "/Users/chris/Developer/doves-italic/build/DovesItalic-Trial1.ttf"

INK = "#1c1a17"; PAPER = "#f7f4ee"


class MplPen(BasePen):
    def __init__(self, glyphSet):
        super().__init__(glyphSet)
        self.v, self.c = [], []
    def _moveTo(self, p): self.v.append(p); self.c.append(Path.MOVETO)
    def _lineTo(self, p): self.v.append(p); self.c.append(Path.LINETO)
    def _curveToOne(self, a, b, e):
        self.v.extend([a, b, e]); self.c.extend([Path.CURVE4] * 3)
    def _closePath(self):
        if self.c and self.c[-1] != Path.CLOSEPOLY:
            self.v.append(self.v[0]); self.c.append(Path.CLOSEPOLY)


def flatten_glyph(font, ch, steps=28):
    """Dense point cloud of a glyph's outline (decomposes composites, TTF-safe)."""
    from fontTools.pens.qu2cuPen import Qu2CuPen
    from fontTools.pens.recordingPen import DecomposingRecordingPen
    gs = font.getGlyphSet(); cmap = font.getBestCmap()
    dec = DecomposingRecordingPen(gs)
    gs[cmap[ord(ch)]].draw(dec)
    rp = RecordingPen()
    q2c = Qu2CuPen(rp, 10)
    for op, args in dec.value:
        getattr(q2c, op)(*args)
    pts, cur = [], None
    for op, args in rp.value:
        if op == "moveTo":
            cur = args[0]; pts.append(cur)
        elif op == "lineTo":
            p0, p1 = cur, args[0]
            pts += [(p0[0]+t*(p1[0]-p0[0]), p0[1]+t*(p1[1]-p0[1]))
                    for t in np.linspace(0, 1, steps)]
            cur = p1
        elif op == "curveTo":
            p0 = cur; c1, c2, p3 = args
            pts += [((1-t)**3*p0[0]+3*(1-t)**2*t*c1[0]+3*(1-t)*t*t*c2[0]+t**3*p3[0],
                     (1-t)**3*p0[1]+3*(1-t)**2*t*c1[1]+3*(1-t)*t*t*c2[1]+t**3*p3[1])
                    for t in np.linspace(0, 1, steps)]
            cur = p3
    return np.array(pts)


def row_runs(pts, y, tol=2.0, gap=4.0):
    """Ink x-runs at scanline y (within tol), split on gaps > gap."""
    xs = sorted(pts[np.abs(pts[:, 1] - y) < tol][:, 0])
    if not xs: return []
    runs, start, prev = [], xs[0], xs[0]
    for x in xs[1:]:
        if x - prev > gap:
            runs.append((start, prev)); start = x
        prev = x
    runs.append((start, prev))
    return runs


def quote_metrics(font, ch):
    pts = flatten_glyph(font, ch)
    xmin, ymin = pts.min(0); xmax, ymax = pts.max(0)
    w, h = xmax - xmin, ymax - ymin
    # max horizontal thickness across scanlines
    best = 0
    for y in np.linspace(ymin + 2, ymax - 2, 40):
        for a, b in row_runs(pts, y):
            best = max(best, b - a)
    # lean: centroid x of top third vs bottom third
    mid = (ymin + ymax) / 2
    top = pts[pts[:, 1] > mid + h * 0.2][:, 0].mean()
    bot = pts[pts[:, 1] < mid - h * 0.2][:, 0].mean()
    return dict(w=round(w), h=round(h), ratio=round(w / h, 3),
                maxth=round(best), lean=round(top - bot, 1))


def e_metrics(font):
    pts = flatten_glyph(font, "e")
    ymin, ymax = pts[:, 1].min(), pts[:, 1].max()
    xh = ymax - ymin
    # find bar: scanlines with 2+ runs in the middle band
    bar_rows = []
    for y in np.linspace(ymin + xh * 0.3, ymin + xh * 0.75, 60):
        runs = row_runs(pts, y, gap=6)
        if len(runs) >= 2:
            bar_rows.append((y, runs))
    if not bar_rows:
        return None
    # bar angle: left edge x of first run across bar rows
    ys = np.array([y for y, _ in bar_rows])
    lx = np.array([r[0][0] for _, r in bar_rows])
    slope = np.polyfit(ys, lx, 1)[0]
    # eye (counter) offset: counter centroid x vs glyph center at bar rows
    counters = []
    for y, runs in bar_rows:
        if len(runs) >= 2:
            cx = (runs[0][1] + runs[1][0]) / 2
            counters.append(cx)
    eye_x = np.mean(counters)
    allx = pts[:, 0]
    return dict(bar_angle=round(math_deg(slope)), eye_offset=round(eye_x - (allx.min() + allx.max()) / 2, 1),
                bar_rows=len(bar_rows))


def math_deg(slope):
    import math
    return math.degrees(math.atan(slope))


def three_top(font):
    pts = flatten_glyph(font, "3")
    ymin, ymax = pts[:, 1].min(), pts[:, 1].max()
    h = ymax - ymin
    top = pts[pts[:, 1] > ymax - h * 0.06][:, 0]
    upper = pts[(pts[:, 1] > ymax - h * 0.25) & (pts[:, 1] < ymax - h * 0.12)][:, 0]
    return dict(top_span=round(top.max() - top.min()) if len(top) else 0,
                upper_span=round(upper.max() - upper.min()) if len(upper) else 0,
                top_minx=round(top.min()) if len(top) else None)


def render_proof(out="/Users/chris/Developer/doves-italic/proofs/dna-v1.png"):
    chars = ["\u201d", "\u2019", "\u201c", "\u2018", "3", "e", "5", "0123456789"]
    fonts = [("Doves Type roman (the DNA)", TTFont(ROMAN), 1.0),
             ("Doves Italic Trial 1 (current)", TTFont(TRIAL), 1.0)]
    fig, ax = plt.subplots(figsize=(15, 8.5), dpi=150)
    fig.patch.set_facecolor(PAPER); ax.set_facecolor(PAPER)
    y = 0; labels = []
    for label, f, s in fonts:
        gs = f.getGlyphSet(); cmap = f.getBestCmap()
        x = 40
        for ch in chars:
            for c in ch:
                pen = MplPen(gs)
                gs[cmap[ord(c)]].draw(pen)
                verts = [(vx + x, vy + y) for vx, vy in pen.v]
                ax.add_patch(PathPatch(Path(verts, pen.c), facecolor=INK, edgecolor=INK, lw=0.5))
                x += gs[cmap[ord(c)]].width * s + 14
            x += 46
        labels.append((label, y))
        y -= 900
    total = 2600
    for label, base in labels:
        ax.text(-40, base + 500, label, ha="left", fontsize=12,
                color="#6b6456", style="italic")
    ax.set_xlim(-40, total); ax.set_ylim(y + 300, 800)
    ax.set_aspect("equal"); ax.axis("off")
    fig.text(0.5, 0.015, "Doves DNA study — quotes, figures, e: roman vs Trial 1 "
             "(same scale)", ha="center", fontsize=9, color="#8a8272")
    fig.savefig(out, facecolor=PAPER, bbox_inches="tight")
    print("wrote", out)


if __name__ == "__main__":
    r = TTFont(ROMAN); t = TTFont(TRIAL)
    print("== quotes (U+201D double-right, U+2019 single-right) ==")
    for ch, nm in [("\u201d", 'roman "'), ("\u2019", "roman '")]:
        print(f"  {nm}: {quote_metrics(r, ch)}")
    for ch, nm in [("\u201d", 'trial "'), ("\u2019", "trial '")]:
        print(f"  {nm}: {quote_metrics(t, ch)}")
    print("== e: bar angle (deg from horizontal) + eye offset (units) ==")
    print("  roman:", e_metrics(r))
    print("  trial:", e_metrics(t))
    print("== 3: top structure ==")
    print("  roman:", three_top(r))
    print("  trial:", three_top(t))
    render_proof()
