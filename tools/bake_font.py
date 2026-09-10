"""Bake the Doves companion italic: Cormorant 550 -> static, scaled, sheared.

Targets (from DovesType Regular 3.117):
  x-height 374, visual lean 7deg right, word space 193 units.
"""
import math
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.misc.transform import Transform

SRC = "/Users/chris/Developer/doves-italic/sources/Cormorant-Italic-VF.ttf"
OUT = "/Users/chris/Developer/doves-italic/build/DovesItalic-Trial1.ttf"

TARGET_XH = 374
TARGET_SPACE = 193
TARGET_LEAN = 7.0          # degrees, rightward
FAMILY = "Doves Italic Trial"
PSNAME = "DovesItalic-Trial"


def lean_deg(pts, y0=150, y1=450):
    sel = [(x, y) for x, y in pts if y0 < y < y1]
    ys = np.array([p[1] for p in sel]); xs = np.array([p[0] for p in sel])
    m, _ = np.polyfit(ys, xs, 1)
    return math.degrees(math.atan(m))


def flattened_l(font):
    from fontTools.pens.recordingPen import RecordingPen
    gs = font.getGlyphSet(); cmap = font.getBestCmap()
    rp = RecordingPen(); gs[cmap[ord("l")]].draw(rp)
    pts, cur = [], None
    for op, args in rp.value:
        if op == "moveTo":
            cur = args[0]
        elif op == "lineTo":
            p0, p1 = cur, args[0]
            pts += [(p0[0] + t*(p1[0]-p0[0]), p0[1] + t*(p1[1]-p0[1]))
                    for t in np.linspace(0, 1, 20)]
            cur = p1
        elif op == "curveTo":
            p0 = cur; c1, c2, p3 = args
            pts += [( (1-t)**3*p0[0] + 3*(1-t)**2*t*c1[0] + 3*(1-t)*t*t*c2[0] + t**3*p3[0],
                      (1-t)**3*p0[1] + 3*(1-t)**2*t*c1[1] + 3*(1-t)*t*t*c2[1] + t**3*p3[1])
                    for t in np.linspace(0, 1, 24)]
            cur = p3
    return pts


def scale_gpos(font, s):
    """Scale every coordinate-bearing value in GPOS by s."""
    if "GPOS" not in font:
        return
    gpos = font["GPOS"].table

    def scale_anchor(a):
        if a is None:
            return
        if hasattr(a, "XCoordinate"):
            a.XCoordinate = round(a.XCoordinate * s)
            a.YCoordinate = round(a.YCoordinate * s)

    def scale_valuerecord(vr):
        if vr is None:
            return
        for attr in ("XAdvance", "YAdvance", "XPlacement", "YPlacement"):
            if getattr(vr, attr, 0):
                setattr(vr, attr, round(getattr(vr, attr) * s))

    for lookup in gpos.LookupList.Lookup:
        for st in lookup.SubTable:
            t = type(st).__name__
            if t == "PairPos":
                if st.Format == 1:
                    for pair in st.PairSet:
                        for pvr in pair.PairValueRecord:
                            scale_valuerecord(pvr.Value1)
                            scale_valuerecord(pvr.Value2)
                else:
                    for g1 in range(st.Class1Count):
                        for g2 in range(st.Class2Count):
                            rec = st.Class1Record[g1].Class2Record[g2]
                            scale_valuerecord(rec.Value1)
                            scale_valuerecord(rec.Value2)
            elif t == "SinglePos":
                if st.Format == 1:
                    scale_valuerecord(st.Value)
                elif st.Format == 2:
                    for vr in st.Value:
                        scale_valuerecord(vr)
            elif t == "MarkBasePos":
                for mr in st.MarkArray.MarkRecord:
                    scale_anchor(mr.MarkAnchor)
                for br in st.BaseArray.BaseRecord:
                    scale_anchor(br.BaseAnchor)
            elif t == "MarkMarkPos":
                for mr in st.Mark1Array.MarkRecord:
                    scale_anchor(mr.MarkAnchor)
                for mr2 in st.Mark2Array.Mark2Record:
                    scale_anchor(mr2.Mark2Anchor)
            elif t == "MarkLigPos":
                for mr in st.MarkArray.MarkRecord:
                    scale_anchor(mr.MarkAnchor)
                for lig in st.LigatureArray.LigatureAttach:
                    for ar in lig.ComponentRecord:
                        for a in getattr(ar, "LigAnchor", []) or getattr(ar, "MarkAnchor", []):
                            scale_anchor(a)
            elif t == "CursivePos":
                for entry in st.EntryExitRecord:
                    scale_anchor(entry.EntryAnchor)
                    scale_anchor(entry.ExitAnchor)


