# Vesica Dome

One compass drawing, laid over photos of domes from around the world.

Vesica Dome is a single web page. It builds the drawing step by step over a dome photo, turns the dome into 3D, and can lay the
same drawing over an eye. Nothing is installed and nobody signs in. Your settings stay in your own browser.

## Run it on your own computer

You need Python 3.

```bash
python build_map.py
python -m http.server 8765 --directory site
```

Then open http://localhost:8765 in a browser.

## What is in here

| Path | What it is |
|---|---|
| `app_template.html` | The page: layout, styles and behaviour, in one file |
| `build_map.py` | Fills the page with the dome data and writes the finished site into `site/` |
| `domes/` | The dome photos, where the drawing sits on each, and who took each photo |
| `eyes/` | The eye photos and the two pictures that can lie under the drawing |
| `lib/` | The two libraries the page uses, Leaflet (maps) and three.js (3D), each with its licence |
| `draw_all.py`, `straighten.py`, `fetch_*.py` and the rest | How the photos were found, straightened and given a first placement |
| `site/` | The built site. Made by `build_map.py`, not kept in the repository |

Building needs only Python's standard library. The photo scripts also need Pillow and Requests.

## The photos

Every photo is someone else's work, used under an open licence. The page lists each photo's author and licence under
Photo Credits, with a link back to where it came from. Dome photos are straightened and cropped; the others are only made
smaller. Photos that are not under an open licence are not used.

The same credits are kept in `domes/*/_index.json`, `domes/all/photo_meta.json` and `eyes/_index.json`.

## Licence

The code is under the MIT licence: see `LICENSE`. That covers the page, the build script and the photo scripts.

It does not cover the photos, which stay under their own licences as listed in the credits, or the two libraries in `lib/`,
which carry their own licence files. The name Vesica Dome and its eye mark are not part of the licence.
