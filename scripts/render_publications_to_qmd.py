"""
Render publications into a single QMD fragment (_generated/publications_body.qmd).

Reads:
- bib/published.bib
- bib/submitted.bib
- bib/inprep.bib

Formatting rules:
- Bold "Xiyuan Bao" in author list (both "Bao, Xiyuan" and "Xiyuan Bao").
- Italicize title.
- Bold journal.
- Append year in parentheses after authors (omit if missing).
- Always render DOI or URL as a markdown link labeled "link".
- For submitted entries, also append `howpublished` or `note` if provided.
- Entries are sorted by year (descending) then title.
"""

import re, sys
from pathlib import Path

try:
    import bibtexparser
except Exception:
    print("ERROR: bibtexparser is required", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parents[1]
BIBDIR = ROOT / "bib"
OUT = ROOT / "_generated" / "publications_body.qmd"
OUT.parent.mkdir(parents=True, exist_ok=True)

CATEGORIES = [
    ("Peer-reviewed", BIBDIR / "published.bib"),
    ("Manuscripts submitted", BIBDIR / "submitted.bib"),
    ("Manuscripts in preparation", BIBDIR / "inprep.bib"),
]

ME_NAMES = [r"Bao,\s*Xiyuan", r"Xiyuan\s*Bao"]
ME_PAT = re.compile("(" + "|".join(ME_NAMES) + ")", re.IGNORECASE)

def bold_me(s: str) -> str:
    return ME_PAT.sub(r"**\1**", s)

def format_authors(field: str) -> str:
    parts = [p.strip() for p in re.split(r"\band\b", field, flags=re.IGNORECASE) if p.strip()]
    parts = [bold_me(p) for p in parts]
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]
    return ", ".join(parts[:-1]) + " and " + parts[-1]

def load_bib(path: Path):
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        db = bibtexparser.load(f)
    return db.entries

def sort_entries(entries):
    def y(e):
        try:
            return int(re.findall(r"\d{4}", e.get("year","0000"))[0])
        except Exception:
            return 0
    return sorted(entries, key=lambda e: (y(e), e.get("title","")), reverse=False)

def fmt_entry(e, category: str) -> str:
    authors = format_authors(e.get("author",""))
    title = e.get("title","").rstrip(".")
    journal = e.get("journal","")
    year = (e.get("year","") or "").strip()
    doi = (e.get("doi","") or "").strip()
    url = (e.get("url","") or "").strip()
    note = (e.get("note","") or "").strip()
    howpub = (e.get("howpublished","") or "").strip()

    pieces = []
    if authors:
        if year:
            pieces.append(f"{authors} ({year}).")
        else:
            pieces.append(f"{authors}.")
    if title:
        pieces.append(f"*{title}*.")
    if journal:
        pieces.append(f"**{journal}**.")

    # Always render as link
    link_target = ""
    if doi:
        link_target = f"https://doi.org/{doi}"
    elif url:
        link_target = url
    if link_target:
        pieces.append(f"[Link]({link_target})")

    if category.lower().startswith("manuscripts submitted"):
        extra = howpub or note
        if extra:
            extra_clean = extra.strip()
            m = re.match(r'(?i)\s*(under review in|submitted to|in revision|revision under review in)\s+(.+)', extra_clean)
            if m:
                prefix, journal_extra = m.group(1), m.group(2)
                pieces.append(f"{prefix} **{journal_extra.strip()}**")
            else:
                pieces.append(extra_clean)

    return " ".join(pieces).strip()

def render():
    lines = []
    lines.append("<!-- Auto-generated. Do not edit directly. -->\n")
    for heading, bibpath in CATEGORIES:
        entries = sort_entries(load_bib(bibpath))
        lines.append(f"## {heading}\n")
        if not entries:
            lines.append("_No entries._\n\n")
            continue
        for e in entries:
            lines.append(f"- {fmt_entry(e, heading)}\n")
        lines.append("\n")
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT}")

if __name__ == "__main__":
    render()
