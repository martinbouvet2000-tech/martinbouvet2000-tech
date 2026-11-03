"""Count one day of the agent city, on my machine, for assets/ville.json.

The city is Founder OS, a private repository: a small company of AI agents that
wake on a schedule. This script reads its org chart and its database in
read-only mode and copies out numbers only. Every string in the output comes
from the ROLES table below, written in this file, never from the database: no
message, mail, task, person, amount or local path can leave the machine.

    python scripts/collect_ville.py            # the day that just ended before 6 am, today after
    python scripts/collect_ville.py 2026-11-03 # a given local day

FOUNDER_OS points at the repository (default: ~/Desktop/Mes Projets/founder-os).
"""
import json
import os
import sqlite3
import sys
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "ville.json"
SRC = Path(os.environ.get(
    "FOUNDER_OS", Path.home() / "Desktop" / "Mes Projets" / "founder-os"))

# Agent id -> (public key, building name, quarter, what it does).
# Only these words are ever published. An active agent missing from this
# table still gets a building, under a neutral name.
ROLES = {
    "patron": ("patron", "Le Patron", "mairie",
               "Reads every report, decides what reaches Martin and hands work to the quarters."),
    "medecin": ("medecin", "L'Hôpital", "hopital",
                "Admits an agent that keeps failing and lets it out once it works again."),
    "business": ("comptoir", "Le Comptoir", "business",
                 "Runs the business quarter and sets the day's order for its agents."),
    "prospecteur": ("prospecteur", "Le Prospecteur", "business",
                    "Looks for small businesses the audit offer could help."),
    "relanceur": ("plume", "La Plume", "business",
                  "Drafts first messages and follow-ups. Nothing leaves without Martin."),
    "trieur-inbox": ("tri", "Le Tri", "business",
                     "Sorts the inbox into piles. It reads, it never answers."),
    "compteur": ("compteur", "Le Compteur", "business",
                 "Counts what the city produced and what it cost."),
    "ecole": ("ecole", "L'École", "ecole",
              "Keeps the school calendar and prepares what is due next."),
    "relecteur": ("relecteur", "Le Relecteur", "ecole",
                  "Rereads every draft before Martin sees it."),
    "studio": ("studio", "Le Studio", "studio",
               "Briefs the design workshop and decides what gets shown."),
    "studio-graphisme": ("graphisme", "Graphisme", "studio",
                         "Draws layouts and type for the workshop."),
    "studio-interface": ("interface", "Interface", "studio",
                         "Builds interface mockups that can be clicked."),
    "studio-mouvement": ("mouvement", "Mouvement", "studio",
                         "Works on motion: easing, timing, transitions."),
    "studio-critique": ("critique", "Le Critique", "studio",
                        "Scores every mockup before Martin does."),
}
OTHER = ("Un atelier", "faubourg", "A newer agent, not yet described on this map.")

DONE = {"ok", "passation", "rapide", "btw"}
ERRORS = {"erreur", "reseau"}
CAPPED = {"refuse_budget"}
STUDIO = {"sans_capture": "no_capture", "a_noter": "to_score",
          "a_reprendre": "to_rework", "a_montrer": "to_show", "prete": "ready"}

# The published shape, all of it. Anything else fails validate().
TOP = {"schema", "date", "generated_at", "agents", "today", "hospital",
       "studio", "vault", "tests", "buildings"}
NESTED = {
    "agents": {"active", "total"},
    "today": {"wakes", "done", "errors", "capped", "by_hour"},
    "hospital": {"patients"},
    "studio": set(STUDIO.values()),
    "vault": {"writes"},
    "tests": {"declared"},
}
BUILDING = {"key", "name", "quarter", "role", "wakes", "done", "errors",
            "capped", "in_hospital"}
ALLOWED_TEXT = ({v for r in ROLES.values() for v in r}
                | set(OTHER) | {f"atelier-{i}" for i in range(1, 100)})


def validate(d):
    """Raise ValueError if the document holds one field or string too many."""
    def ints(obj, keys, where):
        for k, v in obj.items():
            if k not in keys:
                raise ValueError(f"field not allowed: {where}.{k}")
            ok = isinstance(v, int) and not isinstance(v, bool) and v >= 0
            if k == "by_hour":
                ok = (isinstance(v, list) and len(v) == 24
                      and all(isinstance(x, int) and x >= 0 for x in v))
            if not ok:
                raise ValueError(f"not a count: {where}.{k}")

    for k in d:
        if k not in TOP:
            raise ValueError(f"field not allowed: {k}")
    if d["schema"] != 1:
        raise ValueError("unknown schema")
    date.fromisoformat(d["date"])
    datetime.strptime(d["generated_at"], "%Y-%m-%dT%H:%M")
    for k, keys in NESTED.items():
        ints(d[k], keys, k)
    for i, b in enumerate(d["buildings"]):
        for k, v in b.items():
            if k not in BUILDING:
                raise ValueError(f"field not allowed: buildings[{i}].{k}")
            if k in ("key", "name", "quarter", "role"):
                if v not in ALLOWED_TEXT:
                    raise ValueError(f"text not from the ROLES table: buildings[{i}].{k}")
            elif k == "in_hospital":
                if not isinstance(v, bool):
                    raise ValueError(f"not a flag: buildings[{i}].{k}")
            elif not (isinstance(v, int) and not isinstance(v, bool) and v >= 0):
                raise ValueError(f"not a count: buildings[{i}].{k}")
    return d


