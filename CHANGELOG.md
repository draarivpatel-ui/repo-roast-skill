# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [1.0.1] - 2026-11-07

### Fixed

- `facts.py` now counts root-level test files such as `test.js`, `tests.py` and `spec.ts`. Before,
  a repo whose only tests lived in `test.js` was reported as having no tests.
- `facts.py` now treats a `.travis.yml` with no `script:` as running tests, since Travis runs the
  language's default test command (for example `npm test`) in that case.

## [1.0.0] - 2026-11-07

### Added

- `roast-repo`: gathers facts, convenes six judges in parallel, validates every jab's evidence,
  and writes `roast/ROAST.md` with an overall score, per-judge roasts, the top 10 fixes and the
  one thing to fix today.
- `roast-card`: 1200x630 SVG scorecard and a shields-style score badge, with before and after
  support.
- `roast-readme`: first-five-minutes roast of the README with a measured lint and a rewrite of
  the top, saved only after approval.
- `roast-pr`: roasts a diff or pull request with new-side line numbers; review comments are
  posted only on confirmation.
- `roast-fix`: turns the roast into `roast/FIXPLAN.md` and applies approved quick wins one at a
  time with the test suite as referee.
- `roast-rematch`: re-roasts after fixes and reports the score delta per judge.
- Six read-only judge agents: security, performance, newcomer, maintainer, product, ops.
- Helper scripts `facts.py`, `verdict.py`, `card.py`, `badge.py`, `readme_lint.py`, `delta.py`
  (standard library only) with unit tests.
- Fictional example roast, card and badge in `examples/`.
