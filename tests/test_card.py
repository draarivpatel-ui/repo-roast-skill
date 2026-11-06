import io
import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from contextlib import redirect_stdout
from pathlib import Path

from _load import load

card = load("roast-card", "card")
SVG = "{http://www.w3.org/2000/svg}"


def sample(**extra):
    data = {
        "repo": "acme/widget", "overall": 6.2, "headline": "Solid ingredients, questionable cooking.",
        "date": "2026-11-07", "mode": "default",
        "judges": [
            {"name": "The Paranoid", "role": "Security", "score": 4.5, "quote": "Line 42 builds SQL."},
            {"name": "The Stopwatch", "role": "Performance", "score": 8.0, "quote": "Fast enough."},
        ],
    }
    data.update(extra)
    return data


def texts(svg: str) -> str:
    root = ET.fromstring(svg)
    return " ".join("".join(t.itertext()) for t in root.iter(f"{SVG}text"))


class CardRenderTests(unittest.TestCase):
    def test_parses_and_has_social_preview_size(self):
        root = ET.fromstring(card.render(sample()))
        self.assertEqual(root.tag, f"{SVG}svg")
        self.assertEqual(root.get("width"), "1200")
        self.assertEqual(root.get("height"), "630")
        self.assertEqual(root.get("viewBox"), "0 0 1200 630")

    def test_contains_repo_score_tier_and_judges(self):
        t = texts(card.render(sample()))
        for expected in ["acme/widget", "6.2", "Needs Seasoning", "The Paranoid", "4.5", "Security"]:
            self.assertIn(expected, t)

    def test_self_contained(self):
        svg = card.render(sample())
        self.assertNotIn("<script", svg)
        self.assertNotIn("<image", svg)
        self.assertNotIn("http://", svg.replace("http://www.w3.org/2000/svg", ""))
        self.assertNotIn("https://", svg)

    def test_escapes_markup_and_quotes(self):
        nasty = '<script>alert("x")</script> & \'quotes\''
        svg = card.render(sample(repo=nasty, headline=nasty,
                                 judges=[{"name": nasty, "role": "<b>", "score": 5, "quote": nasty}]))
        root = ET.fromstring(svg)  # must still parse
        self.assertNotIn("<script>", svg)
        self.assertIn("&lt;script&gt;", svg)
        self.assertIn("&amp;", svg)
        self.assertIsNotNone(root)

    def test_strips_control_characters(self):
        svg = card.render(sample(repo="bad\x00name\x07here", headline="a\x1bb"))
        ET.fromstring(svg)
        self.assertIn("badnamehere", svg)

    def test_handles_non_ascii(self):
        svg = card.render(sample(repo="café/naïve", headline="Ünïcødé ✓ works"))
        self.assertIn("café/naïve", texts(svg))

    def test_before_and_after(self):
        data = sample(previous_overall=5.1)
        data["judges"][0]["previous"] = 3.0
        t = texts(card.render(data))
        self.assertIn("was 5.1", t)
        self.assertIn("+1.1", t)
        self.assertIn("3.0 → 4.5", t)
        self.assertIn("+1.5", t)

    def test_negative_delta(self):
        data = sample()
        data["judges"][1]["previous"] = 9.0
        self.assertIn("-1.0", texts(card.render(data)))

    def test_caps_judges_at_six(self):
        judges = [{"name": f"Judge {i}", "score": i, "quote": "q"} for i in range(9)]
        t = texts(card.render(sample(judges=judges)))
        self.assertIn("Judge 5", t)
        self.assertNotIn("Judge 6", t)

    def test_no_judges_and_missing_fields(self):
        svg = card.render({})
        ET.fromstring(svg)
        self.assertIn("No judges", svg)
        self.assertIn("0.0", texts(svg))

    def test_zero_score_draws_no_arc(self):
        svg = card.render(sample(overall=0))
        self.assertNotIn("stroke-dasharray", svg)

    def test_scores_are_clamped(self):
        t = texts(card.render(sample(overall=42, judges=[{"name": "X", "score": -3}])))
        self.assertIn("10.0", t)
        self.assertIn("0.0", t)


