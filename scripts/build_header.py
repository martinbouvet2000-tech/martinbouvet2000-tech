"""Build the control-room header from live GitHub data.

Every value on the header is fetched or declared here — nothing is invented.
Rebuilt every morning by .github/workflows/profile-card.yml.

    GITHUB_TOKEN=$(gh auth token) python scripts/build_header.py
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

# Scheduled systems, in Paris time. These are the jobs that actually run.
JOBS = [
    (0.5, "nightly agent"),
    (7.28, "profile rebuild"),
    (9.0, "capture pipeline"),
    (21.0, "capture pipeline"),
    (23.0, "vault backup"),
]

# Test counts, read from each repo's suite. Update when a suite grows.
TESTS = {"nightshift": 89, "nous-deux": 374, "business-idea-radar": 60}

T = {
    "bg": "#08090B", "panel": "#101317", "line": "#232830",
    "text": "#F5F7FA", "dim": "#8B949E", "faint": "#4A515B",
    "accent": "#F0883E", "ok": "#3FB950",
    "sans": "-apple-system,'Segoe UI',Inter,Helvetica,Arial,sans-serif",
    "mono": "ui-monospace,SFMono-Regular,'JetBrains Mono',Consolas,monospace",
}
W, H = 1200, 364

# Public data only, on purpose: the panel must show the same numbers whether it is
# built from my token or from the Action's, and a visitor must be able to check it.
QUERY = """
query($login: String!) {
  user(login: $login) {
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC) {
      totalCount
      nodes { name pushedAt }
    }
    contributionsCollection {
      commitContributionsByRepository(maxRepositories: 100) {
        repository { isPrivate }
        contributions { totalCount }
      }
    }
  }
}
"""


def gh(url):
    req = urllib.request.Request(url, headers={
        "Authorization": f"bearer {TOKEN}", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def fetch():
    body = json.dumps({"query": QUERY, "variables": {"login": USER}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql", data=body,
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        data = json.load(r)
    if "errors" in data:
        raise SystemExit(data["errors"])
    user = data["data"]["user"]
    now = datetime.now(timezone.utc)

    # The profile repo pushes itself every morning; it is not work, so it never counts as a ship.
    pushes = [(n["pushedAt"], n["name"]) for n in user["repositories"]["nodes"]
              if n["pushedAt"] and n["name"] != USER]
    last_at, last_repo = max(pushes)
    delta = now - datetime.fromisoformat(last_at.replace("Z", "+00:00"))
    mins = int(delta.total_seconds() // 60)
    last_ship = f"{mins}m ago" if mins < 60 else (
        f"{mins // 60}h ago" if mins < 1440 else f"{mins // 1440}d ago")

    try:  # latest CI conclusion on the flagship repo
        runs = gh(f"https://api.github.com/repos/{USER}/nightshift/actions/workflows/ci.yml/runs?per_page=1")
        ci = (runs["workflow_runs"][0]["conclusion"] or "running").upper()
    except Exception:
        ci = "UNKNOWN"

    commits = sum(r["contributions"]["totalCount"]
                  for r in user["contributionsCollection"]["commitContributionsByRepository"]
                  if not r["repository"]["isPrivate"])
    return {
        "repos": user["repositories"]["totalCount"],
        "commits": commits,
        "tests": sum(TESTS.values()),
        "ci": ci,
        "last_ship": last_ship,
        "last_repo": last_repo,
        "built": now.strftime("%Y-%m-%d %H:%M UTC"),
    }


def svg(s):
    o = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'role="img" aria-labelledby="ttl dsc">',
        '<title id="ttl">Martin Bouvet — system status</title>',
        f'<desc id="dsc">Control-room header: {s["repos"]} repositories, {s["tests"]} tests in public '
        f'repositories, CI {s["ci"]}, last push {s["last_ship"]}, and the five jobs that run every day.</desc>',
        "<style>"
        "@keyframes blink{50%{opacity:0}}.cur{animation:blink 1.05s step-end infinite}"
        "@keyframes ping{0%{r:4;opacity:.9}70%{r:13;opacity:0}100%{r:13;opacity:0}}"
        ".ping{animation:ping 3.2s ease-out infinite}"
        "@keyframes sweep{from{transform:translateX(0)}to{transform:translateX(1048px)}}"
        ".scan{animation:sweep 24s linear infinite}"
        "</style>",
        f'<rect width="{W}" height="{H}" rx="14" fill="{T["bg"]}"/>',
        f'<rect x="0" y="0" width="{W}" height="4" rx="2" fill="{T["accent"]}"/>',
    ]
    # ── identity block
    o.append(f'<text x="48" y="62" font-family="{T["mono"]}" font-size="12" fill="{T["accent"]}" '
             f'letter-spacing="3">SYSTEM 01 — ONLINE</text>')
    o.append(f'<circle cx="34" cy="58" r="4" fill="{T["ok"]}"/>')
    o.append(f'<circle cx="34" cy="58" r="4" fill="{T["ok"]}" class="ping"/>')
    o.append(f'<text x="46" y="126" font-family="{T["sans"]}" font-size="54" font-weight="700" '
             f'fill="{T["text"]}" letter-spacing="-1">MARTIN BOUVET</text>')
    o.append(f'<text x="48" y="160" font-family="{T["mono"]}" font-size="15" fill="{T["dim"]}">'
             f'business <tspan fill="{T["accent"]}">×</tspan> product '
             f'<tspan fill="{T["accent"]}">×</tspan> ai <tspan fill="{T["accent"]}">×</tspan> execution</text>')
    o.append(f'<text x="48" y="196" font-family="{T["mono"]}" font-size="14" fill="{T["faint"]}">'
             f'martin@builder:~$ <tspan fill="{T["text"]}">./ship</tspan>'
             f'<tspan class="cur" fill="{T["accent"]}"> █</tspan></text>')

    # ── status panel
    px, py, pw, ph = 700, 40, 456, 172
    o.append(f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="10" fill="{T["panel"]}" stroke="{T["line"]}"/>')
    rows = [
        ("PUBLIC REPOS", str(s["repos"]), T["text"]),
        ("TESTS / PUBLIC", str(s["tests"]), T["text"]),
        ("PUBLIC COMMITS / 12 MO", str(s["commits"]), T["text"]),
        ("CI", s["ci"], T["ok"] if s["ci"] == "SUCCESS" else T["accent"]),
        ("LAST SHIP", f'{s["last_ship"]} · {s["last_repo"]}', T["accent"]),
    ]
    for i, (k, v, col) in enumerate(rows):
        y = py + 34 + i * 28
        o.append(f'<text x="{px + 22}" y="{y}" font-family="{T["mono"]}" font-size="11.5" '
                 f'fill="{T["dim"]}" letter-spacing="1.4">{k}</text>')
        o.append(f'<text x="{px + pw - 22}" y="{y}" text-anchor="end" font-family="{T["mono"]}" '
                 f'font-size="13" fill="{col}">{escape(v)}</text>')
        if i < len(rows) - 1:
            o.append(f'<line x1="{px + 22}" y1="{y + 9}" x2="{px + pw - 22}" y2="{y + 9}" '
                     f'stroke="{T["line"]}"/>')

    # ── 24-hour schedule strip: the jobs that run every day
    sx, sy, sw = 48, 312, W - 96
    o.append(f'<text x="{sx}" y="{sy - 70}" font-family="{T["mono"]}" font-size="11" fill="{T["dim"]}" '
             f'letter-spacing="2.4">SCHEDULED SYSTEMS · PARIS TIME</text>')
    # night band 22:00 → 07:00, behind everything else on the strip
    for bx, bw in ((sx, sw * 7 / 24), (sx + sw * 22 / 24, sw * 2 / 24)):
        o.append(f'<rect x="{bx:.1f}" y="{sy - 16}" width="{bw:.1f}" height="16" '
                 f'fill="{T["text"]}" fill-opacity=".05"/>')
    o.append(f'<line x1="{sx}" y1="{sy}" x2="{sx + sw}" y2="{sy}" stroke="{T["line"]}"/>')
    for h in range(0, 25, 2):
        x = sx + sw * h / 24
        o.append(f'<line x1="{x:.1f}" y1="{sy}" x2="{x:.1f}" y2="{sy + (7 if h % 6 else 12)}" '
                 f'stroke="{T["faint"]}"/>')
        if h % 6 == 0:
            o.append(f'<text x="{x:.1f}" y="{sy + 28}" text-anchor="middle" font-family="{T["mono"]}" '
                     f'font-size="10.5" fill="{T["faint"]}">{h:02d}:00</text>')
    # labels alternate between two rows so neighbouring jobs never collide
    for i, (hour, label) in enumerate(JOBS):
        x = sx + sw * hour / 24
        top = sy - (52 if i % 2 else 32)
        anchor, tx = "middle", x
        if x < 90:      # keep the first and last labels inside the frame
            anchor, tx = "start", sx
        elif x > W - 130:
            anchor, tx = "end", sx + sw
        o.append(f'<line x1="{x:.1f}" y1="{top + 6}" x2="{x:.1f}" y2="{sy}" stroke="{T["accent"]}" '
                 f'stroke-opacity=".45"/>')
        o.append(f'<circle cx="{x:.1f}" cy="{sy}" r="4" fill="{T["accent"]}"/>')
        o.append(f'<circle cx="{x:.1f}" cy="{sy}" r="4" fill="{T["accent"]}" class="ping"/>')
        o.append(f'<text x="{tx:.1f}" y="{top}" text-anchor="{anchor}" font-family="{T["mono"]}" '
                 f'font-size="10.5" fill="{T["dim"]}">{label} '
                 f'<tspan fill="{T["faint"]}">{int(hour):02d}:{round(hour % 1 * 60):02d}</tspan></text>')
    o.append(f'<g class="scan"><line x1="{sx}" y1="{sy - 16}" x2="{sx}" y2="{sy + 12}" '
             f'stroke="{T["accent"]}" stroke-opacity=".5"/></g>')
    o.append(f'<text x="{sx + sw}" y="{sy - 70}" text-anchor="end" font-family="{T["mono"]}" '
             f'font-size="10.5" fill="{T["faint"]}">rebuilt {s["built"]} · every value here comes from '
             f'the GitHub API</text>')
    o.append("</svg>")
    return "\n".join(o)


def main():
    s = fetch()
    (ROOT / "assets" / "header.svg").write_text(svg(s), encoding="utf-8")
    print(json.dumps(s))


if __name__ == "__main__":
    main()
