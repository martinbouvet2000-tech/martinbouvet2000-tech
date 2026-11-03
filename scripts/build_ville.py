"""Draw the agent city as an animated isometric map, from assets/ville.json.

One building per active agent. Its windows are lit when the agent worked that
day, one window turns red per error, and a few residents walk the streets in
proportion to the work done. Pure SVG: CSS animations only, no script, so it
renders inside a README. Every moving thing has a visible resting state,
because GitHub shows this file as an <img> and some browsers freeze its clock.

    python scripts/build_ville.py
"""
import hashlib
import json
import math
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "assets" / "ville.json"
OUT = ROOT / "assets" / "ville.svg"

T = {
    "bg": "#08090B", "chrome": "#14171C", "border": "#252A31", "panel": "#101317",
    "rule": "#232830", "text": "#F5F7FA", "dim": "#8B949E", "faint": "#4A515B",
    "accent": "#F0883E", "ok": "#3FB950", "blue": "#79C0FF", "red": "#F85149",
    "lit": "#F2B66D", "dark": "#1E232A",
    "ground": "#111418", "rim": "#0B0D10", "street": "#181C22", "water": "#0D1F2E",
    "top": "#2A3038", "left": "#171B21", "right": "#20252C",
    "mono": "ui-monospace,SFMono-Regular,'JetBrains Mono',Consolas,monospace",
    "sans": "-apple-system,'Segoe UI',Helvetica,Arial,sans-serif",
}
W, H = 1200, 660
S = 22                   # one grid tile, in pixels
OX, OY = 400, 112        # where grid (0, 0) lands on screen
GRID = 20

# Lots: grid x, grid y, width, depth, height (in tiles). Fixed so the city
# keeps its shape from one day to the next.
LOTS = {
    "patron": (7.0, 7.0, 2.6, 2.6, 4.2),
    "comptoir": (2.2, 2.0, 2.4, 2.2, 3.0),
    "prospecteur": (6.8, 2.0, 1.6, 1.6, 2.0),
    "plume": (9.0, 2.2, 1.6, 1.6, 2.4),
    "tri": (9.2, 4.2, 1.6, 1.2, 1.6),
    "compteur": (6.8, 4.2, 1.4, 1.2, 1.4),
    "ecole": (2.2, 11.3, 2.6, 2.2, 2.2),
    "relecteur": (2.6, 15.2, 1.6, 1.4, 1.6),
    "studio": (15.4, 7.0, 2.8, 2.4, 2.2),
    "graphisme": (15.4, 2.4, 1.6, 1.6, 2.6),
    "interface": (17.2, 3.6, 1.3, 1.6, 3.2),
    "mouvement": (17.4, 11.2, 1.4, 1.6, 1.8),
    "critique": (15.4, 11.2, 1.6, 1.6, 2.8),
    "medecin": (7.2, 15.0, 2.6, 2.0, 1.8),
}
SPARE = [(9.2, 11.4, 1.4, 1.4, 1.6), (15.6, 15.0, 1.4, 1.4, 1.4), (6.8, 11.4, 1.4, 1.4, 1.8),
         (17.6, 14.8, 1.2, 1.2, 2.0), (10.0, 15.4, 0.8, 0.9, 1.4), (4.4, 15.4, 0.9, 1.0, 1.4)]
LIBRARY = (2.4, 7.4, 2.4, 1.8, 1.3)
RIVER = (12.4, 13.8)
STREETS_X = (1.4, 6.0, 11.4, 14.6)   # streets running along grid y
STREETS_Y = (1.0, 6.0, 10.6, 14.2, 18.6)  # streets running along grid x
LABELS = {"patron", "comptoir", "ecole", "studio", "medecin"}


def h01(*parts):
    """A stable number in [0, 1) from any parts: same data, same drawing."""
    return int(hashlib.md5("|".join(map(str, parts)).encode()).hexdigest()[:8], 16) / 2**32


def inside(x, y):
    """The island is a rounded square: superellipse of radius 9.7 around (10, 10)."""
    return ((x - 10) / 9.7) ** 4 + ((y - 10) / 9.7) ** 4 < 1


