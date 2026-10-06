"""Find and pull photos for the domes in world_list.py: straight-up views from Wikimedia Commons, open licences only.

  python fetch_world.py find     search Commons for each dome, keep small copies of what comes back in domes/found/ (not kept in the
                                 repository) and make numbered sheets of the most dome-like ones for picking by eye
  python fetch_world.py where    look up where each building is (Wikidata, by way of its English Wikipedia article)
  python fetch_world.py pull     fetch the photos named in domes/world_picks.json at 1280 px into domes/world/, with their credits
                                 in domes/world/_index.json and their camera details in domes/all/photo_meta.json, and write
                                 domes/world.json: the list draw_all.py and build_map.py read

Only photos under a Creative Commons Attribution or Attribution-ShareAlike licence, CC0 or the public domain are considered.
A photo is "dome-like" here if it looks much the same turned a quarter and a half turn about some point near its middle: that
is what a dome seen from straight below does. The score only puts the likeliest photos first on the sheets. The picking is by eye.
"""
import json, os, re, sys, time
from concurrent.futures import ThreadPoolExecutor
import requests
from PIL import Image, ImageChops, ImageDraw, ImageStat
from world_list import domes

HERE = os.path.dirname(os.path.abspath(__file__))
FOUND = os.path.join(HERE, "domes", "found"); WORLD = os.path.join(HERE, "domes", "world")
API = "https://commons.wikimedia.org/w/api.php"
UA = {"User-Agent": "VesicaDome/1.0 (https://github.com/LaunchCraftSolutions/vesica-dome)"}
OPEN = re.compile(r"^(CC BY(-SA)? \d|CC0|Public domain|PDM)", re.I)
# Buildings whose English Wikipedia article gives no position, or that have no article: placed by hand (latitude, longitude, country).
BY_HAND = {"333 Collins Street": (-37.8163, 144.9617, "Australia"), "Centcelles": (41.1561, 1.2289, "Spain"),
           "Church of St. Francis of Assisi (Prague)": (50.0864, 14.4142, "Czech Republic"), "Church of the Society of Jesus (Cusco)": (-13.5175, -71.9779, "Peru"),
           "Galeries Lafayette Haussmann": (48.8737, 2.3320, "France"), "Hoshang Shah's Tomb": (22.3353, 75.4158, "India"), "Hyōkeikan": (35.7186, 139.7748, "Japan"),
           "Koski Mehmed Pasha Mosque": (43.3397, 17.8147, "Bosnia and Herzegovina"), "Mosque of Qaitbay": (30.0439, 31.2750, "Egypt"),
           "Rotunda (Thessaloniki)": (40.6333, 22.9528, "Greece"), "St. Ludwig, Darmstadt": (49.8681, 8.6508, "Germany")}
strip = lambda s: re.sub("<[^>]+>", "", s or "").strip()
asc = lambda s: s.encode("ascii", "replace").decode()


def get(url, **kw):
    for wait in (0, 3, 10, 30):
        time.sleep(wait)
        try:
            r = requests.get(url, headers=UA, timeout=60, **kw)
            if r.status_code == 200:
                return r
            if r.status_code not in (429, 500, 502, 503):
                return None
        except requests.RequestException:
            pass
    return None


def search(query, limit=14, width=330):
    params = {"action": "query", "format": "json", "generator": "search", "gsrnamespace": 6, "gsrsearch": query + " filetype:bitmap", "gsrlimit": limit,
              "prop": "imageinfo", "iiprop": "url|size|extmetadata", "iiurlwidth": width}
    r = get(API, params=params)
    pages = (r.json().get("query", {}).get("pages", {}) if r else {})
    hits = []
    for p in sorted(pages.values(), key=lambda p: p.get("index", 0)):
        ii = (p.get("imageinfo") or [{}])[0]; ext = ii.get("extmetadata", {}); lic = ext.get("LicenseShortName", {}).get("value", "")
        if not ii.get("thumburl") or not OPEN.match(lic) or min(ii.get("width", 0), ii.get("height", 0)) < 900:
            continue
        hits.append({"title": p["title"], "thumb": ii["thumburl"], "page": ii["descriptionurl"], "w": ii["width"], "h": ii["height"],
                     "license": lic, "artist": strip(ext.get("Artist", {}).get("value", ""))[:80]})
    return hits


