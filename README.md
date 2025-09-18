# Quarto Academic Website Starter (v9.9)

- Home: centered badges; two-column layout; responsive to single-column on mobile.
- News: each post stores its own image (`news.jpg`); listing reads `image` field; titles bold.
- Research: cards + per-area pages; per-area bibs split from `references.bib` via `scripts/split_bib.py`.
- Publications: Chicago Author-Date CSL with DOI + URL; Lua filter post-process bolds "Bao, Xiyuan" and adds daggers to configured names; improved readability (bullets & spacing).
- Media & Outreach, Tools & Resources, CV pages included. CV pulls from `assets/cv.pdf` (your uploaded file copied if available).
- GitHub Actions workflow for `gh-pages` publishing.
- Publications: v9.10 groups by Published / Submitted / In prep using keywords; Bao is bolded via HTML replacement in Lua filter.

- Publications: v9.12 uses scripts/split_bib.py to generate bib/published.bib, bib/submitted.bib, bib/inprep.bib for categorized output.

- Publications: v9.13 also uses `topic={...}` field to split into bib/plume-dynamics.bib, bib/lagrangian-analysis.bib, bib/rheology.bib for research area pages.

- Publications: v9.14 uses separate bibliography blocks for published/submitted/inprep to ensure proper rendering.
