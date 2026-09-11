# gpx2core

The shared engine of the gpx2 tools, meant to be included as a **git submodule**:

- [gpx2engraving](https://github.com/YannickRiou/gpx2engraving) — GPX to laser-ready SVG (LightBurn).
  The reference implementation; `engine.py` is that script turned into a library.
- [gpx2map](https://github.com/YannickRiou/gpx2map) — GPX to themed map picture (PNG).
- [gpx2anim](https://github.com/YannickRiou/gpx2anim) — GPX to animated GIF / MP4.

Nothing here is meant to be run by itself (although `python engine.py track.gpx` behaves like
gpx2engraving and writes the SVG).

## Contents

### `engine.py` — the pipeline

The gpx2engraving pipeline, split into a parser and a builder so that other tools can add
their own options and consume the result in memory:

```python
import engine
ap = engine.build_parser(add_output=False)      # all gpx2engraving options, minus --out
ap.add_argument("--dpi", type=int, default=300)  # the tool's own options
args = ap.parse_args()
plate = engine.build(args)                       # runs everything, writes nothing
```

`build()` reads and merges the GPX files, smooths and despikes them, projects to Lambert-93,
lays the plate out, downloads and caches the IGN RGE ALTI DEM, computes the contour lines and
the IGN BD TOPO lakes, converts the texts to paths, draws the elevation profile. It returns a
`Plate`:

| Attribute | Content |
|---|---|
| `plate.svg` | `SvgDoc`: the drawing in mm, one list of SVG elements per group (`frame`, `contours`, `contours_index`, `water`, `water_hatch`, `track`, `track_line`, `profile`, `profile_fill`, `text`); `svg.write(path)` writes the LightBurn SVG |
| `plate.lay` | `Layout`: plate size, map window, geographic frame, scale |
| `plate.track` | `Track`: projected points, cumulative distance, times, stages |
| `plate.meta` | dict: `plate_mm`, `map_mm`, `frame` (EPSG:2154), `track` (centre line in mm with cumulative distance, one list per segment), `profile` (plot rectangle, elevation range, curve), `title`, `stats`, `distance_m`, `ascent_m`... |
| `plate.summary` | the JSON summary gpx2engraving prints |

Fonts are looked up in the `fonts/` folder of the **tool** that embeds the engine (then the
system fonts), and the DEM cache defaults to that tool's `cache/`.

### `render.py` — themes

Rendering of a `Plate` with matplotlib, in a theme: a dict of colours (`bg`, `text`, `track`,
`contours`, `index`, `water`, `water_edge`, `profile`, `curve`, `frame`, `map_bg`,
`track_halo`) and effects (`fade`, `grain`, `sat_dim`, per-layer alphas, `satellite`).

```python
import render
fig = render.render(plate, "midnight", dpi=300)                       # matplotlib Figure
rgb = render.render_array(plate, "satellite", dpi=150, exclude=("track",))   # numpy (H, W, 3)
render.save_png(plate, "ink", "plate_ink.png", dpi=300, overrides={"track": "#DBE64C"})
render.add_theme_options(ap)          # --theme, --list-themes, --bg, --track, ..., --set KEY=VALUE
render.overrides_from_args(args)      # -> dict for resolve_theme / render(..., overrides=)
```

Eighteen themes: `wood`, `paper`, `ink`, `topo`, `monoblue`, `pastel`, `forest`, `ocean`,
`terracotta`, `copper`, `sunset`, `autumn`, `noir`, `midnight`, `blueprint`, `emerald`, `neon`
and `satellite` (IGN orthophoto under the contours). The gallery is in the gpx2map README.

## Using it in a tool

```bash
git submodule add https://github.com/YannickRiou/gpx2core core
```

```python
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "core"))
import engine, render
```

Users clone the tool with `git clone --recursive`, or run `git submodule update --init`.

## Requirements

Python 3.10 or newer with numpy, scipy, shapely, pyproj, requests, contourpy, fontTools, and
matplotlib (with Pillow) for `render.py`. The Python bundled with QGIS has all of them.

## Keeping it in sync with gpx2engraving

`engine.py` is gpx2engraving.py with `main()` split into `build_parser()` and `build()`, a
`Plate` class, `TOOL_DIR` for fonts and cache, and the in-memory `meta` dict. When
gpx2engraving changes, port the change here (the SVG written by `engine.py` must stay identical
to gpx2engraving's).

## Licence

MIT.
