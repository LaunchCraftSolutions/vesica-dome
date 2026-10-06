"""Build the Vesica Dome site into site/: one small page, with every photo beside it as a file of its own.

The page's layout, styles and behaviour live in app_template.html. This script fills it with the data:
for each dome where the first circle sits, from domes/all/results.json (written by draw_all.py), and how the photo was
taken and by whom (domes/all/photo_meta.json). The photos go into site/photos and site/eyes and are loaded when asked for,
so the page itself stays small. The two libraries the page uses (lib/) are copied in as well, so nothing but map tiles and
fonts is fetched from anyone else.

Run it with:  python build_map.py     then serve site/ (any web server will do).

Only the standard library is needed to build. Pillow is needed only when a small copy has to be made afresh: a card
picture for a new or changed dome photo, or the web copy of a new eye photo. Those copies are kept in the repository,
so a plain checkout builds without it.
"""
import hashlib, json, os, re, shutil, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, "site")
# Where each licence is written out in full. Shown beside every photo's credit.
LICENCE_LINKS = {
    "CC BY-SA 4.0": "https://creativecommons.org/licenses/by-sa/4.0/", "CC BY-SA 3.0": "https://creativecommons.org/licenses/by-sa/3.0/",
    "CC BY-SA 3.0 at": "https://creativecommons.org/licenses/by-sa/3.0/at/", "CC BY-SA 2.0": "https://creativecommons.org/licenses/by-sa/2.0/",
    "CC BY 4.0": "https://creativecommons.org/licenses/by/4.0/", "CC BY 3.0": "https://creativecommons.org/licenses/by/3.0/",
    "CC BY 2.0": "https://creativecommons.org/licenses/by/2.0/", "CC0": "https://creativecommons.org/publicdomain/zero/1.0/",
    "GFDL": "https://www.gnu.org/licenses/fdl-1.3.html",
}
NOT_DOMES = {"Basilica of St. Peter and St. Paul, Prague", "Klosterneuburg Abbey", "Fertőd", "Timișoara Orthodox Cathedral", "Belvedere, Vienna", "Saint Sophia Church, Sofia"}
DRAWN_KEYS = {"St. Nicholas Church (Malá Strana)", "National Museum (Prague)", "Melk Abbey", "Kunsthistorisches Museum", "Karlskirche", "Esztergom Basilica",
              "St. Stephen's Basilica", "Subotica Synagogue", "Szeged Synagogue", "Saint Alexander Nevsky Cathedral, Sofia",
              "Rila Monastery", "Dzhumaya Mosque", "Üç Şerefeli Mosque", "Dresden Academy of Fine Arts", "Kirche am Steinhof", "Peterskirche, Vienna",
              "Vác Cathedral", "Hungarian Parliament Building", "Széchenyi thermal bath", "Gellért Baths", "Cathedral Basilica of Eger",
              "Downtown Candlemas Church of the Blessed Virgin Mary", "Bajrakli Mosque, Belgrade", "Church of Saint Sava",
              "Sofia Synagogue", "Saint Nedelya Cathedral, Sofia", "Old Mosque, Edirne"}
LINE_KM = 1429
# Where the construction sat in the first drawings of the two striking domes, before the single fitting procedure existed.
FIRST_DRAWING = {"Dresden": {"u": 102.0, "turn": 0.0}, "Edirne, Selimiye": {"u": 78.0, "turn": 0.0}}
# Turns set by Casey with the rotation line. They replace the automatic turn, which picks its angle by edge strength and can lock onto ribs.
TURN_BY_HAND = {"Dresden": 0.0}


