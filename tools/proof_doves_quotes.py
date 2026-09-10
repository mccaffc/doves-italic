"""Big annotated proof of the four Doves roman quotes -- the construction targets."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import PathPatch
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen

ROMAN = ("/Users/chris/Library/CloudStorage/GoogleDrive-chris@mccaff.us/"
         "Shared drives/McCaffery Ops/IT/Fonts/DovesType_3.117_OTF/DovesType-Regular.otf")
f = TTFont(ROMAN); gs = f.getGlyphSet(); cmap = f.getBestCmap()
INK = "#1c1a17"; PAPER = "#f7f4ee"; ACC = "#b23a30"


class Pen(BasePen):
    def __init__(self, gs, sx, sy):
        super().__init__(gs); self.v, self.c = [], []
        self.sx, self.sy = sx, sy
    def _moveTo(self, p): self.v.append((p[0]+self.sx, p[1]+self.sy)); self.c.append(Path.MOVETO)
    def _lineTo(self, p): self.v.append((p[0]+self.sx, p[1]+self.sy)); self.c.append(Path.LINETO)
    def _curveToOne(self, a, b, e):
        self.v += [(a[0]+self.sx, a[1]+self.sy), (b[0]+self.sx, b[1]+self.sy), (e[0]+self.sx, e[1]+self.sy)]
        self.c += [Path.CURVE4]*3
    def _closePath(self):
        if self.c and self.c[-1] != Path.CLOSEPOLY:
            self.v.append(self.v[0]); self.c.append(Path.CLOSEPOLY)


def glyph_pen(g):
    p = Pen(gs, 0, 0); g.draw(p); return p


# pick four columns
chars = {"\u201c": "quotedblleft  U+201C  (low)", "\u2018": "quoteleft  U+2018  (low)",
         "\u201d": "quotedblright  U+201D  (high)", "\u2019": "quoteright  U+2019  (high)"}
SC = 0.85
fig, ax = plt.subplots(figsize=(13, 9), dpi=150)
fig.patch.set_facecolor(PAPER); ax.set_facecolor(PAPER)
x = 40
for ch, label in chars.items():
    g = gs[cmap[ord(ch)]]
    p = glyph_pen(g)
    ax.add_patch(PathPatch(Path(p.v, p.c), fc=INK, ec=INK, lw=1.0))
    top = max(v[1] for v in p.v)
    ax.text(x + g.width*SC/2, top + 70, label, ha="center", fontsize=10, color="#555")
    x += g.width * SC + 90
ax.plot([40, x], [0, 0], color=ACC, lw=1, ls="--")
ax.text(40, -26, "baseline 0", fontsize=9, color=ACC)
h = 800
ax.plot([40, x], [374, 374], color="#999", lw=1, ls=":")
ax.text(40, 382, "x-height 374", fontsize=9, color="#999")
ax.set_xlim(20, x+40); ax.set_ylim(-80, 700); ax.set_aspect("equal"); ax.axis("off")
fig.text(0.5, 0.015, "Doves Type roman -- the four quotation marks, actual outlines (scale 0.85). "
         "Note: left quotes sit LOW (near x-height 374), right quotes/apostrophe sit HIGH (near cap).",
         ha="center", fontsize=9, color="#8a8272")
out = "/Users/chris/Developer/doves-italic/proofs/doves_quotes_roman.png"
fig.savefig(out, facecolor=PAPER, bbox_inches="tight")
print("wrote", out)