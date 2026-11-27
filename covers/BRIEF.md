# Brief: localized blog cover images (Akdeniz Dental site)

Goal: each blog cover image in `site/images/blog/` has English text baked in. For every assigned image you produce
(1) a TEXT-FREE optimized copy and (2) a JSON spec that places the same text back as HTML in 5 languages (en, de, pl, ro, ru).
Tooling and spec format: read `tools/covers.py` (docstring) first. A finished example: `covers/kill-tooth-pain-nerve-in-3-seconds-permanently.json`
+ `site/images/blog/clean/kill-tooth-pain-nerve-in-3-seconds-permanently.webp` (+ `-480.webp`).

## Steps per image (slug = article slug given to you; image file = given to you)
1. Look at the original (Read tool shows images). Note every text element: position, alignment, colour, weight, size, caps, letter spacing, font style.
2. Erase all baked-in text with Python (PIL + numpy available; no OpenCV/scipy). Techniques:
   - flat panel: sample the panel colour, fill the text bounding box / the whole panel region (follow diagonal edges per row);
   - gradient or soft background: rebuild each text row by linear interpolation between clean pixels left/right of the text box, then a light blur only inside the mask;
   - photo/complex background: build a text mask (pixels far from local background), dilate 2–3 px, fill masked pixels iteratively from neighbours (diffusion fill), small blur inside mask. If a clean result is impossible, put the overlay on a semi-transparent box ("bg": "rgba(...)") that covers the remnants.
   Keep logos ("AKDENIZ dental clinic" logo) and non-language marks (photos, arrows, tooth shade codes like A1/B2, numbers, "Before/After" photo labels may stay if tiny) untouched.
   Save: `site/images/blog/clean/<slug>.webp` at 800px wide (quality 82, method 6) and `site/images/blog/clean/<slug>-480.webp` (480px, LANCZOS, quality 80).
   Record "height" = height of the 800px version in the spec.
3. Write `covers/<slug>.json`: one box per text block (title, subtitle, small paragraph, labels…), positions in % of the image, size in cqw (% of image width).
   Translate every text into de, pl, ro, ru (natural, short enough to fit the same area; keep medical meaning; use the article's own topic wording).
   Use "\n" in text to force line breaks where the original has deliberate breaks (white-space: pre-line). Keep dental brand terms (E-max, All-on-4, Akdeniz Dental).
   If the image has NO text: `"boxes": []` (still produce the optimized clean copy).
4. Run `python3 tools/covers.py preview <slug>` and LOOK at `covers/_preview/<slug>.png` (original | EN, DE | PL, RO | RU, DE at 360 px).
   Iterate until: no remnants of old text, overlay text sits where the original text was, similar look, nothing overflows the image or covers faces/teeth,
   longest language still fits, mobile (360px) is legible-ish. Then delete nothing; leave the preview PNG.
5. Do not modify any HTML page, any other image, or files of slugs not assigned to you.

Report at the end: per slug one line — method used, number of boxes, any compromise (e.g. semi-transparent box, kept English label because it's a code).
