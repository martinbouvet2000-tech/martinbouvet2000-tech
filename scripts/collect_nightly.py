"""Collect last night's run counters, on my machine, for assets/last-run.json.

Runs locally after the night agent, because the agent's state never leaves this
computer. It copies counters only — integers and one model name. The journal is
read with a strict regex that captures four numbers from the health line; no
sentence, title or link from the vault is ever read out of it.

    python scripts/collect_nightly.py
"""
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = Path(os.environ.get(
    "NIGHTLY_STATE", Path.home() / ".claude/scheduled-tasks/nightly-agent/state.json"))
VAULT = Path(os.environ.get("OBSIDIAN_VAULT_PATH", Path.home() / "Documents/Vault Principal"))

HEALTH = re.compile(
    r"Sant[ée]\s*:\s*\*\*(\d+)\*\*\s*notes.*?\*\*(\d+)\*\*\s*orphelines.*?"
    r"\*\*([\d.,]+)\*\*\s*liens/note", re.S)


def health(journal_date):
    """Return (notes, orphans, links per note) from the journal's health line."""
    f = VAULT / "Journal" / f"{journal_date}.md"
    if not f.exists():
        return None
    m = HEALTH.search(f.read_text(encoding="utf-8", errors="ignore"))
    return (m.group(1), m.group(2), m.group(3).replace(",", ".")) if m else None


def main():
    s = json.loads(STATE.read_text(encoding="utf-8-sig"))
    run_id = s["run_id"]
    night = run_id.split("_")[0]
    h = health(s["journal"]) or health(night)
    if not h:
        raise SystemExit(f"health line not found for {s['journal']} — nothing written")
    out = {
        "run_id": run_id,
        "night": night,
        "finished_at": s["last_success"],
        "model": s["model"],
        "since": s["journal"],
        "notes": s["notes"],
        "links": s["liens"],
        "proposals": s["propositions"],
        "vault_notes": h[0],
        "orphans": h[1],
        "links_per_note": h[2],
    }
    (ROOT / "assets" / "last-run.json").write_text(
        json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out))


if __name__ == "__main__":
    main()
