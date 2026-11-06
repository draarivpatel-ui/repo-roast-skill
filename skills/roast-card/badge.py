#!/usr/bin/env python3
"""Render a small shields-style SVG badge: "roast score | 7.4/10".

The colour follows the same score bands as the card. Text width is estimated
from a per-character table so the badge needs no font metrics. Standard
library only.

Usage:
    python3 badge.py --score 7.4 --out roast/badge.svg
    python3 badge.py --in roast/card.json --out roast/badge.svg
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape

SCORE_BANDS = [(4.0, "#c62828"), (6.0, "#d9480f"), (8.0, "#b7791f"), (10.01, "#2f855a")]
LABEL_BG = "#555"
_INVALID_XML = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\x7f￾￿]")

NARROW = set("fijlrt.,:;!|'()[] 1/")
WIDE = set("mwMW@%")


def clean(text) -> str:
    return re.sub(r"\s+", " ", _INVALID_XML.sub("", str(text))).strip()


def esc(text) -> str:
    return escape(clean(text), {'"': "&quot;", "'": "&apos;"})


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


def text_width(text: str) -> int:
    """Approximate rendered width in px of Verdana 11px."""
    total = 0.0
    for ch in text:
        if ch in NARROW:
            total += 3.9
        elif ch in WIDE:
            total += 10.5
        elif ch.isupper() or ch.isdigit():
            total += 7.6
        else:
            total += 6.8
    return int(round(total))


def render(score, label: str = "roast score") -> str:
    s = clamp(score)
    label = clean(label) or "roast score"
    message = f"{s:.1f}/10"
    lw = text_width(label) + 12
    mw = text_width(message) + 12
    w = lw + mw
    colour = score_color(s)
    aria = f"{label}: {message}"
    font = "Verdana,Geneva,DejaVu Sans,sans-serif"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="20" role="img" aria-label="{esc(aria)}">'
        f"<title>{esc(aria)}</title>"
        '<linearGradient id="s" x2="0" y2="100%"><stop offset="0" stop-color="#bbb" stop-opacity=".1"/>'
        '<stop offset="1" stop-opacity=".1"/></linearGradient>'
        f'<clipPath id="r"><rect width="{w}" height="20" rx="3" fill="#fff"/></clipPath>'
        f'<g clip-path="url(#r)"><rect width="{lw}" height="20" fill="{LABEL_BG}"/>'
        f'<rect x="{lw}" width="{mw}" height="20" fill="{colour}"/>'
        f'<rect width="{w}" height="20" fill="url(#s)"/></g>'
        f'<g fill="#fff" text-anchor="middle" font-family="{font}" font-size="11">'
        f'<text x="{lw / 2:.1f}" y="15" fill="#010101" fill-opacity=".3">{esc(label)}</text>'
        f'<text x="{lw / 2:.1f}" y="14">{esc(label)}</text>'
        f'<text x="{lw + mw / 2:.1f}" y="15" fill="#010101" fill-opacity=".3">{message}</text>'
        f'<text x="{lw + mw / 2:.1f}" y="14">{message}</text>'
        "</g></svg>\n"
    )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Render a shields-style 'roast score' SVG badge.")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--score", type=float, help="score from 0 to 10")
    src.add_argument("--in", dest="inp", help="card.json or roast.json to read 'overall' from")
    p.add_argument("--label", default="roast score", help="left-hand label (default: roast score)")
    p.add_argument("--out", required=True, help="SVG file to write")
    p.add_argument("--link", default="roast/ROAST.md", help="where the markdown snippet links to")
    args = p.parse_args(argv)
    score = args.score
    if args.inp:
        score = json.loads(Path(args.inp).read_text(encoding="utf-8")).get("overall", 0)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(score, args.label), encoding="utf-8")
    print(f"wrote {out.as_posix()}")
    print(f"[![{clean(args.label)} {clamp(score):.1f}/10]({out.as_posix()})]({args.link})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
