#!/usr/bin/env python3
import re, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
BIB = ROOT / "references.bib"
OUTDIR = ROOT / "bib"
OUTDIR.mkdir(exist_ok=True)

def parse_bib_entries(text):
    entries, cur, depth = [], [], 0
    for line in text.splitlines():
        if line.strip().startswith("@") and depth == 0 and cur:
            entries.append("\n".join(cur)); cur = [line]
            depth = line.count("{") - line.count("}")
        else:
            cur.append(line)
            depth += line.count("{") - line.count("}")
    if cur: entries.append("\n".join(cur))
    return entries

def extract_field(entry, field):
    m = re.search(field + r'\s*=\s*[{"]([^}"]+)[}"]', entry, re.IGNORECASE)
    if not m:
        return []
    raw = m.group(1)
    return [s.strip().lower() for s in re.split(r'\s*,\s*|;', raw) if s.strip()]

def extract_year(entry):
    """Extract year from entry, return 0 if not found"""
    m = re.search(r'year\s*=\s*[{"]?(\d{4})[}"]?', entry, re.IGNORECASE)
    return int(m.group(1)) if m else 0

def sort_entries_with_original_order(entries_with_positions):
    """Sort entries: published by year ascending, same year by reverse original order, then unpublished by reverse order"""
    
    def sort_key(item):
        entry, original_pos = item
        year = extract_year(entry)
        reverse_pos = -original_pos
        
        if year > 0:
            return (0, year, reverse_pos)
        else:
            return (1, 0, reverse_pos)
    
    entries_with_positions.sort(key=sort_key)
    return [entry for entry, pos in entries_with_positions]

def main():
    if not BIB.exists():
        print("No references.bib found; skipping split.")
        return

    text = BIB.read_text(encoding="utf-8")
    entries = parse_bib_entries(text)

    # Create entries with their original positions
    entries_with_positions = [(entry, i) for i, entry in enumerate(entries)]

    cats = {"published": [], "submitted": [], "inprep": []}
    topics = {
        "mantle dynamics": [],
        "interior–surface coupling": [],
        "geodynamical methods": []
    }

    for entry, original_pos in entries_with_positions:
        kws = extract_field(entry, "keywords")
        tops = extract_field(entry, "topic")

        if "submitted" in kws:
            cats["submitted"].append((entry, original_pos))
        elif "inprep" in kws:
            cats["inprep"].append((entry, original_pos))
        elif "published" in kws:
            cats["published"].append((entry, original_pos))

        for t in topics:
            if t in tops:
                topics[t].append((entry, original_pos))

    # Write category bibs (with sorting)
    for name, lst in cats.items():
        out = OUTDIR / f"{name}.bib"
        if lst:
            sorted_lst = sort_entries_with_original_order(lst)
            out.write_text("\n\n".join(sorted_lst) + "\n", encoding="utf-8")
        else:
            dummy = f"@misc{{empty_{name}, title={{No {name} entries}}, author={{}}, year={{9999}} }}"
            out.write_text(dummy + "\n", encoding="utf-8")

    # Write topic bibs (with sorting)
    mapping = {
        "mantle dynamics": "mantle-dynamics.bib",
        "interior–surface coupling": "interior-surface-coupling.bib",
        "geodynamical methods": "geodynamical-methods.bib"
    }
    for key, fn in mapping.items():
        out = OUTDIR / fn
        if topics[key]:
            sorted_lst = sort_entries_with_original_order(topics[key])
            out.write_text("\n\n".join(sorted_lst) + "\n", encoding="utf-8")
        else:
            dummy = f"@misc{{empty_{key.replace(' ', '_')}, title={{No publications yet in {key}}}, author={{}}, year={{9999}} }}"
            out.write_text(dummy + "\n", encoding="utf-8")

if __name__ == "__main__":
    main()
