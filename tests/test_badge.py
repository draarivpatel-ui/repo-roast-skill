import io
import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from contextlib import redirect_stdout
from pathlib import Path

from _load import load

badge = load("roast-card", "badge")
card = load("roast-card", "card")
SVG = "{http://www.w3.org/2000/svg}"


class BadgeTests(unittest.TestCase):
    def test_parses_and_shows_score(self):
        svg = badge.render(7.4)
        root = ET.fromstring(svg)
        self.assertEqual(root.get("height"), "20")
        text = " ".join("".join(t.itertext()) for t in root.iter(f"{SVG}text"))
        self.assertIn("roast score", text)
        self.assertIn("7.4/10", text)
        self.assertIn('aria-label="roast score: 7.4/10"', svg)

    def test_color_thresholds_match_card(self):
        self.assertEqual(badge.SCORE_BANDS, card.SCORE_BANDS)
        for score in [0, 3.9, 4.0, 5.9, 6.0, 7.9, 8.0, 10]:
            self.assertEqual(badge.score_color(score), card.score_color(score), score)

    def test_color_used_in_svg(self):
        self.assertIn(badge.score_color(2.0), badge.render(2.0))
        self.assertIn(badge.score_color(9.0), badge.render(9.0))

    def test_width_grows_with_label(self):
        short = ET.fromstring(badge.render(5, "roast"))
        long = ET.fromstring(badge.render(5, "a much longer roast score label"))
        self.assertGreater(int(long.get("width")), int(short.get("width")))

    def test_escapes_label(self):
        svg = badge.render(5, '<x> & "y"')
        ET.fromstring(svg)
        self.assertIn("&lt;x&gt; &amp;", svg)

    def test_clamps_score(self):
        self.assertIn("10.0/10", badge.render(99))
        self.assertIn("0.0/10", badge.render(-1))

    def test_cli_from_card_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "card.json"
            src.write_text(json.dumps({"overall": 6.2}), encoding="utf-8")
            out = Path(tmp) / "badge.svg"
            buf = io.StringIO()
            with redirect_stdout(buf):
                self.assertEqual(badge.main(["--in", str(src), "--out", str(out)]), 0)
            ET.parse(out)
            self.assertIn("6.2/10", buf.getvalue())

    def test_cli_from_score(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "badge.svg"
            with redirect_stdout(io.StringIO()):
                self.assertEqual(badge.main(["--score", "8.8", "--out", str(out)]), 0)
            self.assertIn("8.8/10", out.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
