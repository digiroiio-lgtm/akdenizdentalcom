"""Assemble translated pages into the site.

Usage: python3 tools/build_translations.py site OUT_DIR
OUT_DIR/<lang>/<slug>.html  translated body fragment (between </header> and <footer)
OUT_DIR/<lang>/<slug>.json  {"title","description","card_title","card_excerpt"}
OUT_DIR/ru/_blog.json       {"title","description","h1","breadcrumb","intro"} -> builds ru/blog.html

Header/footer come from <lang>/our-team.html of the same language. Afterwards run
tools/rebuild_links.py to refresh canonical/hreflang/sitemap.
"""
import re, sys, json, html, pathlib, datetime

ROOT = pathlib.Path(sys.argv[1]); OUT = pathlib.Path(sys.argv[2])
BASE = "https://akdenizdental.com"; TODAY = datetime.date.today().isoformat()
IN_LANG = {"de": "de-DE", "pl": "pl-PL", "ro": "ro-RO", "ru": "ru-RU"}
OG_LOCALE = {"de": "de_DE", "pl": "pl_PL", "ro": "ro_RO", "ru": "ru_RU"}
DOCTORS = {"ali-burak-bozkurt", "ali-burak-kacmaz", "ayse-boharali", "ayse-kuskacmaz", "duygu-kolay-toklu", "funda-ozen",
           "mehmet-buyuktarakci", "mehmet-onur-merey", "mustafa-akca", "omer-isen", "ozer-ilhan", "selen-elif-merey"}
CLINIC_ID = BASE + "/#clinic"

def esc(s): return html.escape(s, quote=True)
def plain(s): return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()

def template(lang):
    t = (ROOT / lang / "our-team.html").read_text("utf-8")
    head, rest = t.split("</header>", 1)
    return head + "</header>", "<footer" + rest.split("<footer", 1)[1]

def set_head(prefix, lang, slug, meta):
    p = re.sub(r'\s*<script type="application/ld\+json">.*?</script>', "", prefix, flags=re.S)
    p = re.sub(r"<title>.*?</title>", f"<title>{esc(meta['title'])}</title>", p, count=1, flags=re.S)
    for prop, val in [('name="description"', meta["description"]), ('property="og:description"', meta["description"]),
                      ('name="twitter:description"', meta["description"]), ('property="og:title"', meta["title"]),
                      ('name="twitter:title"', meta["title"]), ('property="og:url"', f"{BASE}/{lang}/{slug}"),
                      ('property="og:locale"', OG_LOCALE[lang])]:
        p = re.sub(rf'(<meta\s+{prop}\s+content=")[^"]*(")', lambda m: m.group(1) + esc(val) + m.group(2), p, flags=re.S)
    p = re.sub(r'(<meta\s+property="og:type"\s+content=")[^"]*(")', r"\1article\2", p)
    return p

def fix_paths(frag, lang):
    def fix(m):
        attr, val = m.group(1), m.group(2)
        if re.match(r"(https?:|//|/|\.\./|#|mailto:|tel:|javascript:|data:|whatsapp:)", val) or not val: return m.group(0)
        path = val.split("#")[0].split("?")[0]
        stem = path[:-5] if path.endswith(".html") else path
        if (ROOT / lang / (stem + ".html")).exists() or (OUT / lang / (stem + ".html")).exists() or stem == "blog":
            return m.group(0)
        return f'{attr}="../{val}"'
    frag = re.sub(r'\b(src|href|data-src|data-bg)="([^"]*)"', fix, frag)
    frag = re.sub(r'srcset="([^"]*)"', lambda m: 'srcset="' + ", ".join(
        (x.strip() if re.match(r"(https?:|//|/|\.\./)", x.strip()) else "../" + x.strip()) for x in m.group(1).split(",")) + '"', frag)
    return frag

