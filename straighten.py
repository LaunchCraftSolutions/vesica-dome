"""Straighten a dome photographed from off to one side, so it reads as if taken from straight under the crown.

Every ring of a dome is a level circle on one upright axis. A camera standing off that axis still sees each ring
as a circle (an oval if the camera is also tipped), but each ring gets its own middle: the higher the ring, the
less it shifts. So the oculus, the base of the shell, the drum and the cornice below it sit like a tilted stack of
plates, their middles strung along one line.

This finds those rings and their middles, which gives the dome's true middle (the crown) and the line the rest
drift along. That is the grid: rings at every height, and lines running down the dome from the crown to its foot.
Sliding every ring back along the line until it sits on the crown is exactly what walking to the middle of the
floor would do to the picture, so the photo is re-drawn that way from its own pixels. Nothing is invented; where
the camera saw a wall at a glancing angle the picture is stretched, and that is reported.

Two things the photo cannot give. Inside a shell with no rings on it the drift is filled in as for a half-sphere.
And the lens is taken as an ordinary wide one unless the photo's own details say otherwise.
"""
import json, math, os, sys
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "domes", "straight")
GOLD, PALE, RUBY = (232, 190, 96), (236, 228, 208), (190, 40, 60)
UNSEEN = 0.2


class View:
    """The same camera turned to look straight up the dome's axis, not moved. Points are (u, v) about its middle."""

    def __init__(self, W, H, f, tx=0.0, ty=0.0):
        self.W, self.H, self.f, self.tx, self.ty = W, H, f, tx, ty
        self.x0, self.y0 = W / 2, H / 2
        t = math.hypot(tx, ty); self.flat = t < 1e-9
        if self.flat:
            self.R = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
        else:
            kx, ky = -ty / t, tx / t; c, s = math.cos(t), math.sin(t); v = 1 - c
            self.R = ((c + v * kx * kx, v * kx * ky, s * ky), (v * kx * ky, c + v * ky * ky, -s * kx), (-s * ky, s * kx, c))

    def to_photo(self, u, v):
        if self.flat:
            return self.x0 + u, self.y0 + v
        R, f = self.R, self.f
        z = R[2][0] * u + R[2][1] * v + R[2][2] * f
        if z <= 1e-6:
            return -1e9, -1e9
        return self.x0 + f * (R[0][0] * u + R[0][1] * v + R[0][2] * f) / z, self.y0 + f * (R[1][0] * u + R[1][1] * v + R[1][2] * f) / z

    def from_photo(self, x, y):
        if self.flat:
            return x - self.x0, y - self.y0
        R, f = self.R, self.f; a, b = x - self.x0, y - self.y0
        z = R[0][2] * a + R[1][2] * b + R[2][2] * f
        return f * (R[0][0] * a + R[1][0] * b + R[2][0] * f) / z, f * (R[0][1] * a + R[1][1] * b + R[2][1] * f) / z


def focal_px(W, H, meta=None):
    f35 = (meta or {}).get("focal35_mm") or 26.0   # an ordinary wide lens when the photo does not say
    return f35 / 43.27 * math.hypot(W, H)