def iso(x, y, z=0.0):
    return (OX + (x - y) * S * 0.866, OY + (x + y) * S * 0.5 - z * S)


def pts(*ps):
    return " ".join(f"{a:.1f},{b:.1f}" for a, b in ps)


def island():
    ring = []
    for i in range(96):
        a = 2 * math.pi * i / 96
        c, s = math.cos(a), math.sin(a)
        r = 9.7 / (c ** 4 + s ** 4) ** 0.25
        ring.append((10 + r * c, 10 + r * s))
    top = [iso(x, y) for x, y in ring]
    low = [(a, b + 14) for a, b in top]
    return top, low


def box(x, y, w, d, h, fill=None):
    """Three visible faces of a block: top, the face toward +y, the face toward +x."""
    f = fill or (T["top"], T["left"], T["right"])
    a, b, c, e = iso(x, y, h), iso(x + w, y, h), iso(x + w, y + d, h), iso(x, y + d, h)
    b0, c0, e0 = iso(x + w, y, 0), iso(x + w, y + d, 0), iso(x, y + d, 0)
    return [f'<polygon points="{pts(e0, c0, c, e)}" fill="{f[1]}"/>',
            f'<polygon points="{pts(b0, c0, c, b)}" fill="{f[2]}"/>',
            f'<polygon points="{pts(a, b, c, e)}" fill="{f[0]}"/>']


def windows(key, x, y, w, d, h, lit_share, errors):
    """Window grid on the two visible faces. Lit ones are picked by a stable hash."""
    slots = []
    for face in ("y", "x"):
        length = w if face == "y" else d
        cols = max(1, int(length / 0.55))
        rows = max(1, int((h - 0.3) / 0.62))
        for r in range(rows):
            for k in range(cols):
                u0 = (k + 0.28) * length / cols
                z0 = 0.35 + r * 0.62
                slots.append((face, u0, z0, length / cols * 0.44))
    order = sorted(range(len(slots)), key=lambda i: h01(key, i))
    n_lit = round(len(slots) * lit_share)
    lit = set(order[:n_lit])
    red = set(order[n_lit:n_lit + min(errors, 3)]) if errors else set()
    out = []
    for i, (face, u, z, ww) in enumerate(slots):
        if face == "y":
            p = [iso(x + u, y + d, z), iso(x + u + ww, y + d, z),
                 iso(x + u + ww, y + d, z + 0.3), iso(x + u, y + d, z + 0.3)]
        else:
            p = [iso(x + w, y + u, z), iso(x + w, y + u + ww, z),
                 iso(x + w, y + u + ww, z + 0.3), iso(x + w, y + u, z + 0.3)]
        if i in red:
            out.append(f'<polygon points="{pts(*p)}" fill="{T["red"]}"/>')
        elif i in lit:
            cls = ' class="fl"' if h01(key, "fl", i) < 0.3 else ""
            delay = f' style="animation-delay:-{h01(key, "d", i) * 7:.1f}s"' if cls else ""
            out.append(f'<polygon points="{pts(*p)}" fill="{T["lit"]}"{cls}{delay}/>')
        else:
            out.append(f'<polygon points="{pts(*p)}" fill="{T["dark"]}"/>')
    return out


