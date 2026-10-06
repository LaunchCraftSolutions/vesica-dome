"""Search Wikimedia Commons for straight-up dome photos and save candidates with a contact sheet per query."""
import json, os, re, sys
import requests
from PIL import Image

API = "https://commons.wikimedia.org/w/api.php"
UA = {"User-Agent": "DomeGeometryStudy/0.1 (personal research script)"}
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "domes", "candidates")

QUERIES = {
    "pantheon": "Pantheon Rome oculus dome",
    "hagia_sophia": "Hagia Sophia dome interior",
    "st_peters": "St. Peter's Basilica dome interior from below",
    "florence": "Florence Cathedral dome interior Vasari",
    "lotfollah": "Sheikh Lotfollah Mosque dome interior ceiling",
    "selimiye": "Selimiye Mosque Edirne dome interior",
    "invalides": "Invalides coupole intérieur",
    "frauenkirche": "Frauenkirche Dresden Kuppel innen",
}


def search(query, limit=6, width=900):
    params = {
        "action": "query", "format": "json", "generator": "search", "gsrnamespace": 6,
        "gsrsearch": query + " filetype:bitmap", "gsrlimit": limit,
        "prop": "imageinfo", "iiprop": "url|size|extmetadata", "iiurlwidth": width,
    }
    pages = requests.get(API, params=params, headers=UA, timeout=30).json().get("query", {}).get("pages", {})
    hits = []
    for p in sorted(pages.values(), key=lambda p: p.get("index", 0)):
        ii = p["imageinfo"][0]
        meta = ii.get("extmetadata", {})
        hits.append({
            "title": p["title"], "thumb": ii["thumburl"], "page": ii["descriptionurl"],
            "w": ii["width"], "h": ii["height"],
            "license": meta.get("LicenseShortName", {}).get("value", ""),
            "artist": re.sub("<[^>]+>", "", meta.get("Artist", {}).get("value", "")).strip()[:80],
        })
    return hits


def main(names):
    os.makedirs(OUT, exist_ok=True)
    index = {}
    for name in names:
        hits = search(QUERIES[name])
        tiles = []
        for i, h in enumerate(hits):
            path = os.path.join(OUT, f"{name}_{i}.jpg")
            r = requests.get(h["thumb"], headers=UA, timeout=60)
            if r.status_code != 200:
                continue
            with open(path, "wb") as f:
                f.write(r.content)
            h["file"] = os.path.relpath(path, os.path.dirname(OUT))
            im = Image.open(path).convert("RGB")
            im.thumbnail((300, 300))
            tiles.append(im)
        sheet = Image.new("RGB", (300 * max(1, len(tiles)), 300), "white")
        for i, t in enumerate(tiles):
            sheet.paste(t, (300 * i + (300 - t.width) // 2, (300 - t.height) // 2))
        sheet.save(os.path.join(OUT, f"_sheet_{name}.jpg"), quality=80)
        index[name] = hits
        print(name, len(tiles), "saved")
    with open(os.path.join(OUT, "_index.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main(sys.argv[1:] or list(QUERIES))