def dome_like(im):
    """0 to 1: how nearly the picture is its own quarter and half turn about the best point near its middle."""
    g = im.convert("L"); g.thumbnail((128, 128)); w, h = g.size; r = int(min(w, h) * 0.36); best = 0.0
    if r < 12:
        return 0.0
    mask = Image.new("L", (2 * r, 2 * r), 0); ImageDraw.Draw(mask).ellipse((0, 0, 2 * r - 1, 2 * r - 1), fill=255)
    for i in range(7):
        for j in range(7):
            cx = r + (w - 2 * r) * i / 6; cy = r + (h - 2 * r) * j / 6
            c = g.crop((int(cx - r), int(cy - r), int(cx - r) + 2 * r, int(cy - r) + 2 * r)); sd = ImageStat.Stat(c, mask).stddev[0]
            if sd < 8:
                continue
            d = sum(ImageStat.Stat(ImageChops.difference(c, c.rotate(a)), mask).mean[0] for a in (90, 180)) / 2
            best = max(best, 1 - d / (1.13 * sd))
    return round(max(0.0, best), 3)


def middle_by_turning(im):
    """Where the dome's middle is in a photo taken from straight below: the point about which the picture best matches itself
    turned a half turn, and a quarter or a sixth. Each point is tried with the widest disc that fits in the photo about it, and
    a point that only allows a small disc has to match that much better, since these photos were picked for having the dome
    near their middle. Coarse first, then to the nearest pixel or two. Gives (x, y) in the photo's own pixels."""
    g0 = im.convert("L"); W, H = g0.size; whole = ImageStat.Stat(g0).stddev[0] or 1.0; masks = {}

    def score(g, cx, cy, full):
        w, h = g.size; r = int(min(cx, cy, w - cx, h - cy, full))
        if r < 0.35 * full:
            return None
        if r not in masks:
            masks[r] = Image.new("L", (2 * r, 2 * r), 0); ImageDraw.Draw(masks[r]).ellipse((0, 0, 2 * r - 1, 2 * r - 1), fill=255)
        x0, y0 = int(round(cx - r)), int(round(cy - r)); c = g.crop((x0, y0, x0 + 2 * r, y0 + 2 * r)); sd = ImageStat.Stat(c, masks[r]).stddev[0]
        if sd < 0.5 * whole:   # a plain patch matches itself however it is turned
            return None
        off = lambda a: ImageStat.Stat(ImageChops.difference(c, c.rotate(a, resample=Image.BILINEAR)), masks[r]).mean[0]
        return (off(180) + 0.5 * min(off(90), off(60))) / sd + 0.45 * (1 - r / full)

    def best_at(size, centres):
        g = g0.copy(); g.thumbnail((size, size)); k = W / g.width; w, h = g.size; full = 0.46 * min(w, h); top = None; masks.clear()
        for cx, cy in centres(w, h, k):
            s = score(g, cx, cy, full)
            if s is not None and (top is None or s < top[0]):
                top = (s, cx * k, cy * k)
        return top
    first = best_at(128, lambda w, h, k: [(x, y) for x in range(int(.2 * w), int(.8 * w) + 1, 2) for y in range(int(.2 * h), int(.8 * h) + 1, 2)])
    if not first:
        return None
    for size, span in ((384, 5), (800, 4)):
        nxt = best_at(size, lambda w, h, k, f=first, s=span: [(round(f[1] / k) + i, round(f[2] / k) + j) for i in range(-s, s + 1) for j in range(-s, s + 1)])
        first = nxt or first
    return [round(first[1]), round(first[2])]


