import io
import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from contextlib import redirect_stdout
from pathlib import Path

from _load import load

delta = load("roast-rematch", "delta")
card = load("roast-card", "card")


def roast(overall, scores, roasts=None, date="2026-11-01"):
    roasts = roasts or {}
    return {
        "repo": "demo", "date": date, "mode": "default", "overall": overall, "tier": card.tier(overall),
        "headline": "h",
        "judges": [{"judge": k, "persona": f"The {k.title()}", "score": v, "verdict": f"{k} says",
                    "roasts": [{"line": f"{k} jab", "evidence": ev, "fix": "f"} for ev in roasts.get(k, [])]}
                   for k, v in scores.items()],
    }


BEFORE = roast(4.0, {"security": 3.0, "maintainer": 5.0, "ops": 4.0},
               {"security": ["a.py:1", "b.py:2"], "maintainer": ["c.py:3"]})
AFTER = roast(6.0, {"security": 6.5, "maintainer": 4.5, "product": 7.0},
              {"security": ["b.py:2"], "maintainer": ["d.py:9"]}, date="2026-11-07")


class CompareTests(unittest.TestCase):
    def setUp(self):
        self.c = delta.compare(BEFORE, AFTER)
        self.rows = {r["judge"]: r for r in self.c["rows"]}

    def test_overall_delta(self):
        self.assertEqual(self.c["overall_delta"], 2.0)

    def test_per_judge_delta(self):
        self.assertEqual(self.rows["security"]["delta"], 3.5)
        self.assertEqual(self.rows["maintainer"]["delta"], -0.5)

    def test_absent_judges(self):
        self.assertIsNone(self.rows["product"]["before"])
        self.assertIsNone(self.rows["ops"]["after"])
        self.assertIsNone(self.rows["ops"]["delta"])

    def test_charges(self):
        self.assertEqual({r["evidence"] for r in self.c["dropped"]}, {"a.py:1", "c.py:3"})
        self.assertEqual({r["evidence"] for r in self.c["new"]}, {"d.py:9"})
        self.assertEqual(self.c["persisting"], 1)

    def test_markdown(self):
        md = delta.render_markdown(self.c)
        self.assertIn("4.0 → 6.0 (+2.0)", md)
        self.assertIn("| +3.5 |", md)
        self.assertIn("| -0.5 |", md)
        self.assertIn("absent", md)
        self.assertIn("Most improved: The Security (+3.5)", md)
        self.assertIn("## Charges dropped (2)", md)

    def test_signed(self):
        self.assertEqual(delta.signed(1.04), "+1.0")
        self.assertEqual(delta.signed(-0.25), "-0.2")
        self.assertEqual(delta.signed(0), "0.0")


class CardPayloadTests(unittest.TestCase):
    def test_payload_renders_before_after(self):
        payload = delta.card_payload(BEFORE, AFTER)
        self.assertEqual(payload["previous_overall"], 4.0)
        prev = {j["role"]: j.get("previous") for j in payload["judges"]}
        self.assertEqual(prev["Security"], 3.0)
        self.assertIsNone(prev["Product"])
        svg = card.render(payload)
        ET.fromstring(svg)
        self.assertIn("was 4.0", svg)


class CliTests(unittest.TestCase):
    def test_cli_writes_report_and_card(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp)
            (t / "before.json").write_text(json.dumps(BEFORE), encoding="utf-8")
            (t / "after.json").write_text(json.dumps(AFTER), encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                code = delta.main(["--before", str(t / "before.json"), "--after", str(t / "after.json"),
                                   "--out", str(t / "REMATCH.md"), "--card-out", str(t / "card.json")])
            self.assertEqual(code, 0)
            self.assertIn("# Rematch: demo", (t / "REMATCH.md").read_text(encoding="utf-8"))
            self.assertIn("previous_overall", (t / "card.json").read_text(encoding="utf-8"))

    def test_cli_json_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp)
            (t / "b.json").write_text(json.dumps(BEFORE), encoding="utf-8")
            buf = io.StringIO()
            with redirect_stdout(buf):
                delta.main(["--before", str(t / "b.json"), "--after", str(t / "b.json"), "--json"])
            self.assertEqual(json.loads(buf.getvalue())["overall_delta"], 0.0)

    def test_cli_rejects_non_roast(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.json"
            bad.write_text("{}", encoding="utf-8")
            self.assertEqual(delta.main(["--before", str(bad), "--after", str(bad)]), 2)


if __name__ == "__main__":
    unittest.main()
