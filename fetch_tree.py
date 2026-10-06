"""Find domes nobody listed: walk Wikimedia Commons' own "Dome interiors" categories and keep the photos that look straight up.

  python fetch_tree.py walk    list the categories under "Dome interiors" (domes/found/_tree.json)
  python fetch_tree.py look    for each category, fetch small copies of up to 30 open-licence photos and score how dome-like each is
  python fetch_tree.py name    work out which building each likely photo shows (from its categories and Wikidata), when it was
                               built and where it is; keep the best photo of each building built by 1935 or earlier
  python fetch_tree.py sheets  numbered sheets of those, for picking by eye

What a building is called, where it is, when it was begun and who designed it all come from Wikidata here, not from the photo.
Small copies and working files stay in domes/found/, which is not kept in the repository.
"""
import json, os, re, sys, time
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw
from fetch_world import API, FOUND, OPEN, asc, dome_like, get, strip

WD = "https://www.wikidata.org/w/api.php"
ROOTS = ["Category:Dome interiors by country", "Category:Church dome interiors", "Category:Mosque dome interiors", "Category:Mausoleum dome interiors", "Category:House dome interiors"]
SKIP = re.compile(r"Tokyo Dome|Restoration of|Stadium|Planetarium|exterior", re.I)
LIKELY = 0.30     # a photo scoring less than this is not looked at further
LATEST = 1935     # buildings begun after this are outside the collection's span
P = lambda *a: os.path.join(FOUND, *a)
load = lambda name, empty: json.load(open(P(name), encoding="utf-8")) if os.path.exists(P(name)) else empty
save = lambda name, data: json.dump(data, open(P(name), "w", encoding="utf-8"), ensure_ascii=False)


def walk(depth=6):
    seen = {}; level = list(ROOTS)
    for d in range(depth):
        nxt = []
        for c in level:
            cont = {}
            while True:
                r = get(API, params={"action": "query", "format": "json", "generator": "categorymembers", "gcmtitle": c, "gcmtype": "subcat", "gcmlimit": 500, "prop": "categoryinfo", **cont})
                j = r.json() if r else {}
                for p in j.get("query", {}).get("pages", {}).values():
                    if p["title"] not in seen:
                        ci = p.get("categoryinfo", {}); seen[p["title"]] = (ci.get("files", 0), ci.get("subcats", 0), d + 1)
                        if ci.get("subcats"):
                            nxt.append(p["title"])
                cont = j.get("continue", {})
                if not cont:
                    break
            time.sleep(0.15)
        level = nxt
    save("_tree.json", {"seen": seen}); print(len(seen), "categories,", sum(v[0] for v in seen.values()), "files")


def look(per=30):
    os.makedirs(P("tree"), exist_ok=True)
    cats = [c for c, v in load("_tree.json", {})["seen"].items() if v[0] and not SKIP.search(c)] + ROOTS
    files = load("_tree_files.json", {}); done = set(load("_tree_done.json", []))
    for k, c in enumerate(cats):
        if c in done:
            continue
        r = get(API, params={"action": "query", "format": "json", "generator": "categorymembers", "gcmtitle": c, "gcmtype": "file", "gcmlimit": 60,
                             "prop": "imageinfo", "iiprop": "url|size|extmetadata|mime", "iiurlwidth": 330})
        pages = list((r.json().get("query", {}).get("pages", {}) if r else {}).values()); new = []
        for p in pages:
            ii = (p.get("imageinfo") or [{}])[0]; lic = ii.get("extmetadata", {}).get("LicenseShortName", {}).get("value", "")
            if p["title"] in files or not ii.get("thumburl") or ii.get("mime") not in ("image/jpeg", "image/png") or not OPEN.match(lic) or min(ii.get("width", 0), ii.get("height", 0)) < 900:
                continue
            new.append({"title": p["title"], "id": p["pageid"], "thumb": ii["thumburl"], "page": ii["descriptionurl"], "w": ii["width"], "h": ii["height"], "license": lic,
                        "artist": strip(ii["extmetadata"].get("Artist", {}).get("value", ""))[:80], "cat": c})
        new = new[:per]

        def fetch(h):
            path = P("tree", f"t{h['id']}.jpg"); r = get(h["thumb"])
            if not r:
                return None
            try:
                open(path, "wb").write(r.content); im = Image.open(path); im.load(); h["score"] = dome_like(im); return h
            except Exception:
                return None
        with ThreadPoolExecutor(3) as ex:
            for h in ex.map(fetch, new):
                if h:
                    files[h["title"]] = h
                    if h["score"] < LIKELY:   # not worth the room
                        try: os.remove(P("tree", f"t{h['id']}.jpg"))
                        except OSError: pass
        done.add(c)
        if k % 10 == 0 or k == len(cats) - 1:
            save("_tree_files.json", files); save("_tree_done.json", sorted(done))
            print(f"{k + 1}/{len(cats)} categories; {len(files)} photos scored; {sum(1 for h in files.values() if h['score'] >= LIKELY)} likely", flush=True)
    save("_tree_files.json", files); save("_tree_done.json", sorted(done))


