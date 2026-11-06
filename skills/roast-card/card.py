#!/usr/bin/env python3
"""Render a shareable 1200x630 SVG scorecard for a roast.

Input is a JSON file (roast/card.json, written by roast-repo's verdict.py):

    {"repo": "acme/widget", "overall": 6.2, "headline": "one-liner",
     "date": "2026-11-07", "mode": "default", "previous_overall": 5.1,
     "judges": [{"name": "The Paranoid", "role": "Security", "score": 4.5,
                 "quote": "one line", "previous": 3.0}]}

`previous_overall` and per-judge `previous` are optional; when present the
card shows "before -> after". The SVG is self-contained (no fonts, images or
scripts are fetched), escapes all text, and draws its own light background so
it reads well anywhere. Standard library only.

Usage:
    python3 card.py --in roast/card.json --out roast/card.svg
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape

WIDTH, HEIGHT = 1200, 630
MAX_JUDGES = 6
REPO_CHARS = 64  # longer names shrink the title font before anything is cut
QUOTE_CHARS = 74
NAME_CHARS = 30
HEADLINE_LINE_CHARS = 34
HEADLINE_LINES = 3

BG = "#fffaf3"
INK = "#1f2328"
MUTED = "#57606a"
TRACK = "#eee3d6"
FLAME = "#d9480f"
FONT = "'Segoe UI', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Helvetica, Arial, sans-serif"

# Score bands: below the limit -> this colour. Dark enough for white text and for text on BG.
SCORE_BANDS = [(4.0, "#c62828"), (6.0, "#d9480f"), (8.0, "#b7791f"), (10.01, "#2f855a")]
# Keep in sync with roast-repo/verdict.py.
TIERS = [(3.0, "Dumpster Fire"), (5.0, "Smoke Alarm"), (7.0, "Needs Seasoning"),
         (8.5, "Nicely Done"), (10.01, "Chef's Kiss")]

_INVALID_XML = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\x7f￾￿]")


def clean(text) -> str:
    """Drop characters XML 1.0 forbids and collapse whitespace."""
    text = _INVALID_XML.sub("", str(text if text is not None else ""))
    return re.sub(r"\s+", " ", text).strip()


def esc(text) -> str:
    """Clean then escape for use in XML text and double-quoted attributes."""
    return escape(clean(text), {'"': "&quot;", "'": "&apos;"})


def truncate(text, limit: int) -> str:
    text = clean(text)
    if len(text) <= limit:
        return text
    cut = text[: max(limit - 1, 0)].rstrip()
    space = cut.rfind(" ")
    if space > limit * 0.6:
        cut = cut[:space].rstrip(" ,.;:-")
    return cut + "…"


def wrap(text, width: int, max_lines: int) -> list[str]:
    """Word-wrap to at most max_lines lines; the last line ends with an ellipsis on overflow."""
    words = [w if len(w) <= width else truncate(w, width) for w in clean(text).split(" ") if w]
    lines: list[str] = []
    current = ""
    for i, word in enumerate(words):
        candidate = f"{current} {word}".strip()
        if len(candidate) <= width:
            current = candidate
            continue
        lines.append(current)
        current = word
        if len(lines) == max_lines:
            lines[-1] = truncate(lines[-1] + " " + " ".join(words[i:]), width)
            return lines
    if current:
        lines.append(current)
    return lines


def clamp(score) -> float:
    try:
        value = float(score)
    except (TypeError, ValueError):
        return 0.0
    return round(min(10.0, max(0.0, value)), 1)


def score_color(score) -> str:
    s = clamp(score)
    for limit, colour in SCORE_BANDS:
        if s < limit:
            return colour
    return SCORE_BANDS[-1][1]


def tier(score) -> str:
    s = clamp(score)
    for limit, name in TIERS:
        if s < limit:
            return name
    return TIERS[-1][1]


def fmt_delta(before: float, after: float) -> str:
    d = round(after - before, 1)
    return f"+{d:.1f}" if d > 0 else (f"{d:.1f}" if d < 0 else "±0.0")


def delta_color(before: float, after: float) -> str:
    d = round(after - before, 1)
    return "#2f855a" if d > 0 else ("#c62828" if d < 0 else MUTED)


def repo_font_size(repo: str) -> int:
    """42px fits about 40 bold characters across the card; scale down for longer names."""
    return 42 if len(repo) <= 40 else max(26, int(42 * 40 / len(repo)))


def render(data: dict) -> str:
    repo = truncate(data.get("repo") or "this repo", REPO_CHARS)
    overall = clamp(data.get("overall"))
    prev_overall = data.get("previous_overall")
    colour = score_color(overall)
    judges = [j for j in (data.get("judges") or []) if isinstance(j, dict)][:MAX_JUDGES]
    mode = clean(data.get("mode") or "default")
    date = clean(data.get("date") or "")
    meta = " · ".join(x for x in [date, f"{mode} mode"] if x)

    out: list[str] = []
    add = out.append
    label = f"Roast of {truncate(data.get('repo') or 'this repo', 80)}: {overall:.1f} out of 10, {tier(overall)}"
    add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="{esc(label)}">')
    add(f"<title>{esc(label)}</title>")
    add('<defs><linearGradient id="flame" x1="0" y1="0" x2="1" y2="0">'
        '<stop offset="0" stop-color="#f59f00"/><stop offset="1" stop-color="#d9480f"/></linearGradient></defs>')
    add(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="{BG}"/>')
    add(f'<rect width="{WIDTH}" height="10" fill="url(#flame)"/>')
    add(f'<g font-family="{esc(FONT)}">')

    # Header
    add(f'<text x="60" y="70" font-size="18" font-weight="700" letter-spacing="3" fill="{FLAME}">THE ROAST OF</text>')
    add(f'<text x="60" y="118" font-size="{repo_font_size(repo)}" font-weight="800" fill="{INK}">{esc(repo)}</text>')
    if meta:
        add(f'<text x="1140" y="70" font-size="16" fill="{MUTED}" text-anchor="end">{esc(meta)}</text>')
    add(f'<line x1="60" y1="150" x2="1140" y2="150" stroke="{TRACK}" stroke-width="2"/>')

    # Left: overall ring
    cx, cy, r = 230, 320, 112
    circumference = 2 * 3.141592653589793 * r
    arc = circumference * overall / 10
    add(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{TRACK}" stroke-width="20"/>')
    if arc > 0:
        add(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{colour}" stroke-width="20" '
            f'stroke-linecap="round" stroke-dasharray="{arc:.1f} {circumference:.1f}" '
            f'transform="rotate(-90 {cx} {cy})"/>')
    add(f'<text x="{cx}" y="{cy + 22}" font-size="76" font-weight="800" fill="{INK}" '
        f'text-anchor="middle">{overall:.1f}</text>')
    add(f'<text x="{cx}" y="{cy + 58}" font-size="20" fill="{MUTED}" text-anchor="middle">out of 10</text>')
    y = cy + r + 50
    if prev_overall is not None:
        before = clamp(prev_overall)
        add(f'<text x="{cx}" y="{y}" font-size="20" font-weight="700" text-anchor="middle" '
            f'fill="{delta_color(before, overall)}">was {before:.1f} → now {overall:.1f} '
            f'({fmt_delta(before, overall)})</text>')
        y += 34
    add(f'<text x="{cx}" y="{y}" font-size="28" font-weight="800" fill="{colour}" '
        f'text-anchor="middle">{esc(tier(overall))}</text>')
    y += 36
    max_lines = HEADLINE_LINES if prev_overall is None else HEADLINE_LINES - 1
    for line in wrap(data.get("headline") or "", HEADLINE_LINE_CHARS, max_lines):
        add(f'<text x="{cx}" y="{y}" font-size="18" font-style="italic" fill="{MUTED}" '
            f'text-anchor="middle">{esc(line)}</text>')
        y += 26

    # Right: the panel
    x0, x1 = 470, 1140
    bar_w = x1 - x0
    row_y = 190
    step = 70
    if not judges:
        add(f'<text x="{x0}" y="{row_y}" font-size="20" fill="{MUTED}">No judges on the panel.</text>')
    for j in judges:
        s = clamp(j.get("score"))
        jc = score_color(s)
        name = truncate(j.get("name") or "Judge", NAME_CHARS)
        role = truncate(j.get("role") or "", 18)
        role_part = f'<tspan fill="{MUTED}" font-weight="400"> · {esc(role)}</tspan>' if role else ""
        add(f'<text x="{x0}" y="{row_y}" font-size="20" font-weight="700" fill="{INK}">{esc(name)}{role_part}</text>')
        if j.get("previous") is not None:
            b = clamp(j.get("previous"))
            add(f'<text x="{x1}" y="{row_y}" font-size="20" font-weight="800" text-anchor="end" fill="{jc}">'
                f'<tspan fill="{MUTED}" font-weight="400">{b:.1f} → </tspan>{s:.1f}'
                f'<tspan fill="{delta_color(b, s)}" font-size="16"> ({fmt_delta(b, s)})</tspan></text>')
        else:
            add(f'<text x="{x1}" y="{row_y}" font-size="22" font-weight="800" text-anchor="end" fill="{jc}">{s:.1f}</text>')
        add(f'<rect x="{x0}" y="{row_y + 10}" width="{bar_w}" height="8" rx="4" fill="{TRACK}"/>')
        if s > 0:
            add(f'<rect x="{x0}" y="{row_y + 10}" width="{bar_w * s / 10:.1f}" height="8" rx="4" fill="{jc}"/>')
        quote = j.get("quote")
        if quote:
            add(f'<text x="{x0}" y="{row_y + 36}" font-size="16" font-style="italic" fill="{MUTED}">'
                f'“{esc(truncate(quote, QUOTE_CHARS))}”</text>')
        row_y += step

    # Footer
    add(f'<text x="60" y="612" font-size="15" fill="{MUTED}">Roast the code, never the people. '
        f'Every jab comes with evidence and a fix.</text>')
    add(f'<text x="1140" y="612" font-size="15" font-weight="700" fill="{FLAME}" text-anchor="end">'
        f'repo-roast-skill</text>')
    add("</g></svg>")
    return "\n".join(out) + "\n"


def markdown_snippet(card_path: str, data: dict, badge_path: str | None = None, link: str = "roast/ROAST.md") -> str:
    overall = clamp(data.get("overall"))
    alt = f"Roast of {clean(data.get('repo') or 'this repo')}: {overall:.1f}/10"
    lines = []
    if badge_path:
        lines.append(f"[![Roast score {overall:.1f}/10]({badge_path})]({link})")
    lines.append(f"[![{alt}]({card_path})]({link})")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Render a 1200x630 SVG roast scorecard from card.json.")
    p.add_argument("--in", dest="inp", required=True, help="card JSON (use - for stdin)")
    p.add_argument("--out", required=True, help="SVG file to write")
    p.add_argument("--badge-path", help="badge SVG path to include in the printed markdown snippet")
    p.add_argument("--link", default="roast/ROAST.md", help="where the snippet links to")
    args = p.parse_args(argv)
    raw = sys.stdin.read() if args.inp == "-" else Path(args.inp).read_text(encoding="utf-8")
    try:
        data = json.loads(raw)
    except ValueError as exc:
        print(f"error: card JSON does not parse: {exc}", file=sys.stderr)
        return 2
    if len(data.get("judges") or []) > MAX_JUDGES:
        print(f"note: only the first {MAX_JUDGES} judges fit on the card", file=sys.stderr)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(data), encoding="utf-8")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(f"wrote {out.as_posix()}")
    print()
    print("Markdown:")
    print(markdown_snippet(out.as_posix(), data, args.badge_path, args.link), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
