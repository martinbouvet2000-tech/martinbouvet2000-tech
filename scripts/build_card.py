"""Build the activity card (dark + light SVG) from live GitHub data.

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
      totalPullRequestContributions
      totalRepositoriesWithContributedCommits
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""

# Pixel monogram "MB" (drawn as SVG rects: font-independent, unlike box-drawing ASCII)
_UNUSED_MONOGRAM = [
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
        "lang_bars": [(l, langs[l]) for l in sorted(langs, key=langs.get, reverse=True)[:6]],
        "days": [(d["date"], d["contributionCount"])
                 for w in cc["contributionCalendar"]["weeks"] for d in w["contributionDays"]],
        "prs": cc["totalPullRequestContributions"],
        "active_repos": cc["totalRepositoriesWithContributedCommits"],
        "updated": now.strftime("%Y-%m-%d"),
    }


NL = chr(10)

LANG_COLORS = {"TypeScript": "#3178c6", "JavaScript": "#f1e05a", "Python": "#3572A5",
               "HTML": "#e34c26", "CSS": "#563d7c", "Liquid": "#67b8de", "Shell": "#89e051",
               "PowerShell": "#012456", "Jupyter Notebook": "#DA5B0B", "PLpgSQL": "#336790"}


def pulse_svg(s, t):
    """Second card: where the code goes (languages) and when it happens (12-month pulse)."""
    c = THEMES[t]
    w, h = 860, 250
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="12">',
        "<style>@keyframes grow{from{transform:scaleX(0)}to{transform:scaleX(1)}}"
        ".bar{transform-box:fill-box;transform-origin:left;animation:grow .9s cubic-bezier(.2,.8,.2,1) both}"
        "@keyframes rise{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}"
        ".up{animation:rise .6s ease both}</style>",
        f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="10" fill="{c["bg"]}" stroke="{c["border"]}"/>',
    ]
    # ── languages
    bars, total = s["lang_bars"], max(1, sum(v for _, v in s["lang_bars"]))
    out.append(f'<text x="24" y="32" fill="{c["key"]}" font-size="11" letter-spacing="1.5">WHERE THE CODE GOES</text>')
    x, bw = 24, 360
    for i, (name, size) in enumerate(bars):
        seg = max(4, bw * size / total)
        out.append(f'<rect class="bar" style="animation-delay:{0.07*i:.2f}s" x="{x:.1f}" y="46" '
                   f'width="{seg:.1f}" height="12" rx="3" fill="{LANG_COLORS.get(name, c["dim"])}"/>')
        x += seg + 2
    for i, (name, size) in enumerate(bars[:4]):
        col, row = i % 2, i // 2
        lx, ly = 24 + col * 190, 84 + row * 22
        out.append(f'<circle class="up" style="animation-delay:{0.3+0.06*i:.2f}s" cx="{lx+4}" cy="{ly-4}" r="4" '
                   f'fill="{LANG_COLORS.get(name, c["dim"])}"/>')
        out.append(f'<text class="up" style="animation-delay:{0.3+0.06*i:.2f}s" x="{lx+15}" y="{ly}" '
                   f'fill="{c["text"]}">{escape(name)} <tspan fill="{c["dim"]}">{100*size/total:.0f}%</tspan></text>')
    stats = [(f'{s["commits"]}', "commits"), (f'{s["prs"]}', "pull requests"), (f'{s["active_repos"]}', "active repos")]
    for i, (v, label) in enumerate(stats):
        sx = 24 + i * 125
        out.append(f'<text class="up" style="animation-delay:{0.5+0.08*i:.2f}s" x="{sx}" y="176" '
                   f'fill="{c["val"]}" font-size="22" font-family="inherit">{v}</text>')
        out.append(f'<text x="{sx}" y="194" fill="{c["dim"]}" font-size="10.5">{label}</text>')
    out.append(f'<text x="24" y="224" fill="{c["dim"]}" font-size="10.5">last 12 months · '
               f'{s["contribs"]} contributions</text>')
    # ── 12-month pulse (weekly buckets, area + line)
    days = s["days"]
    weeks = [sum(n for _, n in days[i:i + 7]) for i in range(0, len(days), 7)] or [0]
    gx, gy, gw, gh = 448, 46, w - 448 - 28, 150
    peak = max(weeks) or 1
    step = gw / max(1, len(weeks) - 1)
    pts = [(gx + i * step, gy + gh - (v / peak) * gh) for i, v in enumerate(weeks)]
    line = " ".join(f"{px:.1f},{py:.1f}" for px, py in pts)
    out.append(f'<text x="{gx}" y="32" fill="{c["key"]}" font-size="11" letter-spacing="1.5">WHEN IT HAPPENS</text>')
    out.append(f'<defs><linearGradient id="g{t}" x1="0" y1="0" x2="0" y2="1">'
               f'<stop offset="0" stop-color="{c["key"]}" stop-opacity=".45"/>'
               f'<stop offset="1" stop-color="{c["key"]}" stop-opacity="0"/></linearGradient></defs>')
    out.append(f'<polygon points="{gx},{gy+gh} {line} {gx+gw},{gy+gh}" fill="url(#g{t})"/>')
    out.append(f'<polyline points="{line}" fill="none" stroke="{c["key"]}" stroke-width="2" '
               f'stroke-linejoin="round"/>')
    bx, by = pts[max(range(len(weeks)), key=lambda i: weeks[i])]
    out.append(f'<circle cx="{bx:.1f}" cy="{by:.1f}" r="4" fill="{c["bg"]}" stroke="{c["key"]}" stroke-width="2"/>')
    out.append(f'<text x="{bx:.1f}" y="{by-10:.1f}" text-anchor="middle" fill="{c["val"]}" font-size="10.5">'
               f'{peak}/wk</text>')
    out.append(f'<line x1="{gx}" y1="{gy+gh}" x2="{gx+gw}" y2="{gy+gh}" stroke="{c["border"]}"/>')
    for frac, lbl in ((0, days[0][0][:7]), (0.5, days[len(days)//2][0][:7]), (1, days[-1][0][:7])):
        anchor = "start" if frac == 0 else "end" if frac == 1 else "middle"
        out.append(f'<text x="{gx + gw*frac:.0f}" y="{gy+gh+16}" text-anchor="{anchor}" fill="{c["dim"]}" '
                   f'font-size="10">{lbl}</text>')
    out.append(f'<text x="{w-28}" y="224" text-anchor="end" fill="{c["dim"]}" font-size="10.5">'
               f'auto-updated {s["updated"]}</text>')
    out.append("</svg>")
    return NL.join(out)


def main():
    s = stats(fetch())
    for t in THEMES:
        (ROOT / "assets" / f"pulse-{t}.svg").write_text(pulse_svg(s, t), encoding="utf-8")
    printable = {k: v for k, v in s.items() if k not in ("days", "lang_bars")}
    print(json.dumps(printable))


if __name__ == "__main__":
    main()
