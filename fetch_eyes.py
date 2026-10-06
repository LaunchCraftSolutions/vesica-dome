"""Fetch the eye photos used by the desk's Eye layer, and find the iris in each.

The photos are close-ups of one human eye from Wikimedia Commons, all freely licensed (credits are kept in eyes/_index.json).
Each is fetched 2000 px wide into eyes/eNN.jpg. The iris is then found in each photo: the circle whose left and right edges
stand out most sharply against the white of the eye, with a dark pupil in its middle. The desk lays that circle on the first
circle of the drawing, so the eye needs no placing by hand (it can still be re-placed there with "Place eye").

    python fetch_eyes.py            fetch what is missing, find every iris, write eyes/_index.json and eyes/_check.jpg
"""
import json, math, os, re, sys, time
import requests
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "eyes")
API = "https://commons.wikimedia.org/w/api.php"
UA = {"User-Agent": "DomeDesk/1.0 (private study of dome geometry)"}
WIDTH = 2000

# (Commons title, the name shown on the desk)
PICKED = [
    ("File:Human eye iris 5.jpg", "Blue, dark brow"),
    ("File:Human eye iris 1.jpg", "Green, brow"),
    ("File:Human eye iris 2.jpg", "Blue-grey"),
    ("File:Human eye iris 3.jpg", "Grey, brow"),
    ("File:Eyes tell no lies (Unsplash).jpg", "Bright blue, brow"),
    ("File:Eye Contact (Unsplash).jpg", "Grey-green, brow"),
    ("File:A human male brown eye.jpg", "Brown, close"),
    ("File:Light brown amber eye.JPG", "Amber"),
    ("File:Auge iris braun brown eye human menschlich Bjoern markmann.JPG", "Brown, brow"),
    ("File:The human eye.JPG", "Brown, lashes"),
    ("File:Eye closeup greebrown.jpg", "Green-brown"),
    ("File:Blue eye limbal ring.jpg", "Pale blue"),
    ("File:Grey-Brown eye.jpg", "Grey-brown"),
    ("File:Occhio nocciola.jpg", "Hazel"),
]

# Not eyes: other round things laid under the drawing the same way. The Eye box lists them after the eyes. The circle that goes
# on the first circle is set by hand here, as (cx, cy, r) in shares of the photo's width, because the finder below looks for an
# iris. They are fetched at their own size into eyes/cNN.jpg.
#   Embryo, 8 cells: the circle is the inner edge of the shell (the zona pellucida), the space the cells sit in. In this photo
#   the shell's outer edge is about 1.29 times that, and one cell is about 0.39 of it across its radius.
#   Nuclear pore, face on: the left half of figure 2a of Zhang, Li, Zeng and others, Cell Research 30 (2020), a frog-egg pore
#   averaged from many frozen ones and seen straight on. The picture is cut down to that view (crop, in the original's pixels)
#   and two scraps of lettering inside the cut are painted out (blank). The circle is the central channel, which the figure
#   gives as 49 nm across; its other two rings are 122 nm and 154 nm.
# Each: (Commons title, name on the desk, id, circle, crop or None, blanks, note for the credit)
OTHERS = [
    ("File:Embryo, 8 cells.jpg", "Embryo, 8 cells", "c01", (0.497, 0.3375, 0.189), None, [], ""),
    ("File:PoroNuclear Xenopus2020.jpg", "Nuclear pore, face on", "c02", (0.508, 0.480, 0.158), (46, 0, 451, 390), [(0, 160, 24, 208)], "cropped"),
]


def info(title):
    r = requests.get(API, headers=UA, timeout=40, params={"action": "query", "format": "json", "titles": title, "prop": "imageinfo",
                     "iiprop": "url|size|extmetadata", "iiurlwidth": WIDTH, "iiextmetadatafilter": "LicenseShortName|Artist|LicenseUrl"}).json()
    p = next(iter(r["query"]["pages"].values())); ii = p["imageinfo"][0]; em = ii.get("extmetadata", {})
    clean = lambda k: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", em.get(k, {}).get("value", ""))).strip()
    return {"title": title, "page": ii.get("descriptionurl", ""), "thumb": ii.get("thumburl") or ii["url"], "by": clean("Artist") or "not recorded",
            "licence": clean("LicenseShortName"), "licence_url": clean("LicenseUrl")}


# In a pale eye the pupil's edge can be sharper than the iris's. For these photos the search starts from a larger circle
# (the smallest radius tried, as a share of the photo's width).
LARGER = {"File:Human eye iris 3.jpg": 0.11}


