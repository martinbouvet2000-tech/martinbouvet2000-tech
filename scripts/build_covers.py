"""Generate the project covers used in the profile README.

One system, three projects: same grid, same type scale, same restrained accent;
a different concept glyph per project. Stdlib only, no network.

    python scripts/build_covers.py
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "covers"

T = {  # design tokens
    "bg": "#0B0D10", "surface": "#11151A", "border": "#252A31",
    "text": "#F5F7FA", "muted": "#8B949E", "accent": "#F0883E",
    "sans": "-apple-system,'Segoe UI',Inter,Helvetica,Arial,sans-serif",
    "mono": "ui-monospace,SFMono-Regular,Consolas,monospace",
}
W, H = 1200, 260


def night_glyph() -> str:
    """nightshift: a 24-hour arc, the agent working through the night."""
    p = ['<g transform="translate(1000,130)">']
    p.append(f'<path d="M0 -84 A84 84 0 0 1 59 59" fill="none" stroke="{T["text"]}" '
             f'stroke-opacity=".06" stroke-width="26"/>')
    p.append(f'<circle r="84" fill="none" stroke="{T["border"]}"/>')
    for hour, label in ((0, "00"), (6, "06"), (12, "12"), (18, "18")):
        import math
        a = (hour / 24) * 2 * math.pi - math.pi / 2
        x1, y1 = 84 * math.cos(a), 84 * math.sin(a)
        x2, y2 = 93 * math.cos(a), 93 * math.sin(a)
        tx, ty = 108 * math.cos(a), 108 * math.sin(a)
        p.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{T["muted"]}"/>')
        p.append(f'<text x="{tx:.1f}" y="{ty + 4:.1f}" text-anchor="middle" font-family="{T["mono"]}" '
                 f'font-size="10" fill="{T["muted"]}">{label}</text>')
    for x, y in ((-6, -70), (52, -50), (70, 8), (-70, 6)):
        p.append(f'<circle cx="{x}" cy="{y}" r="4" fill="{T["accent"]}"/>')
    p.append(f'<line x1="0" y1="0" x2="-42" y2="-42" stroke="{T["text"]}" stroke-width="2" stroke-linecap="round"/>')
    p.append(f'<circle r="3" fill="{T["text"]}"/>')
    p.append("</g>")
    return "".join(p)


def couple_glyph() -> str:
    """Nous Deux: two spaces, one link, locked at the database."""
    p = ['<g transform="translate(1000,130)">']
    p.append(f'<circle cx="-62" cy="0" r="40" fill="none" stroke="{T["muted"]}" stroke-opacity=".7"/>')
    p.append(f'<circle cx="62" cy="0" r="40" fill="none" stroke="{T["accent"]}"/>')
    p.append(f'<path d="M-62 0V-24M-62 0l16 12" stroke="{T["muted"]}" stroke-linecap="round" fill="none"/>')
    p.append(f'<path d="M62 0V-20M62 0l-18 10" stroke="{T["accent"]}" stroke-linecap="round" fill="none"/>')
    p.append(f'<path d="M-22 0h44" stroke="{T["border"]}" stroke-dasharray="4 5"/>')
    p.append(f'<rect x="-9" y="-11" width="18" height="15" rx="3" fill="{T["bg"]}" stroke="{T["accent"]}"/>')
    p.append(f'<path d="M-4 -11v-5a4 4 0 0 1 8 0v5" fill="none" stroke="{T["accent"]}"/>')
    p.append(f'<text x="0" y="62" text-anchor="middle" font-family="{T["mono"]}" font-size="10" '
             f'fill="{T["muted"]}">ROW-LEVEL SECURITY</text>')
    p.append("</g>")
    return "".join(p)


def cortex_glyph() -> str:
    """Cortex: a handout in, a study system out."""
    p = ['<g transform="translate(908,124)">']
    p.append(f'<rect x="-40" y="-46" width="62" height="86" rx="6" fill="none" stroke="{T["muted"]}"/>')
    for i, wdt in enumerate((40, 40, 26)):
        p.append(f'<path d="M-28 {-26 + i * 16}h{wdt}" stroke="{T["muted"]}" stroke-opacity=".8"/>')
    p.append(f'<path d="M34 -3h26" stroke="{T["accent"]}" stroke-width="2"/>')
    p.append(f'<path d="M56 -8l8 5-8 5z" fill="{T["accent"]}"/>')
    p.append(f'<rect x="72" y="-40" width="74" height="30" rx="6" fill="none" stroke="{T["accent"]}"/>')
    p.append(f'<rect x="72" y="4" width="74" height="30" rx="6" fill="none" stroke="{T["accent"]}"/>')
    p.append(f'<text x="109" y="-21" text-anchor="middle" font-family="{T["mono"]}" font-size="9" '
             f'fill="{T["text"]}">SHEET</text>')
    p.append(f'<text x="109" y="23" text-anchor="middle" font-family="{T["mono"]}" font-size="9" '
             f'fill="{T["text"]}">QUIZ</text>')
    for i, r in enumerate((3, 3.5, 4, 4.5, 5)):
        p.append(f'<circle cx="{176 + i * 18}" cy="-3" r="{r}" fill="{T["accent"]}" '
                 f'fill-opacity="{0.25 + i * 0.15:.2f}"/>')
    p.append(f'<text x="212" y="30" text-anchor="middle" font-family="{T["mono"]}" font-size="9" '
             f'fill="{T["muted"]}">D+1 · 3 · 7 · 14 · 30</text>')
    p.append("</g>")
    return "".join(p)


PROJECTS = [
    {"slug": "nightshift", "index": "01", "kind": "AI SYSTEM", "name": "nightshift",
     "tagline": "A second brain that works while you sleep.", "glyph": night_glyph,
     "readouts": [("STATUS", "OPEN SOURCE", True), ("TESTS", "89", False),
                  ("CI", "LINUX + WINDOWS", False), ("RUNS", "NIGHTLY · 00:30", False)]},
    {"slug": "nous-deux", "index": "02", "kind": "PRODUCT", "name": "Nous Deux",
     "tagline": "Warm product, paranoid backend.", "glyph": couple_glyph,
     "readouts": [("STATUS", "LIVE", True), ("TESTS", "374", False),
                  ("MIGRATIONS", "24", False), ("SIGN-UPS", "CAPPED AT 2", False)]},
    {"slug": "cortex", "index": "03", "kind": "PRODUCT", "name": "Cortex",
     "tagline": "Course handout in, study system out.", "glyph": cortex_glyph,
     "readouts": [("STATUS", "LIVE · DEMO MODE", True), ("TESTS", "33", False),
                  ("BILLING", "STRIPE", False), ("CODE", "PRIVATE", False)]},
]


def readouts(p) -> str:
    """The instrument row: four values you can check against the repo."""
    out = []
    for i, (label, value, live) in enumerate(p["readouts"]):
        x = 64 + i * 178
        out.append(f'<text x="{x}" y="196" font-family="{T["mono"]}" font-size="10" '
                   f'fill="{T["muted"]}" letter-spacing="1.8">{label}</text>')
        vx = x + (14 if live else 0)
        if live:
            out.append(f'<circle cx="{x + 4}" cy="{214}" r="3.5" fill="{T["accent"]}"/>')
        out.append(f'<text x="{vx}" y="219" font-family="{T["mono"]}" font-size="14" '
                   f'fill="{T["text"]}">{value}</text>')
    return "".join(out)


def cover(p) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" \
role="img" aria-labelledby="t-{p['slug']} d-{p['slug']}">
  <title id="t-{p['slug']}">{p['index']} — {p['name']}</title>
  <desc id="d-{p['slug']}">{p['tagline']} \
{' '.join(f'{k} {v}.' for k, v, _ in p['readouts'])}</desc>
  <defs>
    <pattern id="g-{p['slug']}" width="40" height="40" patternUnits="userSpaceOnUse">
      <path d="M40 0H0V40" fill="none" stroke="{T['border']}" stroke-width="1" stroke-opacity=".55"/>
    </pattern>
  </defs>
  <rect width="{W}" height="{H}" rx="14" fill="{T['bg']}"/>
  <rect width="{W}" height="{H}" rx="14" fill="url(#g-{p['slug']})"/>
  <rect x="0" y="0" width="4" height="{H}" rx="2" fill="{T['accent']}"/>
  <text x="64" y="54" font-family="{T['mono']}" font-size="12" fill="{T['accent']}" \
letter-spacing="2.6">{p['index']} / {p['kind']}</text>
  <text x="64" y="106" font-family="{T['sans']}" font-size="42" font-weight="700" \
fill="{T['text']}" letter-spacing="-0.5">{p['name']}</text>
  <text x="64" y="142" font-family="{T['sans']}" font-size="20" fill="{T['muted']}">{p['tagline']}</text>
  <line x1="64" y1="168" x2="760" y2="168" stroke="{T['border']}"/>
  {readouts(p)}
  {p['glyph']()}
</svg>
"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for p in PROJECTS:
        path = OUT / f"{p['slug']}.svg"
        path.write_text(cover(p), encoding="utf-8")
        print(f"{path.relative_to(ROOT)}  {path.stat().st_size} bytes")


if __name__ == "__main__":
    main()
