"""Pull named photos: files picked by eye, not found by search.

All are from Wikimedia Commons, chosen from a building's own category: only photos under an open licence are used. Each is saved at
1280 px wide into domes/corridor/ beside the searched ones, with its title, photographer and licence in _index.json and
its camera details in domes/all/photo_meta.json, the same records the searched photos have.
"""
import io, json, os, re, time
import requests
from PIL import Image
from fetch_domes import API, UA

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "domes", "corridor")
# place name as it appears in domes/corridor.json -> the Commons file
PICKED = {
    "Dresden Academy of Fine Arts": "File:Kunstakademie Dresden Oktogon RK01.jpg",
    "Kirche am Steinhof": "File:Wien - Otto-Wagner-Kirche am Steinhof - Innenverkleidung der Kuppel.jpg",
    "Peterskirche, Vienna": "File:Iglesia de San Pedro, Viena, Austria, 2020-01-31, DD 89-91 HDR.jpg",
    "Vác Cathedral": "File:Vác, római katolikus székesegyház kupolafreskója 2025 01.jpg",
    "Hungarian Parliament Building": "File:Roof in the Hungarian Parliament (5985719082).jpg",
    "Széchenyi thermal bath": "File:Budapest Széchenyi-Bad, Kuppel Eingang.jpg",
    "Gellért Baths": "File:Budapest, Gellért fürdő, előcsarnok, 33.jpg",
    "Cathedral Basilica of Eger": "File:Eger Kathedrale St. Johannes Innen Kuppel 5.JPG",
    "Downtown Candlemas Church of the Blessed Virgin Mary": "File:Pécs Ex-Moschee Gazi Khassim Innen Kuppel 07.JPG",
    "Esztergom Basilica": "File:Esztergom Kathedrale Mariä Himmelfahrt Innen Kuppel 1.JPG",
    "Church of Saint Sava": "File:Temple of Saint Sava interior 03.jpg",
    "Saint Alexander Nevsky Cathedral, Sofia": "File:Sofia Alexander Nevsky Cathedral Interior 01.jpg",
    "Sofia Synagogue": "File:Sofia Synagogue - 28.jpg",
    "Saint Nedelya Cathedral, Sofia": "File:20140616 Sofia 001.jpg",
    "Old Mosque, Edirne": "File:Edirne Old Mosque Ceiling in 2024 5985.jpg",
    "Bajrakli Mosque, Belgrade": "File:Bajrakli džamija20.JPG",
}
strip = lambda s: re.sub("<[^>]+>", "", s or "").strip()


def num(v):
    try:
        return round(float(v), 1)
    except (TypeError, ValueError):
        return None


def main(width=1280):
    idx_path = os.path.join(OUT, "_index.json"); meta_path = os.path.join(HERE, "domes", "all", "photo_meta.json")
    index = json.load(open(idx_path, encoding="utf-8")); meta = json.load(open(meta_path, encoding="utf-8"))
    n = 1 + max(int(h["file"][1:4]) for h in index)

    def save():
        json.dump(index, open(idx_path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        json.dump(meta, open(meta_path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    def say(hit, path):
        print(hit["file"], Image.open(path).size, os.path.getsize(path) // 1024, "KB", hit["place"].encode("ascii", "replace").decode(), "|", hit["license"], "|",
              hit["artist"].encode("ascii", "replace").decode(), flush=True)

    for place, title in PICKED.items():
        old = next((h for h in index if h["title"] == title), None)
        if old and "corridor/" + old["file"] in meta:
            continue
        params = {"action": "query", "format": "json", "titles": title, "prop": "imageinfo", "iiprop": "url|size|extmetadata|metadata", "iiurlwidth": width}
        page = next(iter(requests.get(API, params=params, headers=UA, timeout=30).json()["query"]["pages"].values()))
        ii = page["imageinfo"][0]; ext = ii.get("extmetadata", {}); exif = {m["name"]: m["value"] for m in ii.get("metadata") or []}
        path = os.path.join(OUT, old["file"] if old else f"c{n:03d}.jpg")
        if not old:
            r = requests.get(ii["thumburl"], headers=UA, timeout=90); r.raise_for_status()
            open(path, "wb").write(r.content); Image.open(path).verify()
        hit = old or {"title": page["title"], "thumb": ii["thumburl"], "page": ii["descriptionurl"], "w": ii["width"], "h": ii["height"],
                      "license": ext.get("LicenseShortName", {}).get("value", ""), "artist": strip(ext.get("Artist", {}).get("value", ""))[:80],
                      "file": os.path.basename(path), "place": place, "picked_by_eye": True}
        if not old:
            index.append(hit); n += 1
        f35 = num(exif.get("FocalLengthIn35mmFilm"))
        meta["corridor/" + hit["file"]] = {
            "taken": (exif.get("DateTimeOriginal") or strip(ext.get("DateTimeOriginal", {}).get("value", "")))[:10].replace(":", "-") or None,
            "make": exif.get("Make"), "model": exif.get("Model"), "lens": exif.get("LensModel"), "focal_mm": num(exif.get("FocalLength")),
            "focal35_mm": int(f35) if f35 else None, "software": exif.get("Software"), "original_size": [ii["width"], ii["height"]],
            "description": strip(ext.get("ImageDescription", {}).get("value", ""))[:200], "artist": hit["artist"], "license": hit["license"]}
        say(hit, path); save(); time.sleep(1.0)


if __name__ == "__main__":
    main()