# The building behind each dome: its name, where it is, when it was built and by whom. From general reference knowledge, not from
# the photos; "Not recorded" where no builder's name has come down. Shown by the Building button on the desk.
BUILDINGS = {
    "Dresden": ("Frauenkirche", "Dresden, Germany", "1726–43. Destroyed 1945, rebuilt 1994–2005", "George Bähr, the city's master carpenter"),
    "Dresden, academy": ("Academy of Fine Arts (Lipsius building)", "Dresden, Germany", "1887–94", "Constantin Lipsius"),
    "Prague, St Nicholas": ("St Nicholas Church, Malá Strana", "Prague, Czech Republic", "Church 1703–52; the dome 1737–52", "Christoph Dientzenhofer, then his son Kilian Ignaz Dientzenhofer, who built the dome"),
    "Prague, museum": ("National Museum", "Prague, Czech Republic", "1885–91", "Josef Schulz"),
    "Melk": ("Melk Abbey church", "Melk, Austria", "1702–36", "Jakob Prandtauer, completed by Joseph Munggenast"),
    "Vienna, Steinhof": ("Kirche am Steinhof (St Leopold)", "Vienna, Austria", "1904–07", "Otto Wagner"),
    "Vienna, museum": ("Kunsthistorisches Museum", "Vienna, Austria", "1871–91", "Gottfried Semper and Karl von Hasenauer"),
    "Vienna, Karlskirche": ("Karlskirche", "Vienna, Austria", "1716–37", "Johann Bernhard Fischer von Erlach, completed by his son Joseph Emanuel"),
    "Vienna, Peterskirche": ("Peterskirche", "Vienna, Austria", "1701–33", "Gabriele Montani, then Johann Lucas von Hildebrandt"),
    "Esztergom": ("Esztergom Basilica", "Esztergom, Hungary", "1822–69", "Pál Kühnel and János Packh, completed by József Hild"),
    "Esztergom, off-centre photo": ("Esztergom Basilica", "Esztergom, Hungary", "1822–69", "Pál Kühnel and János Packh, completed by József Hild"),
    "Vác": ("Vác Cathedral", "Vác, Hungary", "1761–77", "Isidore Canevale"),
    "Budapest": ("St Stephen's Basilica", "Budapest, Hungary", "1851–1905", "József Hild, then Miklós Ybl, completed by József Kauser"),
    "Budapest, parliament": ("Hungarian Parliament Building", "Budapest, Hungary", "1885–1904", "Imre Steindl"),
    "Budapest, Széchenyi bath": ("Széchenyi Thermal Bath", "Budapest, Hungary", "1909–13", "Designed by Győző Czigler"),
    "Budapest, Gellért bath": ("Gellért Baths", "Budapest, Hungary", "1912–18", "Ármin Hegedűs, Artúr Sebestyén and Izidor Sterk"),
    "Eger": ("Cathedral Basilica of Eger", "Eger, Hungary", "1831–36", "József Hild"),
    "Pécs": ("Mosque of Pasha Qasim (now the Downtown Candlemas Church)", "Pécs, Hungary", "1543–46", "Built for Pasha Qasim the Victorious. Builder not recorded"),
    "Subotica": ("Subotica Synagogue", "Subotica, Serbia", "1901–02", "Marcell Komor and Dezső Jakab"),
    "Szeged, synagogue, second photo": ("New Synagogue", "Szeged, Hungary", "1900–02", "Lipót Baumhorn"),
    "Szeged, synagogue": ("New Synagogue", "Szeged, Hungary", "1900–02", "Lipót Baumhorn"),
    "Belgrade, Bajrakli mosque": ("Bajrakli Mosque", "Belgrade, Serbia", "About 1575", "Not recorded"),
    "Belgrade, St Sava": ("Church of Saint Sava", "Belgrade, Serbia", "1935–2004", "Aleksandar Deroko and Bogdan Nestorović; continued from 1985 under Branko Pešić"),
    "Sofia, synagogue": ("Sofia Synagogue", "Sofia, Bulgaria", "1905–09", "Friedrich Grünanger"),
    "Sofia, St Nedelya": ("St Nedelya Church", "Sofia, Bulgaria", "1856–63. Rebuilt 1927–33 after the bombing of 1925", "Rebuilt by Ivan Vasilyov and Dimitar Tsolov"),
    "Sofia": ("St Alexander Nevsky Cathedral", "Sofia, Bulgaria", "1882–1912", "Alexander Pomerantsev"),
    "Rila": ("Rila Monastery, main church", "Rila, Bulgaria", "1834–37", "Master builder Pavel Ioanov"),
    "Plovdiv": ("Dzhumaya Mosque", "Plovdiv, Bulgaria", "About 1363–64, rebuilt in the 15th century under Murad II", "Not recorded"),
    "Edirne, Old Mosque": ("Old Mosque (Eski Cami)", "Edirne, Turkey", "1403–14", "Hacı Alaeddin of Konya"),
    "Edirne, Üç Şerefeli": ("Üç Şerefeli Mosque", "Edirne, Turkey", "1438–47", "Built for Sultan Murad II. Builder not recorded"),
    "Edirne, Selimiye": ("Selimiye Mosque", "Edirne, Turkey", "1568–75", "Mimar Sinan, for Sultan Selim II"),
    "London": ("St Paul's Cathedral", "London, England", "1675–1710", "Sir Christopher Wren"),
    "St Petersburg": ("St Isaac's Cathedral", "St Petersburg, Russia", "1818–58", "Auguste de Montferrand"),
    "Rome": ("Pantheon", "Rome, Italy", "About 113–125", "Built under the emperors Trajan and Hadrian. Builder not recorded"),
    "Isfahan": ("Sheikh Lotfollah Mosque", "Isfahan, Iran", "1603–19", "Mohammad Reza Isfahani, for Shah Abbas I"),
    "Istanbul": ("Little Hagia Sophia (Church of Saints Sergius and Bacchus)", "Istanbul, Turkey", "527–536", "Built for Emperor Justinian I. Builder not recorded"),
}


