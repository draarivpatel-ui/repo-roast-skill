"""Structural checks for the plugin: frontmatter, manifests, README coverage, license."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO_NAME = "repo-roast-skill"
PREFIX = "roast-"


def frontmatter(path: Path) -> dict:
    """Parse simple YAML frontmatter by hand: key: value and folded (>-) blocks."""
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    data, key = {}, None
    for line in text[4:end].split("\n"):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if m and not line.startswith((" ", "\t")):
            key, value = m.group(1), m.group(2).strip()
            data[key] = "" if value in {">-", ">", "|", "|-"} else value.strip('"').strip("'")
        elif key is not None:
            data[key] = (data[key] + " " + line.strip()).strip()
    return data


def skill_dirs():
    return sorted(p for p in (ROOT / "skills").iterdir() if p.is_dir())


def agent_files():
    return sorted((ROOT / "agents").glob("*.md"))


class SkillTests(unittest.TestCase):
    def test_has_five_to_seven_skills(self):
        self.assertTrue(5 <= len(skill_dirs()) <= 7, [p.name for p in skill_dirs()])

    def test_skill_frontmatter(self):
        for d in skill_dirs():
            with self.subTest(skill=d.name):
                skill_md = d / "SKILL.md"
                self.assertTrue(skill_md.exists())
                fm = frontmatter(skill_md)
                self.assertEqual(fm.get("name"), d.name)
                self.assertTrue(d.name.startswith(PREFIX))
                self.assertTrue(fm.get("description"))
                self.assertLess(len(fm["description"]), 1024)
                self.assertIn("Use when", fm["description"])

    def test_skill_length_and_sections(self):
        for d in skill_dirs():
            with self.subTest(skill=d.name):
                text = (d / "SKILL.md").read_text(encoding="utf-8")
                lines = text.count("\n") + 1
                self.assertTrue(60 <= lines <= 200, f"{d.name} has {lines} lines")
                self.assertIn("What NOT to do", text)

    def test_referenced_scripts_exist(self):
        for d in skill_dirs():
            text = (d / "SKILL.md").read_text(encoding="utf-8")
            for rel in re.findall(r"\$\{CLAUDE_SKILL_DIR\}/([\w./-]+\.py)", text):
                with self.subTest(skill=d.name, script=rel):
                    self.assertTrue((d / rel).resolve().exists(), rel)


class AgentTests(unittest.TestCase):
    def test_six_judges(self):
        self.assertEqual(len(agent_files()), 6)

    def test_agent_frontmatter(self):
        for f in agent_files():
            with self.subTest(agent=f.name):
                fm = frontmatter(f)
                self.assertEqual(fm.get("name"), f.stem)
                self.assertTrue(fm.get("description"))
                tools = {t.strip() for t in fm.get("tools", "").split(",")}
                self.assertEqual(tools, {"Read", "Grep", "Glob", "Bash"}, "judges are read-only")

    def test_agent_length_and_contract(self):
        for f in agent_files():
            with self.subTest(agent=f.name):
                text = f.read_text(encoding="utf-8")
                lines = text.count("\n") + 1
                self.assertTrue(40 <= lines <= 120, f"{f.name} has {lines} lines")
                for key in ['"score"', '"rubric"', '"verdict"', '"roasts"', '"evidence"', '"fix"']:
                    self.assertIn(key, text)
                self.assertIn("never the people", text)

    def test_agent_example_json_parses_and_rubric_sums(self):
        for f in agent_files():
            with self.subTest(agent=f.name):
                text = f.read_text(encoding="utf-8")
                block = re.search(r"```json\n(.*?)\n```", text, re.S)
                self.assertIsNotNone(block)
                data = json.loads(block.group(1))
                self.assertEqual(data["judge"], f.stem.replace("judge-", ""))
                self.assertEqual(len(data["rubric"]), 5)
                self.assertAlmostEqual(sum(data["rubric"].values()), data["score"])


class ManifestTests(unittest.TestCase):
    def test_plugin_json(self):
        data = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(data["name"], REPO_NAME)
        self.assertEqual(data["name"], ROOT.name if ROOT.name == REPO_NAME else REPO_NAME)
        self.assertRegex(data["version"], r"^\d+\.\d+\.\d+$")
        self.assertEqual(data["license"], "MIT")
        self.assertEqual(data["author"]["name"], "Vivek Bhange")
        self.assertTrue(6 <= len(data["keywords"]) <= 10)
        self.assertIn("claude-code", data["keywords"])
        self.assertIn("claude-skills", data["keywords"])

    def test_marketplace_json(self):
        data = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual(data["name"], REPO_NAME)
        self.assertEqual(data["owner"]["name"], "Vivek Bhange")
        self.assertEqual(len(data["plugins"]), 1)
        plugin = data["plugins"][0]
        self.assertEqual(plugin["name"], REPO_NAME)
        self.assertEqual(plugin["source"], "./")
        self.assertEqual(plugin["category"], "development")
        self.assertTrue(plugin["homepage"].endswith("/" + REPO_NAME))


class DocsTests(unittest.TestCase):
    def test_readme_mentions_every_skill_and_agent(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for d in skill_dirs():
            self.assertIn(d.name, readme)
        for f in agent_files():
            self.assertIn(f.stem, readme)
        self.assertIn(f"/plugin marketplace add vivekbhange-hub/{REPO_NAME}", readme)
        self.assertIn(f"/plugin install {REPO_NAME}@{REPO_NAME}", readme)

    def test_readme_local_links_exist(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for target in re.findall(r"\]\(([^)#\s]+)\)", readme):
            if re.match(r"https?:", target):
                continue
            with self.subTest(target=target):
                self.assertTrue((ROOT / target).exists(), target)

    def test_license(self):
        text = (ROOT / "LICENSE").read_text(encoding="utf-8")
        self.assertIn("MIT", text)
        self.assertIn("Copyright (c) 2026 Vivek Bhange", text)

    def test_changelog_and_contributing(self):
        version = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"]
        self.assertIn(f"## [{version}] - ", (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"),
                      "every released version needs a CHANGELOG entry")
        self.assertTrue((ROOT / "CONTRIBUTING.md").exists())

    def test_examples_present(self):
        for name in ["ROAST.example.md", "card.example.svg", "panel.example.json"]:
            self.assertTrue((ROOT / "examples" / name).exists(), name)


if __name__ == "__main__":
    unittest.main()