def default_day(now):
    """Before 6 am the day worth showing is the one that just ended."""
    return (now - timedelta(days=1)).date() if now.hour < 6 else now.date()


def count_tests(src):
    """Declared tests, counted by reading the files. The suite is never run."""
    n = 0
    for f in sorted((src / "test").glob("*.mjs")):
        for line in f.read_text(encoding="utf-8", errors="ignore").splitlines():
            s = line.lstrip()
            if s.startswith(("test(", "it(")):
                n += 1
    return n


def collect(src, day, now):
    org = json.loads((src / "org.json").read_text(encoding="utf-8-sig"))
    agents = org["agents"] if isinstance(org, dict) else org
    active = [a for a in agents if a.get("actif")]

    uri = (src / "data" / "core.db").resolve().as_uri() + "?mode=ro"
    db = sqlite3.connect(uri, uri=True)
    tz = now.astimezone().tzinfo
    start = datetime.combine(day, time(), tz)
    lo = (start - timedelta(hours=1)).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M")
    hi = (start + timedelta(days=1, hours=1)).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M")

    per, total, by_hour = {}, {"wakes": 0, "done": 0, "errors": 0, "capped": 0}, [0] * 24
    for agent, statut, debut in db.execute(
            "SELECT agent, statut, debut FROM runs WHERE debut >= ? AND debut < ?", (lo, hi)):
        t = datetime.fromisoformat(debut.replace("Z", "+00:00"))
        if t.tzinfo is None:
            t = t.replace(tzinfo=timezone.utc)
        t = t.astimezone(tz)
        if t.date() != day:
            continue
        kind = ("done" if statut in DONE else "errors" if statut in ERRORS
                else "capped" if statut in CAPPED else None)
        if kind is None:
            continue
        c = per.setdefault(agent, {"wakes": 0, "done": 0, "errors": 0, "capped": 0})
        for bucket in (c, total):
            bucket["wakes"] += 1
            bucket[kind] += 1
        by_hour[t.hour] += 1

    sick = {a for (a,) in db.execute(
        "SELECT agent FROM hopital_dossiers WHERE sorti_le IS NULL")}
    studio = {v: 0 for v in STUDIO.values()}
    for statut, n in db.execute("SELECT statut, COUNT(*) FROM studio_maquettes GROUP BY statut"):
        if statut in STUDIO:
            studio[STUDIO[statut]] = n
    writes = 0
    for (le,) in db.execute("SELECT le FROM vault_ecritures WHERE statut = 'ok' AND le >= ? AND le < ?",
                            (lo, hi)):
        t = datetime.fromisoformat(le.replace("Z", "+00:00"))
        if t.tzinfo is None:
            t = t.replace(tzinfo=timezone.utc)
        writes += t.astimezone(tz).date() == day
    db.close()

    buildings, spare = [], 0
    for a in active:
        if a["id"] in ROLES:
            key, name, quarter, role = ROLES[a["id"]]
        else:
            spare += 1
            key, (name, quarter, role) = f"atelier-{spare}", OTHER
        c = per.get(a["id"], {"wakes": 0, "done": 0, "errors": 0, "capped": 0})
        buildings.append({"key": key, "name": name, "quarter": quarter, "role": role,
                          **c, "in_hospital": a["id"] in sick})

    return validate({
        "schema": 1,
        "date": day.isoformat(),
        "generated_at": now.strftime("%Y-%m-%dT%H:%M"),
        "agents": {"active": len(active), "total": len(agents)},
        "today": {**total, "by_hour": by_hour},
        "hospital": {"patients": len(sick)},
        "studio": studio,
        "vault": {"writes": writes},
        "tests": {"declared": count_tests(src)},
        "buildings": buildings,
    })


def main():
    now = datetime.now().astimezone()
    day = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else default_day(now)
    d = collect(SRC, day, now)
    OUT.write_text(json.dumps(d, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    t = d["today"]
    print(f"{OUT.relative_to(ROOT)}  {d['date']}  {d['agents']['active']} agents  "
          f"{t['wakes']} wake-ups  {t['errors']} errors")


if __name__ == "__main__":
    main()