def find(per_sheet=6, show=4):
    os.makedirs(os.path.join(FOUND, "sheets"), exist_ok=True)
    rec_path = os.path.join(FOUND, "_found.json"); found = json.load(open(rec_path, encoding="utf-8")) if os.path.exists(rec_path) else {}
    todo = [d for d in domes() if d["place"] not in found]
    for k, d in enumerate(todo):
        hits = search(d["query"]); time.sleep(0.4)
        if len(hits) < 4:   # too few: try the building's name alone with plainer words
            seen = {h["title"] for h in hits}; hits += [h for h in search(d["wiki"] + " dome ceiling interior") if h["title"] not in seen]; time.sleep(0.4)
        n = len(found)

        def fetch(ih):
            i, h = ih; path = os.path.join(FOUND, f"f{n:03d}_{i:02d}.jpg"); r = get(h["thumb"])
            if not r:
                return None
            try:
                open(path, "wb").write(r.content); im = Image.open(path); im.load(); h["file"] = os.path.basename(path); h["score"] = dome_like(im); return h
            except Exception:
                return None
        with ThreadPoolExecutor(3) as ex:
            got = [h for h in ex.map(fetch, enumerate(hits)) if h]
        found[d["place"]] = sorted(got, key=lambda h: -h["score"])
        json.dump(found, open(rec_path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        print(f"{k + 1}/{len(todo)}", asc(d["place"]), len(got), "photos; best", [h["score"] for h in found[d["place"]][:3]], flush=True)
    sheets(per_sheet, show)


def again():
    """A second look for the domes nothing has been picked for: plainer words, and more of what comes back."""
    picks_path = os.path.join(HERE, "domes", "world_picks.json"); picked = set(json.load(open(picks_path, encoding="utf-8"))) if os.path.exists(picks_path) else set()
    first = json.load(open(os.path.join(FOUND, "_found.json"), encoding="utf-8"))
    rec_path = os.path.join(FOUND, "_found2.json"); found = json.load(open(rec_path, encoding="utf-8")) if os.path.exists(rec_path) else {}
    todo = [d for d in domes() if d["place"] not in picked and d["place"] not in found]
    for k, d in enumerate(todo):
        seen = {h["title"] for h in first.get(d["place"], [])}; hits = []; name = re.sub(r"\s*\([^)]*\)$", "", d["wiki"])
        for q in (name + " dome", name + " cupola", name + " ceiling", name + " interior"):
            for h in search(q, limit=20):
                if h["title"] not in seen:
                    seen.add(h["title"]); hits.append(h)
            time.sleep(0.4)
        n = len(found)

        def fetch(ih):
            i, h = ih; path = os.path.join(FOUND, f"g{n:03d}_{i:02d}.jpg"); r = get(h["thumb"])
            if not r:
                return None
            try:
                open(path, "wb").write(r.content); im = Image.open(path); im.load(); h["file"] = os.path.basename(path); h["score"] = dome_like(im); return h
            except Exception:
                return None
        with ThreadPoolExecutor(3) as ex:
            got = [h for h in ex.map(fetch, enumerate(hits[:40])) if h]
        found[d["place"]] = sorted(got, key=lambda h: -h["score"])
        json.dump(found, open(rec_path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        print(f"{k + 1}/{len(todo)}", asc(d["place"]), len(got), "more photos; best", [h["score"] for h in found[d["place"]][:3]], flush=True)
    sheets(6, 4, "_found2.json", "again", "A", "_key2.json", skip=picked)


def sheets(per_sheet=6, show=4, record="_found.json", stem="sheet", prefix="", keyfile="_key.json", skip=()):
    """A row per dome, its likeliest photos, each with the number to pick it by."""
    found = json.load(open(os.path.join(FOUND, record), encoding="utf-8"))
    places = [d["place"] for d in domes() if found.get(d["place"]) and d["place"] not in skip]; T = 300; key = {}
    for s in range(0, len(places), per_sheet):
        sheet = Image.new("RGB", (T * show, (T + 26) * per_sheet), (20, 20, 24)); dr = ImageDraw.Draw(sheet)
        for row, place in enumerate(places[s:s + per_sheet]):
            y = row * (T + 26); num = s + row
            dr.text((6, y + 3), f"{prefix}{num}  {asc(place)}", fill=(255, 230, 150), font_size=18)
            for col, h in enumerate(found[place][:show]):
                try:
                    im = Image.open(os.path.join(FOUND, h["file"])).convert("RGB")
                except Exception:
                    continue
                im.thumbnail((T - 4, T - 4)); x = col * T
                sheet.paste(im, (x + (T - im.width) // 2, y + 26 + (T - im.height) // 2))
                dr.rectangle((x, y + 26, x + 104, y + 46), fill=(0, 0, 0)); dr.text((x + 3, y + 27), f"{prefix}{num}{'abcd'[col]} {h['score']:.2f}", fill=(255, 255, 0), font_size=16)
                key[f"{prefix}{num}{'abcd'[col]}"] = {"place": place, "title": h["title"]}
        sheet.save(os.path.join(FOUND, "sheets", f"{stem}_{s // per_sheet:02d}.jpg"), quality=80)
    json.dump(key, open(os.path.join(FOUND, keyfile), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(len(places), "domes on", (len(places) + per_sheet - 1) // per_sheet, "sheets")


def where():
    """Latitude, longitude and country for each building, from Wikidata by way of its English Wikipedia article."""
    path = os.path.join(HERE, "domes", "world_places.json"); got = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
    titles = sorted({d["wiki"] for d in domes()} - set(got)); WD = "https://www.wikidata.org/w/api.php"
    for i in range(0, len(titles), 40):
        part = titles[i:i + 40]
        r = get("https://en.wikipedia.org/w/api.php", params={"action": "query", "format": "json", "redirects": 1, "prop": "pageprops|coordinates", "ppprop": "wikibase_item", "colimit": "max", "titles": "|".join(part)})
        q = r.json()["query"]; back = {x["to"]: x["from"] for x in q.get("redirects", [])}; back.update({x["to"]: back.get(x["from"], x["from"]) for x in q.get("normalized", [])})
        for p in q["pages"].values():
            t = back.get(p["title"], p["title"]); c = (p.get("coordinates") or [{}])[0]
            got[t] = {"article": p["title"], "missing": "missing" in p, "item": p.get("pageprops", {}).get("wikibase_item"), "lat": c.get("lat"), "lon": c.get("lon")}
        time.sleep(0.5)
    items = sorted({v["item"] for v in got.values() if v.get("item") and "country" not in v})
    country = {}
    for i in range(0, len(items), 45):
        r = get(WD, params={"action": "wbgetentities", "format": "json", "ids": "|".join(items[i:i + 45]), "props": "claims"})
        for qid, e in r.json().get("entities", {}).items():
            cl = e.get("claims", {})
            def first(prop):
                for s in cl.get(prop, []):
                    v = s.get("mainsnak", {}).get("datavalue", {}).get("value")
                    if v:
                        return v
            c = first("P17"); co = first("P625")
            country[qid] = {"country_item": c.get("id") if isinstance(c, dict) else None, "lat": co.get("latitude") if isinstance(co, dict) else None, "lon": co.get("longitude") if isinstance(co, dict) else None}
        time.sleep(0.5)
    cids = sorted({v["country_item"] for v in country.values() if v["country_item"]}); names = {}
    for i in range(0, len(cids), 45):
        r = get(WD, params={"action": "wbgetentities", "format": "json", "ids": "|".join(cids[i:i + 45]), "props": "labels", "languages": "en"})
        for qid, e in r.json().get("entities", {}).items():
            names[qid] = e.get("labels", {}).get("en", {}).get("value")
    for v in got.values():
        c = country.get(v.get("item"))
        if c:
            v["country"] = names.get(c["country_item"]) or v.get("country")
            if v.get("lat") is None and c["lat"] is not None:
                v["lat"], v["lon"] = c["lat"], c["lon"]
    for t, (lat, lon, c) in BY_HAND.items():
        got[t] = dict(got.get(t, {}), lat=lat, lon=lon, country=c, by_hand=True)
    json.dump(got, open(path, "w", encoding="utf-8"), indent=1, ensure_ascii=False, sort_keys=True)
    lost = [t for t in {d["wiki"] for d in domes()} if got.get(t, {}).get("lat") is None]
    print(len(got), "articles looked up;", len(lost), "without a place:", [asc(t) for t in sorted(lost)])


def num(v):
    try:
        return round(float(v), 1)
    except (TypeError, ValueError):
        return None


def pull(width=1280):
    os.makedirs(WORLD, exist_ok=True)
    picks = json.load(open(os.path.join(HERE, "domes", "world_picks.json"), encoding="utf-8"))
    places = json.load(open(os.path.join(HERE, "domes", "world_places.json"), encoding="utf-8"))
    idx_path = os.path.join(WORLD, "_index.json"); meta_path = os.path.join(HERE, "domes", "all", "photo_meta.json")
    index = json.load(open(idx_path, encoding="utf-8")) if os.path.exists(idx_path) else []; meta = json.load(open(meta_path, encoding="utf-8"))
    n = 1 + max([int(h["file"][1:4]) for h in index] or [0]); by_place = {d["place"]: d for d in domes()}
    for place, pick in picks.items():
        title = pick["title"]; old = next((h for h in index if h["place"] == place), None)
        if old and old["title"] == title and "world/" + old["file"] in meta:
            continue
        r = get(API, params={"action": "query", "format": "json", "titles": title, "prop": "imageinfo", "iiprop": "url|size|extmetadata|metadata", "iiurlwidth": width})
        page = next(iter(r.json()["query"]["pages"].values())); ii = page["imageinfo"][0]; ext = ii.get("extmetadata", {}); exif = {m["name"]: m["value"] for m in ii.get("metadata") or []}
        lic = ext.get("LicenseShortName", {}).get("value", "")
        if not OPEN.match(lic):
            print("SKIPPED, licence not open:", asc(place), lic); continue
        path = os.path.join(WORLD, old["file"] if old else f"w{n:03d}.jpg"); img = get(ii["thumburl"])
        if not img:
            print("COULD NOT FETCH", asc(place)); continue
        open(path, "wb").write(img.content); Image.open(path).verify()
        hit = {"title": page["title"], "thumb": ii["thumburl"], "page": ii["descriptionurl"], "w": ii["width"], "h": ii["height"], "license": lic,
               "artist": strip(ext.get("Artist", {}).get("value", ""))[:80], "file": os.path.basename(path), "place": place, "picked_by_eye": True}
        if old:
            index[index.index(old)] = hit
        else:
            index.append(hit); n += 1
        f35 = num(exif.get("FocalLengthIn35mmFilm"))
        meta["world/" + hit["file"]] = {
            "taken": (str(exif.get("DateTimeOriginal") or "") or strip(ext.get("DateTimeOriginal", {}).get("value", "")))[:10].replace(":", "-") or None,
            "make": exif.get("Make"), "model": exif.get("Model"), "lens": exif.get("LensModel"), "focal_mm": num(exif.get("FocalLength")),
            "focal35_mm": int(f35) if f35 else None, "software": exif.get("Software"), "original_size": [ii["width"], ii["height"]],
            "description": strip(ext.get("ImageDescription", {}).get("value", ""))[:200], "artist": hit["artist"], "license": lic}
        json.dump(index, open(idx_path, "w", encoding="utf-8"), indent=1, ensure_ascii=False); json.dump(meta, open(meta_path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        print(hit["file"], Image.open(path).size, asc(place), "|", lic, "|", asc(hit["artist"]), flush=True); time.sleep(0.6)
    # a photo whose dome is no longer picked is taken out, with its credit and its camera details
    for h in [h for h in index if h["place"] not in picks]:
        index.remove(h); meta.pop("world/" + h["file"], None)
        if os.path.exists(os.path.join(WORLD, h["file"])):
            os.remove(os.path.join(WORLD, h["file"]))
    # where Commons gives no author in the field meant for it, the name written on the file's own page is given with the pick
    for h in index:
        if picks[h["place"]].get("artist"):
            h["artist"] = picks[h["place"]]["artist"]; meta["world/" + h["file"]]["artist"] = h["artist"]
    json.dump(meta, open(meta_path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    # the list the drawing and the site are made from
    out = []
    for h in index:
        d = by_place.get(h["place"]); pl = places.get(d["wiki"], {}) if d else {}; pick = picks.get(h["place"], {})
        if not d or h["place"] not in picks or pl.get("lat") is None:
            continue
        town = d["place"].split(",")[0]; name = re.sub(r"\s*\([^)]*\)$", "", d["wiki"])
        name = name[:-len(", " + town)] if name.endswith(", " + town) else name
        # the middle: by hand if one was given; otherwise by turning the picture on itself, unless the pick asks for the ring-finder ("middle": "rings")
        if "turned" not in h and not pick.get("hand") and pick.get("middle") != "rings":
            h["turned"] = middle_by_turning(Image.open(os.path.join(WORLD, h["file"])))
        mid = None if pick.get("hand") or pick.get("middle") == "rings" else h.get("turned")
        out.append({"place": d["place"], "photo": "world/" + h["file"], "built": d["built"], "note": d["note"], "hand": pick.get("hand"), "turned": mid, "squash": pick.get("squash", False),   # these were picked for looking straight up; the oval test is asked for by name
                    "lat": round(pl["lat"], 4), "lon": round(pl["lon"], 4),
                    "building": {"name": pick.get("name") or name, "where": ", ".join(x for x in (town if town != name else "", pl.get("country")) if x), "built": d["built"], "by": d["by"] or "Not looked up yet"}})
    json.dump(index, open(idx_path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    json.dump(out, open(os.path.join(HERE, "domes", "world.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(len(out), "domes in domes/world.json;", len(picks) - len(out), "picked but not ready (no place found, or not fetched)")


if __name__ == "__main__":
    {"find": find, "again": again, "sheets": sheets, "where": where, "pull": pull}[sys.argv[1]]()
