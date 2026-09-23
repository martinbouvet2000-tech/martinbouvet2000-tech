"""Replay last night's agent run as a terminal.

Reads assets/last-run.json — counters written by the night agent on my machine —
and draws the run as a terminal that types itself out. Counters only: no note
title, no vault content, ever leaves the machine.

    python scripts/build_nightly.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "assets" / "last-run.json"
OUT = ROOT / "assets" / "nightly.svg"

T = {
    "bg": "#08090B", "chrome": "#14171C", "border": "#252A31",
    "text": "#F5F7FA", "dim": "#8B949E", "faint": "#4A515B",
    "accent": "#F0883E", "ok": "#3FB950", "blue": "#79C0FF",
    "mono": "ui-monospace,SFMono-Regular,'JetBrains Mono',Consolas,monospace",
}
W, LINE, TOP, PAD = 1200, 26, 92, 34
DOTS = (("#FF5F57", 26), ("#FEBC2E", 46), ("#28C840", 66))


def lines(d):
    """Every line is a value read from the run, or a fixed label."""
    t = d["finished_at"][11:19]
    return [
        [(T["ok"], "martin@nightshift"), (T["dim"], ":~$ "),
         (T["text"], f'agent --run {d["run_id"]}')],
        [(T["faint"], f'[{t}] '), (T["dim"], "model    "), (T["text"], d["model"])],
        [(T["faint"], f'[{t}] '), (T["dim"], "window   "),
         (T["text"], f'since {d["since"]}')],
        [(T["faint"], f'[{t}] '), (T["dim"], "read     "),
         (T["accent"], str(d["notes"])), (T["text"], " new notes")],
        [(T["faint"], f'[{t}] '), (T["dim"], "linked   "),
         (T["accent"], str(d["links"])), (T["text"], " links into the vault")],
        [(T["faint"], f'[{t}] '), (T["dim"], "health   "),
         (T["text"], f'{d["vault_notes"]} notes · {d["links_per_note"]} links/note · '
                     f'{d["orphans"]} orphans')],
        [(T["faint"], f'[{t}] '), (T["dim"], "proposed "),
         (T["accent"], str(d["proposals"])), (T["text"], " changes — never applied alone")],
        [],
        [(T["ok"], f'NIGHTSHIFT_OK notes={d["notes"]} links={d["links"]} '
                   f'proposals={d["proposals"]}')],
        [(T["faint"], "I read the proposals over coffee. The agent never decides.")],
    ]


def svg(d):
    rows = lines(d)
    h = TOP + len(rows) * LINE + 34
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" '
         f'viewBox="0 0 {W} {h}" role="img" aria-labelledby="t d">',
         '<title id="t">Last night&#39;s agent run</title>',
         f'<desc id="d">Terminal replay of the {d["run_id"]} run: {d["notes"]} notes read, '
         f'{d["links"]} links created, {d["proposals"]} changes proposed for review.</desc>',
         "<style>"
         # No fade-in on the lines. GitHub renders this file as an <img>, where
         # Chrome freezes the animation clock at t=0: anything that starts hidden
         # stays hidden forever. Only the cursor blinks, because its base state is
         # visible and a frozen clock simply leaves it on.
         "@keyframes blink{50%{opacity:0}}.cur{animation:blink 1.05s step-end infinite}"
         "</style>",
         f'<rect width="{W}" height="{h}" rx="12" fill="{T["bg"]}" stroke="{T["border"]}"/>',
         f'<path d="M12 0h{W - 24}a12 12 0 0 1 12 12v40H0V12A12 12 0 0 1 12 0z" '
         f'fill="{T["chrome"]}"/>',
         f'<line x1="0" y1="52" x2="{W}" y2="52" stroke="{T["border"]}"/>']
    for col, cx in DOTS:
        o.append(f'<circle cx="{cx}" cy="26" r="6" fill="{col}"/>')
    o.append(f'<text x="{W / 2}" y="31" text-anchor="middle" font-family="{T["mono"]}" '
             f'font-size="12.5" fill="{T["dim"]}">nightshift — the night of {d["night"]}</text>')

    for i, row in enumerate(rows):
        if not row:
            continue
        y = TOP + i * LINE
        # one string, no newline between tspans: xml:space keeps every space literal
        spans = "".join(f'<tspan fill="{c}">{t}</tspan>' for c, t in row)
        o.append(f'<text x="{PAD}" y="{y}" '
                 f'font-family="{T["mono"]}" font-size="14.5" xml:space="preserve">'
                 f'{spans}</text>')

    y = TOP + len(rows) * LINE
    o.append(f'<text x="{PAD}" y="{y}" '
             f'font-family="{T["mono"]}" font-size="14.5">'
             f'<tspan fill="{T["ok"]}">martin@nightshift</tspan>'
             f'<tspan fill="{T["dim"]}">:~$ </tspan>'
             f'<tspan class="cur" fill="{T["accent"]}">█</tspan></text>')
    o.append("</svg>")
    return "\n".join(o)


def main():
    d = json.loads(DATA.read_text(encoding="utf-8-sig"))
    OUT.write_text(svg(d), encoding="utf-8")
    print(f"{OUT.relative_to(ROOT)}  {OUT.stat().st_size} bytes  run {d['run_id']}")


if __name__ == "__main__":
    main()
