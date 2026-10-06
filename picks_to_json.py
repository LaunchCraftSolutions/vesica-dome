"""Turn the codes picked from the sheets (domes/found/picks.txt) into domes/world_picks.json: place -> the Commons file chosen."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__)); F = os.path.join(HERE, "domes", "found")
key = {}
for name in ("_key.json", "_key2.json", "_key3.json"):
    if os.path.exists(os.path.join(F, name)):
        key.update(json.load(open(os.path.join(F, name), encoding="utf-8")))
out_path = os.path.join(HERE, "domes", "world_picks.json"); out = json.load(open(out_path, encoding="utf-8")) if os.path.exists(out_path) else {}
for code in open(os.path.join(F, "picks.txt"), encoding="utf-8").read().split():
    k = key[code]; out[k["place"]] = dict(out.get(k["place"], {}), title=k["title"])
json.dump(out, open(out_path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(len(out), "domes picked")