written = set()   # every file this build put into site/; anything else found there afterwards is left over from an older build


def put(src, rel):
    """Copy one file into the site and give back the address the page uses for it."""
    out = os.path.join(SITE, rel.replace("/", os.sep)); os.makedirs(os.path.dirname(out), exist_ok=True)
    shutil.copyfile(src, out); written.add(os.path.normcase(out)); return rel


def write(rel, text):
    out = os.path.join(SITE, rel.replace("/", os.sep)); os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    written.add(os.path.normcase(out))


def digest(path):
    with open(path, "rb") as f:
        return hashlib.sha1(f.read()).hexdigest()[:16]


def plain_name(slug):
    """A file name every host serves the same way: accents dropped, anything else unusual turned into an underscore."""
    s = "".join(c for c in unicodedata.normalize("NFKD", slug) if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9_]", "_", s.lower())


def card_picture(photo, made):
    """The small copy of a dome photo shown on its card: 320 px, made once and kept beside the photo. Made again only when
    the photo itself has changed (told by its contents, not its date, so a fresh checkout never needs Pillow)."""
    out = photo[:-len("_photo.jpg")] + "_thumb.jpg"; key = os.path.basename(out); h = digest(photo)
    if made.get(key) != h or not os.path.exists(out):
        from PIL import Image
        im = Image.open(photo).convert("RGB"); im.thumbnail((320, 320), Image.LANCZOS); im.save(out, "JPEG", quality=80); made[key] = h
    return out


def by_line(artist):
    """Commons sometimes hands back its own boilerplate where the author's name should be; keep only the name."""
    m = re.match(r"No machine-readable author provided\.\s*(.+?) assumed", artist or "")
    return m.group(1) if m else (artist or "")


def load(rel):
    p = os.path.join(HERE, "domes", rel)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None


def credits():
    out = {}
    cand = load("candidates/_index.json") or {}
    for name, hits in cand.items():
        for i, h in enumerate(hits):
            out[f"candidates/{name}_{i}.jpg"] = h
    for folder in ("sample", "corridor"):
        for h in load(f"{folder}/_index.json") or []:
            out[f"{folder}/{h['file']}"] = h
    return out


def eyes():
    """The eye photos for the desk's Eye layer (see fetch_eyes.py), each at most 1400 px wide, with its iris and its credit.
    The web copies are kept in eyes/web and made again only when the photo they come from has changed."""
    p = os.path.join(HERE, "eyes", "_index.json")
    if not os.path.exists(p):
        return []
    web = os.path.join(HERE, "eyes", "web"); os.makedirs(web, exist_ok=True)
    record = os.path.join(web, "_web.json"); made = json.load(open(record, encoding="utf-8")) if os.path.exists(record) else {}
    out = []
    for e in json.load(open(p, encoding="utf-8")):
        src = os.path.join(HERE, e["file"]); small = os.path.join(web, e["id"] + ".jpg"); h = digest(src); rec = made.get(e["id"])
        if not rec or rec["of"] != h or not os.path.exists(small):
            from PIL import Image
            im = Image.open(src).convert("RGB"); k = min(1, 1400 / im.width)
            im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS); im.save(small, "JPEG", quality=84)
            rec = made[e["id"]] = {"of": h, "w": im.width, "h": im.height, "k": k}
        k = rec["k"]
        out.append({"id": e["id"], "name": e["name"], "img": put(small, f'eyes/{e["id"]}.jpg'), "w": rec["w"], "h": rec["h"],
                    "cx": round(e["iris"]["cx"] * k, 1), "cy": round(e["iris"]["cy"] * k, 1), "r": round(e["iris"]["r"] * k, 1),
                    "credit": f'{e["by"]}, {e["licence"]}' + (f', {e["note"]}' if e.get("note") else ""), "title": e["title"], "page": e["page"],
                    "by": e["by"], "licence": e["licence"], "licence_url": e.get("licence_url", "")})
    with open(record, "w", encoding="utf-8") as f:
        json.dump(made, f, indent=1)
    return out


