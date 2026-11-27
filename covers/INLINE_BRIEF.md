# Brief: localize in-page images with baked English text (Akdeniz Dental site, /home/user/akdenizdentalcom/site)

Languages: en (root pages), de, pl, ro, ru (pages in site/<lang>/). Target readers: DE/AT/CH, PL, RO/MD, Russian speakers. Natural, native wording.
Read first: covers/BRIEF.md (technique for erasing text + overlay spec) and tools/covers.py.

Two techniques — choose per image:
1. **Overlay** (short labels/titles): text-free copy + spec `covers/inline/<name>.json` (same format as covers/BRIEF.md;
   clean file `site/images/blog/clean/inline-<name>.webp` + `-480.webp`). Preview: `python3 tools/covers.py preview inline/<name>`
   → `covers/_preview/inline/<name>.png`; LOOK at it and iterate until clean.
   Insert in a page with python: `import sys; sys.path.insert(0,'tools'); import covers; covers.figure('inline/<name>', lang, prefix, alt)`
   (prefix '' for root pages, '../' for language folders) and make sure the page <head> links `css/ad-cover.css`
   (`<link rel="stylesheet" href="{prefix}css/ad-cover.css">`, add once if missing).
2. **HTML text** (paragraphs, lists, long text): crop/erase the text part of the image so only the visual remains (save clean copy as above, no spec needed,
   use a plain <img> with srcset), and put the text as real HTML next to/below the image in that language (headings/paragraphs/lists with existing
   site/Bootstrap classes, e.g. a `row` with `col-md-6` image + `col-md-6` text, or a `<ul>` under the image). Mobile must stack cleanly.

Rules
- Facts: only what the image/page already says; translate faithfully, no new claims. Keep brand/treatment names (All-on-4, E-max, Akdeniz Dental).
- Every <img> you place: localized alt, width/height, loading="lazy", srcset 480w/800w.
- Never touch the header, footer, <head> except the css link, other sections, or files outside your assignment. Don't run git. Another process edits
  blog cover images (first image of blog articles) — do not touch those.
- After editing pages, verify: `python3 tools/site_report.py site | python3 -c "import json,sys;d=json.load(sys.stdin);print(d['issues'])"` must print `{}`,
  and render each edited page section with Playwright (chromium, require('playwright')) at 1366px and 390px wide via a local `python3 -m http.server`
  in site/ (use a free port: yours is given below) and LOOK at the screenshots. Kill the server afterwards.
- Report: per image the technique, files created, pages changed, any compromise (max 15 lines).