class TruncationTests(unittest.TestCase):
    def test_short_text_unchanged(self):
        self.assertEqual(card.truncate("short", 10), "short")

    def test_long_text_truncated_with_ellipsis(self):
        out = card.truncate("word " * 40, 30)
        self.assertLessEqual(len(out), 30)
        self.assertTrue(out.endswith("…"))

    def test_long_quote_on_card_is_truncated(self):
        long_quote = "x" * 300
        svg = card.render(sample(judges=[{"name": "A", "score": 5, "quote": long_quote}]))
        self.assertNotIn("x" * 100, svg)
        self.assertIn("…", svg)

    def test_long_repo_name_truncated(self):
        svg = card.render(sample(repo="a" * 120))
        self.assertNotIn("a" * 65, texts(svg))
        self.assertNotIn("a" * 100, svg)

    def test_wrap_respects_width_and_lines(self):
        lines = card.wrap("one two three four five six seven eight nine ten eleven twelve", 12, 2)
        self.assertEqual(len(lines), 2)
        self.assertTrue(all(len(line) <= 12 for line in lines))
        self.assertTrue(lines[-1].endswith("…"))

    def test_wrap_fits_without_ellipsis(self):
        self.assertEqual(card.wrap("one two", 20, 2), ["one two"])

    def test_wrap_handles_giant_word(self):
        lines = card.wrap("a" * 80, 20, 3)
        self.assertTrue(all(len(line) <= 20 for line in lines))


class ColourAndTierTests(unittest.TestCase):
    def test_score_color_thresholds(self):
        red, orange, amber, green = (c for _, c in card.SCORE_BANDS)
        self.assertEqual(card.score_color(0), red)
        self.assertEqual(card.score_color(3.9), red)
        self.assertEqual(card.score_color(4.0), orange)
        self.assertEqual(card.score_color(5.9), orange)
        self.assertEqual(card.score_color(6.0), amber)
        self.assertEqual(card.score_color(7.9), amber)
        self.assertEqual(card.score_color(8.0), green)
        self.assertEqual(card.score_color(10), green)
        self.assertEqual(card.score_color("nonsense"), red)

    def test_tiers(self):
        self.assertEqual(card.tier(2.9), "Dumpster Fire")
        self.assertEqual(card.tier(3.0), "Smoke Alarm")
        self.assertEqual(card.tier(5.0), "Needs Seasoning")
        self.assertEqual(card.tier(7.0), "Nicely Done")
        self.assertEqual(card.tier(8.5), "Chef's Kiss")
        self.assertEqual(card.tier(10), "Chef's Kiss")


class CliTests(unittest.TestCase):
    def test_cli_writes_svg_and_prints_snippet(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "card.json"
            out = Path(tmp) / "out" / "card.svg"
            src.write_text(json.dumps(sample()), encoding="utf-8")
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = card.main(["--in", str(src), "--out", str(out), "--badge-path", "roast/badge.svg"])
            self.assertEqual(code, 0)
            ET.parse(out)
            self.assertIn("[![Roast score 6.2/10](roast/badge.svg)](roast/ROAST.md)", buf.getvalue())
            self.assertIn("card.svg", buf.getvalue())

    def test_cli_rejects_bad_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "card.json"
            src.write_text("{not json", encoding="utf-8")
            code = card.main(["--in", str(src), "--out", str(Path(tmp) / "c.svg")])
            self.assertEqual(code, 2)


class ExampleTests(unittest.TestCase):
    def test_committed_example_card_parses(self):
        path = Path(__file__).resolve().parent.parent / "examples" / "card.example.svg"
        root = ET.parse(path).getroot()
        self.assertEqual(root.get("width"), "1200")


if __name__ == "__main__":
    unittest.main()