def find_iris(path, rmin=0.05):
    """The iris as (cx, cy, r) in the photo's own pixels, and how clearly it stood out."""
    im = Image.open(path).convert("L"); W, H = im.size; k = 300 / W
    sm = im.resize((300, max(1, round(H * k))), Image.LANCZOS).filter(ImageFilter.GaussianBlur(1.2)); w, h = sm.size; px = sm.load()
    at = lambda x, y: px[min(w - 1, max(0, int(x))), min(h - 1, max(0, int(y)))]
    # Only the sides of the iris are sure to be clear of the lids, so the edge is judged on two arcs, left and right.
    ARC = [math.radians(a) for a in list(range(-28, 29, 7)) + list(range(152, 209, 7))]
    DIRS = [(math.cos(a), math.sin(a)) for a in ARC]
    def score(cx, cy, r):
        edge = 0.0
        for dx, dy in DIRS: edge += max(-25, min(70, at(cx + dx * (r + 2.5), cy + dy * (r + 2.5)) - at(cx + dx * (r - 2.5), cy + dy * (r - 2.5))))   # brighter outside than inside; no one spot counts for too much
        edge /= len(DIRS)
        pupil = sum(at(cx + dx * r * 0.18, cy + dy * r * 0.18) for dx, dy in DIRS) / len(DIRS)
        ring = sum(at(cx + dx * r * 0.75, cy + dy * r * 0.75) for dx, dy in DIRS) / len(DIRS)
        # and a pupil darker than the iris round it; a circle that is as dark at three quarters out as in its middle is the pupil itself
        return edge + 0.35 * max(0.0, ring - pupil) - (40.0 if ring - pupil < 12 else 0.0)
    best = (-1e9, 0, 0, 0)
    for cy in range(int(h * .2), int(h * .8), 3):
        for cx in range(int(w * .2), int(w * .8), 3):
            for r in range(int(w * rmin), int(w * .34), 2):
                s = score(cx, cy, r)
                if s > best[0]: best = (s, cx, cy, r)
    s0, cx0, cy0, r0 = best
    for cy in [cy0 + d * .5 for d in range(-6, 7)]:
        for cx in [cx0 + d * .5 for d in range(-6, 7)]:
            for r in [r0 + d * .5 for d in range(-5, 6)]:
                s = score(cx, cy, r)
                if s > best[0]: best = (s, cx, cy, r)
    s, cx, cy, r = best
    return round(cx / k, 1), round(cy / k, 1), round(r / k, 1), round(s, 1)


def main():
    os.makedirs(OUT, exist_ok=True); index = []
    try: known = {e["title"]: e for e in json.load(open(os.path.join(OUT, "_index.json"), encoding="utf-8"))}
    except Exception: known = {}
    for n, (title, name) in enumerate(PICKED, 1):
        f = os.path.join(OUT, f"e{n:02d}.jpg"); old = known.get(title.replace("File:", ""))
        meta = old if old and os.path.exists(f) else info(title)                                    # credits already on record are not asked for again
        if not os.path.exists(f):
            r = requests.get(meta["thumb"], headers=UA, timeout=120); r.raise_for_status()
            with open(f, "wb") as fh: fh.write(r.content)
            time.sleep(1)
        im = Image.open(f)
        if im.width > WIDTH:                                    # Commons hands back its nearest standard size, which can be larger than asked for
            im = im.convert("RGB").resize((WIDTH, round(im.height * WIDTH / im.width)), Image.LANCZOS); im.save(f, quality=88)
        w, h = Image.open(f).size; cx, cy, r, clear = find_iris(f, LARGER.get(title, 0.05))
        index.append({"id": f"e{n:02d}", "name": name, "file": f"eyes/e{n:02d}.jpg", "w": w, "h": h, "iris": {"cx": cx, "cy": cy, "r": r, "clear": clear},
                      "title": title.replace("File:", ""), "by": meta["by"][:80], "licence": meta["licence"], "licence_url": meta["licence_url"], "page": meta["page"]})
        print(f"e{n:02d} {w}x{h} {os.path.getsize(f)//1024} KB  iris ({cx}, {cy}) r {r}  clear {clear}  {name}")
    for title, name, eid, (fx, fy, fr), crop, blanks, note in OTHERS:
        f = os.path.join(OUT, f"{eid}.jpg"); old = known.get(title.replace("File:", ""))
        meta = old if old and os.path.exists(f) else info(title)
        if not os.path.exists(f):
            r = requests.get(meta["thumb"], headers=UA, timeout=120); r.raise_for_status()
            with open(f, "wb") as fh: fh.write(r.content)
            if crop:
                im = Image.open(f).convert("RGB").crop(crop); d = ImageDraw.Draw(im)
                for box in blanks: d.rectangle(box, fill=(255, 255, 255))
                im.save(f, quality=92)
            time.sleep(1)
        w, h = Image.open(f).size
        index.append({"id": eid, "name": name, "file": f"eyes/{eid}.jpg", "w": w, "h": h, "iris": {"cx": round(fx * w, 1), "cy": round(fy * w, 1), "r": round(fr * w, 1), "clear": None},
                      "title": title.replace("File:", ""), "by": meta["by"][:80], "licence": meta["licence"], "licence_url": meta["licence_url"], "page": meta["page"], "note": note})
        print(f"{eid} {w}x{h} {os.path.getsize(f)//1024} KB  circle set by hand  {name}")
    json.dump(index, open(os.path.join(OUT, "_index.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    # one sheet to check the found circles by eye
    cell = 400; cols = 5; rows = -(-len(index) // cols); sheet = Image.new("RGB", (cols * cell, rows * 290), (17, 17, 17))
    for i, e in enumerate(index):
        im = Image.open(os.path.join(ROOT, e["file"])).convert("RGB"); k = cell / im.width; im = im.resize((cell, round(im.height * k))); d = ImageDraw.Draw(im)
        c = e["iris"]; x, y, r = c["cx"] * k, c["cy"] * k, c["r"] * k
        d.ellipse([x - r, y - r, x + r, y + r], outline=(255, 220, 0), width=2); d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(255, 0, 0)); d.text((6, 4), e["id"], fill=(255, 255, 255))
        sheet.paste(im.crop((0, 0, cell, 290)), ((i % cols) * cell, (i // cols) * 290))
    sheet.save(os.path.join(OUT, "_check.jpg"), quality=85)


if __name__ == "__main__":
    main()
