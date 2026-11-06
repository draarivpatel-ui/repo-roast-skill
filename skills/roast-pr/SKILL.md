---
name: roast-pr
description: >-
  Roasts a diff or pull request with the same evidence rules as the full roast: every jab cites a
  changed file and line in the new code, and every jab comes with a fix. Reads `git diff` against
  a base branch or `gh pr diff <number>`, runs the relevant judges on only the changed lines, and
  writes roast/PR-<id>.md with a score, blockers, and suggested review comments that are posted
  only if the user confirms. Use when the user says "roast this PR", "roast my diff", "roast my
  branch before I open the PR", "be brutal about PR 42", "review my changes like a grumpy senior",
  or "what will reviewers hate about this diff".
argument-hint: "[PR number | base branch] [--gentle|--savage]"
---

# roast-pr: roast the diff, not the whole repo

Reviewers are busy and polite. This skill is neither busy nor, in `--savage`, particularly polite,
but it is always specific: it reads only what changed, cites the new line numbers, and pairs
every jab with the change that would make it go away. The result is a pre-review that catches
what human reviewers would have flagged, before they have to.

## Inputs

- A PR number (uses `gh`), a base branch (default: the repo's default branch), or nothing (diff
  of the current branch against its merge base with the default branch, plus uncommitted changes).
- Mode flag: `--gentle`, none, or `--savage` (`${CLAUDE_SKILL_DIR}/../roast-repo/tone.md`).

## Outputs

- `roast/PR-<number or branch>.md`: score, blockers, roasts, suggested review comments.
- Nothing is posted to GitHub unless the user confirms.

## Steps

1. **Get the diff.**
   - PR number: `gh pr view <n> --json title,body,baseRefName,headRefName,files` and
     `gh pr diff <n>`. If `gh` is missing or not authenticated, say so and fall back to asking for a
     branch name.
   - Branch: `git merge-base HEAD <base>` then `git diff <merge-base>...HEAD` and `git diff HEAD`
     for uncommitted work. Get stats with `git diff --stat`.
   If the diff is empty, stop and say so.

2. **Map the new line numbers.** For each hunk header `@@ -a,b +c,d @@`, lines starting with `+`
   are new lines numbered from `c`. Evidence must use the new file's path and line
   (`src/api.ts:118`). Read the full new version of each changed file around each hunk so you
   judge the change in context, not in isolation.

3. **Pick the panel by what changed.**
   - Always: The Greybeard (`judge-maintainer`): tests for the change, error handling, structure.
   - Auth, input handling, SQL, shell, dependencies, config, secrets: add `judge-security`.
   - Loops, queries, network calls, rendering, bundle-affecting imports: add `judge-performance`.
   - CLI flags, API surface, user-facing messages, UI: add `judge-product`.
   - Dockerfiles, CI, config, logging, timeouts: add `judge-ops`.
   - README or docs: add `judge-newcomer`.
   For diffs under ~300 changed lines, run the lenses yourself in sequence using the agent files in
   `${CLAUDE_SKILL_DIR}/../../agents/` as rubrics. For larger diffs, launch the chosen agents in
   parallel in one message, passing `repo`, `mode` and `scope` (the list of changed files plus the
   diff text). Tell each judge to roast only changed lines and their direct consequences.

4. **Check the PR-level basics** and roast what is missing: tests changed alongside code, a
   description that says why (from the PR body), size (over ~400 changed lines: suggest a split
   and name the seams), unrelated changes riding along, debug leftovers (`console.log`, `print(`,
   `debugger`, `.only(`, commented-out code), new TODOs without an issue.

5. **Verify every citation** by reading the cited new line. Drop anything you cannot confirm.

6. **Score and write roast/PR-<id>.md**:
   - Score out of 10: the mean of the judges you ran, each scored on their own rubric but only for
     what this diff touches (criteria the diff does not touch are marked n/a and score 2).
   - Blockers: roasts with impact high. Then the rest, ordered by impact for the effort.
   - Each roast: line, evidence (`path:line`), fix (concrete; a suggested code change is welcome).
   - "Suggested review comments": for each blocker, a plain, polite comment a reviewer could post,
     without the joke. Comments posted to GitHub are for humans; keep them kind.

7. **Offer to post, never post by default.** If the user wants the comments on the PR, show the
   exact `gh pr review <n> --comment --body-file <file>` (or per-line comments via
   `gh api repos/{owner}/{repo}/pulls/<n>/comments`) you would run, and run it only after an
   explicit yes. Post the plain versions, not the roast lines.

## What NOT to do

- Do not roast code the diff did not touch, except to show that a change breaks it.
- Do not name or describe the PR author. The diff is the defendant.
- No profanity or slurs in any mode.
- Do not approve, request changes, merge, push, or comment on GitHub without explicit confirmation.
- Do not run the project or its tests unless the user asks; reading is enough for a roast.

## Hand-off

- Fix the findings -> `roast-fix` can work from roast/PR-<id>.md the same way it works from
  ROAST.md.
- Whole-repo context needed -> `roast-repo`.
