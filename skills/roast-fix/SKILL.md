---
name: roast-fix
description: >-
  Turns a roast into an executable fix plan and then, with the user's go-ahead, fixes the quick
  wins one at a time, re-running the tests after each and stopping on the first failure. Reads
  roast/roast.json (or a roast-pr report), writes roast/FIXPLAN.md with exact files, steps and a
  check for each fix, and never commits. Use when the user says "fix the roast", "fix the quick
  wins", "do the top fixes", "make the roast go away", "turn the roast into a plan", "start on the
  fix for today", or "apply the roast fixes".
argument-hint: "[--only N] [--quick-wins] [roast/roast.json]"
---

# roast-fix: from punchline to pull request

A roast is only worth something if the repo gets better. This skill takes the panel's top fixes,
turns each into a step anyone could follow, and then works through the quick wins one by one with
the test suite as the referee. Nothing is changed before the user sees the plan, and nothing is
committed at all.

## Inputs

- `roast/roast.json` from roast-repo (default), or a `roast/PR-<id>.md` from roast-pr.
- `--quick-wins`: only fixes with effort S. `--only N`: only fix number N from the plan.

## Outputs

- `roast/FIXPLAN.md`: the plan, with a status column that this skill updates as it goes.
- Code changes in the working tree, uncommitted, one fix at a time.

## Steps

1. **Load the roast.** Read `roast/roast.json`: `top_fixes` (ranked), `fix_today`, and each
   judge's roasts. If there is no roast, suggest `roast-repo` and stop. If the roast is older than
   the latest commit touching a cited file (`git log -1 --format=%cs -- <file>`), warn that some
   evidence may have moved and re-check those lines first.

2. **Find the referee.** Work out how to run the tests and linters from the repo itself:
   `package.json` scripts, `Makefile`, `pyproject.toml`/`tox.ini`, `Cargo.toml`, `go.mod`, CI
   workflow steps. Run the test command once now and record the baseline (pass, fail, or none).
   If the baseline already fails, tell the user and ask whether to continue; fixes cannot be
   judged against a red suite.

3. **Write roast/FIXPLAN.md.** One section per fix, in roast rank order, quick wins (effort S)
   first if `--quick-wins`:
   ```
   ## 3. Add a timeout to the payments client          [status: todo]
   Roast: "No timeout on line 30..." (The On-Call)
   Evidence: src/payments/client.py:30
   Change: pass timeout=10 to requests.post; make it a setting PAYMENTS_TIMEOUT_S, default 10
   Files: src/payments/client.py, .env.example
   Check: pytest tests/test_payments.py, then grep shows no requests call without timeout
   Risk: low | Effort: S | Auto-fixable: yes
   ```
   Mark as **not auto-fixable** anything that needs a decision or an outside action: rotating a
   leaked credential, rewriting git history, choosing a new dependency, architecture splits
   (effort L), product decisions. Those get a checklist for the human instead of code.

4. **Ask before touching code.** Show the plan summary (number, title, effort, auto-fixable) and
   ask which to apply: all auto-fixable quick wins, a list of numbers, or none. Wait for the answer.

5. **Fix one at a time.** For each approved fix:
   1. Re-read the cited lines; if the evidence no longer matches, mark `skipped (evidence moved)`.
   2. Make the smallest change that resolves the roast. Match the surrounding style. Add or update
      a test when the fix changes behaviour.
   3. Run the check from the plan, then the full test command.
   4. Green: mark `done` in FIXPLAN.md with a one-line note of what changed.
      Red: try once to correct your own change. Still red: revert only your change to those files
      (`git diff` to confirm what is yours), mark `failed: <reason>`, and stop the run.

6. **Report.** Done, skipped, failed, and the not-auto-fixable checklist. Show `git diff --stat`.
   Suggest the commit messages the user could use, one per fix, without committing.

## Decision rules

- A confirmed leaked credential: the plan's first item is "rotate it at the provider" for the human,
  even if the roast ranked it lower. Removing it from the code comes second; scrubbing history is a
  human decision with a warning that it rewrites shared history.
- Never batch several fixes into one change; one fix, one test run, one status line.
- Formatting-only or lint-only fixes run the linter as their check, not just the tests.

## What NOT to do

- Do not commit, push, open a PR or change branches. Leave the diff for the user.
- Do not delete tests, skip tests, or loosen assertions to get green.
- Do not upgrade or add dependencies without asking first, even if a roast suggested it.
- Do not "fix" things the roast did not raise. Scope creep is how quick wins become long weekends.
- Do not edit `roast/roast.json`; it is the record that rematch compares against.

## Hand-off

- When the fixes are in: `roast-rematch` re-convenes the panel and shows the score change per judge.
