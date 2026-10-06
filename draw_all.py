"""One procedure, one ratio, every dome.

For each photo: find the dome's true middle, undo the oval squash of an off-axis camera, then draw the same figure
every time: first circle 1, eight-flower ring sqrt(3), rim 2*sqrt(3), next ring 3*sqrt(3), and eight outer circles of
radius sqrt(3) on that ring. The ratio never changes. The only things fitted to the photo are the size (the one that
puts the most of the four rings on measured ring edges) and the turn (the one that puts the outer circles on the
most edge). Every drawing comes with its evidence: how far each ring is from the nearest measured edge.
"""
import json, math, os, random, sys
from PIL import Image
import analyze as A
from chain import edge_on_circles
from rectify import oval_energy
from straighten import straighten, redraw, draw_grid

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "domes", "all")
S3 = A.S3
RINGS = [("first circle", 1.0), ("eight-flower ring", S3), ("rim", 2 * S3), ("next ring out", 3 * S3)]
LAND = 0.05
T8 = math.sqrt(2) - 1  # each star inside the eight leaves a smaller eight this much the size
FULL = [("third band inward", 1 / (3 * S3)), ("thirteen circles: radius of each", A.RHO), ("star in the eight: second inner eight", A.R8 * T8 * T8),
        ("second band inward", 1 / 3), ("first band inward (star's crossings)", 1 / S3), ("star in the eight: first inner eight", A.R8 * T8),
        ("first circle", 1.0), ("cube corners", 2 / S3), ("thirteen circles: outer reach", 2 / S3 + A.RHO), ("eight-flower ring and diamond", S3),
        ("octagon corners", A.R8), ("seed's outer reach", 2.0), ("second square's corners", math.sqrt(6)), ("flower of life's edge and doubled circles' reach", 3.0),
        ("rim (eight-flower's reach)", 2 * S3), ("next ring out (outer circles' centres)", 3 * S3), ("outer circles' far side", 4 * S3)]

