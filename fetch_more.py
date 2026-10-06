"""Pull a wider sample of dome interiors from Wikimedia Commons for the single-ratio test."""
import json, os, time
import requests
from PIL import Image
from fetch_domes import search, UA

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "domes", "sample")
QUERIES = [
    "St Paul's Cathedral dome interior", "Florence Cathedral dome interior", "St. Peter's Basilica dome interior looking up",
    "Blue Mosque Istanbul dome interior", "Süleymaniye Mosque dome interior", "Shah Mosque Isfahan dome interior",
    "Taj Mahal dome interior", "Gol Gumbaz dome interior", "Dome of the Rock interior dome", "United States Capitol rotunda dome interior",
    "Les Invalides dome interior", "Panthéon Paris coupole", "Berliner Dom Kuppel innen", "Saint Isaac's Cathedral dome interior",
    "Karlskirche Wien Kuppel", "Sant'Ivo alla Sapienza cupola interno", "San Carlo alle Quattro Fontane dome",
    "Sant'Andrea al Quirinale cupola", "Battistero Pisa cupola interno", "Battistero Firenze cupola mosaico",
    "Duomo Parma cupola Correggio", "Santa Maria della Salute cupola interno", "San Lorenzo Torino cupola Guarini",
    "Cappella della Sindone cupola", "Mezquita Córdoba cúpula mihrab", "Alhambra Abencerrajes cúpula",
    "Aachener Dom Kuppel Mosaik", "Chora Church dome", "Daphni Monastery dome Pantocrator", "Sheikh Zayed Mosque dome interior",
    "Nasir al-Mulk Mosque ceiling dome", "Jameh Mosque Isfahan dome interior", "Texas State Capitol dome interior",
    "Wisconsin State Capitol dome interior", "Library of Congress reading room dome", "Hungarian Parliament dome interior",
    "St. Stephen's Basilica Budapest dome interior", "Esztergom Basilica dome interior", "Cathedral of Christ the Saviour dome interior",
    "St. Nicholas Church Malá Strana dome", "Melk Abbey church dome fresco", "Val-de-Grâce coupole", "Mosta Rotunda dome interior",
    "Siena Cathedral dome interior", "Basilica di Superga cupola interno", "Santa Maria delle Grazie Milano cupola",
    "Sultan Ahmed Mosque central dome", "Rüstem Pasha Mosque dome", "Hagia Sophia Thessaloniki dome", "Pennsylvania State Capitol rotunda dome",
]


# Wording that tends to return straight-up views, used for the second batch.
GENERIC = [
    "dome interior looking up", "cupola from below", "dome ceiling symmetrical", "Kuppel von unten", "coupole vue de dessous",
    "cupola vista dal basso", "cúpula desde abajo", "mosque dome interior ceiling", "church dome interior fresco looking up",
    "rotunda dome looking up", "dome oculus looking up", "cathedral dome from directly below",
]


def main(queries=QUERIES, per_query=2):
    os.makedirs(OUT, exist_ok=True)
    idx_path = os.path.join(OUT, "_index.json")
    index = json.load(open(idx_path, encoding="utf-8")) if os.path.exists(idx_path) else []
    n, seen = len(index), {h["title"] for h in index}
    for q in queries:
        hits = None
        for wait in (1.5, 6, 20):  # the search service refuses when asked too fast; back off and retry
            time.sleep(wait)
            try:
                hits = search(q, limit=per_query, width=1280); break
            except Exception:
                continue
        if hits is None:
            print("search failed:", q); continue
        hits = [h for h in hits if h["title"] not in seen]
        for h in hits:
            path = os.path.join(OUT, f"d{n:03d}.jpg")
            try:
                r = requests.get(h["thumb"], headers=UA, timeout=60)
                if r.status_code != 200:
                    continue
                with open(path, "wb") as f:
                    f.write(r.content)
                Image.open(path).verify()
            except Exception:
                continue
            h.update(file=os.path.basename(path), query=q); index.append(h); seen.add(h["title"]); n += 1
            time.sleep(0.8)
    with open(idx_path, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=1, ensure_ascii=False)
    # contact sheets, 30 per sheet, numbered so photos can be picked by number
    for s in range(0, n, 30):
        sheet = Image.new("RGB", (6 * 200, 5 * 200), "white")
        for i in range(s, min(n, s + 30)):
            im = Image.open(os.path.join(OUT, f"d{i:03d}.jpg")).convert("RGB"); im.thumbnail((196, 196))
            x, y = ((i - s) % 6) * 200, ((i - s) // 6) * 200
            sheet.paste(im, (x + (200 - im.width) // 2, y + (200 - im.height) // 2))
        sheet.save(os.path.join(OUT, f"_sheet_{s // 30}.jpg"), quality=78)
    print(n, "photos saved")


if __name__ == "__main__":
    import sys
    main(GENERIC, 10) if "generic" in sys.argv else main()