def walkers(done):
    """Residents: each walks one stretch of street and back, eased."""
    n = max(3, min(18, round(done / 6)))
    segs = []
    for sx in STREETS_X:
        segs.append(((sx, 1.6), (sx, 18.4)))
    for sy in STREETS_Y:
        segs.append(((1.6, sy), (18.4, sy)))
    out, css = [], []
    for i in range(n):
        (x0, y0), (x1, y1) = segs[int(h01("seg", i) * len(segs))]
        t0, t1 = sorted((h01("a", i), h01("b", i)))
        t1 = max(t1, t0 + 0.25)
        t1 = min(t1, 1.0)
        pa = (x0 + (x1 - x0) * t0, y0 + (y1 - y0) * t0)
        pb = (x0 + (x1 - x0) * t1, y0 + (y1 - y0) * t1)
        if not (inside(*pa) and inside(*pb)) or RIVER[0] - 0.4 < pa[0] < RIVER[1] + 0.4:
            continue
        a, b = iso(*pa, 0.12), iso(*pb, 0.12)
        dur = 9 + h01("dur", i) * 14
        col = T["accent"] if h01("c", i) < 0.35 else T["text"]
        css.append(f"@keyframes w{i}{{to{{transform:translate({b[0] - a[0]:.1f}px,{b[1] - a[1]:.1f}px)}}}}"
                   f".w{i}{{animation:w{i} {dur:.1f}s ease-in-out -{h01('off', i) * dur:.1f}s infinite alternate}}")
        out.append(f'<circle class="w{i}" cx="{a[0]:.1f}" cy="{a[1] - 2:.1f}" r="2.3" fill="{col}" opacity=".85"/>')
    return out, "".join(css)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace("'", "&#39;")


def stale(d, now):
    age = (now.date() - datetime.fromisoformat(d["date"]).date()).days
    if age < 2:
        return ""
    return f"no data for {age} days, laptop off. This is still the last real day."