def entities(ids, props="claims|labels"):
    out = {}
    ids = sorted(set(ids))
    for i in range(0, len(ids), 45):
        r = get(WD, params={"action": "wbgetentities", "format": "json", "ids": "|".join(ids[i:i + 45]), "props": props, "languages": "en"})
        out.update((r.json() if r else {}).get("entities", {})); time.sleep(0.3)
    return out


def vals(e, prop):
    return [s["mainsnak"]["datavalue"]["value"] for s in e.get("claims", {}).get(prop, []) if s.get("mainsnak", {}).get("datavalue")]


def when(e):
    """The year a building was begun, and the words to show for it, from its inception (P571)."""
    for v in vals(e, "P571"):
        m = re.match(r"([+-])(\d+)-", v.get("time", ""))
        if not m:
            continue
        y = int(m.group(2)) * (1 if m.group(1) == "+" else -1); pr = v.get("precision", 9)
        era = lambda n: f"{abs(n)} BC" if n < 0 else str(n)
        if pr >= 9:
            return y, era(y)
        if pr == 8:
            return y, era(y // 10 * 10) + "s"
        if pr == 7:
            c = (abs(y) - 1) // 100 + 1; th = "th" if 10 <= c % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(c % 10, "th")
            return y, f"{c}{th} century" + (" BC" if y < 0 else "")
        return y, "About " + era(y)
    return None, ""


def name():
    files = {t: h for t, h in load("_tree_files.json", {}).items() if h["score"] >= LIKELY}
    info = load("_tree_cats.json", {})   # file title -> its own categories
    todo = [t for t in files if t not in info]
    for i in range(0, len(todo), 40):
        cont = {}; part = todo[i:i + 40]
        for t in part:
            info[t] = []
        while True:
            r = get(API, params={"action": "query", "format": "json", "titles": "|".join(part), "prop": "categories", "clshow": "!hidden", "cllimit": 500, **cont})
            j = r.json() if r else {}
            for p in j.get("query", {}).get("pages", {}).values():
                info.setdefault(p["title"], []).extend(c["title"] for c in p.get("categories", []))
            cont = j.get("continue", {})
            if not cont:
                break
        if i % 400 == 0:
            save("_tree_cats.json", info); print("categories of", i + len(part), "of", len(todo), "photos", flush=True)
        time.sleep(0.2)
    save("_tree_cats.json", info)
    # which Wikidata item each category stands for; a category about the inside or the dome of a building is traced up to the building
    cat_item = load("_tree_catitems.json", {}); parents = load("_tree_parents.json", {})
    def items_for(cats):
        cats = [c for c in dict.fromkeys(cats) if c not in cat_item]
        for i in range(0, len(cats), 40):
            cont = {}; part = cats[i:i + 40]
            for c in part:
                cat_item[c] = None; parents.setdefault(c, [])
            while True:
                r = get(API, params={"action": "query", "format": "json", "titles": "|".join(part), "prop": "pageprops|categories", "ppprop": "wikibase_item", "clshow": "!hidden", "cllimit": 500, **cont})
                j = r.json() if r else {}
                for p in j.get("query", {}).get("pages", {}).values():
                    if p.get("pageprops", {}).get("wikibase_item"):
                        cat_item[p["title"]] = p["pageprops"]["wikibase_item"]
                    parents[p["title"]] = list(dict.fromkeys(parents.get(p["title"], []) + [c["title"] for c in p.get("categories", [])]))
                cont = j.get("continue", {})
                if not cont:
                    break
            time.sleep(0.2)
    own = sorted({c for t in files for c in info.get(t, [])})
    items_for(own); print(len(own), "categories looked up", flush=True)
    inner = re.compile(r"interior|dome|cupola|ceiling|vault|fresco|mosaic|oculus|rotunda|inside|nave|k[uo]ppel|c[uú]p[uo]la|coupole|kubbe", re.I)
    up = sorted({p for c in own if cat_item.get(c) is None and inner.search(c) for p in parents.get(c, [])})
    items_for(up); print(len(up), "parent categories looked up", flush=True)
    save("_tree_catitems.json", cat_item); save("_tree_parents.json", parents)
    ents = load("_tree_ents.json", {})
    need = {q for q in cat_item.values() if q and q not in ents}; ents.update(entities(need))
    main = {v["id"] for e in ents.values() for p in ("P301", "P971") for v in vals(e, p) if isinstance(v, dict) and v.get("id")}   # a category's main topic, or what it combines
    ents.update(entities(main - set(ents)))
    labels = {v["id"] for e in ents.values() for p in ("P17", "P84", "P131") for v in vals(e, p) if isinstance(v, dict) and v.get("id")}
    lab = load("_tree_labels.json", {}); got = entities(labels - set(lab), "labels")
    lab.update({q: e.get("labels", {}).get("en", {}).get("value") for q, e in got.items()})
    save("_tree_ents.json", ents); save("_tree_labels.json", lab)

    def building(q):
        """The item, or its main topic, if it is a place with a position and a date."""
        e = ents.get(q) or {}
        for cand in [q] + [v["id"] for p in ("P301", "P971") for v in vals(e, p) if isinstance(v, dict)]:
            b = ents.get(cand) or {}; co = vals(b, "P625"); y, words = when(b)
            if co and y is not None:
                return cand, b, co[0], y, words
        return None
    best = {}
    for t, h in files.items():
        cands = []
        for c in info.get(t, []):
            for cc in [c] + (parents.get(c, []) if cat_item.get(c) is None and inner.search(c) else []):
                if cat_item.get(cc):
                    got = building(cat_item[cc])
                    if got:
                        cands.append(got)
        if not cands:
            continue
        q, b, co, y, words = max(cands, key=lambda g: g[3])   # the youngest: a church, not the town it stands in
        if y > LATEST:
            continue
        if q not in best or h["score"] > best[q]["score"]:
            ids = lambda p: [lab.get(v["id"]) for v in vals(b, p) if isinstance(v, dict) and lab.get(v["id"])]
            best[q] = dict(h, item=q, name=b.get("labels", {}).get("en", {}).get("value") or "", lat=round(co["latitude"], 4), lon=round(co["longitude"], 4), year=y, built=words,
                           country=(ids("P17") or [""])[0], town=(ids("P131") or [""])[0], by=", ".join(ids("P84")))
    out = sorted(best.values(), key=lambda h: (h["country"], h["town"], h["name"])); save("_tree_buildings.json", out)
    print(len(files), "likely photos;", len(out), "buildings named, dated", LATEST, "or earlier, each with its best photo")


def sheets(cols=5, rows=4, T=300):
    out = load("_tree_buildings.json", []); os.makedirs(P("sheets"), exist_ok=True); per = cols * rows
    for s in range(0, len(out), per):
        sheet = Image.new("RGB", (T * cols, (T + 40) * rows), (20, 20, 24)); dr = ImageDraw.Draw(sheet)
        for i, h in enumerate(out[s:s + per]):
            x, y = (i % cols) * T, (i // cols) * (T + 40)
            try:
                im = Image.open(P("tree", f"t{h['id']}.jpg")).convert("RGB")
            except Exception:
                continue
            im.thumbnail((T - 4, T - 4)); sheet.paste(im, (x + (T - im.width) // 2, y + 40 + (T - im.height) // 2))
            dr.text((x + 4, y + 2), f"T{s + i}  {asc(h['name'])[:30]}", fill=(255, 230, 150), font_size=15)
            dr.text((x + 4, y + 20), f"{asc(h['town'])[:16]}, {asc(h['country'])[:12]}  {asc(h['built'])}", fill=(200, 200, 200), font_size=14)
        sheet.save(P("sheets", f"tree_{s // per:02d}.jpg"), quality=80)
    print(len(out), "buildings on", (len(out) + per - 1) // per, "sheets")


if __name__ == "__main__":
    {"walk": walk, "look": look, "name": name, "sheets": sheets}[sys.argv[1]]()
