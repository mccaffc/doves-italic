"""Parametric Doves-style quote marks (ball head -> throat -> hooked swash tail).

Clean-room: reconstructed from measured geometry (bbox, maxth 21, placement)
and the known Doves construction -- NOT traced from their outlines.
Tuned against an ASCII silhouette mirroring the roman's.

`contours(style)` -> list of contours; each contour is a list of
pen ops capture_tuple-style: ('moveTo',((x,y),)) / ('curveTo',((x1,y1),(x2,y2),(x3,y3))).
"""
import math

# ---- Doves roman measured metas ----
RIGHT_H = 186.0      # quoteright / quotedblright height (near cap)
LEFT_H = 219.0       # quoteleft / quotedblleft height (near x-height)
RIGHT_SINGLE_W = 106.0
RIGHT_DOUBLE_W = 301.0
LEFT_SINGLE_W = 120.0
LEFT_DOUBLE_W = 319.0
RIGHT_Y0 = 430.0     # bbox bottom of right quotes
LEFT_Y0 = 254.0      # bbox bottom of left quotes
LEAN_DEG = 7.0       # italic lean applied to punctuation too


def _shear(pts, deg):
    t = math.tan(math.radians(deg))
    return [(x + y * t, y) for x, y in pts]


def _mirror(pts):
    return [(-x, y) for x, y in pts]


def _bbox(pts):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def _scale(pts, w, h):
    x0, y0, x1, y1 = _bbox(pts)
    sx, sy = w / (x1 - x0), h / (y1 - y0)
    return [((x - x0) * sx, (y - y0) * sy) for x, y in pts]


def _center(pts, cx):
    x0, _, x1, _ = _bbox(pts)
    shift = cx - (x0 + x1) / 2
    return [(x + shift, y) for x, y in pts]


def _lobe():
    """One closing-comma outline: fat ball head -> pinches -> long sweeping tail
    that tapers to an upturned point. Single closed contour.
    Returns control points as (x,y) in construction order:
    A(top) + 3 control pts per cubic -> R0(ball lower-right) -> T(tail tip)
    -> L0(ball lower-left) -> back to A. That's 1 + 12 points.
    """
    return [
        # A top of ball
        (6, 171),
        # ball right edge -> R0 (lower-right flank)
        (16, 166), (17, 156), (13, 146),
        # tail OUTER edge, short & thick, sweeping down-left to the sweep point S
        (5, 120), (-4, 98), (-8, 78),
        # the upturn hook: from S curl up into a rounded end (not a point)
        (0, 62), (8, 52), (12, 48),
        # tail INNER edge returning, widening up toward the ball
        (4, 74), (-2, 100), (3, 144),
        # ball lower-left flank up to A
        (-2, 156), (1, 163), (6, 171),
    ]


def _to_ops(pts):
    """Emit pen ops: first point moveTo, every 3 following a curveTo; last closes."""
    if not pts:
        return []
    ops = [("moveTo", ((pts[0][0], pts[0][1]),))]
    i = 1
    while i + 2 < len(pts):
        ops.append(("curveTo",
                    ((pts[i][0], pts[i][1]),
                     (pts[i + 1][0], pts[i + 1][1]),
                     (pts[i + 2][0], pts[i + 2][1]))))
        i += 3
    # close: curve back to start if there is a remainder segment
    if i < len(pts):
        p0 = pts[0]
        ps = pts[i:]
        n = len(ps)
        if n == 1:
            ops.append(("curveTo", (ps[0], p0, p0)))
        elif n == 2:
            ops.append(("curveTo", (ps[0], ps[1], p0)))
        else:
            ops.append(("curveTo", ((ps[0][0], ps[0][1]), (ps[1][0], ps[1][1]), (p0[0], p0[1]))))
    ops.append(("closePath", ()))
    return ops


def contours(style, lean=LEAN_DEG):
    """Contours for quoteright/quoteleft/quotedblright/quotedblleft."""
    is_left = "left" in style
    is_double = "dbl" in style
    if is_left:
        h, y0 = LEFT_H, LEFT_Y0
        w = LEFT_SINGLE_W if not is_double else LEFT_DOUBLE_W
    else:
        h, y0 = RIGHT_H, RIGHT_Y0
        w = RIGHT_SINGLE_W if not is_double else RIGHT_DOUBLE_W

    def unit():
        p = _lobe()
        if is_left:
            p = _mirror(p)
        return p

    if is_double:
        wl = w * 0.46
        gap = w * 0.08
        base = _scale(unit(), wl, h)
        x0b, _, x1b, _ = _bbox(base)
        bw = x1b - x0b
        # left lobe flush at margin, right lobe to its right; centre the pair
        pair_w = 2 * bw + gap
        margin = (w - pair_w) / 2
        placed = []
        for k in (0, 1):
            off = margin + k * (bw + gap) - x0b
            placed.append([(x + off, y) for x, y in base])
    else:
        placed = [_scale(unit(), w, h)]
        placed[0] = _center(placed[0], w / 2)

    result = []
    for p in placed:
        p = _shear(p, lean)
        ys = [q[1] for q in p]
        off = y0 - min(ys)
        p = [(x, y + off) for x, y in p]
        result.append(_to_ops(p))
    return result


if __name__ == "__main__":
    for style in ("quoteright", "quotedblright", "quoteleft", "quotedblleft"):
        cs = contours(style)
        allp = []
        for c in cs:
            for op, args in c:
                for pt in args:
                    allp.append(pt)
        xs = [p[0] for p in allp]; ys = [p[1] for p in allp]
        print(f"{style:16s} contours={len(cs)} pad bbox x[{min(xs):.0f},{max(xs):.0f}] "
              f"y[{min(ys):.0f},{max(ys):.0f}] w{max(xs)-min(xs):.0f} h{max(ys)-min(ys):.0f}")