"""Measure a straight-up dome photo and draw the construction on it.

For each photo: find the centre, measure the ring edges and the fold count, pick the ring that
works best as the first circle, then draw the six stage and the eight stage over the photo.
Pure Python + Pillow (no numpy), so it is slow but has no other dependencies.
"""
import json, math, os, random, sys
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
# --mesh: try every crisp inner ring as the first circle and keep the one the rest of the drawing sits best on.
MESH = "--mesh" in sys.argv
OUT = os.path.join(HERE, "domes", "meshed" if MESH else "drawn")
S3 = math.sqrt(3)
RHO = 1 / (2 * S3)
R8 = S3 / math.cos(math.radians(22.5))
# Radii the construction produces, in units of the first circle.
PREDICTED = {
    "third star ring 1/(3r3)": 1 / (3 * S3), "thirteen-circle radius": RHO, "second band 1/3": 1 / 3,
    "first band 1/r3": 1 / S3, "cube corners 2/r3": 2 / S3, "thirteen circles outer reach": 2 / S3 + RHO,
    "diamond ring r3": S3, "octagon corners": R8, "seed outer reach 2": 2.0,
    "second square corners r6": math.sqrt(6), "doubled circles outer reach 3": 3.0, "eight-flower reach 2r3": 2 * S3,
}
TOL = 0.02


def ring_mean(px, w, h, cx, cy, r, trig):
    s = n = 0
    for c, sn in trig:
        x, y = int(cx + r * c), int(cy + r * sn)
        if 0 <= x < w and 0 <= y < h:
            s += px[x, y]; n += 1
    return s / n if n >= 0.6 * len(trig) else None


def profile(px, w, h, cx, cy, rmax, nth):
    trig = [(math.cos(2 * math.pi * k / nth), math.sin(2 * math.pi * k / nth)) for k in range(nth)]
    return [ring_mean(px, w, h, cx, cy, r, trig) for r in range(1, rmax)]


def edge_energy(prof):
    return sum((b - a) ** 2 for a, b in zip(prof, prof[1:]) if a is not None and b is not None)


def find_centre(gray):
    """The true centre is where rings line up, so the ring-averaged brightness changes most sharply with radius.
    Searched coarse to fine (96 px, 240 px, full size) so a small sharp medallion off to one side cannot win."""
    cx = cy = None
    for size, span, nth in ((96, None, 90), (240, 5, 120), (None, 4, 180)):
        im = gray if size is None else gray.copy()
        if size is not None:
            im.thumbnail((size, size))
        k = gray.width / im.width
        px, w, h = im.load(), im.width, im.height
        rmax = int(0.42 * min(w, h))
        if span is None:
            xs, ys = range(int(.25 * w), int(.75 * w)), range(int(.25 * h), int(.75 * h))
        else:
            x0, y0 = int(round(cx / k)), int(round(cy / k))
            xs, ys = range(x0 - span, x0 + span + 1), range(y0 - span, y0 + span + 1)
        best = None
        for x in xs:
            for y in ys:
                e = edge_energy(profile(px, w, h, x, y, rmax, nth))
                if span is None:
                    # Coarse pass only: a straight-up photo is roughly centred, so lean gently toward the middle.
                    d2 = ((x - w / 2) ** 2 + (y - h / 2) ** 2) / (0.3 * min(w, h)) ** 2
                    e *= math.exp(-d2 / 2)
                if best is None or e > best[0]:
                    best = (e, x, y)
        cx, cy = best[1] * k, best[2] * k
    return cx, cy


