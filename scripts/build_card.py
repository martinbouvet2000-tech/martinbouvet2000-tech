"""Build the neofetch-style profile card (dark + light SVG) from live GitHub data.

Runs daily in .github/workflows/profile-card.yml. Stdlib only.
Local run: GITHUB_TOKEN=$(gh auth token) python scripts/build_card.py
"""
import json
import os
import urllib.request
from datetime import datetime, timezone
from html import escape
from pathlib import Path

USER = "martinbouvet2000-tech"
ROOT = Path(__file__).resolve().parent.parent
TOKEN = os.environ["GITHUB_TOKEN"]

QUERY = """
query($login: String!) {
  user(login: $login) {
    createdAt
    repositories(first: 100, ownerAffiliations: OWNER, privacy: PUBLIC, isFork: false) {
      totalCount
      nodes {
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name } }
        }
      }
    }
    contributionsCollection {
      totalCommitContributions
      restrictedContributionsCount
      contributionCalendar { totalContributions }
    }
  }
}
"""

# Pixel monogram "MB" (drawn as SVG rects: font-independent, unlike box-drawing ASCII)
MONOGRAM = [
    "X...X.XXXX.",
    "XX.XX.X...X",
    "X.X.X.X...X",
    "X.X.X.XXXX.",
    "X...X.X...X",
    "X...X.X...X",
    "X...X.XXXX.",
]
TAGLINE = ["builder × business", "× AI"]

THEMES = {
    "dark": {"bg": "#0d1117", "border": "#30363d", "text": "#c9d1d9", "key": "#f0883e",
             "val": "#a5d6ff", "dim": "#6e7681", "art": "#f0883e", "accent": "#7ee787"},
    "light": {"bg": "#ffffff", "border": "#d0d7de", "text": "#24292f", "key": "#bc4c00",
              "val": "#0a3069", "dim": "#8c959f", "art": "#bc4c00", "accent": "#116329"},
}


def fetch():
    body = json.dumps({"query": QUERY, "variables": {"login": USER}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql", data=body,
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        data = json.load(r)
    if "errors" in data:
        raise SystemExit(data["errors"])
    return data["data"]["user"]


def stats(user):
    repos = user["repositories"]
    langs = {}
    for repo in repos["nodes"]:
        for e in repo["languages"]["edges"]:
            langs[e["node"]["name"]] = langs.get(e["node"]["name"], 0) + e["size"]
    top = sorted(langs, key=langs.get, reverse=True)
    top = [l for l in top if l not in ("CSS", "HTML", "Liquid", "PLpgSQL")][:3]
    created = datetime.fromisoformat(user["createdAt"].replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    months = (now.year - created.year) * 12 + now.month - created.month
    cc = user["contributionsCollection"]
    return {
        "repos": repos["totalCount"],
        "stars": sum(r["stargazerCount"] for r in repos["nodes"]),
        "contribs": cc["contributionCalendar"]["totalContributions"],
        "commits": cc["totalCommitContributions"] + cc["restrictedContributionsCount"],
        "langs": " · ".join(top),
        "uptime": f"{months} months shipping",
        "updated": now.strftime("%Y-%m-%d"),
    }


def lines(s):
    # (key, value) ; key None = section header, "" = blank line
    return [
        (None, "martin@bouvet"),
        (None, "─" * 44),
        ("OS", "Global BBA @ emlyon · Lyon, FR"),
        ("Training", "Oxford · LLMs, generative & agentic AI"),
        ("Role", "Founder in the making · AI-native builder"),
        ("Kernel", "Claude Code + Obsidian second brain"),
        ("Uptime", s["uptime"]),
        ("Shell", s["langs"]),
        ("Stack", "React · Next.js · Supabase · Vercel"),
        ("Agents", "nightly vault agent · IG → notes pipeline"),
        ("Building", "e-invoicing readiness audits (FR 2026)"),
        ("", ""),
        (None, "─ GitHub " + "─" * 35),
        ("Repos", f"{s['repos']}   Stars {s['stars']}"),
        ("Contrib", f"{s['contribs']} (last 12 mo)   Commits {s['commits']}"),
    ]


def svg(s, t):
    c = THEMES[t]
    w, lh, top = 860, 22, 48
    rows = lines(s)
    h = top + len(rows) * lh + 44
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'font-family="ui-monospace,SFMono-Regular,Consolas,\'Liberation Mono\',monospace" font-size="15">',
        "<style>@keyframes in{from{opacity:0}to{opacity:1}}"
        ".r{animation:in .35s ease both}"
        "@keyframes blink{50%{opacity:0}}.cur{animation:blink 1s step-end infinite}</style>",
        f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="10" fill="{c["bg"]}" stroke="{c["border"]}"/>',
    ]
    for i, col in enumerate(("#ff5f57", "#febc2e", "#28c840")):
        out.append(f'<circle cx="{22 + i*20}" cy="20" r="6" fill="{col}"/>')
    out.append(f'<text x="{w/2}" y="25" text-anchor="middle" fill="{c["dim"]}" font-size="13">'
               f'martin@bouvet: ~ neofetch</text>')
    px, ox, oy = 18, 38, top + 10
    for r, row in enumerate(MONOGRAM):
        for col, cell in enumerate(row):
            if cell == "X":
                out.append(f'<rect class="r" style="animation-delay:{0.03 * (r + col):.2f}s" '
                           f'x="{ox + col*px}" y="{oy + r*px}" width="{px-3}" height="{px-3}" '
                           f'rx="3" fill="{c["art"]}"/>')
    cx = ox + len(MONOGRAM[0]) * px / 2
    for i, tl in enumerate(TAGLINE):
        out.append(f'<text x="{cx}" y="{oy + len(MONOGRAM)*px + 36 + i*lh}" text-anchor="middle" '
                   f'fill="{c["dim"]}">{escape(tl)}</text>')
    x = 290
    for i, (k, v) in enumerate(rows):
        y = top + 20 + i * lh
        delay = f'style="animation-delay:{0.08 * i:.2f}s"'
        if k is None:
            color = c["accent"] if i == 0 else c["dim"]
            weight = ' font-weight="bold"' if i == 0 else ""
            out.append(f'<text class="r" {delay} x="{x}" y="{y}" fill="{color}"{weight} '
                       f'xml:space="preserve">{escape(v)}</text>')
        elif k:
            out.append(f'<text class="r" {delay} x="{x}" y="{y}" xml:space="preserve">'
                       f'<tspan fill="{c["key"]}">{escape(k)}</tspan>'
                       f'<tspan fill="{c["dim"]}">: </tspan>'
                       f'<tspan fill="{c["val"]}">{escape(v)}</tspan></text>')
    y = top + 20 + len(rows) * lh + 6
    out.append(f'<text x="{x}" y="{y}" fill="{c["accent"]}">❯ <tspan class="cur" fill="{c["text"]}">█</tspan></text>')
    out.append(f'<text x="{w-16}" y="{h-12}" text-anchor="end" fill="{c["dim"]}" font-size="11">'
               f'auto-updated {s["updated"]}</text>')
    out.append("</svg>")
    return "\n".join(out)


def main():
    s = stats(fetch())
    for t in THEMES:
        (ROOT / "assets" / f"card-{t}.svg").write_text(svg(s, t), encoding="utf-8")
    print(json.dumps(s))


if __name__ == "__main__":
    main()
