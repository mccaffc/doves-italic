"""Trial 2: take the already-baked Trial 1 (correct global metrics) and swap
the four quote-mark outlines for our hand-drawn Doves-construction quotes.

Surgical so Trial-1's scaling/kerning/features are untouched -- we only replace
glyph outlines + advances + lsb + family naming.
"""
import os
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.cu2quPen import Cu2QuPen
from doves_quotes import contours

ROOT = Path(__file__).resolve().parents[1]
T1 = ROOT / "build/DovesItalic-Trial1.ttf"
OUT = ROOT / "build/DovesItalic-Trial2.ttf"

# Doves roman advances (upem 1000, matches our target metrics)
ADV = {"quoteright": 176, "quotedblright": 427,
       "quoteleft": 204, "quotedblleft": 444}
# glyph names as mapped in cmap (verify below)
CHARS = {"quoteright": 0x2019, "quotedblright": 0x201D,
         "quoteleft": 0x2018, "quotedblleft": 0x201C}

FAMILY = "Doves Italic Trial 2"
PS = "DovesItalic-Trial2"


def main():
    f = TTFont(T1)
    glyf = f["glyf"]; hmtx = f["hmtx"]
    cmap = f.getBestCmap()
    glyphOrder = list(f.getGlyphOrder())

    # locate names via cmap in case Cormorant used different names
    names = {}
    for cname, cp in CHARS.items():
        gname = cmap.get(cp)
        if gname is None:
            print("!! no glyph for", hex(cp)); continue
        names[cname] = gname
        print(f"  {cname:16s} -> {gname}")

    glyphSet = f.getGlyphSet()
    for cname, gname in names.items():
        outline = TTGlyphPen(glyphSet)
        # TrueType glyf requires quadratic outlines for browser OTS support.
        pen = Cu2QuPen(outline, max_err=0.5, all_quadratic=True)
        for contour in contours(cname):
            for op, args in contour:
                getattr(pen, op)(*args)
        newg = outline.glyph()
        glyf[gname] = newg
        newg.recalcBounds(glyf)
        lsb = newg.xMin if newg.numberOfContours != 0 else 0
        hmtx[gname] = (ADV[cname], lsb)
        print(f"  set {gname}: advance {ADV[cname]}, lsb {lsb}, "
              f"bbox x[{newg.xMin},{newg.xMax}] y[{newg.yMin},{newg.yMax}]")

    # family naming
    name = f["name"]
    full = f"{FAMILY} Regular"
    for nid, val in [(1, FAMILY), (2, "Regular"), (3, f"{PS};trial2"),
                     (4, full), (6, PS), (16, FAMILY), (17, "Regular")]:
        name.setName(val, nid, 3, 1, 0x409)
    orig = name.getDebugName(0) or ""
    name.setName(orig + " | Trial2 2026: hand-drawn Doves-construction quotes "
                 "(oblique companions) added; OFL applies",
                 0, 3, 1, 0x409)

    f.save(OUT)
    print("saved", OUT)

    # verify
    v = TTFont(OUT)
    vcmap = v.getBestCmap()
    print("VERIFY:")
    print("  family:", v["name"].getDebugName(1), "| xh", v["OS/2"].sxHeight)
    for cname, gname in names.items():
        g = v["glyf"][gname]
        print(f"  {gname}: contours={g.numberOfContours} "
              f"bbox y[{g.yMin},{g.yMax}] adv={v['hmtx'][gname][0]}")
    assert v["OS/2"].sxHeight == 374
    for cname, gname in names.items():
        assert v["hmtx"][gname][0] == ADV[cname]
    # Regression: cubic glyf point flags (bit 7) make OTS reject the entire font.
    for gname in v.getGlyphOrder():
        g = v["glyf"][gname]
        if g.numberOfContours > 0:
            assert not any(flag & 0x80 for flag in g.flags), gname
    print("ALL CHECKS PASS")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    main()