def find_circles(gray, size=384):
    """Every circle the photo holds, each with its own middle: edge points vote along their own slope for a centre."""
    im = gray.copy(); im.thumbnail((size, size)); k = gray.width / im.width
    px, w, h = im.load(), im.width, im.height
    edges = []
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            gx = px[x + 1, y - 1] + 2 * px[x + 1, y] + px[x + 1, y + 1] - px[x - 1, y - 1] - 2 * px[x - 1, y] - px[x - 1, y + 1]
            gy = px[x - 1, y + 1] + 2 * px[x, y + 1] + px[x + 1, y + 1] - px[x - 1, y - 1] - 2 * px[x, y - 1] - px[x + 1, y - 1]
            m = math.hypot(gx, gy)
            if m > 0:
                edges.append((m, x, y, gx / m, gy / m))
    edges.sort(reverse=True); edges = edges[:int(0.18 * len(edges))]
    B = 2; cw, ch = w // B + 1, h // B + 1; rmax = int(0.62 * max(w, h)); nr = rmax // B + 1
    acc = [0] * (cw * ch * nr)
    for m, x, y, ux, uy in edges:
        for sgn in (1, -1):
            for r in range(4, rmax):
                cx, cy = x + sgn * r * ux, y + sgn * r * uy
                if not (0 <= cx < w and 0 <= cy < h):
                    break
                acc[(int(cy) // B * cw + int(cx) // B) * nr + r // B] += 1
    rlo = max(3, int(0.035 * max(w, h) / B)); cells = []
    for cyb in range(1, ch - 1):
        for cxb in range(1, cw - 1):
            base = (cyb * cw + cxb) * nr
            for rb in range(rlo, nr - 1):
                if acc[base + rb] < 6:
                    continue
                tot = 0
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        b2 = ((cyb + dy) * cw + cxb + dx) * nr + rb
                        tot += acc[b2 - 1] + acc[b2] + acc[b2 + 1]
                cells.append((tot / (rb * B + 1), cxb, cyb, rb))   # votes per unit of the circle's own length
    cells.sort(reverse=True); picked = []; per_size = {}
    for s, cxb, cyb, rb in cells:   # the best few of every size, so small sharp circles cannot crowd out the big rings
        if per_size.get(rb // 2, 0) < 3 and all(abs(rb - q[3]) > 2 or abs(cxb - q[1]) > 4 or abs(cyb - q[2]) > 4 for q in picked):
            picked.append((s, cxb, cyb, rb)); per_size[rb // 2] = per_size.get(rb // 2, 0) + 1
    return [((cxb + .5) * B * k, (cyb + .5) * B * k, (rb + .5) * B * k, s) for s, cxb, cyb, rb in picked], B * k


def pick_stack(cands, tol, short, seed=None):
    """The dome is the longest run of circles nested one inside the next whose middles step along one direction."""
    cands = sorted(cands, key=lambda c: c[2]); best = (0, [], 0.0)
    toll = 0.5 * sorted(c[3] * math.sqrt(c[2]) for c in cands)[len(cands) // 2] / (0.05 * short) if cands else 0.0   # a typical ring buys a 5% step
    for a in range(0, 360, 15):
        ex, ey = math.cos(math.radians(a)), math.sin(math.radians(a))
        near = [seed is None or math.hypot(c[0] - seed[0], c[1] - seed[1]) <= 0.12 * short for c in cands]   # may start the stack
        sc = [c[3] * math.sqrt(c[2]) for c in cands]; back = [None] * len(cands)
        for j, cj in enumerate(cands):
            top, arg = (0.0 if near[j] else -1e18), None
            for i in range(j):
                ci = cands[i]; dr = cj[2] - ci[2]
                if dr < 2 * tol:
                    continue
                dx, dy = cj[0] - ci[0], cj[1] - ci[1]; along, across = dx * ex + dy * ey, abs(dx * ey - dy * ex)
                if across <= tol and -tol <= along <= 0.85 * dr + tol and sc[i] - toll * max(0.0, along) > top:
                    top, arg = sc[i] - toll * max(0.0, along), i
            sc[j] += top; back[j] = arg
        j = max(range(len(cands)), key=lambda i: sc[i]); total = sc[j]; run = []
        while j is not None:
            run.append(cands[j]); j = back[j]
        run.reverse()
        if run[-1][2] >= 0.2 * short and total > best[0]:
            best = (total, run, a)
    return best[1]


def line_of(rings):
    """The line the rings' middles run along, pointed the way they move as the rings widen."""
    sw = sum(s for *_, s in rings); mu, mv = sum(u * s for u, _, _, s in rings) / sw, sum(v * s for _, v, _, s in rings) / sw
    sxx = sum(s * (u - mu) ** 2 for u, _, _, s in rings); syy = sum(s * (v - mv) ** 2 for _, v, _, s in rings); sxy = sum(s * (u - mu) * (v - mv) for u, v, _, s in rings)
    ang = 0.5 * math.atan2(2 * sxy, sxx - syy); ex, ey = math.cos(ang), math.sin(ang)
    ts = [(u - mu) * ex + (v - mv) * ey for u, v, _, _ in rings]; rs = [r for _, _, r, _ in rings]
    if len(rings) >= 2 and sum((t - sum(ts) / len(ts)) * (r - sum(rs) / len(rs)) for t, r in zip(ts, rs)) < 0:
        ex, ey, ts = -ex, -ey, [-t for t in ts]
    return mu, mv, ex, ey, ts


def sweep(P, W, H, view, rings, floor, nth=72, dr=3, dt=4):
    """Walk the line with circles of every size: wherever one snaps onto an edge is another ring of the stack."""
    mu, mv, ex, ey, ts = line_of(rings); rs = [r for _, _, r, _ in rings]
    trig = [(math.cos(2 * math.pi * k / nth), math.sin(2 * math.pi * k / nth)) for k in range(nth)]
    span = max(rs); t_lo, t_hi = min(ts) - 0.15 * span, max(ts) + 0.45 * span
    tv = [t_lo + i * dt for i in range(int((t_hi - t_lo) / dt) + 1)]; rv = list(range(max(12, int(0.5 * min(rs))), int(0.75 * max(W, H)), dr))
    g = [[ring_score(P, W, H, view, mu + t * ex, mv + t * ey, r, trig) if t - ts[0] <= 0.85 * r + 4 * dt else 0.0 for t in tv] for r in rv]
    peaks = []; mids = [(sorted(v for v in row if v > 0) or [0])[sum(1 for v in row if v > 0) // 2] for row in g]
    for i in range(1, len(rv) - 1):
        for j in range(1, len(tv) - 1):
            v = g[i][j]
            if v >= floor and v >= 2.2 * mids[i] and all(v >= g[i + a][j + b] for a in (-1, 0, 1) for b in (-1, 0, 1)):
                peaks.append((mu + tv[j] * ex, mv + tv[j] * ey, rv[i], v))
    return peaks


def chain(rings, tol=6.0):
    """Of the circles on the line, the heaviest run that stays nested, middles never stepping back."""
    mu, mv, ex, ey, _ = line_of(rings); c = sorted(rings, key=lambda x: x[2])
    t = [(u - mu) * ex + (v - mv) * ey for u, v, _, _ in c]; sc = [x[3] * math.sqrt(x[2]) for x in c]; back = [None] * len(c)
    for j in range(len(c)):
        top, arg = 0.0, None
        for i in range(j):
            dr = c[j][2] - c[i][2]
            if dr >= 8 and -tol <= t[j] - t[i] <= dr + tol and sc[i] > top:
                top, arg = sc[i], i
        sc[j] += top; back[j] = arg
    j = max(range(len(c)), key=lambda i: sc[i]); run = []
    while j is not None:
        run.append(c[j]); j = back[j]
    return run[::-1]


def ring_score(px, W, H, view, cu, cv, r, trig, nsec=24, half=2.0):
    """How strongly a brightness step runs along this circle, arc by arc, so a ring that flips light to dark still counts."""
    per = len(trig) // nsec; tot = 0.0; good = 0; flat = view.flat; x0, y0 = view.x0 + cu, view.y0 + cv
    for s in range(nsec):
        acc = 0.0; n = 0
        for c, sn in trig[s * per:(s + 1) * per]:
            if flat:
                x1, y1, x2, y2 = x0 + (r - half) * c, y0 + (r - half) * sn, x0 + (r + half) * c, y0 + (r + half) * sn
            else:
                x1, y1 = view.to_photo(cu + (r - half) * c, cv + (r - half) * sn); x2, y2 = view.to_photo(cu + (r + half) * c, cv + (r + half) * sn)
            if 0 <= x1 < W and 0 <= y1 < H and 0 <= x2 < W and 0 <= y2 < H:
                acc += px[x2, y2] - px[x1, y1]; n += 1
        if n >= 0.7 * per:
            tot += abs(acc / n); good += 1
    return tot / nsec if good >= 0.45 * nsec else 0.0


def settle(px, W, H, view, cu, cv, r, steps=((3, 4), (1.5, 2), (0.75, 2)), nth=192):
    """Nudge one circle's middle and size to where its edge is sharpest."""
    trig = [(math.cos(2 * math.pi * k / nth), math.sin(2 * math.pi * k / nth)) for k in range(nth)]
    best = (ring_score(px, W, H, view, cu, cv, r, trig), cu, cv, r)
    for step, n in steps:
        _, bu, bv, br = best
        for i in range(-n, n + 1):
            for j in range(-n, n + 1):
                for m in range(-n, n + 1):
                    if i == j == m == 0:
                        continue
                    s = ring_score(px, W, H, view, bu + i * step, bv + j * step, br + m * step, trig)
                    if s > best[0]:
                        best = (s, bu + i * step, bv + j * step, br + m * step)
    return best


def pchip(xs, ys):
    """A smooth curve through the points that never doubles back between them."""
    n = len(xs)
    if n == 1:
        return lambda x: ys[0]
    h = [xs[i + 1] - xs[i] for i in range(n - 1)]; d = [(ys[i + 1] - ys[i]) / h[i] for i in range(n - 1)]
    m = [d[0]] + [0.0 if d[i - 1] * d[i] <= 0 else 3 * (h[i - 1] + h[i]) / ((2 * h[i] + h[i - 1]) / d[i - 1] + (h[i] + 2 * h[i - 1]) / d[i]) * 1.0 for i in range(1, n - 1)] + [d[-1]]

    m = [min(v, 0.95) for v in m]

    def f(x):
        if x <= xs[0]:
            return ys[0]
        if x >= xs[-1]:
            return ys[-1]
        i = max(k for k in range(n - 1) if xs[k] <= x); t = (x - xs[i]) / h[i]
        if d[i] > 0.6:
            return ys[i] + d[i] * (x - xs[i])
        return ((2 * t ** 3 - 3 * t ** 2 + 1) * ys[i] + (t ** 3 - 2 * t ** 2 + t) * h[i] * m[i] + (-2 * t ** 3 + 3 * t ** 2) * ys[i + 1] + (t ** 3 - t ** 2) * h[i] * m[i + 1])
    return f


def oval_points(cx, cy, r, sq, ang, n=48):
    ca, sa = math.cos(ang), math.sin(ang)
    return [(cx + sq * r * math.cos(2 * math.pi * k / n) * ca - r * math.sin(2 * math.pi * k / n) * sa,
             cy + sq * r * math.cos(2 * math.pi * k / n) * sa + r * math.sin(2 * math.pi * k / n) * ca) for k in range(n)]


def fit_oval(P, W, H, cx, cy, r, ex, ey):
    """One big ring as an oval in the photo: (score, middle x, y, long half-width, squash, direction of the squash)."""
    def run(cx, cy, r, sq, ang, trig, nsec=24, half=2.0):
        ca, sa = math.cos(ang), math.sin(ang); per = len(trig) // nsec; tot = 0.0; good = 0
        for q in range(nsec):
            acc = 0.0; n = 0
            for c, sn in trig[q * per:(q + 1) * per]:
                dx, dy = sq * c * ca - sn * sa, sq * c * sa + sn * ca
                x1, y1, x2, y2 = cx + (r - half) * dx, cy + (r - half) * dy, cx + (r + half) * dx, cy + (r + half) * dy
                if 0 <= x1 < W and 0 <= y1 < H and 0 <= x2 < W and 0 <= y2 < H:
                    acc += P[x2, y2] - P[x1, y1]; n += 1
            if n >= 0.7 * per:
                tot += abs(acc / n); good += 1
        return tot / nsec if good >= 0.45 * nsec else 0.0
    coarse = [(math.cos(2 * math.pi * k / 48), math.sin(2 * math.pi * k / 48)) for k in range(48)]
    fine = [(math.cos(2 * math.pi * k / 144), math.sin(2 * math.pi * k / 144)) for k in range(144)]
    line = math.atan2(ey, ex); sc, sr = 0.02 * r, 0.015 * r; tops = []
    for sq in (1.0, .97, .94, .91, .88, .85, .82):
        for da in ((0,) if sq == 1.0 else (-30, -15, 0, 15, 30)):
            ang = line + math.radians(da); best = (0.0,)
            for i in range(-6, 7):
                for j in (-1, 0, 1):
                    x, y = cx + sc * (i * ex - j * ey), cy + sc * (i * ey + j * ex)
                    for m in range(-5, 6):
                        v = run(x, y, r + m * sr, sq, ang, coarse)
                        if v > best[0]:
                            best = (v, x, y, r + m * sr, sq, ang)
            tops.append(best)
    tops.sort(reverse=True); out = (0.0,)
    for _, x0, y0, r0, sq, ang in tops[:4]:   # look closely at the best few shapes
        for i in (-2, -1, 0, 1, 2):
            for j in (-2, -1, 0, 1, 2):
                for m in (-2, -1, 0, 1, 2):
                    for dq in (-.015, 0, .015):
                        v = run(x0 + i * sc / 3, y0 + j * sc / 3, r0 + m * sr / 3, sq + dq, ang, fine)
                        if v > out[0]:
                            out = (v, x0 + i * sc / 3, y0 + j * sc / 3, r0 + m * sr / 3, round(sq + dq, 3), ang)
    return out


def circle_of(pts):
    """The circle that best fits the points: ((middle), radius, how far out of round as a share of the radius)."""
    n = len(pts); sx = sum(p[0] for p in pts) / n; sy = sum(p[1] for p in pts) / n
    q = [(x - sx, y - sy) for x, y in pts]
    suu = sum(u * u for u, v in q); svv = sum(v * v for u, v in q); suv = sum(u * v for u, v in q)
    suuu = sum(u ** 3 for u, v in q); svvv = sum(v ** 3 for u, v in q); suvv = sum(u * v * v for u, v in q); svuu = sum(v * u * u for u, v in q)
    det = suu * svv - suv * suv
    if abs(det) < 1e-9:
        return (sx, sy), 0.0, 1.0
    uc = (svv * (suuu + suvv) - suv * (svvv + svuu)) / (2 * det); vc = (suu * (svvv + svuu) - suv * (suuu + suvv)) / (2 * det)
    ds = [math.hypot(u - uc, v - vc) for u, v in q]; rad = sum(ds) / n
    return (sx + uc, sy + vc), rad, math.sqrt(sum((d - rad) ** 2 for d in ds) / n) / rad


def solve_tilt(W, H, f, ovals):
    """The turn of the camera (degrees, x and y) that makes the ovals circles, lower rings further from straight-up."""
    pts = [(oval_points(*o[1:]), o[0] * math.sqrt(o[3])) for o in ovals]; wsum = sum(w for _, w in pts)

    def cost(tx, ty, free=False):
        vw = View(W, H, f, math.radians(tx), math.radians(ty)); tot = 0.0; got = []
        for p, w in pts:
            c, rad, off = circle_of([vw.from_photo(*xy) for xy in p]); tot += w * off; got.append((rad, c))
        got.sort()
        (r0, c0), (r1, c1) = got[0], got[-1]
        if not free and math.hypot(c1[0] - c0[0], c1[1] - c0[1]) > 0.03 * r1 and (c1[0] - c0[0]) * c1[0] + (c1[1] - c0[1]) * c1[1] < 0:
            return None   # the wider, lower rings must drift away from straight-up, not toward it
        return tot / wsum
    was = cost(0, 0, True); level = cost(0, 0); best = (was if level is not None else 9.0, 0.0, 0.0)
    for tx in range(-36, 37, 2):
        for ty in range(-36, 37, 2):
            c = cost(tx, ty)
            if c is not None and c + 1e-4 * math.hypot(tx, ty) < best[0] + 1e-4 * math.hypot(best[1], best[2]):
                best = (c, float(tx), float(ty))
    return best[1], best[2], was, best[0]


def hunt(P, W, H, view, u, v, r, nth=72):
    """Look widely round one circle for where its ring really is in this view, then settle on it."""
    trig = [(math.cos(2 * math.pi * k / nth), math.sin(2 * math.pi * k / nth)) for k in range(nth)]
    sc, sr = max(4.0, 0.015 * r), max(3.0, 0.012 * r); best = (0.0, u, v, r)
    for i in range(-4, 5):
        for j in range(-4, 5):
            for m in range(-7, 8):
                s = ring_score(P, W, H, view, u + i * sc, v + j * sc, r + m * sr, trig)
                if s > best[0]:
                    best = (s, u + i * sc, v + j * sc, r + m * sr)
    return settle(P, W, H, view, *best[1:], steps=((2, 2), (1, 2)))


def fit(gray, meta=None, log=None, seed=None):
    """Find the stack of rings, the line their middles run along, and the crown. Returns the model as a dict."""
    W, H = gray.size; f = focal_px(W, H, meta); say = log or (lambda *a: None)
    px = gray.filter(ImageFilter.GaussianBlur(1.2)).load()

    class Px:   # nearest-pixel read with float coordinates
        def __getitem__(self, xy):
            return px[int(xy[0]), int(xy[1])]
    P = Px(); fine = [(math.cos(2 * math.pi * k / 192), math.sin(2 * math.pi * k / 192)) for k in range(192)]
    scorer = lambda vw: (lambda u, v, r: ring_score(P, W, H, vw, u, v, r, fine))
    cands, tol = find_circles(gray)
    stack = pick_stack(cands, 1.6 * tol, min(W, H), seed)
    flat = View(W, H, f); view = flat
    rings = tidy([list(settle(P, W, H, flat, cx - W / 2, cy - H / 2, r)[1:]) + [0] for cx, cy, r, _ in stack], rescore=scorer(flat))
    if not rings:
        return None
    say("first rings:", [(round(u + W / 2), round(v + H / 2), round(r), round(s, 1)) for u, v, r, s in rings])

    # Is the camera also tipped? A tipped camera turns the big rings into ovals. Fit the big rings as ovals in the
    # photo, then find the one turn of the camera that makes them all circles again.
    mu, mv, ex, ey, _ = line_of(rings); big = [x for x in sorted(rings, key=lambda x: -x[2])[:3] if x[2] >= 0.2 * rings[-1][2]]
    ovals = [fit_oval(P, W, H, u + W / 2, v + H / 2, r, ex, ey) for u, v, r, _ in big]
    say("big rings as ovals (middle, long half-width, squash, direction):", [(round(o[1]), round(o[2]), round(o[3]), o[4], round(math.degrees(o[5]))) for o in ovals])
    tx, ty, was, now = solve_tilt(W, H, f, ovals)
    say("camera tipped", tx, ty, "degrees; ovals out of round by", round(100 * was, 2), "% ->", round(100 * now, 2), "%")
    if was - now < 0.003:
        tx = ty = 0.0
    else:
        view = View(W, H, f, math.radians(tx), math.radians(ty)); moved = []
        for u, v, r, _ in rings:
            hit = [o for o, bg in zip(ovals, big) if bg[2] == r]
            if hit:   # start from where the oval lands in the level view
                (cu, cv), rr = circle_of([view.from_photo(*p) for p in oval_points(*hit[0][1:])])[:2]
            else:
                (cu, cv), rr = view.from_photo(u + W / 2, v + H / 2), r
            moved.append(list(hunt(P, W, H, view, cu, cv, rr)[1:]) + [0])
        rings = tidy(moved, rescore=scorer(view))

    # Walk the line for every other ring of the stack.
    say("rings in the level view:", [(round(u), round(v), round(r), round(s, 1)) for u, v, r, s in rings])
    floor = 0.25 * sorted(x[3] for x in rings)[len(rings) // 2]
    found = sweep(P, W, H, view, rings, floor)
    more = chain(rings + found)
    rings = tidy([list(settle(P, W, H, view, u, v, r, steps=((2, 2), (1, 2)))[1:]) + [0] for u, v, r, _ in more], rescore=scorer(view))
    say("rings:", [(round(u), round(v), round(r), round(s, 1)) for u, v, r, s in rings])

    # The line the middles run along, and how far along it each ring sits.
    mu, mv, ex, ey, ts = line_of(rings); rs = [r for _, _, r, _ in rings]
    across = max(abs((u - mu) * ey - (v - mv) * ex) for u, v, _, _ in rings)
    # Never backwards (neighbours that disagree are pooled), one knot per band of sizes, rings kept nested.
    pool = [[r, t, s * math.sqrt(r), 1] for (_, _, r, s), t in zip(rings, ts)]; i = 0
    while i < len(pool) - 1:
        if pool[i][1] > pool[i + 1][1]:
            w = pool[i][2] + pool[i + 1][2]; t = (pool[i][1] * pool[i][2] + pool[i + 1][1] * pool[i + 1][2]) / w
            pool[i][1] = pool[i + 1][1] = t; pool[i][2] = pool[i + 1][2] = w; i = max(0, i - 1) if i and pool[i - 1][1] > t else i + 1
        else:
            i += 1
    band = 0.05 * rs[-1]; knots = []; grp = []
    for r, t, w, _ in pool + [[1e9, 0, 0, 0]]:
        if grp and r - grp[0][0] > band:
            ww = sum(g[2] for g in grp); knots.append([sum(g[0] * g[2] for g in grp) / ww, sum(g[1] * g[2] for g in grp) / ww]); grp = []
        grp.append((r, t, w))
    for k in range(1, len(knots)):
        knots[k][1] = min(max(knots[k][1], knots[k - 1][1]), knots[k - 1][1] + 0.97 * (knots[k][0] - knots[k - 1][0]))
    drift = knots[-1][1] - knots[0][1]
    crown_seen = knots[0][0] <= 0.3 * knots[-1][0]
    guessed = 0.0
    if not crown_seen and len(knots) >= 2 and drift > 0:
        # No ring near the crown. Fill the shell in as a half-sphere springing from the innermost ring found.
        m = min(0.85, drift / (knots[-1][0] - knots[0][0])); r1, t1 = knots[0]; a = f / r1
        guessed = m * r1 / (a + 1); extra = []
        for deg in (0, 30, 50, 65, 78):
            ph = math.radians(deg)
            extra.append([r1 * a * math.sin(ph) / (a + math.cos(ph)), t1 - guessed + guessed * (1 / (a + math.cos(ph)) - 1 / (a + 1)) / (1 / a - 1 / (a + 1))])
        knots = extra + knots
    t0 = knots[0][1]
    return {"photo_size": [W, H], "focal_px": round(f, 1), "tilt_deg": [round(tx, 2), round(ty, 2)], "line_origin": [mu, mv], "line_dir": [ex, ey],
            "knots": [[round(r, 2), round(t, 2)] for r, t in knots], "rings": [[round(u, 1), round(v, 1), round(r, 1), round(s, 2)] for u, v, r, s in rings],
            "crown_seen": crown_seen, "crown_guess_px": round(guessed, 1), "drift_px": round(knots[-1][1] - t0, 1), "outer_ring_px": round(knots[-1][0], 1),
            "off_line_px": round(across, 1)}


def tidy(rings, rescore=None):
    """One entry per ring, inside to outside, each nested in the next."""
    if rescore:
        rings = [[u, v, r, rescore(u, v, r)] for u, v, r, _ in rings]
    rings = sorted((x for x in rings if x[3] > 0), key=lambda x: -x[3]); kept = []
    for x in rings:
        if all(abs(x[2] - y[2]) > 7 for y in kept):
            kept.append(x)
    kept.sort(key=lambda x: x[2]); out = []
    for x in kept:
        while out and math.hypot(x[0] - out[-1][0], x[1] - out[-1][1]) > x[2] - out[-1][2] + 6:
            if out[-1][3] * math.sqrt(out[-1][2]) < x[3] * math.sqrt(x[2]):
                out.pop()
            else:
                x = None; break
        if x:
            out.append(x)
    return out


class Model:
    def __init__(self, m):
        self.m = m; W, H = m["photo_size"]
        self.view = View(W, H, m["focal_px"], *(math.radians(a) for a in m["tilt_deg"]))
        ks = m["knots"]; self.q = pchip([k[0] for k in ks], [k[1] for k in ks]); self.rmax = ks[-1][0]
        tail = ks[-3:] if len(ks) >= 3 else ks
        self.tail = min(0.8, max(0.0, (tail[-1][1] - tail[0][1]) / (tail[-1][0] - tail[0][0]))) if len(tail) >= 2 else 0.0
        self.qmax = ks[-1][1]

    def middle(self, r):
        """Where the ring of this size has its middle, in the level view."""
        ease = 0.12 * self.rmax
        t = self.q(r) if r <= self.rmax else self.qmax + self.tail * ease * (1 - math.exp(-(r - self.rmax) / ease))
        (mu, mv), (ex, ey) = self.m["line_origin"], self.m["line_dir"]
        return mu + t * ex, mv + t * ey

    def to_photo(self, dx, dy):
        """A point of the straight-on picture, measured from the crown, back to where it is in the photo."""
        cu, cv = self.middle(math.hypot(dx, dy))
        return self.view.to_photo(cu + dx, cv + dy)

    def crown(self):
        return self.view.to_photo(*self.middle(0.0))

    def stretch(self, r, th):
        """How much one step outward in the straight picture covers in the photo: under 1 is a wall seen at a glance."""
        x1, y1 = self.to_photo(r * math.cos(th), r * math.sin(th)); x2, y2 = self.to_photo((r + 4) * math.cos(th), (r + 4) * math.sin(th))
        return math.hypot(x2 - x1, y2 - y1) / 4


def redraw(rgb, model, cell=8, dim=True):
    """The straight-on picture, made from the photo's own pixels. With dim off, unseen parts are left as they smear."""
    W, H = rgb.size; cx, cy = model.crown()
    N = int(2 * max(math.hypot(cx, cy), math.hypot(W - cx, cy), math.hypot(cx, H - cy), math.hypot(W - cx, H - cy)) * 0.75)
    n = N // cell + 1; c = N / 2
    grid = [[model.to_photo(i * cell - c, j * cell - c) for i in range(n + 1)] for j in range(n + 1)]
    data = []
    for j in range(n):
        for i in range(n):
            a, b, d, e = grid[j][i], grid[j + 1][i], grid[j + 1][i + 1], grid[j][i + 1]
            if max(a[0], b[0], d[0], e[0]) < 0 or min(a[0], b[0], d[0], e[0]) > W or max(a[1], b[1], d[1], e[1]) < 0 or min(a[1], b[1], d[1], e[1]) > H:
                continue
            data.append(((i * cell, j * cell, (i + 1) * cell, (j + 1) * cell), (a[0], a[1], b[0], b[1], d[0], d[1], e[0], e[1])))
    out = rgb.transform((N, N), Image.MESH, data, resample=Image.BICUBIC)
    # Where the camera saw the dome at a glance (a near wall hidden behind its own cornice) there is nothing real to
    # show: one step outward here covers under a fifth of a step in the photo. Grey those parts down rather than
    # leave smeared stone that looks like evidence.
    thin = Image.new("L", (n, n), 0); tp = thin.load(); any_thin = False
    for j in range(n):
        for i in range(n):
            dx, dy = (i + .5) * cell - c, (j + .5) * cell - c; r = math.hypot(dx, dy)
            if 8 < r < 1.05 * model.rmax:
                x1, y1 = model.to_photo(dx, dy); x2, y2 = model.to_photo(dx * (1 + 4 / r), dy * (1 + 4 / r))
                if 0 <= x1 < W and 0 <= y1 < H and math.hypot(x2 - x1, y2 - y1) / 4 < UNSEEN:
                    tp[i, j] = 255; any_thin = True
    if any_thin and dim:
        mask = thin.resize((n * cell, n * cell), Image.BILINEAR).crop((0, 0, N, N))
        dull = Image.blend(out.convert("L").convert("RGB"), Image.new("RGB", (N, N), (18, 16, 22)), 0.72)
        out = Image.composite(dull, out, mask)
    return out


def draw_grid(rgb, model, spokes=24):
    """The grid on the photo as taken: the rings found, and lines running down the dome from the crown to its foot."""
    im = rgb.copy(); d = ImageDraw.Draw(im); wd = max(2, max(im.size) // 500); m = model.m
    rmax = m["outer_ring_px"]; found = [r for _, _, r, _ in m["rings"]]
    for k in range(spokes):
        th = 2 * math.pi * k / spokes
        d.line([model.to_photo(r * math.cos(th), r * math.sin(th)) for r in range(0, int(rmax) + 1, 6)], fill=PALE, width=wd)
    for r in found:
        d.line([model.to_photo(r * math.cos(2 * math.pi * k / 240), r * math.sin(2 * math.pi * k / 240)) for k in range(241)], fill=GOLD, width=wd)
    x, y = model.crown(); s = 5 * wd
    d.line([(x - s, y), (x + s, y)], fill=RUBY, width=wd); d.line([(x, y - s), (x, y + s)], fill=RUBY, width=wd)
    return im


def straighten(rgb, gray=None, meta=None, log=None, seed=None, dim=True):
    """Returns (straight-on picture, model dict, Model) or None when no stack of rings is found."""
    m = fit(gray or rgb.convert("L"), meta, log=log, seed=seed)
    if not m:
        return None
    model = Model(m)
    looks = [model.stretch(r, 2 * math.pi * k / 72) for r in range(10, int(model.rmax), max(4, int(model.rmax / 60))) for k in range(72)]
    m["worst_stretch"] = round(min(looks), 2); m["unseen_share"] = round(sum(1 for v in looks if v < UNSEEN) / len(looks), 3)
    cx, cy = model.crown(); m["crown_in_photo"] = [round(cx), round(cy)]
    return redraw(rgb, model, dim=dim), m, model


if __name__ == "__main__":
    import draw_all as D
    os.makedirs(OUT, exist_ok=True)
    meta = json.load(open(os.path.join(HERE, "domes", "all", "photo_meta.json"), encoding="utf-8"))
    rep_path = os.path.join(OUT, "straight.json"); report = json.load(open(rep_path, encoding="utf-8")) if os.path.exists(rep_path) else {}
    only = set(sys.argv[1:])
    import analyze as A

    def sharp(img, rmax):
        g = img.convert("L"); n = g.width
        return A.edge_energy(A.profile(g.load(), n, n, n / 2, n / 2, rmax, 360))
    for place, rel, _, _, _, hand in D.DOMES:
        if only and place not in only:
            continue
        rgb = Image.open(os.path.join(HERE, "domes", rel)).convert("RGB"); gray = rgb.convert("L")
        slug = "".join(ch if ch.isalnum() else "_" for ch in place.lower()); name = place.encode("ascii", "replace").decode()
        seed = hand or D.true_middle(gray)
        got = straighten(rgb, gray, meta.get(rel), log=lambda *a: print("  ", *a, flush=True), seed=seed, dim=False)
        if not got:
            print(name, "no stack of rings found", flush=True); continue
        plain, m, model = got; rmax = int(0.42 * min(rgb.size))
        old = sharp(D.unsquash(rgb, gray, *seed)[0], rmax); new = sharp(plain, rmax)
        m["sharpness_before_after"] = [round(old), round(new)]
        out = redraw(rgb, model); out.thumbnail((1100, 1100)); out.save(os.path.join(OUT, slug + "_straight.jpg"), quality=88)
        g = draw_grid(rgb, model); g.thumbnail((1100, 1100)); g.save(os.path.join(OUT, slug + "_grid.jpg"), quality=88)
        report[place] = m
        print(name, "middle was", [round(v) for v in seed], "crown", m["crown_in_photo"], "drift", m["drift_px"], "of", m["outer_ring_px"], "tilt", m["tilt_deg"], "rings", len(m["rings"]),
              "seen" if m["crown_seen"] else "filled in", "unseen", m["unseen_share"], "ring sharpness", round(old), "->", round(new), "x", round(new / max(old, 1), 2), flush=True)
        json.dump(report, open(rep_path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
