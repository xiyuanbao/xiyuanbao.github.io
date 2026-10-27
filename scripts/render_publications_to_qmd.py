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
- Published: render DOI or URL as a markdown link labeled "Link".
- Submitted / in prep: render URL as a link labeled "arXiv".
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
    ("Published", BIBDIR / "published.bib"),
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
    # Sort by year+month descending (month optional).
    # Within the same year, entries where Bao, Xiyuan appears earlier in the author list come first.
    # Finally, sort by title descending.
    has_years = any("year" in e and e["year"].strip() for e in entries)
    if has_years:
        MONTHS = {m: i for i, m in enumerate(
            ["jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"], 1)}

        def y(e):
            # Primary key: (year, month). Missing month counts as the earliest in that year.
            try:
                year = int(re.findall(r"\d{4}", e.get("year", "0000"))[0])
            except Exception:
                year = 0
            raw = (e.get("month", "") or "").strip().lower()
            if raw.isdigit():
                month = int(raw)
            else:
                month = MONTHS.get(raw[:3], 0)
            return (year, month)

        def bao_author_pos(e):
            authors = e.get("author", "")
            parts = [
                p.strip()
                for p in re.split(r"\band\b", authors, flags=re.IGNORECASE)
                if p.strip()
            ]

            for i, author in enumerate(parts):
                if re.search(r"Bao,\s*Xiyuan|Xiyuan\s*Bao", author, flags=re.IGNORECASE):
                    return i

            return 9999

        sorted_entries = list(entries)

        # Tertiary key: title descending, Z -> A
        sorted_entries.sort(
            key=lambda e: e.get("title", "").casefold(),
            reverse=True
        )

        # Secondary key: Bao author position ascending
        sorted_entries.sort(key=bao_author_pos)

        # Primary key: (year, month) descending
        sorted_entries.sort(key=y, reverse=True)

        return sorted_entries
    else:
        return entries

def ensure_terminal_punctuation(s: str) -> str:
    s = s.strip()
    if not s:
        return s

    terminal_punct = ".。?？!！"

    if s[-1] in terminal_punct:
        return s
    else:
        return s + "."
    
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
    # Always render as link.
    # Published: DOI (preferred) or URL, labeled "Link".
    # Submitted / in prep: URL only, always labeled "arXiv".
    is_published = category.lower().startswith("published")
    link_target = ""
    label = "Link"
    if is_published:
        if doi:
            link_target = f"https://doi.org/{doi}"
            label = "DOI"
        elif url:
            link_target = url
            if "arxiv.org" in url.lower():
                label = "arXiv"
    elif url:
        link_target = url
        label = "arXiv"

    if authors:
        if year:
            pieces.append(f"{authors} ({year}).")
        else:
            pieces.append(f"{authors}.")
    if title:
        pieces.append(f"*{ensure_terminal_punctuation(title)}*")
    if journal:
        pieces.append(f"**{journal}**.")
    pubstate = (e.get("pubstate", "") or "").strip()
    if pubstate:
        pieces.append(f"{pubstate}.")

    if category.lower().startswith("manuscripts submitted"):
        extra = howpub or note
        if extra:
            extra_clean = extra.strip()
            m = re.match(r'(?i)\s*(under review at|submitted to|in revision for|revision under review at)\s+(.+)', extra_clean)
            if m:
                prefix, journal_extra = m.group(1), m.group(2)
                pieces.append(f"{prefix} **{journal_extra.strip()}**")
            else:
                pieces.append(extra_clean)

    if link_target:
        pieces.append(f"[{label}]({link_target})")

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
        group_by_year = heading.lower().startswith("published")
        current_year = None
        for e in entries:
            if group_by_year:
                year = (e.get("year", "") or "").strip()
                if year != current_year:
                    if current_year is not None:
                        lines.append("\n")
                    lines.append(f"### {year}\n")
                    current_year = year
            lines.append(f"- {fmt_entry(e, heading)}\n")
        lines.append("\n")
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT}")

if __name__ == "__main__":
    render()
