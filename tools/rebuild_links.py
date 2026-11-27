"""Idempotent rebuild of canonical + hreflang on every page and of sitemap.xml.
Run after adding/removing pages. Usage: python3 tools/rebuild_links.py site
"""
import re, sys, pathlib, datetime

ROOT = pathlib.Path(sys.argv[1]); BASE = "https://akdenizdental.com"; TODAY = datetime.date.today().isoformat()
LANGS = ["en", "ru", "pl", "de", "ro"]
HREFLANG = {"en": ["en", "en-GB", "en-IE"], "de": ["de", "de-DE", "de-AT", "de-CH"], "pl": ["pl", "pl-PL"],
            "ro": ["ro", "ro-RO", "ro-MD"], "ru": ["ru", "ru-RU"]}

def split(rel): return rel.split("/", 1) if rel.split("/")[0] in LANGS[1:] else ("en", rel)
def url_of(rel): return BASE + "/" if rel == "index" else f"{BASE}/{rel}"

pages = sorted(str(p.relative_to(ROOT))[:-5] for p in ROOT.rglob("*.html"))
by_slug = {}
for rel in pages:
    l, s = split(rel); by_slug.setdefault(s, {})[l] = rel

def cluster(slug, lang):
    g = by_slug[slug]; out = []
    for l in LANGS:
        if l in g: out += [(c, url_of(g[l])) for c in HREFLANG[l]]
    out.append(("x-default", url_of(g.get("en", g[lang]))))
    return out

for rel in pages:
    lang, slug = split(rel); f = ROOT / (rel + ".html"); t = f.read_text("utf-8"); o = t
    t = re.sub(r'\s*<link rel="canonical"[^>]*>', "", t)
    t = re.sub(r'\s*<link rel="alternate" hreflang="[^"]*"[^>]*>', "", t)
    t = re.sub(r"\s*<!-- Hreflang -->", "", t)
    block = [f'\t<link rel="canonical" href="{url_of(rel)}">', "\t<!-- Hreflang -->"]
    block += [f'\t<link rel="alternate" hreflang="{c}" href="{u}">' for c, u in cluster(slug, lang)]
    t = re.sub(r"(<title>.*?</title>)", lambda m: m.group(1) + "\n\n" + "\n".join(block), t, count=1, flags=re.S)
    t = re.sub(r'(<meta property="og:url" content=")[^"]*(")', rf"\g<1>{url_of(rel)}\2", t)
    if t != o: f.write_text(t, "utf-8")

out = ['<?xml version="1.0" encoding="UTF-8"?>',
       '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">']

def page_images(rel):
    t = (ROOT / (rel + ".html")).read_text("utf-8")
    if "</header>" not in t: return []
    body = re.sub(r"<!--.*?-->", "", t.split("</header>", 1)[1].split("<footer", 1)[0], flags=re.S)
    seen = []
    for src in re.findall(r'<img\b[^>]*\bsrc="([^"]+)"', body):
        if src.startswith(("http", "//", "data:")) or any(x in src for x in ("flag-", "whatsapp", ".svg", ".gif")): continue
        u = BASE + "/" + re.sub(r"^(\.\./)+", "", src)
        if u not in seen: seen.append(u)
    og = re.findall(r'<meta\s+property="og:image"\s+content="([^"]+)"', t)
    if og and "logo" not in og[0] and og[0] not in seen: seen.append(og[0])
    return seen[:1000]
for rel in pages:
    lang, slug = split(rel)
    if slug == "thank-you": continue
    out.append(f"  <url>\n    <loc>{url_of(rel)}</loc>\n    <lastmod>{TODAY}</lastmod>")
    out += [f'    <xhtml:link rel="alternate" hreflang="{c}" href="{u}"/>' for c, u in cluster(slug, lang)]
    out += [f"    <image:image><image:loc>{u}</image:loc></image:image>" for u in page_images(rel)]
    out.append("  </url>")
out.append("</urlset>")
(ROOT / "sitemap.xml").write_text("\n".join(out) + "\n", "utf-8")
print("pages", len(pages), "sitemap urls", sum(1 for x in out if "<loc>" in x))
