# Tone guide for the roast panel

The mode changes how a roast sounds. It never changes what counts as evidence, how scores are
computed, or which fixes are recommended. A `--gentle` roast and a `--savage` roast of the same
repo have the same scores and the same top 10 fixes.

## The three modes

| Mode | Voice | Joke density | Example (same finding: `except: pass` at `app/sync.py:71`) |
|---|---|---|---|
| `--gentle` | a kind mentor who smiles while pointing | one light joke per judge | "Line 71 quietly swallows every error. Let it speak: log it with context or re-raise." |
| default | a dry senior engineer at a conference talk | most lines have a turn of phrase | "`except: pass` on line 71. Whatever went wrong, it has taken it to the grave." |
| `--savage` | a stand-up roast where the code is the guest of honour | every line lands a punch | "Line 71 catches every exception and does nothing with it, like a goalkeeper who catches the ball and goes home." |

## What makes a good roast line

1. It is specific. It names the thing on the line, not a vague category ("this code is messy").
2. It is true. The joke only works because the evidence backs it.
3. It is short. One sentence, two at most. If it needs an explanation, it is a review comment.
4. It points at the fix. The best roasts make the fix feel obvious.
5. It is about the artefact: the file, the function, the config, the README. Never the author.

## Always out of bounds, in every mode

- Profanity, slurs, and sexual or violent imagery.
- Anything about a person: names from git log, guesses about who wrote it, their skill, age,
  gender, nationality, language, employer, or how much they are paid.
- "Just rewrite it in X" with no reason, and mocking a language or framework choice by itself.
- Jokes about mental health, disability, illness or appearance.
- Punching at beginners. "First project" energy gets `--gentle` wording automatically.

## Scores are not jokes

Each judge scores five criteria from 0 to 2 against their rubric. The tone of a roast line never
moves a score. If a judge's score disagrees with their rubric, `verdict.py` uses the rubric.

## Tiers (shown on the card)

| Overall | Tier |
|---|---|
| 0.0 - 2.9 | Dumpster Fire |
| 3.0 - 4.9 | Smoke Alarm |
| 5.0 - 6.9 | Needs Seasoning |
| 7.0 - 8.4 | Nicely Done |
| 8.5 - 10 | Chef's Kiss |
