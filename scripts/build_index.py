#!/usr/bin/env python3
"""Regenerate index.json from briefings/ and deals/ markdown files."""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAX_BLURB = 120


def clean(s: str) -> str:
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
    s = re.sub(r"[*_`#>~]+", "", s)
    return re.sub(r"\s+", " ", s).strip()


def first_paragraph(text: str) -> str:
    """First non-heading, non-empty paragraph — the verdict sentence."""
    for block in re.split(r"\n\s*\n", text):
        block = block.strip()
        if not block or block.startswith("#"):
            continue
        line = block.splitlines()[0].strip()
        if line:
            return clean(line)
    return ""


def title_of(text: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return clean(line[2:])
    return ""


def scan(dir_name: str):
    d = ROOT / dir_name
    if not d.is_dir():
        return []
    out = []
    dated = sorted((f for f in d.glob("*.md") if f.stem != "current"), key=lambda f: f.name, reverse=True)
    cur = d / "current.md"
    files = ([cur] if cur.exists() else []) + dated
    for f in files:
        text = f.read_text(encoding="utf-8", errors="replace")
        m = re.match(r"(\d{4}-\d{2}-\d{2})(?:-(\d{4}))?", f.stem)
        date, hm = (m.group(1), m.group(2)) if m else (None, None)
        blurb = first_paragraph(text)
        if len(blurb) > MAX_BLURB:
            blurb = blurb[:MAX_BLURB].rstrip() + "…"
        out.append({
            "file": f"{dir_name}/{f.name}",
            "date": date or "",
            "time": f"{hm[:2]}:{hm[2:]}" if hm else "",
            "title": title_of(text),
            "blurb": blurb,
        })
    return out


index = {
    "generated": __import__("datetime").datetime.utcnow().isoformat(timespec="seconds") + "Z",
    "briefings": scan("briefings"),
    "deals": scan("deals"),
}
out = ROOT / "index.json"
new = json.dumps(index, ensure_ascii=False, indent=2) + "\n"
old = out.read_text(encoding="utf-8") if out.exists() else ""
if old != new:
    out.write_text(new, encoding="utf-8")
    print("index.json updated")
else:
    print("index.json unchanged")