def main():
    results = load("all/results.json")
    cr, meta = credits(), load("all/photo_meta.json") or {}
    record = os.path.join(HERE, "domes", "all", "_thumbs.json"); made = json.load(open(record, encoding="utf-8")) if os.path.exists(record) else {}
    names = set()
    for r in results:
        # The desk does not score. Ring-by-ring distances, landing counts and chances stay out of the page.
        for k in ("landed", "luck", "rings", "full", "sizes_tried", "measured_edges_px", "measured_edges_times_first_circle", "reach_px", "smallest_measurable_px"):
            r.pop(k, None)
        photo = os.path.join(HERE, "domes", "all", r["slug"] + "_photo.jpg"); name = plain_name(r["slug"])
        assert name not in names, "two domes would share the file name " + name
        names.add(name)
        r["img"] = put(photo, f"photos/{name}.jpg")
        r["thumb"] = put(card_picture(photo, made), f"photos/{name}_t.jpg")
        grid = os.path.join(HERE, "domes", "all", r["slug"] + "_grid.jpg")
        if r.get("straightened") and os.path.exists(grid):
            r["grid_img"] = put(grid, f"photos/{name}_grid.jpg")
        h = cr.get(r["photo"], {})
        r["file_title"] = h.get("title", "").replace("File:", "")
        r["page"] = h.get("page", "")
        r["meta"] = dict(meta.get(r["photo"], {}))
        r["meta"]["artist"] = by_line(r["meta"].get("artist"))
        r["licence_url"] = LICENCE_LINKS.get(r["meta"].get("license", ""), "")
        if r["place"] in BUILDINGS:
            name, where, built, by = BUILDINGS[r["place"]]
            r["building"] = {"name": name, "where": where, "built": built, "by": by}
        if r["place"] in FIRST_DRAWING:
            f = FIRST_DRAWING[r["place"]]
            r["first_drawing"] = {"u": round(f["u"] * r["view_px"] / r["straightened_px"], 2), "turn": f["turn"]}
        if r["place"] in TURN_BY_HAND:
            r["turn_note"] = f"set with the rotation line; the automatic fit gave {r['turn_deg']}°"
            r["turn_deg"] = TURN_BY_HAND[r["place"]]
    undrawn = [dict(c, km=round(c["along"] * LINE_KM)) for c in load("corridor.json") if c["place"] not in NOT_DOMES and c["place"] not in DRAWN_KEYS]
    template = open(os.path.join(HERE, "app_template.html"), encoding="utf-8").read()
    with open(record, "w", encoding="utf-8") as f:
        json.dump(made, f, indent=1, sort_keys=True)
    html = template.replace("/*DOMES*/[]", json.dumps(results, ensure_ascii=False)).replace("/*UNDRAWN*/[]", json.dumps(undrawn, ensure_ascii=False)).replace("/*EYES*/[]", json.dumps(eyes(), ensure_ascii=False))
    write("index.html", html)
    # The page used to be called map.html. That address still works: it passes straight on, keeping the dome named after the #.
    write("map.html", '<!doctype html><meta charset="utf-8"><title>Vesica Dome</title><script>location.replace("./"+location.hash)</script>\n')
    lib = os.path.join(HERE, "lib")
    for folder, _, files in os.walk(lib):
        for name in files:
            src = os.path.join(folder, name); put(src, "lib/" + os.path.relpath(src, lib).replace(os.sep, "/"))
    # Clear out whatever an older build left behind, without ever emptying the folder a server may be reading from.
    for folder, _, files in os.walk(SITE, topdown=False):
        for name in files:
            if os.path.normcase(os.path.join(folder, name)) not in written:
                os.remove(os.path.join(folder, name))
        if folder != SITE and not os.listdir(folder):
            os.rmdir(folder)
    size = sum(os.path.getsize(os.path.join(f, n)) for f, _, ns in os.walk(SITE) for n in ns)
    print(len(results), "drawn,", len(undrawn), "not drawn; page", round(len(html.encode("utf-8")) / 1e3), "KB; whole site", round(size / 1e6, 1), "MB in", len(written), "files")


if __name__ == "__main__":
    main()
