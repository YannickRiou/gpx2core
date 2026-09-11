#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
render — themed rendering of an engine.Plate with matplotlib.

Shared verbatim by gpx2map (PNG) and gpx2anim (animation background). Themes are plain
dicts of colours and a few effects; the command line can override any of them.
"""

import hashlib
import io
import os
import re
import sys
from collections import OrderedDict

import numpy as np

USER_AGENT = "gpx2map/1.0 (https://github.com/YannickRiou/gpx2map)"
IGN_WMS = "https://data.geopf.fr/wms-r/wms"


def log(*a):
    print(*a, file=sys.stderr, flush=True)


# ----------------------------------------------------------------------------
# Themes
# ----------------------------------------------------------------------------
def theme(desc, bg, text, track, contours, index=None, water=None, water_edge=None, profile=None, curve=None,
          frame=None, map_bg=None, contours_alpha=1.0, index_alpha=1.0, water_alpha=1.0, track_halo=None,
          satellite=False, sat_dim=0.0, fade=0.0, grain=0.0, dark=False):
    """A theme: colours ('#RRGGBB' or '#RRGGBBAA') and a few cosmetic effects.
    water=None: lakes are only outlined (water_edge), which is what you want over a photo.
    fade: fraction of the map height that fades into the plate background (poster look).
    grain: paper grain strength (0..0.1). sat_dim: darkening of the orthophoto (0..1)."""
    return dict(desc=desc, bg=bg, text=text, track=track, contours=contours, index=index or contours,
                water=water, water_edge=water_edge or water or text, profile=profile or text,
                curve=curve or profile or text, frame=frame or text, map_bg=map_bg,
                contours_alpha=contours_alpha, index_alpha=index_alpha, water_alpha=water_alpha,
                track_halo=track_halo, satellite=satellite, sat_dim=sat_dim, fade=fade, grain=grain, dark=dark)


THEMES = OrderedDict([
    # --- light, paper-like ---
    ("wood", theme("engraved wood (default)", bg="#F3E7D3", text="#113B54", track="#113B54",
                   contours="#5A7D8C", index="#113B54", water="#113B54", grain=0.035)),
    ("paper", theme("warm beige, vintage map", bg="#F5F0E8", text="#6B5B4F", track="#8B7355",
                    contours="#C9BBAA", index="#A08B70", water="#DDD5C8", water_edge="#A08B70", grain=0.05)),
    ("ink", theme("japanese ink wash, red accent", bg="#FAF8F5", text="#2C2C2C", track="#8B2500",
                  contours="#B8B8B8", index="#6A6A6A", water="#E8E4E0", water_edge="#909090", grain=0.03)),
    ("topo", theme("classic IGN-style topo map", bg="#FFFFFF", text="#1E1E1E", track="#E1251B",
                   contours="#C3894C", index="#8F5A24", water="#BEE3F5", water_edge="#3F92C9")),
    ("monoblue", theme("single blue family", bg="#F5F8FA", text="#1A3A5C", track="#1A3A5C",
                       contours="#A8C4E0", index="#4A7AA8", water="#D0E0F0", water_edge="#2A5580")),
    ("pastel", theme("dusty blues and mauves", bg="#FAF7F2", text="#5D5A6D", track="#7B8794",
                     contours="#D8D2D8", index="#B5AEBB", water="#D4E4ED", water_edge="#9BA4B0")),
    ("forest", theme("greens and sage", bg="#F0F4F0", text="#2D4A3E", track="#2D4A3E",
                     contours="#A0C8B0", index="#5A8A70", water="#B8D4D4", water_edge="#5A8A70")),
    ("ocean", theme("blues and teals", bg="#F0F8FA", text="#1A5F7A", track="#1A5F7A",
                    contours="#A0D0E0", index="#4A9AB8", water="#B8D8E8", water_edge="#2A7A9A")),
    ("terracotta", theme("mediterranean clay on cream", bg="#F5EDE4", text="#8B4513", track="#A0522D",
                         contours="#D9A08A", index="#B8653A", water="#A8C4C4", water_edge="#7A9A9A", grain=0.03)),
    ("copper", theme("copper on teal patina", bg="#E8F0F0", text="#2A5A5A", track="#B87333",
                     contours="#A8CCCC", index="#6B9E9E", water="#C0D8D8", water_edge="#5A8A8A")),
    ("sunset", theme("oranges and pinks on peach", bg="#FDF5F0", text="#C45C3E", track="#C45C3E",
                     contours="#F0B8A8", index="#D87A5A", water="#F0D8D0", water_edge="#D87A5A")),
    ("autumn", theme("burnt oranges and golds", bg="#FBF7F0", text="#8B4513", track="#8B2500",
                     contours="#E8C888", index="#CC7A30", water="#D8CFC0", water_edge="#B8450A")),
    # --- dark posters ---
    ("noir", theme("black and white", bg="#000000", text="#FFFFFF", track="#FFFFFF",
                   contours="#505050", index="#808080", water="#141414", water_edge="#B0B0B0",
                   fade=0.10, dark=True)),
    ("midnight", theme("navy and gold", bg="#0A1628", text="#D4AF37", track="#D4AF37",
                       contours="#8B7355", index="#C9A227", water="#061020", water_edge="#A8893A",
                       contours_alpha=0.6, fade=0.10, dark=True)),
    ("blueprint", theme("architectural blueprint", bg="#1A3A5C", text="#E8F4FF", track="#FFFFFF",
                        contours="#5A96C0", index="#9FC5E8", water="#0F2840", water_edge="#7BAED4",
                        grain=0.04, dark=True)),
    ("emerald", theme("dark green with mint", bg="#062C22", text="#E3F9F1", track="#4ADEB0",
                      contours="#155C46", index="#249673", water="#0D4536", water_edge="#2DB88F",
                      fade=0.10, dark=True)),
    ("neon", theme("electric pink and cyan", bg="#0D0D1A", text="#00FFFF", track="#FF00FF",
                   contours="#006870", index="#0098A0", water="#0A0A15", water_edge="#00C8C8",
                   track_halo="#FF00FF55", fade=0.12, dark=True)),
    # --- realistic ---
    ("satellite", theme("realistic: IGN orthophoto under the contours", bg="#0E1418", text="#F4F4F0",
                        track="#DBE64C", track_halo="#00000099", contours="#FFFFFF", index="#FFFFFF",
                        contours_alpha=0.32, index_alpha=0.6, water=None, water_edge="#8FD8F0",
                        water_alpha=0.85, curve="#DBE64C", satellite=True, sat_dim=0.22, map_bg="#2B3A2E",
                        dark=True)),
])
DEFAULT_THEME = "wood"

COLOR_KEYS = ("bg", "text", "track", "contours", "index", "water", "water_edge", "profile", "curve", "frame",
              "map_bg", "track_halo")
BOOL_KEYS = ("satellite", "dark")
NUMBER_KEYS = ("contours_alpha", "index_alpha", "water_alpha", "sat_dim", "fade", "grain")


def parse_color(v):
    """'#RRGGBB', 'RRGGBB', '#RRGGBBAA', or 'none' (no fill / no halo)."""
    v = str(v).strip()
    if v.lower() in ("none", "", "off"):
        return None
    v = v.lstrip("#")
    if len(v) not in (6, 8) or any(c not in "0123456789abcdefABCDEF" for c in v):
        raise SystemExit(f"bad colour '{v}': use #RRGGBB or #RRGGBBAA")
    return "#" + v.upper()


def resolve_theme(theme, overrides=None):
    """A theme name or dict plus command-line overrides ({key: value}) -> theme dict.
    Colours accept '#RRGGBB[AA]' or 'none'; effects accept numbers; satellite/dark accept true/false."""
    th = dict(THEMES[theme]) if isinstance(theme, str) else dict(theme)
    for k, v in (overrides or {}).items():
        k = k.strip().lower().replace("-", "_")
        if k in COLOR_KEYS:
            th[k] = parse_color(v)
        elif k in BOOL_KEYS:
            th[k] = str(v).strip().lower() in ("1", "true", "yes", "on")
        elif k in NUMBER_KEYS:
            th[k] = float(v)
        else:
            raise SystemExit(f"unknown theme key '{k}'. Colours: {', '.join(COLOR_KEYS)}; "
                             f"effects: {', '.join(NUMBER_KEYS + BOOL_KEYS)}")
    if th["water_edge"] is None:
        th["water_edge"] = th["water"] or th["text"]
    return th


def add_theme_options(ap, default_theme=DEFAULT_THEME):
    """--theme, --list-themes and the colour overrides, shared by gpx2map and gpx2anim."""
    ap.add_argument("--theme", default=default_theme, metavar="THEMES",
                    help="theme(s), comma-separated, or 'all' (see --list-themes)")
    ap.add_argument("--list-themes", action="store_true", help="list the themes and exit")
    g = ap.add_argument_group("colours (override the theme; '#RRGGBB', or 'none' to drop a fill)")
    for k, help_ in (("bg", "plate background"), ("text", "title, statistics, labels"),
                     ("track", "GPX track"), ("contours", "contour lines"), ("index", "index contours"),
                     ("water", "lake fill ('none' = outline only)"), ("water-edge", "lake outline"),
                     ("profile", "profile axes and ticks"), ("curve", "profile curve"),
                     ("frame", "plate outline")):
        g.add_argument(f"--{k}-color", metavar="COLOUR", help=help_)
    g.add_argument("--set", action="append", default=[], metavar="KEY=VALUE",
                   help="any other theme key, e.g. --set fade=0.15 --set grain=0 --set track_halo=#00000080 "
                        "--set sat_dim=0.4 --set map_bg=#202020")
    ap.add_argument("--no-labels", action="store_true",
                    help="no lake names and no highest-point altitude on the map")
    ap.add_argument("--map-label-size", type=float, default=None, metavar="MM",
                    help="size of the map labels in mm (default: the profile label size)")


def overrides_from_args(args):
    ov = {}
    for k in ("bg", "text", "track", "contours", "index", "water", "water_edge", "profile", "curve", "frame"):
        v = getattr(args, k + "_color", None)
        if v is not None:
            ov[k] = v
    for kv in getattr(args, "set", []) or []:
        if "=" not in kv:
            raise SystemExit(f"--set expects KEY=VALUE, got '{kv}'")
        k, v = kv.split("=", 1)
        ov[k] = v
    return ov


def theme_list(names):
    """'wood', 'wood,satellite' or 'all' -> validated list of theme names."""
    if names.strip().lower() == "all":
        return list(THEMES)
    out = []
    for n in names.split(","):
        n = n.strip().lower()
        if n not in THEMES:
            raise SystemExit(f"unknown theme '{n}'. Available: {', '.join(THEMES)}")
        out.append(n)
    return out


def print_themes():
    for name, th in THEMES.items():
        print(f"{name:<11} {th['desc']}")


# ----------------------------------------------------------------------------
# SVG elements of the plate -> geometry
# ----------------------------------------------------------------------------
_PATH_TOKEN = re.compile(r"[MLHVCQZmlhvcqz]|-?\d*\.?\d+(?:e-?\d+)?")


def svg_d_to_mpl(d):
    from matplotlib.path import Path
    toks = _PATH_TOKEN.findall(d)
    verts, codes = [], []
    i = 0
    cur = (0.0, 0.0)
    cmd = None
    while i < len(toks):
        t = toks[i]
        if t.isalpha():
            cmd = t
            i += 1
            if cmd in "Zz":
                verts.append((0, 0))
                codes.append(Path.CLOSEPOLY)
            continue
        if cmd == "M":
            cur = (float(toks[i]), float(toks[i + 1]))
            verts.append(cur); codes.append(Path.MOVETO); i += 2; cmd = "L"
        elif cmd == "L":
            cur = (float(toks[i]), float(toks[i + 1]))
            verts.append(cur); codes.append(Path.LINETO); i += 2
        elif cmd == "H":
            cur = (float(toks[i]), cur[1]); verts.append(cur); codes.append(Path.LINETO); i += 1
        elif cmd == "V":
            cur = (cur[0], float(toks[i])); verts.append(cur); codes.append(Path.LINETO); i += 1
        elif cmd == "Q":
            p1 = (float(toks[i]), float(toks[i + 1])); p2 = (float(toks[i + 2]), float(toks[i + 3]))
            verts += [p1, p2]; codes += [Path.CURVE3, Path.CURVE3]; cur = p2; i += 4
        elif cmd == "C":
            p1 = (float(toks[i]), float(toks[i + 1])); p2 = (float(toks[i + 2]), float(toks[i + 3]))
            p3 = (float(toks[i + 4]), float(toks[i + 5]))
            verts += [p1, p2, p3]; codes += [Path.CURVE4] * 3; cur = p3; i += 6
        else:
            i += 1
    if not verts:
        return None
    return Path(verts, codes)


def elements(plate, name):
    """Yield ('polyline', (n,2) array) / ('path', d) / ('rect', dict) for a group of the plate."""
    for el in plate.svg.items.get(name, []):
        if el.startswith("<polyline"):
            pts = re.search(r'points="([^"]*)"', el).group(1).split()
            if len(pts) >= 2:
                yield "polyline", np.array([[float(v) for v in p.split(",")] for p in pts])
        elif el.startswith("<path"):
            yield "path", re.search(r'd="([^"]*)"', el).group(1)
        elif el.startswith("<rect"):
            g = lambda k: float(re.search(k + r'="([^"]*)"', el).group(1)) if (k + '="') in el else 0.0
            yield "rect", dict(x=g("x"), y=g("y"), width=g("width"), height=g("height"), rx=g("rx"))


# ----------------------------------------------------------------------------
# IGN orthophoto (satellite theme)
# ----------------------------------------------------------------------------
def fetch_ortho(bbox, width_px, height_px, cache_dir, layer="ORTHOIMAGERY.ORTHOPHOTOS", tile=2000):
    """IGN orthophoto over a Lambert-93 bbox as an RGB array (HxWx3 uint8), through the
    Géoplateforme WMS-Raster (open data, no key). Tiled, cached as JPEG in cache_dir."""
    import requests
    from PIL import Image
    x0, y0, x1, y1 = bbox
    W, H = int(width_px), int(height_px)
    key = hashlib.md5(f"{layer}|{x0:.1f}|{y0:.1f}|{x1:.1f}|{y1:.1f}|{W}|{H}".encode()).hexdigest()[:12]
    os.makedirs(cache_dir, exist_ok=True)
    cache = os.path.join(cache_dir, f"ortho_{key}.jpg")
    if os.path.exists(cache):
        log(f"  Orthophoto: cached ({W}x{H} px)")
        return np.asarray(Image.open(cache).convert("RGB"))
    log(f"  Orthophoto: downloading IGN {layer} ({W}x{H} px)")
    img = Image.new("RGB", (W, H))
    for r0 in range(0, H, tile):
        for c0 in range(0, W, tile):
            r1, c1 = min(H, r0 + tile), min(W, c0 + tile)
            bx0, bx1 = x0 + (x1 - x0) * c0 / W, x0 + (x1 - x0) * c1 / W
            by1, by0 = y1 - (y1 - y0) * r0 / H, y1 - (y1 - y0) * r1 / H
            params = dict(SERVICE="WMS", VERSION="1.3.0", REQUEST="GetMap", LAYERS=layer, STYLES="",
                          CRS="EPSG:2154", BBOX=f"{bx0},{by0},{bx1},{by1}",
                          WIDTH=c1 - c0, HEIGHT=r1 - r0, FORMAT="image/jpeg")
            r = requests.get(IGN_WMS, params=params, headers={"User-Agent": USER_AGENT}, timeout=180)
            ct = r.headers.get("content-type", "")
            if r.status_code != 200 or not ct.startswith("image/"):
                raise RuntimeError(f"IGN WMS request failed ({r.status_code}, {ct}): {r.text[:200]}")
            img.paste(Image.open(io.BytesIO(r.content)).convert("RGB"), (c0, r0))
    img.save(cache, quality=92)
    return np.asarray(img)


# ----------------------------------------------------------------------------
# Rendering
# ----------------------------------------------------------------------------
def rgba(color, alpha=None):
    """'#RRGGBB' or '#RRGGBBAA' -> (r, g, b, a) floats; alpha overrides the alpha channel."""
    c = color.lstrip("#")
    r, g, b = (int(c[i:i + 2], 16) / 255 for i in (0, 2, 4))
    a = int(c[6:8], 16) / 255 if len(c) == 8 else 1.0
    return (r, g, b, a if alpha is None else alpha)


def draw_labels(ax, plate, th, label_size_mm=None):
    """Lake names and the altitude of the highest point, written on the map with a halo in the
    background colour so they stay readable over contours, lakes or the orthophoto.
    Only on renderings (never on the engraving SVG)."""
    from matplotlib import patheffects
    from matplotlib.font_manager import FontProperties
    meta = plate.meta
    size_mm = label_size_mm or meta.get("label_size_mm") or 2.4
    pt = size_mm * 72 / 25.4
    font = FontProperties(fname=meta["fonts"]["body"]) if meta.get("fonts", {}).get("body") else FontProperties()
    color = rgba(th["text"])
    halo = [patheffects.withStroke(linewidth=pt * 0.28, foreground=rgba(th["map_bg"] or th["bg"], 0.9))]
    mx, my, mw, mh = meta["map_mm"]
    x_lo, x_hi, y_lo, y_hi = mx + 1.5, mx + mw - 1.5, my + 1.5, my + mh - 1.5

    def text(x, y, s, ha, va, weight="normal", z=4.5):
        x = min(max(x, x_lo), x_hi); y = min(max(y, y_lo), y_hi)
        t = ax.text(x, y, s, fontproperties=font, fontsize=pt, color=color, ha=ha, va=va, zorder=z,
                    fontweight=weight, clip_on=True)
        t.set_path_effects(halo)

    for lake in meta.get("lakes", []):
        cx, cy = lake["xy_mm"]
        bx0, by0, bx1, by1 = lake["bbox_mm"]
        if lake["area_mm2"] >= 40 and (bx1 - bx0) >= size_mm * 0.55 * len(lake["name"]):
            text(cx, cy, lake["name"], "center", "center")            # big lake: name inside
        else:
            text(bx1 + 0.8, (by0 + by1) / 2, lake["name"], "left", "center")   # small: to its right
    s = meta.get("summit")
    if s:
        x, y = s["xy_mm"]
        ax.plot([x], [y], marker="^", markersize=pt * 0.9, color=color, markeredgecolor=rgba(th["bg"]),
                markeredgewidth=pt * 0.08, zorder=4.4, clip_on=True)
        text(x + size_mm * 0.7, y - size_mm * 0.3, s["label"], "left", "bottom", weight="bold")


def render(plate, theme=DEFAULT_THEME, dpi=300, exclude=(), skip_polyline=None, cache_dir="cache", overrides=None,
           labels=True, label_size_mm=None):
    """Render an engine.Plate with a theme (name or dict); returns a matplotlib Figure sized to
    the plate. exclude: group names not to draw (e.g. ("track",) for an animation background);
    skip_polyline: optional predicate (group, xy) -> bool to leave out some polylines;
    labels: lake names and highest point written on the map."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import PathPatch, FancyBboxPatch, Rectangle
    th = resolve_theme(theme, overrides)
    W, H = plate.W, plate.H
    fig = plt.figure(figsize=(W / 25.4, H / 25.4), dpi=dpi)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W); ax.set_ylim(H, 0); ax.axis("off")
    fig.patch.set_facecolor(th["bg"])
    pt_per_mm = 72 / 25.4
    mx, my, mw, mh = plate.meta["map_mm"]

    # ---- map window: flat colour and/or orthophoto ----
    if th["map_bg"]:
        ax.add_patch(Rectangle((mx, my), mw, mh, facecolor=th["map_bg"], edgecolor="none", zorder=0.5))
    if th["satellite"]:
        try:
            px_w = min(int(mw / 25.4 * dpi), 4000)
            px_h = max(1, int(round(px_w * mh / mw)))
            ortho = fetch_ortho(plate.meta["frame"], px_w, px_h, cache_dir)
            ax.imshow(ortho, extent=(mx, mx + mw, my + mh, my), zorder=0.6, interpolation="bilinear")
        except Exception as e:  # offline, outside France...: flat background instead
            log(f"  Orthophoto unavailable, flat background instead ({e})")
        if th["sat_dim"] > 0:
            ax.add_patch(Rectangle((mx, my), mw, mh, facecolor=(0, 0, 0, th["sat_dim"]), edgecolor="none",
                                   zorder=0.7))

    def draw(name, color, alpha=1.0, lw=0.2, filled=False, edge=None, zorder=2, halo=None):
        if name in exclude:
            return
        col = rgba(color, alpha)
        for kind, el in elements(plate, name):
            if kind == "polyline":
                if skip_polyline and skip_polyline(name, el):
                    continue
                ax.plot(el[:, 0], el[:, 1], color=col, lw=lw * pt_per_mm, solid_capstyle="round",
                        solid_joinstyle="round", zorder=zorder)
            elif kind == "path":
                pth = svg_d_to_mpl(el)
                if pth is None:
                    continue
                if halo:
                    ax.add_patch(PathPatch(pth, facecolor="none", edgecolor=rgba(halo), lw=0.5 * pt_per_mm,
                                           zorder=zorder - 0.1))
                if filled:
                    ax.add_patch(PathPatch(pth, facecolor=col, edgecolor=rgba(edge) if edge else col,
                                           lw=(0.12 if edge else 0.05) * pt_per_mm, zorder=zorder))
                else:
                    ax.add_patch(PathPatch(pth, facecolor="none", edgecolor=rgba(edge or color, alpha),
                                           lw=0.15 * pt_per_mm, zorder=zorder))

    draw("contours", th["contours"], th["contours_alpha"], lw=0.12, zorder=2)
    draw("contours_index", th["index"], th["index_alpha"], lw=0.2, zorder=2.1)
    if th["water"]:
        draw("water", th["water"], th["water_alpha"], filled=True, edge=th["water_edge"], zorder=2.3)
    else:
        draw("water", th["water_edge"], th["water_alpha"], filled=False, zorder=2.3)
    draw("water_hatch", th["water_edge"], th["water_alpha"], lw=0.12, zorder=2.35)
    draw("track", th["track"], filled=True, zorder=3, halo=th["track_halo"])
    draw("track_line", th["track"], lw=0.35, zorder=3, halo=th["track_halo"])
    draw("profile_fill", th["curve"], 0.85, filled=True, zorder=2.8)
    draw("profile", th["profile"], lw=0.2, zorder=3)
    draw("text", th["text"], filled=True, zorder=4)
    if labels and plate.meta.get("summit"):
        draw_labels(ax, plate, th, label_size_mm)

    # ---- poster-like fade of the map into the plate background ----
    if th["fade"] > 0:
        fh = mh * th["fade"]
        r, g, b, _ = rgba(th["bg"])
        grad = np.zeros((64, 1, 4)); grad[..., :3] = (r, g, b)
        grad[:, 0, 3] = np.linspace(1.0, 0.0, 64) ** 1.6
        ax.imshow(grad, extent=(mx, mx + mw, my + fh, my), aspect="auto", zorder=3.5, interpolation="bilinear")
        ax.imshow(grad[::-1], extent=(mx, mx + mw, my + mh, my + mh - fh), aspect="auto", zorder=3.5,
                  interpolation="bilinear")

    # ---- paper grain ----
    if th["grain"] > 0:
        gh, gw = int(H * 4), int(W * 4)
        noise = np.random.default_rng(7).random((gh, gw))
        grain = np.zeros((gh, gw, 4)); grain[..., :3] = 1.0 if th["dark"] else 0.0
        grain[..., 3] = noise * th["grain"]
        ax.imshow(grain, extent=(0, W, H, 0), zorder=5, interpolation="nearest")

    # ---- plate outline ----
    if "frame" not in exclude:
        for kind, el in elements(plate, "frame"):
            if kind != "rect":
                continue
            rx = el["rx"]
            ax.add_patch(FancyBboxPatch((el["x"] + rx, el["y"] + rx), el["width"] - 2 * rx, el["height"] - 2 * rx,
                                        boxstyle=f"round,pad={rx},rounding_size={rx}", fill=False,
                                        edgecolor=rgba(th["frame"], 0.9), lw=0.3 * pt_per_mm, zorder=6))
    return fig


def render_array(plate, theme=DEFAULT_THEME, dpi=300, **kw):
    """Render to an RGB uint8 array (H, W, 3)."""
    import matplotlib.pyplot as plt
    fig = render(plate, theme, dpi, **kw)
    fig.canvas.draw()
    arr = np.asarray(fig.canvas.buffer_rgba())[..., :3].copy()
    plt.close(fig)
    return arr


def save_png(plate, theme, path, dpi=300, **kw):
    import matplotlib.pyplot as plt
    fig = render(plate, theme, dpi, **kw)
    fig.savefig(path, dpi=dpi, facecolor=fig.get_facecolor())
    plt.close(fig)
