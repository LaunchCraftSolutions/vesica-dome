"""Find the ring of round niches/arches around a dome the way an eye would (free fit), then ask the chain's question.

The chain says: niche circles have half the rim's radius and touch the rim, so
    distance to niche centres / niche radius = 3      and      touch circle / niche radius = 2.
Here the niches are fitted freely first (no chain involved), and the two ratios are read off afterwards.
"""
import json, math, os, sys
from PIL import Image
import analyze as A
from chain import edge_on_circles

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "domes", "niches")


def fit(path, name, centre=None, dome_px=None):
    rgb = Image.open(path).convert("RGB"); gray = rgb.convert("L")
    w, h = gray.size; px = gray.load(); m = min(w, h)
    cx, cy = centre or A.find_centre(gray)
    reach = max(math.hypot(cx, cy), math.hypot(w - cx, cy), math.hypot(cx, h - cy), math.hypot(w - cx, h - cy))
    lo = dome_px or 0.15 * m  # niches must sit outside this radius (the dome itself)
    best = []
    for n in (4, 8):
        for t in range(4):
            turn = t * 360 / n / 4
            rho = 0.08 * m
            while rho <= 0.5 * m:
                R = lo + rho * 0.9
                while R <= reach:
                    v = edge_on_circles(px, w, h, cx, cy, R, rho, n, turn, pts=90)
                    if v is not None:
                        best.append((v, R, rho, n, turn))
                    R += 0.02 * m
                rho += 0.015 * m
    best.sort(reverse=True)
    v, R, rho, n, turn = best[0]
    pen = A.Pen(rgb, cx, cy, 1.0, math.radians(turn))
    for p in A.ring_pts(R, 0, n):
        pen.circle(p, rho, A.CYAN, 4)
    pen.circle((0, 0), R - rho, A.PURPLE, 3)   # where the fitted niches touch inward
    pen.circle((0, 0), 2 * rho, A.RED, 2)      # where the chain says the rim should be, given that niche size
    pen.circle((0, 0), rho / A.S3 * 1.0, A.INK, 3)  # the first circle the chain implies
    rgb.save(os.path.join(OUT, f"{name}.jpg"), quality=88)
    return {"centre": [round(cx), round(cy)], "rays": n, "turn_deg": turn, "niche_centres_px": round(R), "niche_radius_px": round(rho),
            "centres_over_radius": round(R / rho, 2), "touch_over_radius": round((R - rho) / rho, 2),
            "first_circle_px": round(rho / A.S3)}


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    report = {}
    for arg in sys.argv[1:]:
        name, rest = arg.split("=")
        rel, _, manual = rest.partition("@")
        mm = (manual.split(",") + ["", "", ""])[:3]
        centre = (float(mm[0]), float(mm[1])) if mm[0] and mm[1] else None
        report[name] = fit(os.path.join(HERE, "domes", rel), name, centre, float(mm[2]) if mm[2] else None)
        print(name, json.dumps(report[name]), flush=True)
    json.dump(report, open(os.path.join(OUT, "niches.json"), "w"), indent=1)
