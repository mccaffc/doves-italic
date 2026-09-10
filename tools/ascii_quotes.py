"""ASCII-silhouette dump of Doves vs trial quotes, so a blind agent can 'see' shape."""
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen

ROMAN = ("/Users/chris/Library/CloudStorage/GoogleDrive-chris@mccaff.us/"
         "Shared drives/McCaffery Ops/IT/Fonts/DovesType_3.117_OTF/DovesType-Regular.otf")
TRIAL = "/Users/chris/Developer/doves-italic/build/DovesItalic-Trial1.ttf"


def pts_of(f, ch):
    gs = f.getGlyphSet(); g = gs[f.getBestCmap()[ord(ch)]]
    out = []
    class Pen(BasePen):
        def _moveTo(self, p): out.append(p)
        def _lineTo(self, p): out.append(p)
        def _curveToOne(self, a, b, e): out.extend([a, b, e])
    g.draw(Pen(gs))
    return np.array(out)


def raster(f, ch, cols=42, thick=2):
    pts = pts_of(f, ch)
    if pts.size == 0: return None
    x0, x1 = pts[:, 0].min(), pts[:, 0].max()
    y0, y1 = pts[:, 1].min(), pts[:, 1].max()
    W = cols; H = max(int((y1 - y0) / (x1 - x0) * W * 1.8), 14)
    grid = np.zeros((H, W), bool)
    for x, y in pts:
        cx = int((x - x0) / (x1 - x0) * (W - 1) + 0.5)
        cy = int((y1 - y) / (y1 - y0) * (H - 1) + 0.5)
        grid[min(cy, H - 1), min(cx, W - 1)] = True
    grid = _dilate(grid, thick)
    return grid, int(x1 - x0), int(y1 - y0)


def _dilate(grid, it):
    H, W = grid.shape
    import numpy as np
    big = np.zeros((H, W), bool)
    ys, xs = np.nonzero(grid)
    for dy in range(-it, it + 1):
        for dx in range(-it, it + 1):
            if dy * dy + dx * dx <= it * it:
                ny, nx = ys + dy, xs + dx
                m = (ny >= 0) & (ny < H) & (nx >= 0) & (nx < W)
                big[ny[m], nx[m]] = True
    return big


if __name__ == "__main__":
    for label, f in [("DOVES ROMAN", TTFont(ROMAN)), ("TRIAL1 (Cormorant)", TTFont(TRIAL))]:
        print("=" * 58)
        for ch in ["\u201d", "\u2019", "\u201c", "\u2018"]:
            r = raster(f, ch)
            if r is None: print(f"--{label} {ch!r} EMPTY"); continue
            g, w, h = r
            g = _dilate(g, 2)
            print(f"--{label}  {ch!r}  w{w} h{h}--")
            for row in g:
                print("  " + "".join("#" if b else "." for b in row))