# place, photo, where on the line (0 = Dresden, 1 = Edirne, None = off the line), built, note, optional hand-placed centre
DOMES = [
    ("Dresden", "candidates/frauenkirche_0.jpg", 0.0, "1726–43, rebuilt 1994–2005", "", None),
    ("Dresden, academy", "corridor/c117.jpg", 0.0, "1887–94", "Glass dome seen through an eight-sided opening", None),
    ("Prague, St Nicholas", "corridor/c001.jpg", 0.07, "1737–52", "", (640, 540)),
    ("Prague, museum", "corridor/c004.jpg", 0.08, "1885–91", "", None),
    ("Melk", "corridor/c111.jpg", 0.21, "1702–36", "", None),
    ("Vienna, Steinhof", "corridor/c010.jpg", 0.24, "1904–07", "Square gridded shell: no rings", None),
    ("Vienna, museum", "corridor/c014.jpg", 0.25, "1871–91", "", None),
    ("Vienna, Karlskirche", "corridor/c060.jpg", 0.25, "1716–37", "Oval dome", None),
    ("Vienna, Peterskirche", "corridor/c118.jpg", 0.25, "1701–33", "Oval dome", None),
    ("Esztergom", "corridor/c125.jpg", 0.36, "1822–69", "", None),
    ("Esztergom, off-centre photo", "corridor/c020.jpg", 0.36, "1822–69", "The same dome as the plate before, from a photo taken well off to one side and straightened", (628, 625)),
    ("Vác", "corridor/c119.jpg", 0.37, "1761–77", "", None),
    ("Budapest", "corridor/c028.jpg", 0.39, "1851–1905", "", None),
    ("Budapest, parliament", "corridor/c120.jpg", 0.39, "1885–1904", "A sixteen-pointed star vault with no rings; window ring clipped top and bottom by the photo", (658, 400)),
    ("Budapest, Széchenyi bath", "corridor/c121.jpg", 0.39, "1909–13", "", None),
    ("Budapest, Gellért bath", "corridor/c122.jpg", 0.39, "1912–18", "", None),
    ("Eger", "corridor/c123.jpg", 0.41, "1831–36", "", None),
    ("Pécs", "corridor/c124.jpg", 0.43, "1543–46", "Built as the Mosque of Pasha Qasim", None),
    ("Subotica", "corridor/c033.jpg", 0.49, "1901–02", "", (631, 470)),
    ("Szeged, synagogue, second photo", "corridor/c034.jpg", 0.50, "1900–02", "The same dome as the next plate. This photo was filed on Commons as the Votive Church, which it is not.", None),
    ("Szeged, synagogue", "corridor/c035.jpg", 0.50, "1900–02", "", None),
    ("Belgrade, Bajrakli mosque", "corridor/c130.jpg", 0.59, "about 1575", "Plain stone dome", (652, 308)),
    ("Belgrade, St Sava", "corridor/c126.jpg", 0.59, "1935–2004", "", (662, 462)),
    ("Sofia, synagogue", "corridor/c127.jpg", 0.82, "1905–09", "The chandelier hangs over the crown", None),
    ("Sofia, St Nedelya", "corridor/c128.jpg", 0.82, "1856–63, rebuilt 1927–33", "Dark dome", (624, 470)),
    ("Sofia", "corridor/c045.jpg", 0.82, "1882–1912", "Photo taken well off-axis", (530, 440)),
    ("Rila", "corridor/c048.jpg", 0.85, "1834–37", "Painted dome", (640, 530)),
    ("Plovdiv", "corridor/c102.jpg", 0.91, "about 1363–64, rebuilt 15th century", "", None),
    ("Edirne, Old Mosque", "corridor/c129.jpg", 1.0, "1403–14", "One of nine domes", (640, 392)),
    ("Edirne, Üç Şerefeli", "corridor/c052.jpg", 1.0, "1438–47", "Small photo (720 px)", None),
    ("Edirne, Selimiye", "candidates/selimiye_0.jpg", 1.0, "1568–75", "", None),
    ("London", "sample/d000.jpg", None, "1675–1710", "", None),
    ("St Petersburg", "sample/d024.jpg", None, "1818–58", "", None),
    ("Rome", "candidates/pantheon_0.jpg", None, "about 113–125", "", None),
    ("Isfahan", "candidates/lotfollah_0.jpg", None, "1603–19", "", (480, 324)),
    ("Istanbul", "candidates/hagia_sophia_0.jpg", None, "527–536", "", None),
]
# Photos taken from well off to one side, straightened by name (straighten.py): each ring is slid back onto the crown,
# as walking to the middle of the floor would do. Tried on all 21 on 2026-10-03: it made the rings about seven times
# sharper here and was worse or wrong on the rest, so it is not applied automatically.
STRAIGHTEN = {"Esztergom, off-centre photo"}
COORDS = {"Belgrade, Bajrakli mosque": (44.8222, 20.4575), "Belgrade, St Sava": (44.7981, 20.4685),
          "Sofia, synagogue": (42.7000, 23.3211), "Sofia, St Nedelya": (42.6967, 23.3214),
          "Edirne, Old Mosque": (41.6767, 26.5557),
          "Dresden, academy": (51.0528, 13.7425), "Vienna, Steinhof": (48.2105, 16.2788), "Vienna, Peterskirche": (48.2093, 16.3695),
          "Esztergom, off-centre photo": (47.7990, 18.7366), "Vác": (47.7759, 19.1314), "Budapest, parliament": (47.5069, 19.0456),
          "Budapest, Széchenyi bath": (47.5186, 19.0819), "Budapest, Gellért bath": (47.4837, 19.0510), "Eger": (47.8994, 20.3733), "Pécs": (46.0769, 18.2281),
          "Dresden": (51.0520, 13.7413), "Prague, St Nicholas": (50.0880, 14.4032), "Prague, museum": (50.0789, 14.4309), "Melk": (48.2281, 15.3331),
          "Vienna, museum": (48.2038, 16.3616), "Vienna, Karlskirche": (48.1983, 16.3719), "Esztergom": (47.7990, 18.7366), "Budapest": (47.5008, 19.0540),
          "Subotica": (46.1022, 19.6628), "Szeged, synagogue, second photo": (46.2545, 20.1406), "Szeged, synagogue": (46.2545, 20.1406), "Sofia": (42.6958, 23.3328),
          "Rila": (42.1335, 23.3402), "Plovdiv": (42.1479, 24.7480), "Edirne, Üç Şerefeli": (41.6783, 26.5535), "Edirne, Selimiye": (41.6781, 26.5594),
          "London": (51.5137, -0.0983), "St Petersburg": (59.9342, 30.3063), "Rome": (41.8986, 12.4769), "Isfahan": (32.6574, 51.6788), "Istanbul": (41.0028, 28.9722)}

