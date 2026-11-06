#!/usr/bin/env python3
"""Measure a README's first-five-minutes experience.

Answers the questions a stranger asks in the first five minutes, with line
numbers: is there a title and a plain one-paragraph pitch, how far down is
the first command, is there an install and a usage section, do the relative
links and images actually exist, how many badges sit in front of the content.
Standard library only, read-only.

Usage:
    python3 readme_lint.py [REPO_OR_README] [--format json|md]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

CANDIDATES = ["README.md", "readme.md", "Readme.md", "README.markdown", "README.rst", "README.txt", "README"]
INSTALL = re.compile(r"(?i)\b(install(ation|ing)?|setup|set up|getting started|quick ?start|requirements)\b")
USAGE = re.compile(r"(?i)\b(usage|use it|try it|example|examples|quick ?start|getting started|how to|tutorial|demo)\b")
LICENSE = re.compile(r"(?i)\blicen[cs]e\b")
FENCE = re.compile(r"^\s*(```|~~~)\s*([\w+-]*)")
SHELL_LANGS = {"sh", "bash", "shell", "console", "zsh", "powershell", "ps1", "cmd", "bat", "fish", ""}
COMMAND = re.compile(
    r"^\s*(\$ |> )?(pip3?|pipx|uv|npm|npx|pnpm|yarn|bun|cargo|go|brew|apt(-get)?|docker|git clone|curl|"
    r"wget|make|python3?|node|deno|gem|bundle|composer|dotnet|mvn|gradle|claude|/plugin)\b"
)
LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
HTML_SRC = re.compile(r"""(?i)<(?:img|a)\s[^>]*(?:src|href)=["']([^"']+)["']""")
BADGE = re.compile(r"\[!\[[^\]]*\]\([^)]*\)\]\([^)]*\)|!\[[^\]]*\]\([^)]*(shields\.io|badge|/workflows/)[^)]*\)")


def find_readme(target: Path) -> Path | None:
    if target.is_file():
        return target
    for name in CANDIDATES:
        candidate = target / name
        if candidate.is_file():
            return candidate
    return None


def headings(lines: list[str]) -> list[dict]:
    out, in_code = [], False
    for i, line in enumerate(lines, 1):
        if FENCE.match(line):
            in_code = not in_code
            continue
        if in_code:
            continue
        m = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", line)
        if m:
            out.append({"level": len(m.group(1)), "text": m.group(2), "line": i})
        elif i > 1 and re.match(r"^(=+|-+)\s*$", line) and lines[i - 2].strip() and not lines[i - 2].startswith(("-", "*", "|")):
            out.append({"level": 1 if line.strip().startswith("=") else 2, "text": lines[i - 2].strip(), "line": i - 1})
    return out


def first_paragraph(lines: list[str]) -> dict | None:
    """First prose paragraph that is not a heading, badge row, image, HTML or code."""
    para: list[str] = []
    start = None
    in_code = False
    for i, line in enumerate(lines, 1):
        s = line.strip()
        if FENCE.match(line):
            in_code = not in_code
            if para:
                break
            continue
        if in_code:
            continue
        prose = s and not s.startswith(("#", "<", "!", "[!", "|", "---", "===", "```")) and not BADGE.search(s)
        if prose:
            if start is None:
                start = i
            para.append(s)
        elif para:
            break
    if not para:
        return None
    text = " ".join(para)
    return {"line": start, "text": text[:400], "words": len(text.split())}


def analyse(readme: Path, root: Path) -> dict:
    text = readme.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    hs = headings(lines)
    title = next((h for h in hs if h["level"] == 1), hs[0] if hs else None)

    code_blocks, first_code, first_command = 0, None, None
    in_code, lang = False, ""
    for i, line in enumerate(lines, 1):
        m = FENCE.match(line)
        if m:
            if not in_code:
                code_blocks += 1
                lang = m.group(2).lower()
                first_code = first_code or i
            in_code = not in_code
            continue
        if in_code and first_command is None and line.strip() and not line.strip().startswith("#"):
            if COMMAND.match(line) or (lang and lang in SHELL_LANGS):
                first_command = {"line": i, "text": line.strip()[:120]}

    badges = sum(len(list(BADGE.finditer(line))) for line in lines[:20])
    targets = []
    for i, line in enumerate(lines, 1):
        for m in list(LINK.finditer(line)) + list(HTML_SRC.finditer(line)):
            targets.append((i, m.group(1)))
    broken = []
    images = 0
    for i, target in targets:
        if re.search(r"\.(png|jpe?g|gif|svg|webp)(\?|#|$)", target, re.I):
            images += 1
        if re.match(r"(?i)^(https?:|mailto:|#|data:|//)", target):
            continue
        path = target.split("#", 1)[0].split("?", 1)[0]
        if not path:
            continue
        resolved = (readme.parent / path) if not path.startswith("/") else (root / path.lstrip("/"))
        if not resolved.exists():
            broken.append({"line": i, "target": target})

    install = next((h for h in hs if INSTALL.search(h["text"])), None)
    usage = next((h for h in hs if USAGE.search(h["text"])), None)
    para = first_paragraph(lines)
    warnings = []
    if not title:
        warnings.append("no title heading")
    if not para:
        warnings.append("no plain-prose description paragraph")
    elif para["words"] > 80:
        warnings.append(f"first paragraph is {para['words']} words (line {para['line']}); aim for under 60")
    if not install:
        warnings.append("no install / getting started section")
    if not usage:
        warnings.append("no usage / example section")
    if first_command is None:
        warnings.append("no copy-pasteable command anywhere")
    elif first_command["line"] > 60:
        warnings.append(f"first command is on line {first_command['line']}; a stranger scrolls a long way to find it")
    if badges > 6:
        warnings.append(f"{badges} badges at the top before any content")
    if broken:
        warnings.append(f"{len(broken)} broken relative link(s) or image(s)")
    if not LICENSE.search(text):
        warnings.append("license is never mentioned")
    if len(lines) < 15:
        warnings.append(f"only {len(lines)} lines long")

    return {
        "readme": readme.relative_to(root).as_posix() if readme.is_relative_to(root) else readme.name,
        "lines": len(lines), "words": len(text.split()),
        "title": title, "first_paragraph": para, "badges_top": badges,
        "headings": hs[:40], "install_section": install, "usage_section": usage,
        "code_blocks": code_blocks, "first_code_line": first_code, "first_command": first_command,
        "images": images, "broken_links": broken, "mentions_license": bool(LICENSE.search(text)),
        "warnings": warnings,
    }


def to_markdown(r: dict) -> str:
    if r.get("readme") is None:
        return "# README check\n\n- No README found. That is the roast.\n"
    o = [f"# README check: {r['readme']}", ""]
    o.append(f"- Length: {r['lines']} lines, {r['words']} words")
    o.append(f"- Title: {r['title']['text']!r} (line {r['title']['line']})" if r["title"] else "- Title: none")
    p = r["first_paragraph"]
    o.append(f"- First paragraph: line {p['line']}, {p['words']} words" if p else "- First paragraph: none")
    o.append(f"- Install section: line {r['install_section']['line']}" if r["install_section"] else "- Install section: none")
    o.append(f"- Usage section: line {r['usage_section']['line']}" if r["usage_section"] else "- Usage section: none")
    fc = r["first_command"]
    o.append(f"- First command: line {fc['line']}: `{fc['text']}`" if fc else "- First command: none")
    o.append(f"- Code blocks: {r['code_blocks']}; images: {r['images']}; badges at top: {r['badges_top']}")
    for b in r["broken_links"]:
        o.append(f"- Broken link: line {b['line']} -> {b['target']}")
    o.append("")
    o.append("## Warnings")
    o.append("")
    if r["warnings"]:
        o.extend(f"- {w}" for w in r["warnings"])
    else:
        o.append("- None")
    return "\n".join(o) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Measure a README's first-five-minutes experience (read-only).")
    ap.add_argument("target", nargs="?", default=".", help="repo directory or README file (default: .)")
    ap.add_argument("--format", choices=["json", "md"], default="md")
    args = ap.parse_args(argv)
    target = Path(args.target).resolve()
    root = target if target.is_dir() else target.parent
    readme = find_readme(target)
    result = {"readme": None, "warnings": ["no README found"]} if readme is None else analyse(readme, root)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.stdout.write(json.dumps(result, indent=2, ensure_ascii=False) + "\n" if args.format == "json" else to_markdown(result))
    return 0 if readme else 1


if __name__ == "__main__":
    sys.exit(main())