def svg(d, now):
    t, st = d["today"], d["studio"]
    lots = {}
    spare = iter(SPARE)
    for b in d["buildings"]:
        lots[b["key"]] = LOTS.get(b["key"]) or next(spare, None)
    by_key = {b["key"]: b for b in d["buildings"]}

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         'role="img" aria-labelledby="t d">',
         '<title id="t">The agent city, one day</title>',
         f'<desc id="d">Isometric map of {d["agents"]["active"]} AI agents on duty on {d["date"]}: '
         f'{t["wakes"]} wake-ups, {t["done"]} done, {t["errors"]} errors. A building per agent, '
         'lit windows where the agent worked that day. Counters only.</desc>']
    walk, walk_css = walkers(t["done"])
    o.append(
        "<defs>"
        f'<radialGradient id="g"><stop offset="0" stop-color="{T["accent"]}" stop-opacity=".30"/>'
        f'<stop offset="1" stop-color="{T["accent"]}" stop-opacity="0"/></radialGradient>'
        f'<clipPath id="isl"><polygon points="{pts(*island()[0])}"/></clipPath>'
        "</defs>"
        "<style>"
        "@keyframes fl{0%,100%{opacity:1}45%{opacity:.55}55%{opacity:.9}}"
        ".fl{animation:fl 7s ease-in-out infinite}"
        "@keyframes glow{0%,100%{opacity:1}50%{opacity:.6}}"
        ".glow{animation:glow 6s ease-in-out infinite}"
        "@keyframes flow{to{stroke-dashoffset:-60}}"
        ".flow{animation:flow 5s linear infinite}"
        "@keyframes ping{0%{r:3;opacity:.9}70%{r:11;opacity:0}100%{r:11;opacity:0}}"
        ".ping{animation:ping 3.2s ease-out infinite}"
        "@keyframes blink{50%{opacity:0}}.cur{animation:blink 1.05s step-end infinite}"
        + walk_css +
        # Narrow viewports (a phone showing the README): drop the fine print,
        # keep three big numbers. Media queries here follow the image's width.
        ".narrow{display:none}"
        "@media (max-width:640px){.wide{display:none}.narrow{display:inline}"
        ".map{transform:translate(-40px,30px) scale(1.1)}}"
        "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
        "</style>")

    # frame and title bar, same as the terminal above it
    o += [f'<rect width="{W}" height="{H}" rx="12" fill="{T["bg"]}" stroke="{T["border"]}"/>',
          f'<path d="M12 0h{W - 24}a12 12 0 0 1 12 12v40H0V12A12 12 0 0 1 12 0z" fill="{T["chrome"]}"/>',
          f'<line x1="0" y1="52" x2="{W}" y2="52" stroke="{T["border"]}"/>',
          f'<circle cx="28" cy="26" r="4" fill="{T["ok"]}"/>',
          f'<circle cx="28" cy="26" r="4" fill="{T["ok"]}" class="ping"/>',
          f'<text x="44" y="30.5" font-family="{T["mono"]}" font-size="12" fill="{T["accent"]}" '
          f'letter-spacing="3" class="wide">THE CITY · {d["agents"]["active"]} AGENTS ON DUTY</text>',
          f'<text x="48" y="40" font-family="{T["mono"]}" font-size="30" fill="{T["accent"]}" '
          f'letter-spacing="4" class="narrow">THE AGENT CITY</text>',
          f'<text x="{W - 28}" y="30.5" text-anchor="end" font-family="{T["mono"]}" font-size="12.5" '
          f'fill="{T["dim"]}" class="wide">founder-os · the day of {d["date"]}</text>']

    # the island
    o.append('<g class="map">')
    top, low = island()
    o.append(f'<polygon points="{pts(*low)}" fill="{T["rim"]}" stroke="{T["border"]}"/>')
    o.append(f'<polygon points="{pts(*top)}" fill="{T["ground"]}" stroke="{T["border"]}"/>')
    o.append('<g clip-path="url(#isl)">')
    for sx in STREETS_X:
        o.append(f'<polygon points="{pts(iso(sx - .45, 0), iso(sx + .45, 0), iso(sx + .45, 20), iso(sx - .45, 20))}" '
                 f'fill="{T["street"]}"/>')
    for sy in STREETS_Y:
        o.append(f'<polygon points="{pts(iso(0, sy - .45), iso(20, sy - .45), iso(20, sy + .45), iso(0, sy + .45))}" '
                 f'fill="{T["street"]}"/>')
    r0, r1 = RIVER
    o.append(f'<polygon points="{pts(iso(r0, -1), iso(r1, -1), iso(r1, 21), iso(r0, 21))}" fill="{T["water"]}"/>')
    for k, off in enumerate((0.35, 0.75, 1.05)):
        a, b = iso(r0 + off, -1), iso(r0 + off, 21)
        o.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="{T["blue"]}" '
                 f'stroke-opacity=".28" stroke-width="1" stroke-dasharray="{6 + 4 * k} {14 + 6 * k}" class="flow" '
                 f'style="animation-duration:{5 + 2 * k}s"/>')
    for sy in (STREETS_Y[1], STREETS_Y[3]):
        o += box(r0 - .3, sy - .45, r1 - r0 + .6, .9, .14, ("#262B33", "#15181D", "#1B1F25"))
    o.append("</g>")

    # glows under the buildings that worked
    for key, lot in lots.items():
        if lot and by_key[key]["done"]:
            x, y, w, dd, _ = lot
            cx, cy = iso(x + w / 2, y + dd / 2)
            rx = 26 + 6 * min(by_key[key]["done"], 30) ** 0.5
            o.append(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.0f}" ry="{rx * .52:.0f}" fill="url(#g)" '
                     f'class="glow" style="animation-delay:-{h01(key, "g") * 6:.1f}s"/>')

    # trees, out of the way of lots and streets
    occupied = [lot for lot in lots.values() if lot] + [LIBRARY]
    trees = []
    for i in range(160):
        x, y = 0.8 + h01("tx", i) * 18.4, 0.8 + h01("ty", i) * 18.4
        if not inside(x, y) or r0 - .5 < x < r1 + .5:
            continue
        if any(abs(x - s) < .9 for s in STREETS_X) or any(abs(y - s) < .9 for s in STREETS_Y):
            continue
        if any(lx - .5 < x < lx + lw + .5 and ly - .5 < y < ly + ld + .5 for lx, ly, lw, ld, _ in occupied):
            continue
        trees.append((x, y))
        if len(trees) >= 34:
            break

    # draw back to front
    items = [(lot[0] + lot[2] + lot[1] + lot[3], "b", key, lot) for key, lot in lots.items() if lot]
    items.append((LIBRARY[0] + LIBRARY[2] + LIBRARY[1] + LIBRARY[3], "lib", None, LIBRARY))
    items += [(x + y, "tree", None, (x, y)) for x, y in trees]
    items.sort(key=lambda it: it[0])
    for _, kind, key, lot in items:
        if kind == "tree":
            x, y = lot
            bx, by = iso(x, y)
            o.append(f'<ellipse cx="{bx:.1f}" cy="{by:.1f}" rx="5" ry="2.4" fill="#07080A"/>'
                     f'<circle cx="{bx:.1f}" cy="{by - 6:.1f}" r="{4.2 + h01("tr", x) * 1.8:.1f}" fill="#16251C"/>')
            continue
        x, y, w, dd, h = lot
        if kind == "lib":
            o += box(x, y, w, dd, h, ("#3A3F46", "#23272D", "#2C3036"))
            for k in range(5):
                cx = x + w * (k + .5) / 5
                a, b = iso(cx, y + dd, 0), iso(cx, y + dd, h - .2)
                o.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" '
                         f'stroke="#5A6068" stroke-width="2"/>')
            if d["vault"]["writes"]:
                c = iso(x + w / 2, y + dd / 2, h)
                o.append(f'<circle cx="{c[0]:.1f}" cy="{c[1]:.1f}" r="3" fill="{T["lit"]}" class="fl"/>')
            continue
        b = by_key[key]
        if b["quarter"] == "hopital":
            o += box(x, y, w, dd, h, ("#3B4048", "#262A30", "#2F343A"))
        else:
            o += box(x, y, w, dd, h)
        share = 0 if not b["done"] else min(1.0, 0.18 + b["done"] / 22)
        o += windows(key, x, y, w, dd, h, share, b["errors"])
        c = iso(x + w / 2, y + dd / 2, h)
        if key == "patron":
            o += box(x + w / 2 - .45, y + dd / 2 - .45, .9, .9, h + 1.6)
            tip = iso(x + w / 2, y + dd / 2, h + 2.5)
            base = iso(x + w / 2, y + dd / 2, h + 1.6)
            o.append(f'<line x1="{base[0]:.1f}" y1="{base[1]:.1f}" x2="{tip[0]:.1f}" y2="{tip[1]:.1f}" '
                     f'stroke="{T["dim"]}" stroke-width="1.5"/>')
            o.append(f'<circle cx="{tip[0]:.1f}" cy="{tip[1]:.1f}" r="3" fill="{T["accent"]}"/>'
                     f'<circle cx="{tip[0]:.1f}" cy="{tip[1]:.1f}" r="3" fill="{T["accent"]}" class="ping"/>')
        if b["quarter"] == "hopital":
            col = T["accent"] if d["hospital"]["patients"] else T["ok"]
            o.append(f'<path d="M{c[0] - 7:.1f} {c[1]:.1f}h14M{c[0]:.1f} {c[1] - 4:.1f}v8" '
                     f'stroke="{col}" stroke-width="3" stroke-linecap="round"/>')
        if b["in_hospital"]:
            o.append(f'<circle cx="{c[0]:.1f}" cy="{c[1]:.1f}" r="3.5" fill="{T["red"]}"/>')
        if key == "studio":
            shown = [("ready", T["ok"]), ("to_show", T["accent"]), ("to_rework", T["dim"]),
                     ("to_score", T["faint"]), ("no_capture", T["faint"])]
            frames = [col for k, col in shown for _ in range(min(st[k], 4))][:8]
            for i, col in enumerate(frames):
                fx = x + .3 + (i % 4) * .6
                fy = y + .35 + (i // 4) * .9
                p = [iso(fx, fy, h), iso(fx + .42, fy, h), iso(fx + .42, fy + .6, h), iso(fx, fy + .6, h)]
                o.append(f'<polygon points="{pts(*p)}" fill="none" stroke="{col}" stroke-width="1.4"/>')

    o += walk

    # labels for the five quarters and the library
    def label(x, y, z, name, value, off):
        dx, dy = off
        a = iso(x, y, z)
        tx, ty = a[0] + dx, a[1] + dy
        anchor = "start" if dx > 0 else "end"
        o.append(f'<g class="wide"><line x1="{a[0]:.1f}" y1="{a[1] - 3:.1f}" x2="{tx:.1f}" y2="{ty + 4:.1f}" '
                 f'stroke="{T["faint"]}"/>'
                 f'<text x="{tx + (4 if dx > 0 else -4):.1f}" y="{ty:.1f}" text-anchor="{anchor}" '
                 f'font-family="{T["mono"]}" font-size="12" fill="{T["dim"]}" letter-spacing=".6">'
                 f'{esc(name.upper())} <tspan fill="{T["accent"]}">{value}</tspan></text></g>')

    side = {"patron": (60, -26), "comptoir": (-60, -34), "ecole": (-64, -6),
            "studio": (66, -60), "medecin": (-56, 34), "library": (-40, -56)}
    for key in ("patron", "comptoir", "ecole", "studio", "medecin"):
        if key in by_key and lots.get(key):
            x, y, w, dd, h = lots[key]
            b = by_key[key]
            z = h + (2.5 if key == "patron" else 0)
            val = (("empty" if not d["hospital"]["patients"] else f'{d["hospital"]["patients"]} in')
                   if key == "medecin" else str(b["wakes"]))
            label(x + w / 2, y + dd / 2, z, b["name"], val, side[key])
    lx, ly, lw, ld, lh = LIBRARY
    label(lx + lw / 2, ly + ld / 2, lh, "La Bibliothèque", d["vault"]["writes"], side["library"])

    o.append("</g>")

    # panel
    px, py, pw = 800, 76, 368
    f = T["mono"]
    o.append(f'<g class="wide"><rect x="{px}" y="{py}" width="{pw}" height="512" rx="10" '
             f'fill="{T["panel"]}" stroke="{T["rule"]}"/>')
    o.append(f'<text x="{px + 22}" y="{py + 34}" font-family="{f}" font-size="11.5" fill="{T["accent"]}" '
             f'letter-spacing="2">THE DAY OF {d["date"]}</text>')
    o.append(f'<text x="{px + 20}" y="{py + 96}" font-family="{T["sans"]}" font-size="56" font-weight="700" '
             f'fill="{T["text"]}" letter-spacing="-1">{t["wakes"]}</text>')
    o.append(f'<text x="{px + 22}" y="{py + 120}" font-family="{f}" font-size="13" fill="{T["dim"]}">'
             f'wake-ups across {d["agents"]["active"]} agents '
             f'<tspan fill="{T["faint"]}">· {d["agents"]["total"]} in the org</tspan></text>')
    studio_txt = " · ".join(f"{st[k]} {lbl}" for k, lbl in
                            (("ready", "ready"), ("to_show", "to show"), ("to_rework", "to rework"),
                             ("to_score", "to score")) if st[k]) or "none"
    rows = [("WORK DONE", str(t["done"]), T["text"]),
            ("ERRORS", str(t["errors"]), T["red"] if t["errors"] else T["text"]),
            ("STOPPED AT BUDGET CAP", str(t["capped"]), T["text"]),
            ("HOSPITAL", "empty" if not d["hospital"]["patients"]
             else f'{d["hospital"]["patients"]} agent{"s" * (d["hospital"]["patients"] > 1)} in', T["text"]),
            ("STUDIO", studio_txt, T["text"]),
            ("VAULT WRITES", str(d["vault"]["writes"]), T["text"]),
            ("TESTS DECLARED", str(d["tests"]["declared"]), T["text"])]
    y = py + 160
    for name, val, col in rows:
        o.append(f'<line x1="{px + 22}" y1="{y - 19}" x2="{px + pw - 22}" y2="{y - 19}" stroke="{T["rule"]}"/>')
        o.append(f'<text x="{px + 22}" y="{y}" font-family="{f}" font-size="11.5" fill="{T["dim"]}" '
                 f'letter-spacing="1.3">{name}</text>')
        o.append(f'<text x="{px + pw - 22}" y="{y}" text-anchor="end" font-family="{f}" font-size="13" '
                 f'fill="{col}">{esc(val)}</text>')
        y += 30
    # the day's heartbeat: wake-ups by hour
    y += 4
    o.append(f'<line x1="{px + 22}" y1="{y - 19}" x2="{px + pw - 22}" y2="{y - 19}" stroke="{T["rule"]}"/>')
    o.append(f'<text x="{px + 22}" y="{y}" font-family="{f}" font-size="11.5" fill="{T["dim"]}" '
             f'letter-spacing="1.3">WAKE-UPS BY HOUR</text>')
    top_h = max(t["by_hour"]) or 1
    bw = (pw - 44) / 24
    base = y + 62
    for i, n in enumerate(t["by_hour"]):
        hh = 2 if not n else max(3, 44 * n / top_h)
        col = T["accent"] if n else T["rule"]
        o.append(f'<rect x="{px + 22 + i * bw + 1:.1f}" y="{base - hh:.1f}" width="{bw - 3:.1f}" '
                 f'height="{hh:.1f}" rx="1" fill="{col}"/>')
    for i in (0, 6, 12, 18):
        o.append(f'<text x="{px + 22 + i * bw + 1:.1f}" y="{base + 16}" font-family="{f}" font-size="10.5" '
                 f'fill="{T["faint"]}">{i:02d}</text>')
    o.append(f'<text x="{px + pw - 22}" y="{base + 16}" text-anchor="end" font-family="{f}" font-size="10.5" '
             f'fill="{T["faint"]}">24</text>')
    # legend
    ly0 = py + 486
    for i, (col, txt) in enumerate(((T["lit"], "worked today"), (T["red"], "an error"), (T["dark"], "asleep"))):
        lx0 = px + 22 + i * 112
        o.append(f'<rect x="{lx0}" y="{ly0 - 9}" width="9" height="11" fill="{col}" stroke="{T["rule"]}"/>'
                 f'<text x="{lx0 + 15}" y="{ly0}" font-family="{f}" font-size="11" fill="{T["dim"]}">{txt}</text>')
    o.append("</g>")

    # narrow: three numbers a phone can read
    big = [(str(d["agents"]["active"]), "agents on duty"), (str(t["wakes"]), "wake-ups"),
           (str(t["errors"]), "errors" if t["errors"] != 1 else "error")]
    o.append('<g class="narrow">')
    for i, (n, lbl) in enumerate(big):
        yy = 190 + i * 150
        o.append(f'<text x="1150" y="{yy}" text-anchor="end" font-family="{T["sans"]}" font-size="104" '
                 f'font-weight="700" fill="{T["red"] if i == 2 and t["errors"] else T["text"]}">{n}</text>'
                 f'<text x="1150" y="{yy + 42}" text-anchor="end" font-family="{f}" font-size="30" '
                 f'fill="{T["dim"]}">{lbl}</text>')
    o.append(f'<text x="1150" y="{H - 30}" text-anchor="end" font-family="{f}" font-size="28" '
             f'fill="{T["accent"]}">{d["date"]}</text></g>')

    # caption under the map
    o.append(f'<text x="34" y="{H - 44}" font-family="{f}" font-size="12.5" fill="{T["faint"]}" class="wide">'
             f'A building per agent. Lit windows: it worked that day. Counters only, never the contents.</text>')
    old = stale(d, now)
    if old:
        o.append(f'<text x="34" y="{H - 22}" font-family="{f}" font-size="12.5" fill="{T["dim"]}" class="wide">'
                 f'· {old}<tspan class="cur" fill="{T["accent"]}"> █</tspan></text>')
    o.append("</svg>")
    return "\n".join(o)


def main():
    d = json.loads(DATA.read_text(encoding="utf-8-sig"))
    now = datetime.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else datetime.now()
    OUT.write_text(svg(d, now), encoding="utf-8")
    print(f"{OUT.relative_to(ROOT)}  {OUT.stat().st_size} bytes  day {d['date']}")


if __name__ == "__main__":
    main()
