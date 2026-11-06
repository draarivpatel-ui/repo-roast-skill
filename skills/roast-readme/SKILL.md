---
name: roast-readme
description: >-
  Roasts only the README and the first five minutes a stranger spends with the project: can they
  tell what it is, install it and see it work in five minutes? Measures the README with a script
  (title, pitch length, line of the first command, install and usage sections, broken links),
  walks the setup on paper, scores it, then rewrites the top of the README and shows the diff
  before saving. Use when the user says "roast my README", "is my README any good", "would a
  stranger understand this repo", "fix my README intro", "why does nobody star my repo", or
  "review my getting started section".
argument-hint: "[path to repo or README]"
---

# roast-readme: the first five minutes

Most people decide whether to use a project before they scroll twice. This skill plays that
stranger, times their five minutes, roasts every place they would give up, and then does the
useful part: rewrites the top of the README so the next stranger does not give up.

## Inputs

- A repo path or README path. Default: the current directory.
- Mode flag: `--gentle`, none, or `--savage`, same meaning as in roast-repo
  (`${CLAUDE_SKILL_DIR}/../roast-repo/tone.md`).

## Outputs

- `roast/README-ROAST.md`: score, the five-minute timeline, roasts with evidence and fixes.
- `roast/README.top.md`: the proposed new top of the README (title through first working command).
- The README itself is changed only after the user approves the diff.

## Steps

1. **Measure.**
   ```
   python3 "${CLAUDE_SKILL_DIR}/readme_lint.py" <path> --format md
   python3 "${CLAUDE_SKILL_DIR}/readme_lint.py" <path> --format json
   ```
   Exit code 1 means there is no README. That is the whole roast; skip to step 5 and write one.

2. **Run the five-minute clock on paper.** Read the README top to bottom as someone who has never
   seen the project. Record a timeline, one entry per obstacle, each with its README line:
   - 0:00-0:30: Do I know what this is and who it is for? (title, first paragraph)
   - 0:30-2:00: Can I install it? Every command the README gives: does the script, file, package
     name or version it refers to exist in the repo (`package.json` scripts, `Makefile`,
     `pyproject.toml`, `Cargo.toml`)? Check by reading; do not run installs.
   - 2:00-4:00: Can I see it work? Is there a first command with its expected output, a screenshot
     or a GIF?
   - 4:00-5:00: Where do I go next? Docs, examples, how to get help, license.
   Use `judge-newcomer` for a second opinion on large READMEs (pass it the repo path and mode).

3. **Score it** on five criteria, 0-2 each: Pitch (what and for whom, one paragraph), Install
   (steps exist and match the repo), First success (a command plus expected output), Navigation
   (headings, next steps, no broken links) and Trust signals (license, maintenance status,
   honest limits). Each criterion below 1 needs a roast with evidence (`README.md:<line>` or a
   readme_lint fact).

4. **Write roast/README-ROAST.md**: score and the one-line verdict, the timeline, then each roast as
   line / evidence / fix. Keep the jokes about the README, never the author.

5. **Rewrite the top.** Draft `roast/README.top.md` containing, in order:
   - `# Name` and a one-sentence hook that states the outcome for the user, not the tech stack.
   - A two to four sentence paragraph: the problem, what this does about it, who it is for.
   - Install: the shortest real path, using commands that exist in this repo.
   - A first command and a short block of its real or clearly-labelled example output.
   - A pointer to the rest of the docs.
   Every command must come from the repo (manifests, scripts, existing docs). If you cannot verify
   one, mark it `<!-- verify: ... -->` instead of guessing.

6. **Show the diff and ask.** Show the old top next to the new one. Only after the user says yes,
   replace the top of the README (everything above the first section you are not rewriting) and
   leave the rest untouched.

## Decision rules

- First command below line 60, or no command at all: Install and First success both max at 1.
- More than six badges before the first paragraph: roast it; badges are not a pitch.
- Broken relative links from readme_lint are always fixes with effort S.
- Keep the author's voice where it works. A rewrite that sounds like a brochure is worse.

## What NOT to do

- Do not invent features, benchmarks, install commands, star counts or testimonials.
- Do not change anything below the rewritten top unless the user asks.
- Do not save the README before the user has seen and approved the diff.
- Do not add badges that claim facts (coverage, downloads) the repo cannot back up.

## Hand-off

- Rest of the repo needs a roast -> `roast-repo`.
- README fixed after a full roast -> `roast-rematch` to see the newcomer judge's score move.
