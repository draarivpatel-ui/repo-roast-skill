---
name: roast-repo
description: >-
  Puts the whole repository in front of a panel of six senior engineers (security, performance,
  newcomer, maintainer, product, ops). Gathers hard facts first, runs the six judges in parallel,
  throws out any jab without a real file:line or command output, and writes roast/ROAST.md with an
  overall score, each judge's roast and score, the top 10 fixes ranked by impact for the effort,
  the one thing to fix today, and a shareable SVG scorecard. Use when the user says "roast my
  repo", "roast this codebase", "be brutally honest about my code", "rate my project",
  "what's wrong with this repo", "tear my code apart", or "give me a savage code review".
argument-hint: "[path] [--gentle|--savage]"
---

# roast-repo: the main event

Six judges, one repository, no mercy and no made-up evidence. The point is a review people
actually read to the end and share, because it is funny, and actually act on, because every jab
names a file, a line and a fix. Tone is adjustable. The evidence bar is not.

## Inputs

- `path`: repository root. Default: the current working directory.
- Mode flag: `--gentle`, none (default), or `--savage`. Mode changes wording only. Read
  `${CLAUDE_SKILL_DIR}/tone.md` before writing any roast line.

## Outputs (in the roasted repo)

```
roast/facts.json      hard facts from facts.py
roast/panel/*.json    one verdict per judge
roast/roast.json      assembled, validated verdict (input for rematch)
roast/card.json       input for the card
roast/ROAST.md        the report
roast/card.svg        1200x630 shareable scorecard
roast/badge.svg       small "roast score 7.4/10" badge
roast/history/        previous roast.json files, archived automatically
```

## Steps

1. **Confirm the target.** Resolve the path and `cd` into it; run every command below from the
   repo root so paths in the output stay relative. If it has no source files at all, stop and say
   so; there is nothing to roast. Tell the user which mode you are using in one line.

2. **Gather facts before any opinion.**
   ```
   python3 "${CLAUDE_SKILL_DIR}/facts.py" . --out roast/facts.json
   python3 "${CLAUDE_SKILL_DIR}/facts.py" . --format md
   ```
   Show the markdown summary to the user in a few lines. If `secrets.total` is above zero, say so
   now, before any jokes: open each suspect, confirm or dismiss it, and never print the value.

3. **Convene the panel in parallel.** In ONE message, launch six Agent calls with subagent types
   `judge-security`, `judge-performance`, `judge-newcomer`, `judge-maintainer`, `judge-product`
   and `judge-ops` (they may be listed as `repo-roast-skill:judge-security` and so on; use the name
   exactly as listed). Give each the same brief:
   ```
   repo: <absolute path>
   facts: <absolute path>/roast/facts.json
   mode: <gentle|default|savage>
   Read the facts, then read the code yourself. Return your verdict as one json block.
   ```
   If the agents are not installed, run the six lenses yourself one after another, using each
   file in `${CLAUDE_SKILL_DIR}/../../agents/` as the rubric, and tell the user the panel ran
   without subagents.

4. **Save each verdict** exactly as returned to `roast/panel/<judge>.json` (just the JSON object).
   If a judge returned invalid JSON, fix only the syntax, never the content. If a judge failed
   entirely, rerun it once; if it fails again, continue with five and say so in the report.

5. **Spot-check before you publish.** For each judge, open the cited lines of their two
   highest-impact roasts and confirm the code says what the roast claims. If a roast misreads the
   code, delete it from the panel file. Wrong evidence is worse than a missing joke.

6. **Assemble the verdict.** Write a headline: one line, under 90 characters, about the repo as a
   whole, in the chosen tone. Then:
   ```
   python3 "${CLAUDE_SKILL_DIR}/verdict.py" --judges roast/panel --repo . \
     --facts roast/facts.json --out-dir roast --mode <mode> --headline "<headline>"
   ```
   The script is the bailiff: it drops any roast whose `path:line` does not exist, whose
   `facts.<key>` is unknown, or that has no fix, and recomputes any score that does not match its
   rubric. It lists everything it threw out in ROAST.md. It archives an existing roast.json into
   `roast/history/` first.

7. **Make the card.**
   ```
   python3 "${CLAUDE_SKILL_DIR}/../roast-card/card.py" --in roast/card.json --out roast/card.svg --badge-path roast/badge.svg
   python3 "${CLAUDE_SKILL_DIR}/../roast-card/badge.py" --in roast/card.json --out roast/badge.svg
   ```

8. **Deliver.** In chat, show: the overall score and tier, the headline, a six-row table of judge
   scores, the one thing to fix today, and the paths written. Keep it under 25 lines; the full
   roast lives in ROAST.md. Offer the markdown snippet the card script printed for the README.

## Decision rules

- Overall score is the plain mean of the judges, computed by `verdict.py`. Never hand-edit it.
- "Fix today" is the highest-ranked fix with effort S. Ranking is impact divided by effort.
- A confirmed live credential overrides everything: it becomes the fix for today, and the chat
  reply starts with "Rotate this credential first" before any score.
- Large repos (over ~2,000 source files): tell the judges to focus on the top-level entry points
  and the ten churn hotspots in `facts.git.churn_hotspots`, and say so in the report.
- A `roast/` folder already exists: keep it; `verdict.py` archives the last result for rematch.

## What NOT to do

- Do not roast people. No names from git history, no guessing who wrote what, no jokes about
  anyone's identity, age, nationality, gender or experience. The code is the defendant.
- No profanity or slurs, even in `--savage`. Savage means sharper wit, not meaner words.
- Do not add a roast the panel did not make, or keep one whose evidence you could not confirm.
- Do not modify any file outside `roast/`. This skill is read-only for the user's code.
- Do not run the project, its tests, installs or anything that touches the network.
- Do not paste secrets, tokens or `.env` contents anywhere, including ROAST.md.
- Do not commit, push, open issues or post the card anywhere. Offer; the user decides.

## Hand-off

- "Fix it" / "let's fix these" -> `roast-fix` (reads `roast/roast.json`).
- After fixes -> `roast-rematch` for the before and after card.
- README got hammered -> `roast-readme` for a focused rewrite of the top of the README.
- Reviewing a branch instead of the whole repo -> `roast-pr`.
