"""Walk the chain out past the rim.

The eight-flower ends on the dome's rim. Keep walking the same circle outward along each ray, each one through
the centre of the last, and the third circle of each chain sits outside the dome: radius half the rim's, centred
one and a half rim-radii out, touching the rim. This draws that on a photo and says how close it sits to what is
really there.

Done the way a person would: try each crisp ring as the rim, try four or eight rays and a few turns, and keep the
one where the outer circles sit best on edges in the photo. Then report how close, and how often luck would do as well.
"""
import json, math, os, sys
from PIL import Image
import analyze as A

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "domes", "chain")
S3 = A.S3


def edge_on_circles(px, w, h, cx, cy, R, rho, n, turn, pts=120):
    """Average brightness step across n circles of radius rho whose centres sit R out from (cx, cy)."""
    tot = cnt = 0
    for k in range(n):
        a = math.radians(turn + 360 * k / n)
        ox, oy = cx + R * math.cos(a), cy + R * math.sin(a)
        for j in range(pts):
            b = 2 * math.pi * j / pts; c, s = math.cos(b), math.sin(b)
            x1, y1, x2, y2 = ox + (rho - 3) * c, oy + (rho - 3) * s, ox + (rho + 3) * c, oy + (rho + 3) * s
            if 0 <= x1 < w and 0 <= y1 < h and 0 <= x2 < w and 0 <= y2 < h:
                tot += abs(px[int(x1), int(y1)] - px[int(x2), int(y2)]); cnt += 1
    return tot / cnt if cnt >= 0.2 * n * pts else None


def walk(path, name, centre=None):
    rgb = Image.open(path).convert("RGB"); gray = rgb.convert("L")
    w, h = gray.size; px = gray.load(); m = min(w, h)
    cx, cy = centre or A.find_centre(gray)
    rmax = int(max(math.hypot(cx, cy), math.hypot(w - cx, cy), math.hypot(cx, h - cy), math.hypot(w - cx, h - cy)))
    rings = A.find_rings(A.profile(px, w, h, cx, cy, rmax, 720), rmin=int(0.04 * m))
    best = None
    for rim, _ in rings:
        if not 0.12 * m <= rim <= 0.6 * m:
            continue
        for n in (4, 8):
            for t in range(6):
                turn = t * 360 / n / 6
                v = edge_on_circles(px, w, h, cx, cy, 1.5 * rim, 0.5 * rim, n, turn)
                if v is not None and (best is None or v > best[0]):
                    best = (v, rim, n, turn)
    if best is None:
        return None
    score, rim, n, turn = best
    # How close is the chain's size-and-distance to the best-fitting ones, and how many alternatives are as close?
    grid = [(R / 20 * rim, r / 20 * rim) for R in range(24, 45) for r in range(5, 19)]
    scored = sorted(((edge_on_circles(px, w, h, cx, cy, R, r, n, turn), R, r) for R, r in grid), key=lambda x: (x[0] is None, -(x[0] or 0)))
    scored = [s for s in scored if s[0] is not None]
    top = scored[:5]
    close = lambda R, r: min(max(abs(R - tR) / tR, abs(r - tr) / tr) for _, tR, tr in top)
    off = close(1.5 * rim, 0.5 * rim)
    luck = sum(1 for _, R, r in scored if close(R, r) <= off) / len(scored)
    u = rim / (2 * S3)
    # does the first circle the chain implies fall on a real inner ring?
    inner = min((abs(r / u - 1), r) for r, _ in rings)

    pen = A.Pen(rgb, cx, cy, u, math.radians(turn))
    O = (0, 0)
    pen.circle(O, 1, A.INK, 3); pen.circle(O, S3, A.PALE, 2); pen.circle(O, 2 * S3, A.PURPLE, 3); pen.circle(O, 3 * S3, A.RED, 3)
    for p in A.ring_pts(3 * S3, 0, n):
        pen.circle(p, S3, A.CYAN, 3)
    rgb.save(os.path.join(OUT, f"{name}.jpg"), quality=88)
    return {"centre": [round(cx), round(cy)], "rim_px": rim, "rays": n, "turn_deg": round(turn, 1),
            "off_pct": round(off * 100, 1), "luck_pct": round(luck * 100, 1),
            "best_fits_in_rim_units": [(round(R / rim, 2), round(r / rim, 2)) for _, R, r in top],
            "first_circle_px": round(u, 1), "nearest_inner_ring_px": inner[1], "first_circle_off_pct": round(inner[0] * 100, 1)}


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    cached = {}
    p = os.path.join(HERE, "domes", "ratio", "rings.json")
    if os.path.exists(p):
        cached = {k: tuple(v["centre"]) for k, v in json.load(open(p)).items()}
    report = {}
    for arg in sys.argv[1:]:
        name, rel = arg.split("=")
        report[name] = walk(os.path.join(HERE, "domes", rel), name, cached.get(os.path.basename(rel)))
        print(name, json.dumps(report[name]), flush=True)
    json.dump(report, open(os.path.join(OUT, "chain.json"), "w"), indent=1)