def schemas(lang, slug, meta, frag):
    url = f"{BASE}/{lang}/{slug}"
    out = [{"@context": "https://schema.org", "@type": "ProfilePage" if slug in DOCTORS else "MedicalWebPage", "@id": url + "#webpage",
            "url": url, "name": meta["title"], "description": meta["description"], "inLanguage": IN_LANG[lang],
            "isPartOf": {"@type": "WebSite", "@id": BASE + "/#website", "name": "Akdeniz Dental Clinic", "url": BASE + "/"},
            "about": {"@id": CLINIC_ID}, "publisher": {"@type": "Dentist", "@id": CLINIC_ID, "name": "Akdeniz Dental Clinic", "url": BASE + "/"},
            "dateModified": TODAY}]
    qs = []
    for m in re.finditer(r'<button class="accordion-button[^>]*>(.*?)</button>.*?<div class="accordion-body">(.*?)</div>', frag, re.S):
        q, a = plain(m.group(1)), plain(m.group(2))
        if q and a: qs.append({"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}})
    if qs:
        out.append({"@context": "https://schema.org", "@type": "FAQPage", "@id": url + "#faq", "inLanguage": IN_LANG[lang], "mainEntity": qs})
    return "".join('\t<script type="application/ld+json">\n' + json.dumps(o, ensure_ascii=False, indent=1) + "\n\t</script>\n" for o in out)

built = []
cards = {}
for langdir in sorted(OUT.iterdir()):
    lang = langdir.name
    if lang not in IN_LANG: continue
    prefix, suffix = template(lang)
    for f in sorted(langdir.glob("*.html")):
        slug = f.stem
        meta = json.loads((langdir / f"{slug}.json").read_text("utf-8"))
        frag = fix_paths(f.read_text("utf-8"), lang)
        # UK-only finance banner (Ideal4Finance) does not apply to non-UK readers
        frag = re.sub(r"\s*<!-- Dental Finance Callout Banner -->.*?<!-- /Dental Finance Callout Banner -->", "", frag, flags=re.S)
        if meta.get("card_title"):
            # breadcrumb shows the article itself; fix copied image alt text from the English source
            frag = re.sub(r'(current-item">)[^<]*(</span>)', lambda m: m.group(1) + esc(meta["card_title"]) + m.group(2), frag, count=1)
            frag = re.sub(r'(<img[^>]*src="[^"]*"[^>]*?)alt="[^"]*" title="[^"]*"', lambda m: m.group(1) + f'alt="{esc(meta["card_title"])}" title="{esc(meta["card_title"])}"', frag, count=1)
        page = set_head(prefix, lang, slug, meta).replace("</head>", schemas(lang, slug, meta, frag) + "</head>", 1) + frag + suffix
        (ROOT / lang / f"{slug}.html").write_text(page, "utf-8"); built.append(f"{lang}/{slug}")
        if meta.get("card_title"): cards.setdefault(lang, []).append((slug, meta))

# ---- blog index cards ----
def card_html(slug, meta, img):
    return f'''
							<div class="col-md-4 ad-card">
								<article class="pbmit-service-style-2">
									<div class="pbminfotech-post-item">
										<div class="pbmit-featured-wrapper">
											<a href="{slug}.html"><img src="{img}" class="w-100" alt="{esc(meta['card_title'])}" title="{esc(meta['card_title'])}"></a>
										</div>
										<div class="pbminfotech-box-content">
											<div class="pbminfotech-box-content-inner">
												<h3 class="pbmit-service-title"><a href="{slug}.html">{esc(meta['card_title'])}</a></h3>
												<div class="pbmit-service-content"><p>{esc(meta['card_excerpt'])}</p></div>
											</div>
										</div>
									</div>
								</article>
							</div>
'''

en_blog = (ROOT / "blog.html").read_text("utf-8")
def en_img(slug):
    m = re.search(r'href="' + re.escape(slug) + r'(?:\.html)?"[^>]*>\s*<img[^>]*src="([^"]+)"', en_blog)
    return "../" + m.group(1) if m else "../images/logo.png"

for lang, items in cards.items():
    idx = ROOT / lang / "blog.html"
    if lang == "ru" and not idx.exists():
        b = json.loads((OUT / "ru" / "_blog.json").read_text("utf-8"))
        de_blog = (ROOT / "de" / "blog.html").read_text("utf-8")
        body = de_blog.split("</header>", 1)[1].split("<footer", 1)[0]
        body = re.sub(r"<h1([^>]*)>.*?</h1>", lambda m: f"<h1{m.group(1)}>{esc(b['h1'])}</h1>", body, count=1, flags=re.S)
        body = re.sub(r'(current-item">).*?(</span>)', lambda m: m.group(1) + esc(b["breadcrumb"]) + m.group(2), body, count=1, flags=re.S)
        # mark the cards row, then drop German cards
        i = body.find("pbmit-service-style-2"); r = body.rfind('<div class="row">', 0, i) + len('<div class="row">')
        body = body[:r] + f'\n\t\t\t\t\t\t\t<div class="col-12 ad-blog-intro"><p>{esc(b["intro"])}</p></div><!-- AD-CARDS -->' + body[r:]
        body = re.sub(r'\s*<div class="col-md-4[^"]*">\s*<article class="pbmit-service-style-2">.*?</article>\s*</div>', "", body, flags=re.S)
        body = re.sub(r'<section class="section-lgt ad-faq".*?</section>\s*', "", body, flags=re.S)
        body = re.sub(r'\s*<!-- CTA \(SEO\) -->.*?</section>\s*', "\n", body, flags=re.S)
        prefix, suffix = template("ru")
        meta = {"title": b["title"], "description": b["description"]}
        head = set_head(prefix, "ru", "blog", meta).replace("</head>", schemas("ru", "blog", meta, "") + "</head>", 1)
        idx.write_text(head + body + suffix, "utf-8"); built.append("ru/blog")
    t = idx.read_text("utf-8")
    new = "".join(card_html(s, m, en_img(s)) for s, m in items if f'href="{s}.html"' not in t)
    if new:
        if "<!-- AD-CARDS -->" in t:
            t = t.replace("<!-- AD-CARDS -->", "<!-- AD-CARDS -->" + new, 1)
        else:
            i = t.find("pbmit-service-style-2"); r = t.rfind('<div class="row">', 0, i) + len('<div class="row">')
            t = t[:r] + "<!-- AD-CARDS -->" + new + t[r:]
        idx.write_text(t, "utf-8")
print("built", len(built))
for b in built: print(" ", b)
