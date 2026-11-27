"""Apply localized cover images to all article pages, blog cards and og:image. Idempotent.
Usage: python3 tools/apply_covers.py [--og]      (--og also (re)renders images/blog/og/<slug>-<lang>.jpg)
"""
import re, sys, json, html, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import covers

SITE = covers.SITE; SPEC = covers.SPEC; BASE = "https://akdenizdental.com"
LANGS = covers.LANGS
(SITE / "css" / "ad-cover.css").write_text(covers.CSS, "utf-8")

specs = sorted(p.stem for p in SPEC.glob("*.json") if not p.name.startswith("_"))
if "--og" in sys.argv:
    for s in specs: covers.og(s)

stats = {"figures": 0, "cards": 0, "og": 0, "css": 0}
orig_of = {s: covers.load(s)["src"] for s in specs}

def page(lang, slug):
    return SITE / (f"{slug}.html" if lang == "en" else f"{lang}/{slug}.html")

for slug in specs:
    sp = covers.load(slug); orig = sp["src"]
    for lang in LANGS:
        f = page(lang, slug)
        if not f.exists(): continue
        t = f.read_text("utf-8"); prefix = "" if lang == "en" else "../"
        title = html.unescape(re.sub(r"<[^>]+>", "", (re.findall(r"<h1[^>]*>(.*?)</h1>", t, re.S) or [""])[0])).strip()
        if '<figure class="ad-cover">' in t:
            t = re.sub(r'<figure class="ad-cover">.*?</figure>', lambda m: covers.figure(slug, lang, prefix, title, eager=True), t, count=1, flags=re.S)
        else:
            t, n = re.subn(r'<img\b[^>]*\bsrc="(?:\.\./)?' + re.escape(orig) + r'"[^>]*>', lambda m: covers.figure(slug, lang, prefix, title, eager=True), t, count=1)
            if not n: print("no featured image in", f.relative_to(SITE)); continue
        stats["figures"] += 1
        og = f"{BASE}/images/blog/og/{slug}-{lang}.jpg"
        if (SITE / "images" / "blog" / "og" / f"{slug}-{lang}.jpg").exists():
            for prop in ['property="og:image"', 'name="twitter:image"']:
                t, n = re.subn(rf'(<meta\s+{prop}\s+content=")[^"]*(")', lambda m: m.group(1) + og + m.group(2), t)
                stats["og"] += n
        if "css/ad-cover.css" not in t:
            t = t.replace("</head>", f'\t<link rel="stylesheet" href="{prefix}css/ad-cover.css">\n</head>', 1); stats["css"] += 1
        f.write_text(t, "utf-8")

# every other use of an original cover (blog cards, sidebars) -> clean image without baked English text
for f in SITE.rglob("*.html"):
    t = f.read_text("utf-8"); o = t
    for slug, orig in orig_of.items():
        clean = covers.load(slug)["clean"]; small = clean.replace(".webp", "-480.webp")
        t, n = re.subn(r'src="(\.\./)?' + re.escape(orig) + '"', lambda m: f'src="{m.group(1) or ""}{small}"', t)
        stats["cards"] += n
    if t != o: f.write_text(t, "utf-8")
print(stats)
