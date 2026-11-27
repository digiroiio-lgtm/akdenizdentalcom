"""Blog cover images: text-free image + localized HTML text overlay.

Spec file: covers/<slug>.json (repo root), e.g.
{
  "src": "images/blog/kill-tooth-pain-nerve-in-3-seconds-permanently.jpg",   # original (kept, untouched)
  "clean": "images/blog/clean/kill-tooth-pain-nerve-in-3-seconds-permanently.webp",  # text-free 800w (+ -480.webp)
  "boxes": [
    {"left": 55, "top": 22, "width": 41,            # % of image width/height
     "align": "right", "color": "#ffffff", "size": 3.6,   # font-size in % of image width (cqw)
     "weight": 800, "upper": true, "spacing": 0.18, "lh": 1.55, "font": "Mulish", "italic": false,
     "bg": null,                                    # optional CSS background, e.g. "rgba(0,0,0,.35)"
     "text": {"en": "...", "de": "...", "pl": "...", "ro": "...", "ru": "..."}}
  ]
}
Boxes with an empty "boxes" list = image had no text; only the optimized clean copy is used.

Commands:
  python3 tools/covers.py preview <slug>   -> scratchpad-free preview PNG (original + 5 languages) in covers/_preview/<slug>.png
  python3 tools/covers.py og <slug>        -> images/blog/og/<slug>-<lang>.jpg (text baked in, 1200px) for og:image
"""
import json, sys, html, pathlib, subprocess, tempfile

REPO = pathlib.Path(__file__).resolve().parent.parent
SITE = REPO / "site"; SPEC = REPO / "covers"
LANGS = ["en", "de", "pl", "ro", "ru"]
FONTS = '<link href="https://fonts.googleapis.com/css2?family=Mulish:ital,wght@0,400;0,600;0,700;0,800;1,400&display=swap" rel="stylesheet">'

CSS = """.ad-cover{position:relative;container-type:inline-size;margin:0;overflow:hidden}
.ad-cover img{display:block;width:100%;height:auto}
.ad-cover .ad-cover-t{position:absolute;margin:0;font-family:Mulish,Arial,sans-serif;white-space:pre-line;overflow-wrap:break-word;hyphens:manual}
"""

def load(slug): return json.loads((SPEC / f"{slug}.json").read_text("utf-8"))

def box_style(b):
    s = [f"left:{b['left']}%", f"top:{b['top']}%", f"width:{b['width']}%", f"text-align:{b.get('align','left')}",
         f"color:{b.get('color','#fff')}", f"font-size:{b.get('size',3.5)}cqw", f"font-weight:{b.get('weight',700)}",
         f"line-height:{b.get('lh',1.25)}", f"letter-spacing:{b.get('spacing',0)}em"]
    if b.get("upper"): s.append("text-transform:uppercase")
    if b.get("italic"): s.append("font-style:italic")
    if b.get("rotate"): s.append(f"transform:rotate({b['rotate']}deg);transform-origin:center")
    if b.get("bg"): s.append(f"background:{b['bg']};padding:.4em .6em;border-radius:.3em")
    if b.get("font") and b["font"] != "Mulish": s.append(f"font-family:{b['font']},Mulish,Arial,sans-serif")
    return ";".join(s)

def figure(slug, lang, prefix="", alt="", eager=False):
    """slug may be "inline/<name>" for in-article images (spec in covers/inline/)."""
    """HTML for an article page. prefix = '' for root pages, '../' for language folders."""
    sp = load(slug); clean = sp["clean"]; small = clean.replace(".webp", "-480.webp")
    boxes = "".join(f'<span class="ad-cover-t" style="{box_style(b)}" lang="{lang}">{html.escape(b["text"][lang])}</span>'
                    for b in sp["boxes"])
    load_attr = 'fetchpriority="high"' if eager else 'loading="lazy"'
    return (f'<figure class="ad-cover">'
            f'<img src="{prefix}{clean}" srcset="{prefix}{small} 480w, {prefix}{clean} 800w" sizes="(max-width: 600px) 480px, 800px" '
            f'width="800" height="{sp.get("height", 530)}" {load_attr} alt="{html.escape(alt, quote=True)}">{boxes}</figure>')

def render(pages, out_png, width=1200):
    """pages: list of html fragments (each a figure); screenshot each into out_png (list) via playwright."""
    with tempfile.TemporaryDirectory() as td:
        jobs = []
        for i, (frag, png, w) in enumerate(pages):
            f = pathlib.Path(td) / f"p{i}.html"
            f.write_text(f'<!doctype html><html><head><meta charset="utf-8"><base href="file://{SITE}/">{FONTS}<style>{CSS}body{{margin:0}}figure{{width:{w}px}}</style></head>'
                         f'<body>{frag}</body></html>', "utf-8")
            jobs.append([str(f), str(png)])
        js = pathlib.Path(td) / "r.js"
        js.write_text("""const { chromium } = require('playwright');
(async () => { const jobs = JSON.parse(process.argv[2]); const b = await chromium.launch(); const p = await b.newPage({deviceScaleFactor: 1});
 for (const [f, png] of jobs) { await p.goto('file://' + f); await p.waitForLoadState('networkidle').catch(()=>{}); await p.waitForTimeout(400);
   const el = await p.$('figure'); await el.screenshot({ path: png, type: png.endsWith('.jpg') ? 'jpeg' : 'png', ...(png.endsWith('.jpg') ? {quality: 85} : {}) }); }
 await b.close(); })();""")
        subprocess.run(["node", str(js), json.dumps(jobs)], check=True)

def preview(slug):
    sp = load(slug); outdir = SPEC / "_preview"; (outdir / slug).parent.mkdir(parents=True, exist_ok=True)
    parts = [(f'<figure class="ad-cover"><img src="{sp["src"]}"></figure>', outdir / f"{slug}-orig.png", 800)]
    parts += [(figure(slug, l), outdir / f"{slug}-{l}.png", 800) for l in LANGS]
    parts += [(figure(slug, "de"), outdir / f"{slug}-de-mobile.png", 360)]
    render(parts, None)
    # combine into one sheet
    from PIL import Image
    ims = [Image.open(p[1]) for p in parts]
    W = 800; Hs = [im.height for im in ims[:6]]
    sheet = Image.new("RGB", (W * 2, sum(Hs[::2]) + 20 + ims[6].height), "white")
    y = 0
    for i in range(0, 6, 2):
        sheet.paste(ims[i], (0, y)); sheet.paste(ims[i + 1], (W, y)); y += max(ims[i].height, ims[i + 1].height)
    sheet.paste(ims[6], (0, y + 20))
    out = outdir / f"{slug}.png"; sheet.save(out)
    for p in parts: pathlib.Path(p[1]).unlink()
    print(out, "(rows: original|EN, DE|PL, RO|RU, then DE at 360px)")

def og(slug):
    sp = load(slug); d = SITE / "images" / "blog" / "og"; d.mkdir(parents=True, exist_ok=True)
    render([(figure(slug, l, eager=True), d / f"{slug}-{l}.jpg", 1200) for l in LANGS], None)
    print("og images:", ", ".join(f"{slug}-{l}.jpg" for l in LANGS))

if __name__ == "__main__":
    {"preview": preview, "og": og}[sys.argv[1]](sys.argv[2])