def main():
    import os
    os.makedirs(os.path.dirname(OUT), exist_ok=True)

    f = TTFont(SRC)
    instantiateVariableFont(f, {"wght": 550}, inplace=True)

    xh = f["OS/2"].sxHeight
    s = TARGET_XH / xh
    native_lean = lean_deg(flattened_l(f))
    skew_needed = math.radians(native_lean - TARGET_LEAN)   # reduce to 7
    T = Transform(1, 0, 0, 1, 0, 0).scale(s).skew(skew_needed)
    print(f"native: xh {xh}, lean {native_lean:.2f} deg | scale {s:.5f}, "
          f"skew {math.degrees(skew_needed):+.2f} deg")

    glyf = f["glyf"]
    glyphOrder = f.getGlyphOrder()
    glyphSet = f.getGlyphSet()
    newGlyphs = {}
    for gname in glyphOrder:
        pen = TTGlyphPen(glyphSet)
        tp = TransformPen(pen, T)
        glyphSet[gname].draw(tp)
        newGlyphs[gname] = pen.glyph()
    for gname, g in newGlyphs.items():
        glyf[gname] = g

    # metrics: scale advances, special-case space
    hmtx = f["hmtx"]
    cmap = f.getBestCmap()
    for gname in glyphOrder:
        adv, _ = hmtx[gname]
        newAdv = round(adv * s)
        hmtx[gname] = (newAdv, hmtx[gname][1])
    space_name = cmap[0x20]
    hmtx[space_name] = (TARGET_SPACE, hmtx[space_name][1])
    print(f"space: {round(234*s)} (scaled) -> {TARGET_SPACE} (Doves-matched)")

    # recompute bounds + lsb
    for gname in glyphOrder:
        g = glyf[gname]
        g.recalcBounds(glyf)
        lsb = g.xMin if g.numberOfContours != 0 else 0
        hmtx[gname] = (hmtx[gname][0], lsb)

    # vertical metrics + OS/2
    hhea = f["hhea"]
    hhea.ascent = round(hhea.ascent * s)
    hhea.descent = round(hhea.descent * s)
    hhea.lineGap = round(hhea.lineGap * s)
    os2 = f["OS/2"]
    os2.sxHeight = TARGET_XH
    os2.sCapHeight = round(os2.sCapHeight * s)
    os2.sTypoAscender = round(os2.sTypoAscender * s)
    os2.sTypoDescender = round(os2.sTypoDescender * s)
    os2.usWinAscent = round(os2.usWinAscent * s)
    os2.usWinDescent = round(os2.usWinDescent * s)

    post = f["post"]
    post.italicAngle = -TARGET_LEAN

    scale_gpos(f, s)

    # naming
    name = f["name"]
    FULL = f"{FAMILY} Regular"
    for nid, val in [(1, FAMILY), (2, "Regular"), (3, f"{PSNAME};trial1"),
                     (4, FULL), (6, PSNAME), (16, FAMILY), (17, "Regular")]:
        name.setName(val, nid, 3, 1, 0x409)
    # provenance: keep original copyright, note modification
    orig = name.getDebugName(0) or ""
    name.setName(orig + " | Modified 2026 (scaled/sheared/respaced for private use as Doves companion italic; OFL license applies)",
                 0, 3, 1, 0x409)

    f.save(OUT)
    print("saved", OUT)

    # ---- verification pass ----
    v = TTFont(OUT)
    vh = v["OS/2"].sxHeight
    vl = lean_deg(flattened_l(v))
    vsp = v["hmtx"][v.getBestCmap()[0x20]][0]
    gsub = sorted({fr.FeatureTag for fr in v["GSUB"].table.FeatureList.FeatureRecord}) if "GSUB" in v else []
    gpos = sorted({fr.FeatureTag for fr in v["GPOS"].table.FeatureList.FeatureRecord}) if "GPOS" in v else []
    print(f"VERIFY: xh {vh} | lean {vl:.2f} deg | space {vsp} | "
          f"italicAngle {v['post'].italicAngle} | family {v['name'].getDebugName(1)}")
    print(f"GSUB features: {gsub}")
    print(f"GPOS features: {gpos}")
    comps = sum(1 for gname in v.getGlyphOrder()
                if v["glyf"][gname].numberOfContours == -1)
    print(f"composite glyphs remaining: {comps}")
    assert vh == TARGET_XH and abs(vl - TARGET_LEAN) < 0.3 and vsp == TARGET_SPACE
    print("ALL CHECKS PASS")


if __name__ == "__main__":
    main()
