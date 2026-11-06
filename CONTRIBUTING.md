# Contributing to repo-roast-skill

Thanks for wanting to make the panel sharper. Contributions of every size are welcome: a better
roast line in a tone example, a new check for a judge, a bug in a script, a clearer README.

## Ground rules

- **Evidence first.** Any change to a judge must keep the rule that every roast cites a real
  `path:line`, a command and its output, or a `facts.<key>`, and comes with a fix.
- **Roast the code, never the people.** No examples, tests or prompts that name, describe or mock
  a person. No profanity or slurs, in any mode.
- **Standard library only** for the helper scripts, Python 3.9+, no network calls, deterministic
  output.
- **Read-only judges.** Agents keep `tools: Read, Grep, Glob, Bash` and must not edit files.

## Development

```
git clone https://github.com/vivekbhange-hub/repo-roast-skill
cd repo-roast-skill
python -m unittest discover -s tests -v
```

Tests must pass on Windows and Linux. Use `pathlib`, open files with `encoding="utf-8"`, and do
not assume a shell. Scripts in skill folders are loaded by path in tests via `tests/_load.py`.

If you change `card.py` or `badge.py`, regenerate the examples so the README stays honest:

```
python skills/roast-repo/verdict.py --judges examples/panel.example.json --out-dir /tmp/ex \
  --repo-name fictional-co/snackstack --date 2026-11-07 --headline "..."
python skills/roast-card/card.py --in /tmp/ex/card.json --out examples/card.example.svg
python skills/roast-card/badge.py --in /tmp/ex/card.json --out examples/badge.example.svg
```

## Skill and agent conventions

- Skill folder name equals the `name` in its `SKILL.md` frontmatter, prefixed `roast-`.
- Each `SKILL.md` has numbered steps, decision rules, a "What NOT to do" section and a hand-off.
- Each judge returns exactly one JSON block in the shape shown in its agent file, with a five-part
  rubric scored 0-2 per criterion.

## Pull requests

1. Open an issue first for anything bigger than a fix, so we can agree on the shape.
2. Keep the PR focused; one change per PR.
3. Add or update tests for any script change.
4. Add a line under an "Unreleased" heading in `CHANGELOG.md`.

## Conduct

Be kind and specific in reviews, which is the whole point of this project. This project follows the
[Contributor Covenant](https://www.contributor-covenant.org/version/2/1/code_of_conduct/).