# The wider collection (fetch_world.py): the same procedure on domes from the rest of the world. None are on the line.
# Their middles are found by turning the picture on itself (fetch_world.middle_by_turning) unless one was placed by hand, and a
# dome can be marked as not to be un-squashed (a star vault has no rings for the oval test to read).
TURNED, ROUND_AS_IS = set(), set()
_world = os.path.join(HERE, "domes", "world.json")
if os.path.exists(_world):
    for w in json.load(open(_world, encoding="utf-8")):
        mid = w.get("hand") or w.get("turned")
        DOMES.append((w["place"], w["photo"], None, w["built"], w["note"], tuple(mid) if mid else None)); COORDS[w["place"]] = (w["lat"], w["lon"])
        if w.get("turned") and not w.get("hand"):
            TURNED.add(w["place"])
        if w.get("squash") is False:
            ROUND_AS_IS.add(w["place"])


def true_middle(gray):
    """A dome looks the same turned half-way round its middle, and its rings line up there. Use both."""
    small = gray.copy(); small.thumbnail((96, 96)); k = gray.width / small.width
    px, w, h = small.load(), small.width, small.height
    R = int(0.33 * min(w, h)); rmax = int(0.4 * min(w, h))
    pts = [(dx, dy) for dx in range(-R, R + 1, 2) for dy in range(0, R + 1, 2) if 9 <= dx * dx + dy * dy <= R * R]
    best = None
    for x in range(int(.22 * w), int(.78 * w)):
        for y in range(int(.22 * h), int(.78 * h)):
            tot = n = 0
            for dx, dy in pts:
                x1, y1, x2, y2 = x + dx, y + dy, x - dx, y - dy
                if 0 <= x1 < w and 0 <= y1 < h and 0 <= x2 < w and 0 <= y2 < h:
                    tot += abs(px[x1, y1] - px[x2, y2]); n += 1
            if n < 0.5 * len(pts):
                continue
            score = A.edge_energy(A.profile(px, w, h, x, y, rmax, 60)) / (4.0 + tot / n)
            if best is None or score > best[0]:
                best = (score, x, y)
    cx, cy = best[1] * k, best[2] * k
    for size, span, nth in ((240, 4, 120), (None, 4, 180)):  # sharpen on the rings alone
        im = gray if size is None else gray.copy()
        if size is not None:
            im.thumbnail((size, size))
        kk = gray.width / im.width; px, w, h = im.load(), im.width, im.height
        rm = int(0.42 * min(w, h)); x0, y0 = int(round(cx / kk)), int(round(cy / kk)); b = None
        for x in range(x0 - span, x0 + span + 1):
            for y in range(y0 - span, y0 + span + 1):
                e = A.edge_energy(A.profile(px, w, h, x, y, rm, nth))
                if b is None or e > b[0]:
                    b = (e, x, y)
        cx, cy = b[1] * kk, b[2] * kk
    return cx, cy


def unsquash(rgb, gray, cx, cy, try_oval=True):
    small = gray.copy(); small.thumbnail((240, 240)); k = gray.width / small.width
    px, w, h = small.load(), small.width, small.height
    rmax = int(0.42 * min(w, h)); x0, y0 = cx / k, cy / k
    base = oval_energy(px, w, h, x0, y0, 1.0, 0.0, rmax); best = (base, 1.0, 0.0)
    for s in (0.94, 0.88, 0.82, 0.76, 0.70):
        for a in range(0, 180, 30):
            e = oval_energy(px, w, h, x0, y0, s, math.radians(a), rmax)
            if e > best[0]:
                best = (e, s, math.radians(a))
    e, s, al = best
    if e < 1.08 * base or not try_oval:
        s, al = 1.0, 0.0
    W, H = rgb.size
    N = int(2 * max(math.hypot(cx, cy), math.hypot(W - cx, cy), math.hypot(cx, H - cy), math.hypot(W - cx, H - cy)) * 0.75)
    ca, sa = math.cos(al), math.sin(al)
    m11, m12, m21, m22 = ca * ca + s * sa * sa, ca * sa - s * sa * ca, sa * ca - s * ca * sa, sa * sa + s * ca * ca
    out = rgb.transform((N, N), Image.AFFINE, (m11, m12, cx - (m11 + m12) * N / 2, m21, m22, cy - (m21 + m22) * N / 2), resample=Image.BICUBIC)
    return out, s, round(math.degrees(al))


