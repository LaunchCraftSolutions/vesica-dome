"""Put the dome's true middle at the middle of the picture and undo the squash from a tilted or off-centre camera.

A camera that is not straight under the crown turns the dome's rings into ovals. This finds the centre, then the
oval's squash and direction that make the rings line up best, and re-draws the photo so the rings are round and
the centre sits in the middle. It is an approximation (a straight un-squash, not a full perspective correction),
good for modest tilts.
"""
import json, math, os, sys
from PIL import Image
import analyze as A

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "domes", "rectified")


def oval_energy(px, w, h, cx, cy, s, alpha, rmax, nth=90):
    ca, sa = math.cos(alpha), math.sin(alpha)
    trig = [(math.cos(2 * math.pi * k / nth), math.sin(2 * math.pi * k / nth)) for k in range(nth)]
    prof = []
    for r in range(2, rmax):
        tot = n = 0
        for c, sn in trig:
            x = int(cx + r * c * ca - s * r * sn * sa); y = int(cy + r * c * sa + s * r * sn * ca)
            if 0 <= x < w and 0 <= y < h:
                tot += px[x, y]; n += 1
        prof.append(tot / n if n >= 0.6 * nth else None)
    return A.edge_energy(prof)


def rectify(path, name):
    rgb = Image.open(path).convert("RGB"); gray = rgb.convert("L")
    cx, cy = A.find_centre(gray)
    small = gray.copy(); small.thumbnail((240, 240)); k = gray.width / small.width
    px, w, h = small.load(), small.width, small.height
    rmax = int(0.42 * min(w, h))
    x0, y0 = cx / k, cy / k
    base = oval_energy(px, w, h, x0, y0, 1.0, 0.0, rmax)
    best = (base, 1.0, 0.0, x0, y0)
    for s in (0.94, 0.88, 0.82, 0.76, 0.70):
        for a in range(0, 180, 30):
            al = math.radians(a)
            for dx in (-3, 0, 3):
                for dy in (-3, 0, 3):
                    e = oval_energy(px, w, h, x0 + dx, y0 + dy, s, al, rmax)
                    if e > best[0]:
                        best = (e, s, al, x0 + dx, y0 + dy)
    e, s, al, bx, by = best
    if e < 1.08 * base:  # not clearly better than round: leave the shape alone, only centre it
        s, al, bx, by = 1.0, 0.0, x0, y0
    cx, cy = bx * k, by * k
    W, H = rgb.size
    N = int(2 * max(math.hypot(cx, cy), math.hypot(W - cx, cy), math.hypot(cx, H - cy), math.hypot(W - cx, H - cy)) * 0.75)
    ca, sa = math.cos(al), math.sin(al)
    # output point (u, v) about the middle -> input point: stretch by s across the oval's short direction
    m11, m12 = ca * ca + s * sa * sa, ca * sa - s * sa * ca
    m21, m22 = sa * ca - s * ca * sa, sa * sa + s * ca * ca
    c0, f0 = cx - m11 * N / 2 - m12 * N / 2, cy - m21 * N / 2 - m22 * N / 2
    out = rgb.transform((N, N), Image.AFFINE, (m11, m12, c0, m21, m22, f0), resample=Image.BICUBIC)
    out.save(os.path.join(OUT, f"{name}.jpg"), quality=90)
    return {"centre_in_photo": [round(cx), round(cy)], "photo_size": [W, H], "off_middle_px": [round(cx - W / 2), round(cy - H / 2)],
            "squash": s, "squash_direction_deg": round(math.degrees(al)), "size": N}


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, "rectified.json")
    report = json.load(open(p)) if os.path.exists(p) else {}
    for arg in sys.argv[1:]:
        name, rel = arg.split("=")
        report[name] = rectify(os.path.join(HERE, "domes", rel), name)
        print(name, json.dumps(report[name]), flush=True)
        json.dump(report, open(p, "w"), indent=1)
