"""The city map: what may be published, and that the drawing is reproducible.

    python -m unittest discover tests
"""
import copy
import json
import sqlite3
import sys
import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))

import build_ville  # noqa: E402
import collect_ville  # noqa: E402

FIXTURE = json.loads((HERE / "fixtures" / "ville.json").read_text(encoding="utf-8"))
SECRETS = ["martin.dupont@example.com", "390 €", "C:/Users/someone", "Devoir de finance",
           "Bonjour Madame", "4.87", "cout_usd", "mission secrète"]


def fake_founder_os(root):
    """A tiny Founder OS: org chart, database, one test file, with private text everywhere."""
    (root / "data").mkdir()
    (root / "test").mkdir()
    (root / "test" / "a.test.mjs").write_text("test('one', () => {});\n  it('two', () => {});\n// test( not\n")
    org = {"_doc": "mission secrète", "agents": [
        {"id": "patron", "nom": "Patron", "chef": "martin", "actif": True,
         "mission": "mission secrète: écrire à martin.dupont@example.com"},
        {"id": "relanceur", "nom": "Relanceur", "chef": "patron", "actif": True,
         "mission": "Bonjour Madame, offre à 390 €"},
        {"id": "nouveau-venu", "nom": "Devoir de finance", "chef": "patron", "actif": True},
        {"id": "dormeur", "nom": "Dormeur", "chef": "patron", "actif": False},
    ]}
    (root / "org.json").write_text(json.dumps(org), encoding="utf-8")
    db = sqlite3.connect(root / "data" / "core.db")
    db.executescript("""
      CREATE TABLE runs (id INTEGER PRIMARY KEY, agent TEXT, debut TEXT, fin TEXT, cout_usd REAL,
                         statut TEXT, resume TEXT, erreur TEXT);
      CREATE TABLE hopital_dossiers (id INTEGER PRIMARY KEY, agent TEXT, mal TEXT, preuve TEXT,
                         echecs INTEGER, entre_le TEXT, dernier_echec TEXT, sorti_le TEXT);
      CREATE TABLE studio_maquettes (id INTEGER PRIMARY KEY, titre TEXT, chemin TEXT, statut TEXT);
      CREATE TABLE vault_ecritures (id INTEGER PRIMARY KEY, agent TEXT, cible TEXT, statut TEXT, le TEXT);
    """)
    runs = [("patron", "2026-11-03T08:10:00.000Z", "ok"), ("patron", "2026-11-03T12:00:00.000Z", "erreur"),
            ("patron", "2026-11-03T13:00:00.000Z", "refuse_budget"),
            ("relanceur", "2026-11-03T09:30:00.000Z", "passation"),
            ("relanceur", "2026-11-03T09:40:00.000Z", "session_reinit"),
            ("dormeur", "2026-11-03T10:00:00.000Z", "ok"),
            ("patron", "2026-11-02T10:00:00.000Z", "ok")]
    db.executemany("INSERT INTO runs (agent, debut, cout_usd, statut, resume, erreur) "
                   "VALUES (?, ?, 4.87, ?, 'Bonjour Madame', 'C:/Users/someone')",
                   runs)
    db.execute("INSERT INTO hopital_dossiers (agent, mal, echecs, entre_le, dernier_echec) "
               "VALUES ('relanceur', 'Devoir de finance', 3, 'x', 'y')")
    db.executemany("INSERT INTO studio_maquettes (titre, chemin, statut) VALUES (?, 'C:/Users/someone', ?)",
                   [("mission secrète", "prete"), ("x", "a_reprendre"), ("y", "a_reprendre")])
    db.execute("INSERT INTO vault_ecritures (agent, cible, statut, le) "
               "VALUES ('patron', 'C:/Users/someone', 'ok', '2026-11-03T10:00:00.000Z')")
    db.commit()
    db.close()


class Whitelist(unittest.TestCase):
    def test_fixture_passes(self):
        collect_ville.validate(copy.deepcopy(FIXTURE))

    def bad(self, mutate):
        d = copy.deepcopy(FIXTURE)
        mutate(d)
        with self.assertRaises(ValueError):
            collect_ville.validate(d)

    def test_extra_top_level_field(self):
        self.bad(lambda d: d.__setitem__("messages", []))

    def test_extra_nested_field(self):
        self.bad(lambda d: d["today"].__setitem__("cost_usd", 3))

    def test_extra_building_field(self):
        self.bad(lambda d: d["buildings"][0].__setitem__("mission", "x"))

    def test_free_text_in_a_building(self):
        self.bad(lambda d: d["buildings"][0].__setitem__("role", "Wrote to martin.dupont@example.com"))

    def test_amount_is_not_a_count(self):
        self.bad(lambda d: d["today"].__setitem__("done", 4.87))

    def test_flag_is_not_a_count(self):
        self.bad(lambda d: d["hospital"].__setitem__("patients", True))


