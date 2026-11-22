"""The header's release row and the terminal's title say what really happened.

    python -m unittest discover tests
"""
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
os.environ.setdefault("GITHUB_TOKEN", "offline")  # build_header reads it at import

import build_header  # noqa: E402
import build_nightly  # noqa: E402

RUN = {"run_id": "2026-11-22_0042", "night": "2026-11-22", "finished_at": "2026-11-22T00:42:10",
       "model": "m", "since": "2026-11-21", "notes": 4, "links": 12, "proposals": 4,
       "vault_notes": "1724", "orphans": "5", "links_per_note": "4.39"}


class LatestRelease(unittest.TestCase):
    def test_most_recent_release_wins(self):
        nodes = [{"name": "nous-deux", "latestRelease": None},
                 {"name": "nightshift", "latestRelease": {"tagName": "v0.3.0",
                                                          "publishedAt": "2026-10-24T18:00:00Z"}},
                 {"name": "radar", "latestRelease": {"tagName": "v1.0.0",
                                                     "publishedAt": "2026-06-01T10:00:00Z"}}]
        self.assertEqual(build_header.latest_release(nodes), ("nightshift", "v0.3.0"))

    def test_no_release_at_all(self):
        self.assertIsNone(build_header.latest_release([{"name": "a", "latestRelease": None}]))

    def test_header_has_no_countdown(self):
        s = build_header.svg({"repos": 13, "commits": 270, "tests": 619, "ci": "SUCCESS",
                              "release": "nightshift v0.3.0", "built": "2026-11-22 05:17 UTC"})
        self.assertIn("LATEST RELEASE", s)
        self.assertIn("nightshift v0.3.0", s)
        self.assertNotIn("LAST SHIP", s)
        self.assertNotIn("ago", s)


class TerminalTitle(unittest.TestCase):
    def test_a_run_in_its_night(self):
        self.assertEqual(build_nightly.title(RUN), "nightshift — the night of 2026-11-22 · 00:42")
        self.assertEqual(build_nightly.late(RUN), [])

    def test_a_catch_up_run_says_so(self):
        d = dict(RUN, run_id="2026-11-22_1304", finished_at="2026-11-22T13:04:50")
        self.assertEqual(build_nightly.title(d), "nightshift — catch-up run · 2026-11-22 13:04")
        self.assertIn("due at 00:30", build_nightly.late(d)[0][0][1])
        s = build_nightly.svg(d)
        self.assertIn("catch-up run", s)
        self.assertNotIn("the night of", s)


if __name__ == "__main__":
    unittest.main()