def find_rings(prof, rmin=6, keep=12):
    """Ring edges = radii where the ring-averaged brightness jumps."""
    p = [v for v in prof]
    g = [0.0] * len(p)
    for i in range(2, len(p) - 2):
        if None in (p[i - 2], p[i - 1], p[i + 1], p[i + 2]):
            continue
        g[i] = abs((p[i + 1] + p[i + 2]) - (p[i - 1] + p[i - 2])) / 2
    vals = [v for v in g if v > 0]
    if not vals:
        return []
    # Robust threshold (median + 3 MAD) so one very strong edge, like an open oculus, does not hide the rest.
    sv = sorted(vals); med = sv[len(sv) // 2]; mad = sorted(abs(v - med) for v in vals)[len(vals) // 2] or 1e-9
    peaks = [(g[i], i + 1) for i in range(rmin, len(g) - 3) if g[i] > med + 3 * mad and g[i] == max(g[i - 5:i + 6])]
    peaks.sort(reverse=True)
    return sorted((r, round(s, 2)) for s, r in peaks[:keep])


def folds(px, w, h, cx, cy, r0, r1, nth=720, nmax=48):
    sig = []
    for k in range(nth):
        c, s = math.cos(2 * math.pi * k / nth), math.sin(2 * math.pi * k / nth)
        tot = n = 0
        for r in range(int(r0), int(r1), 2):
            x, y = int(cx + r * c), int(cy + r * s)
            if 0 <= x < w and 0 <= y < h:
                tot += px[x, y]; n += 1
        sig.append(tot / n if n else 0)
    m = sum(sig) / nth; sig = [v - m for v in sig]
    out = []
    for n in range(2, nmax + 1):
        re = sum(v * math.cos(2 * math.pi * n * k / nth) for k, v in enumerate(sig))
        im = sum(v * math.sin(2 * math.pi * n * k / nth) for k, v in enumerate(sig))
        out.append((math.hypot(re, im), n, math.atan2(im, re) / n))
    out = [o for o in out if o[1] >= 4]; out.sort(reverse=True)
    top = out[0][0] or 1
    return [(n, round(p / top, 2), ph) for p, n, ph in out[:4]]


def matches(unit, radii):
    hits = []
    for r in radii:
        if r == unit:
            continue
        ratio = r / unit
        for name, val in PREDICTED.items():
            if abs(ratio / val - 1) <= TOL:
                hits.append((r, round(ratio, 3), name)); break
    return hits


def chance_of(k, ratios):
    """With the first circle fixed by rule, how likely are k or more of the other rings to land on a predicted radius by luck?"""
    m = len(ratios)
    if m == 0:
        return None
    lo, hi = math.log(min(ratios) * .95), math.log(max(ratios) * 1.05)
    bands = sorted((max(lo, math.log(v * (1 - TOL))), min(hi, math.log(v * (1 + TOL)))) for v in PREDICTED.values())
    cover, end = 0.0, lo
    for x0, x1 in bands:
        x0 = max(x0, end)
        if x1 > x0:
            cover += x1 - x0; end = x1
    p0 = cover / (hi - lo)
    return sum(math.comb(m, i) * p0 ** i * (1 - p0) ** (m - i) for i in range(k, m + 1))


def chance_meshed(k, radii, trials=2000):
    """Same question, but allowing for the freedom of trying every inner ring as the first circle and keeping the best."""
    rnd = random.Random(1); lo, hi = math.log(min(radii)), math.log(max(radii)); ge = 0
    for _ in range(trials):
        rs = [math.exp(rnd.uniform(lo, hi)) for _ in radii]
        cands = [r for r in rs if r <= 0.5 * max(rs)] or rs
        if max(len(matches(u, rs)) for u in cands) >= k:
            ge += 1
    return ge / trials


class Pen:
    def __init__(self, im, cx, cy, unit, turn):
        self.d = ImageDraw.Draw(im); self.cx, self.cy, self.u = cx, cy, unit
        self.c, self.s = math.cos(turn), math.sin(turn)
    def pt(self, p):
        x, y = p
        return (self.cx + self.u * (x * self.c - y * self.s), self.cy + self.u * (x * self.s + y * self.c))
    def circle(self, ctr, r, col, w=2):
        x, y = self.pt(ctr); R = r * self.u
        self.d.ellipse((x - R, y - R, x + R, y + R), outline=col, width=w)
    def line(self, a, b, col, w=2):
        self.d.line((self.pt(a), self.pt(b)), fill=col, width=w)
    def poly(self, pts, col, w=2):
        for i, p in enumerate(pts):
            self.line(p, pts[(i + 1) % len(pts)], col, w)


def ring_pts(r, start, n=6):
    return [(r * math.cos(math.radians(start + i * 360 / n)), r * math.sin(math.radians(start + i * 360 / n))) for i in range(n)]


INK, RED, BLUE, PURPLE, GREEN, CYAN, PALE = (20, 20, 20), (215, 50, 40), (40, 95, 210), (130, 60, 200), (30, 140, 80), (0, 150, 180), (245, 245, 245)
O, A, B, T, U = (0, 0), (-1, 0), (1, 0), (0, 1), (0, -1)


def draw_six(pen):
    hexa, inner, outer = ring_pts(1, 0), ring_pts(1 / S3, 30), ring_pts(2 / S3, 30)
    pen.circle(O, 1, INK, 3); pen.circle(A, 1, BLUE); pen.circle(B, 1, RED)   # blue on the left, red on the right, as on the desk
    pen.poly(hexa, INK)
    for i in (0, 1):
        pen.poly([hexa[i], hexa[i + 2], hexa[(i + 4) % 6]], PURPLE)
    pen.circle(O, 1 / S3, GREEN, 3); pen.poly(inner, GREEN); pen.circle(O, 1 / 3, GREEN, 2)
    for p in hexa[1:3] + hexa[4:] + ring_pts(S3, 30) + ring_pts(2, 0):   # the rest of the seed, then the flower of life
        pen.circle(p, 1, INK, 1)
    pen.circle(O, 3, INK, 2)
    for p in [O] + inner + outer:
        pen.circle(p, RHO, PALE, 1)
    pen.poly(outer, INK, 4)
    for i in (1, 3, 5):
        pen.line(O, outer[i], INK, 4)


def draw_eight(pen):
    pen.circle(O, 1, INK, 3)
    pen.circle(A, 2, BLUE); pen.circle(B, 2, RED); pen.circle(T, 2, PURPLE); pen.circle(U, 2, PURPLE)
    pen.poly([(S3, 0), (0, S3), (-S3, 0), (0, -S3)], BLUE); pen.circle(O, S3, PALE, 2)
    pen.poly(ring_pts(R8, 22.5, 8), PURPLE, 4)
    r, ph = R8, 22.5
    for k in range(4):
        v = ring_pts(r, ph, 8)
        for i in range(8):
            pen.line(v[i], v[(i + 3) % 8], BLUE if k % 2 else RED, 2)
        r *= math.sqrt(2) - 1          # not turned: a star that joins every third point has its inner crossings on its own corners' rays
    for p in ring_pts(S3, 0, 8):
        pen.circle(p, S3, PALE, 1)


def analyse(path, name, centre=None, unit_px=None):
    os.makedirs(OUT, exist_ok=True)
    rgb = Image.open(path).convert("RGB"); gray = rgb.convert("L")
    w, h = gray.size; px = gray.load()
    cx, cy = centre or find_centre(gray)
    rmax = int(max(math.hypot(cx, cy), math.hypot(w - cx, cy), math.hypot(cx, h - cy), math.hypot(w - cx, h - cy)))
    prof = profile(px, w, h, cx, cy, rmax, 720)
    rings = find_rings(prof, rmin=int(0.04 * min(w, h)))  # ignore the noisy few pixels at the very centre
    radii = [r for r, _ in rings]
    span = max(radii) if radii else 0.4 * min(w, h)
    fold = {band: folds(px, w, h, cx, cy, a * span, b * span) for band, (a, b) in {"inner": (.15, .4), "middle": (.4, .7), "outer": (.7, 1.0)}.items()}
    # The first circle goes on the opening: the strongest edge in the inner half. Chosen by rule, never by best fit.
    inner_half = [(s_, r) for r, s_ in rings if r <= 0.5 * max(radii)] or [(s_, r) for r, s_ in rings]
    unit = unit_px or max(inner_half)[1]
    if unit not in radii:  # a ring placed by eye: snap to the nearest measured edge
        unit = min(radii, key=lambda r: abs(r - unit))
    hits = matches(unit, radii); hits_n = len(hits)
    p = chance_of(hits_n, [r / unit for r in radii if r != unit])
    tried = None
    if MESH and not unit_px:
        strength = {r: s_ for r, s_ in rings}
        cands = [r for _, r in inner_half]
        tried = {r: len(matches(r, radii)) for r in cands}
        unit = max(cands, key=lambda r: (tried[r], strength[r]))
        hits = matches(unit, radii); hits_n = len(hits)
        p = chance_meshed(hits_n, radii)
    turn = next((ph for n, pw, ph in fold["middle"] if n >= 4), 0.0)

    im = rgb.copy(); d = ImageDraw.Draw(im)
    for r, s in rings:
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(255, 220, 0), width=3 if r == unit else 1)
        d.text((cx + r * .7071 + 3, cy - r * .7071 - 10), f"{r / unit:.2f}", fill=(255, 220, 0))
    d.line((cx - 8, cy, cx + 8, cy), fill=(255, 0, 0), width=2); d.line((cx, cy - 8, cx, cy + 8), fill=(255, 0, 0), width=2)
    im.save(os.path.join(OUT, f"{name}_rings.jpg"), quality=88)
    for tag, fn in (("six", draw_six), ("eight", draw_eight)):
        im = rgb.copy(); fn(Pen(im, cx, cy, unit, turn)); im.save(os.path.join(OUT, f"{name}_{tag}.jpg"), quality=88)

    return {"photo": os.path.basename(path), "size": [w, h], "centre": [round(cx, 1), round(cy, 1)],
            "rings_px": radii, "unit_px": unit, "ratios": [round(r / unit, 3) for r in radii],
            "first_circles_tried": tried, "matches": hits, "match_count": hits_n, "other_rings": len(radii) - 1, "chance_of_this_or_better": p,
            "folds": {b: [(n, pw) for n, pw, _ in v] for b, v in fold.items()}}


if __name__ == "__main__":
    # name=photo            centre and first circle found automatically
    # name=photo@cx,cy,unit  any of the three placed by eye (leave blank to keep automatic), in photo pixels
    report = {}
    for arg in (a for a in sys.argv[1:] if not a.startswith("--")):
        name, rest = arg.split("=")
        rel, _, manual = rest.partition("@")
        m = (manual.split(",") + ["", "", ""])[:3]
        centre = (float(m[0]), float(m[1])) if m[0] and m[1] else None
        report[name] = analyse(os.path.join(HERE, "domes", rel), name, centre, int(m[2]) if m[2] else None)
        report[name]["placed_by_eye"] = {"centre": bool(centre), "first_circle": bool(m[2])}
        print(name, json.dumps(report[name]))
    with open(os.path.join(OUT, "measurements.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1)
