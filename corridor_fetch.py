"""Pull interior dome photos for the buildings between the two domes, with numbered contact sheets for picking."""
import json, os, time
import requests
from PIL import Image, ImageDraw
from fetch_domes import search, UA

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "domes", "corridor")
# place name as it appears in domes/corridor.json -> search wording
QUERIES = {
    "Yenidze": "Yenidze Kuppel innen", "Dresden Academy of Fine Arts": "Kunstakademie Dresden Kuppel innen",
    "St. Nicholas Church (Malá Strana)": "St. Nicholas Church Malá Strana dome interior", "National Museum (Prague)": "National Museum Prague dome interior",
    "Melk Abbey": "Stift Melk Kuppel", "Kirche am Steinhof": "Kirche am Steinhof Kuppel innen", "Karlskirche": "Karlskirche Wien Kuppelfresko",
    "Kunsthistorisches Museum": "Kunsthistorisches Museum Kuppel", "Peterskirche, Vienna": "Peterskirche Wien Kuppel",
    "Esztergom Basilica": "Esztergom Basilica dome interior", "Vác Cathedral": "Vác Cathedral dome interior",
    "Hungarian Parliament Building": "Hungarian Parliament dome interior", "St. Stephen's Basilica": "St. Stephen's Basilica Budapest dome interior",
    "Széchenyi thermal bath": "Széchenyi fürdő kupola", "Cathedral Basilica of Eger": "Eger Basilica dome interior",
    "Downtown Candlemas Church of the Blessed Virgin Mary": "Pécs mosque Gazi Kasim dome interior", "Subotica Synagogue": "Subotica synagogue dome interior",
    "Votive Church, Szeged": "Szeged Votive Church dome interior", "Szeged Synagogue": "Szeged synagogue dome interior",
    "Novi Sad Synagogue": "Novi Sad synagogue interior dome", "Bajrakli Mosque, Belgrade": "Bajrakli mosque Belgrade interior",
    "Church of Saint Mark, Belgrade": "St. Mark's Church Belgrade interior dome", "House of the National Assembly, Belgrade": "National Assembly Serbia dome interior",
    "Church of Saint Sava": "Church of Saint Sava dome interior mosaic", "Oplenac": "Oplenac church dome mosaic",
    "Romanian Athenaeum": "Romanian Athenaeum dome interior", "Banya Bashi Mosque": "Banya Bashi Mosque interior dome",
    "Sofia Synagogue": "Sofia Synagogue interior dome", "Church of Saint George, Sofia": "St. George Rotunda Sofia dome fresco",
    "Saint Nedelya Cathedral, Sofia": "Sveta Nedelya Sofia interior dome", "Saint Alexander Nevsky Cathedral, Sofia": "Alexander Nevsky Cathedral Sofia dome interior",
    "Rila Monastery": "Rila Monastery church dome fresco", "Dzhumaya Mosque": "Dzhumaya Mosque Plovdiv interior dome",
    "Tombul Mosque": "Tombul Mosque interior dome", "Old Mosque, Edirne": "Eski Camii Edirne dome interior", "Üç Şerefeli Mosque": "Üç Şerefeli Mosque dome interior",
}


def main(per=3):
    os.makedirs(OUT, exist_ok=True)
    idx_path = os.path.join(OUT, "_index.json")
    index = json.load(open(idx_path, encoding="utf-8")) if os.path.exists(idx_path) else []
    done = {h["place"] for h in index}; n = len(index)
    for place, q in QUERIES.items():
        if place in done:
            continue
        hits = None
        for wait in (1.5, 6, 20):
            time.sleep(wait)
            try:
                hits = search(q, limit=per, width=1024); break
            except Exception:
                continue
        if hits is None:
            print("search failed:", q); continue
        for h in hits:
            path = os.path.join(OUT, f"c{n:03d}.jpg")
            try:
                r = requests.get(h["thumb"], headers=UA, timeout=60)
                if r.status_code != 200:
                    continue
                open(path, "wb").write(r.content); Image.open(path).verify()
            except Exception:
                continue
            h.update(file=os.path.basename(path), place=place); index.append(h); n += 1
            time.sleep(0.8)
        json.dump(index, open(idx_path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    for s in range(0, n, 30):
        sheet = Image.new("RGB", (6 * 200, 5 * 200), "white"); d = ImageDraw.Draw(sheet)
        for i in range(s, min(n, s + 30)):
            im = Image.open(os.path.join(OUT, f"c{i:03d}.jpg")).convert("RGB"); im.thumbnail((196, 196))
            x, y = ((i - s) % 6) * 200, ((i - s) // 6) * 200
            sheet.paste(im, (x + (200 - im.width) // 2, y + (200 - im.height) // 2))
            d.rectangle((x, y, x + 34, y + 18), fill=(0, 0, 0)); d.text((x + 3, y + 1), str(i), fill=(255, 255, 0), font_size=15)
        sheet.save(os.path.join(OUT, f"_sheet_{s // 30}.jpg"), quality=78)
    print(n, "photos for", len({h['place'] for h in index}), "places")


if __name__ == "__main__":
    main()