class Collect(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        fake_founder_os(self.root)
        self.d = collect_ville.collect(self.root, date(2026, 11, 3),
                                       datetime(2026, 11, 3, 23, 50).astimezone())

    def tearDown(self):
        self.tmp.cleanup()

    def test_no_private_text_leaves(self):
        text = json.dumps(self.d, ensure_ascii=False)
        for s in SECRETS:
            self.assertNotIn(s, text)

    def test_counts(self):
        t = self.d["today"]
        # session_reinit is bookkeeping, not a wake-up; the inactive agent still counts in the day
        self.assertEqual((t["wakes"], t["done"], t["errors"], t["capped"]), (5, 3, 1, 1))
        self.assertEqual(sum(t["by_hour"]), 5)
        self.assertEqual(self.d["agents"], {"active": 3, "total": 4})
        self.assertEqual(self.d["hospital"], {"patients": 1})
        self.assertEqual(self.d["studio"]["ready"], 1)
        self.assertEqual(self.d["studio"]["to_rework"], 2)
        self.assertEqual(self.d["vault"], {"writes": 1})
        self.assertEqual(self.d["tests"], {"declared": 2})

    def test_unknown_agent_gets_a_neutral_name(self):
        keys = [b["key"] for b in self.d["buildings"]]
        self.assertEqual(keys, ["patron", "plume", "atelier-1"])
        self.assertEqual(self.d["buildings"][2]["name"], "Un atelier")
        self.assertTrue(self.d["buildings"][1]["in_hospital"])

    def test_db_is_opened_read_only(self):
        uri = (self.root / "data" / "core.db").resolve().as_uri() + "?mode=ro"
        db = sqlite3.connect(uri, uri=True)
        with self.assertRaises(sqlite3.OperationalError):
            db.execute("DELETE FROM runs")
        db.close()

    def test_default_day(self):
        self.assertEqual(collect_ville.default_day(datetime(2026, 11, 4, 0, 50)), date(2026, 11, 3))
        self.assertEqual(collect_ville.default_day(datetime(2026, 11, 4, 9, 0)), date(2026, 11, 4))


class Build(unittest.TestCase):
    NOW = datetime(2026, 11, 4, 5, 17)

    def test_deterministic(self):
        self.assertEqual(build_ville.svg(FIXTURE, self.NOW), build_ville.svg(FIXTURE, self.NOW))

    def test_light_and_accessible(self):
        s = build_ville.svg(FIXTURE, self.NOW)
        self.assertLess(len(s.encode()), 150_000)
        self.assertIn("prefers-reduced-motion", s)
        self.assertIn("<title", s)
        self.assertNotIn("<script", s)
        self.assertNotIn("\u2014", s)  # no long dash in what I write

    def test_stale_line(self):
        self.assertNotIn("no data for", build_ville.svg(FIXTURE, self.NOW))
        old = build_ville.svg(FIXTURE, datetime(2026, 11, 7, 5, 17))
        self.assertIn("no data for 4 days, laptop off", old)

    def test_every_building_is_drawn(self):
        s = build_ville.svg(FIXTURE, self.NOW)
        self.assertEqual(s.count('class="glow"'), sum(1 for b in FIXTURE["buildings"] if b["done"]))

    def test_lots_on_land_and_apart(self):
        lots = list(build_ville.LOTS.values()) + build_ville.SPARE + [build_ville.LIBRARY]
        r0, r1 = build_ville.RIVER
        for x, y, w, d, _ in lots:
            for cx, cy in ((x, y), (x + w, y), (x, y + d), (x + w, y + d)):
                self.assertTrue(build_ville.inside(cx, cy), (x, y))
            self.assertFalse(x < r1 and x + w > r0, f"lot in the river at {x},{y}")
            for s in build_ville.STREETS_X:
                self.assertFalse(x - .5 < s < x + w + .5, f"street through the lot at {x},{y}")
            for s in build_ville.STREETS_Y:
                self.assertFalse(y - .5 < s < y + d + .5, f"street through the lot at {x},{y}")
        for i, a in enumerate(lots):
            for b in lots[i + 1:]:
                overlap = a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]
                self.assertFalse(overlap, (a, b))


if __name__ == "__main__":
    unittest.main()