def landings(u, radii):
    out = []
    for name, m in RINGS:
        near = min(radii, key=lambda r: abs(r / (u * m) - 1))
        out.append((name, m, u * m, near, abs(near / (u * m) - 1)))
    return out


def draw(place, rel, along, built, note, hand):
    rgb0 = Image.open(os.path.join(HERE, "domes", rel)).convert("RGB"); gray0 = rgb0.convert("L")
    W, H = rgb0.size
    cx, cy = hand or true_middle(gray0)
    st = None
    if place in STRAIGHTEN:
        meta_path = os.path.join(OUT, "photo_meta.json")
        meta = json.load(open(meta_path, encoding="utf-8")).get(rel) if os.path.exists(meta_path) else None
        got = straighten(rgb0, gray0, meta, seed=(cx, cy), dim=False)   # measured on the plain re-drawing
    if place in STRAIGHTEN and got:
        rgb, st, model = got; squash, sq_dir = 1.0, 0; cx, cy = model.crown(); hand = None
        shown = redraw(rgb0, model)   # shown with the parts the camera could not see greyed down
    else:
        rgb, squash, sq_dir = unsquash(rgb0, gray0, cx, cy, try_oval=place not in ROUND_AS_IS); shown = rgb
    gray = rgb.convert("L"); N = rgb.width; px = gray.load(); c = N / 2
    frame = min(cx, cy, W - cx, H - cy)  # how far the photo reaches from the middle before its nearest edge
    rmin = int(0.04 * min(W, H))   # nearer the middle than this, a few pixels of noise swamp any ring
    rings = A.find_rings(A.profile(px, N, N, c, c, int(0.7 * N), 720), rmin=rmin, keep=14)
    radii = [r for r, _ in rings]; strength = dict(rings)
    lo, hi = 0.35 * frame / (2 * S3), 1.6 * frame / (2 * S3)   # the rim must be a real part of the picture, not a speck
    cands = sorted({round(r / m, 2) for r in radii for _, m in RINGS if lo <= r / m <= hi})
    score = lambda u: (sum(1 for *_, off in landings(u, radii) if off <= LAND), sum(strength[n] for _, _, _, n, off in landings(u, radii) if off <= LAND))
    u = max(cands, key=score) if cands else frame / (2 * S3) * 0.9
    land = landings(u, radii); k = sum(1 for *_, off in land if off <= LAND)
    rnd = random.Random(7)
    p = sum(1 for _ in range(1500) if sum(1 for *_, off in landings(math.exp(rnd.uniform(math.log(lo), math.log(hi))), radii) if off <= LAND) >= k) / 1500
    luck = 1 - (1 - p) ** max(1, len(cands))
    best = None
    for t in range(12):
        turn = t * 45 / 12
        v = edge_on_circles(px, N, N, c, c, 3 * S3 * u, S3 * u, 8, turn)
        if v is not None and (best is None or v > best[0]):
            best = (v, turn)
    turn = best[1] if best else 0.0
    # Every radius the full construction produces, measured against the photo.
    prof = A.profile(px, N, N, c, c, int(0.7 * N), 360)
    reach = max((i + 1 for i, v in enumerate(prof) if v is not None), default=0)   # furthest ring still mostly inside the photo
    full = []
    for name, m in FULL:
        d = u * m
        if d > reach or d < rmin:   # cannot be checked: off the photo, or smaller than the smallest ring edge this photo can show
            full.append({"ring": name, "times_first_circle": round(m, 3), "drawn_px": round(d), "nearest_edge_px": None, "off_pct": None, "landed": False,
                         "why": "outside the photo" if d > reach else "too small to measure in this photo"})
        else:
            e = min(radii, key=lambda r: abs(r / d - 1)); off = abs(e / d - 1)
            full.append({"ring": name, "times_first_circle": round(m, 3), "drawn_px": round(d), "nearest_edge_px": e, "off_pct": round(off * 100, 1), "landed": off <= LAND})
    bands = {"first circle to eight-flower ring": (u, S3 * u), "eight-flower ring to rim": (S3 * u, 2 * S3 * u), "rim to next ring out": (2 * S3 * u, 3 * S3 * u)}
    fold = {k: [(n, pw) for n, pw, _ in A.folds(px, N, N, c, c, r0, min(r1, reach))] if r0 + 6 < min(r1, reach) else [] for k, (r0, r1) in bands.items()}

    slug = "".join(ch if ch.isalnum() else "_" for ch in place.lower())
    view = shown.copy(); view.thumbnail((1100, 1100)); view.save(os.path.join(OUT, slug + "_photo.jpg"), quality=86)   # straightened photo, nothing drawn
    if st:   # the grid on the photo as taken: the rings found and lines down the dome from the crown
        g = draw_grid(rgb0, model); g.thumbnail((1100, 1100)); g.save(os.path.join(OUT, slug + "_grid.jpg"), quality=86)
    O = (0, 0)

    def chain(pen, wd):
        pen.circle(O, 1, A.INK, wd); pen.circle(O, S3, A.PALE, wd); pen.circle(O, 2 * S3, A.PURPLE, wd); pen.circle(O, 3 * S3, A.RED, wd)
        for q in A.ring_pts(2 * S3, 0, 8):
            pen.circle(q, S3, A.PALE, max(1, wd // 2))
        for q in A.ring_pts(3 * S3, 0, 8):
            pen.circle(q, S3, A.CYAN, wd)

    wd = max(3, N // 300)
    for tag, stages in (("six", (A.draw_six,)), ("eight", (A.draw_eight,)), ("chain", (lambda pen: chain(pen, wd),)),
                        ("", (A.draw_six, A.draw_eight, lambda pen: chain(pen, wd)))):
        im = shown.copy(); pen = A.Pen(im, c, c, u, math.radians(turn))
        for fn in stages:
            fn(pen)
        im.thumbnail((1100, 1100)); im.save(os.path.join(OUT, slug + ("_" + tag if tag else "") + ".jpg"), quality=86)
    lat, lon = COORDS[place]
    return {"place": place, "slug": slug, "photo": rel, "along": along, "built": built, "note": note, "lat": lat, "lon": lon,
            "photo_size": [W, H], "middle_in_photo": [round(cx), round(cy)], "straightened_px": N, "view_px": view.width, "first_circle_view_px": round(u * view.width / N, 2),
            "placed_by_hand": bool(hand) and place not in TURNED, "off_middle_px": [round(cx - W / 2), round(cy - H / 2)], "squash": squash, "squash_direction_deg": sq_dir,
            "first_circle_px": round(u, 1), "turn_deg": round(turn, 1), "landed": k, "luck": round(luck, 3), "sizes_tried": len(cands),
            "rings": [{"ring": n, "times_first_circle": round(m, 3), "drawn_px": round(d), "nearest_edge_px": e, "off_pct": round(off * 100, 1), "landed": off <= LAND}
                      for n, m, d, e, off in land],
            "full": full, "measured_edges_px": radii, "measured_edges_times_first_circle": [round(r / u, 2) for r in radii], "reach_px": reach, "smallest_measurable_px": rmin, "folds": fold,
            "outer_circles_in_frame": best is not None,
            "straightened": None if not st else {"rings": len(st["rings"]), "drift_px": round(st["drift_px"]), "outer_ring_px": round(st["outer_ring_px"]),
                                                 "tipped_deg": round(math.hypot(*st["tilt_deg"])), "unseen_pct": round(100 * st["unseen_share"], 1),
                                                 "crown_seen": st["crown_seen"], "lens_from_photo": bool((meta or {}).get("focal35_mm"))}}


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "results.json")
    done = {r["place"]: r for r in (json.load(open(path, encoding="utf-8")) if os.path.exists(path) else [])}
    only = set(sys.argv[1:])
    for d in DOMES:
        if only and d[0] not in only:
            continue
        if not only and d[0] in done:
            continue
        try:
            done[d[0]] = draw(*d)
            r = done[d[0]]
            print(r["place"].encode("ascii", "replace").decode(), "landed", r["landed"], "of 4", [x["off_pct"] for x in r["rings"]], "luck", r["luck"],
                  "off-middle", r["off_middle_px"], "squash", r["squash"], flush=True)
        except Exception as e:
            print("FAILED", d[0].encode("ascii", "replace").decode(), repr(e), flush=True)
        json.dump([done[x[0]] for x in DOMES if x[0] in done], open(path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
