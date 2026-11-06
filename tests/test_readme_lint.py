import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from _load import load

lint = load("roast-readme", "readme_lint")

GOOD = """# Widget

[![CI](https://github.com/x/y/actions/workflows/ci.yml/badge.svg)](https://github.com/x/y)

Widget turns messy CSV exports into clean reports for small finance teams.

## Install

```bash
pip install widget
```

## Usage

```
widget report data.csv
```

See [the docs](docs/guide.md) and ![shot](img/missing.png).

## License

MIT
"""


class LintCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "docs").mkdir()
        (self.root / "docs" / "guide.md").write_text("guide", encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def analyse(self, text, name="README.md"):
        (self.root / name).write_text(text, encoding="utf-8")
        return lint.analyse(lint.find_readme(self.root), self.root)


class AnalyseTests(LintCase):
    def test_good_readme(self):
        r = self.analyse(GOOD)
        self.assertEqual(r["title"]["text"], "Widget")
        self.assertEqual(r["first_paragraph"]["line"], 5)
        self.assertEqual(r["install_section"]["line"], 7)
        self.assertEqual(r["usage_section"]["line"], 13)
        self.assertEqual(r["first_command"]["text"], "pip install widget")
        self.assertEqual(r["first_command"]["line"], 10)
        self.assertEqual(r["code_blocks"], 2)
        self.assertEqual(r["badges_top"], 1)
        self.assertTrue(r["mentions_license"])

    def test_broken_relative_links(self):
        r = self.analyse(GOOD)
        self.assertEqual([b["target"] for b in r["broken_links"]], ["img/missing.png"])
        self.assertIn("1 broken relative link(s) or image(s)", r["warnings"])

    def test_bare_readme_warnings(self):
        r = self.analyse("hello\n")
        w = " ".join(r["warnings"])
        for expected in ["no title", "no install", "no usage", "no copy-pasteable command",
                         "license is never mentioned", "only 1 lines long"]:
            self.assertIn(expected, w)

    def test_long_first_paragraph(self):
        r = self.analyse("# T\n\n" + "word " * 120 + "\n")
        self.assertTrue(any("120 words" in w for w in r["warnings"]))

    def test_late_first_command(self):
        filler = "\n".join(f"Line {i}." for i in range(80))
        r = self.analyse(f"# T\n\nIntro.\n\n{filler}\n\n```sh\nnpm install x\n```\n")
        self.assertGreater(r["first_command"]["line"], 60)
        self.assertTrue(any("first command is on line" in w for w in r["warnings"]))

    def test_headings_inside_code_ignored(self):
        r = self.analyse("# Real\n\n```\n# not a heading\n```\n")
        self.assertEqual([h["text"] for h in r["headings"]], ["Real"])

    def test_setext_heading(self):
        r = self.analyse("Title\n=====\n\nText here.\n")
        self.assertEqual(r["title"]["text"], "Title")

    def test_badge_wall(self):
        badges = "\n".join(f"[![b{i}](https://img.shields.io/b{i})](https://x)" for i in range(8))
        r = self.analyse(f"# T\n{badges}\n\nText.\n")
        self.assertEqual(r["badges_top"], 8)
        self.assertTrue(any("8 badges" in w for w in r["warnings"]))

    def test_external_links_not_checked(self):
        r = self.analyse("# T\n\n[a](https://example.com) [b](#anchor) [c](mailto:x@y.z)\n")
        self.assertEqual(r["broken_links"], [])


class CliTests(LintCase):
    def test_missing_readme_exit_code(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(lint.main([str(self.root)]), 1)
        self.assertIn("No README found", buf.getvalue())

    def test_json_output(self):
        (self.root / "README.md").write_text(GOOD, encoding="utf-8")
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(lint.main([str(self.root), "--format", "json"]), 0)
        self.assertEqual(json.loads(buf.getvalue())["readme"], "README.md")

    def test_markdown_output_and_file_target(self):
        (self.root / "README.md").write_text(GOOD, encoding="utf-8")
        buf = io.StringIO()
        with redirect_stdout(buf):
            lint.main([str(self.root / "README.md")])
        out = buf.getvalue()
        self.assertIn("# README check: README.md", out)
        self.assertIn("First command: line 10", out)


if __name__ == "__main__":
    unittest.main()
