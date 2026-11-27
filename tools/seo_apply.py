"""Apply technical SEO fixes + rewritten meta/headings/FAQs to the static site.

Usage: python3 tools/seo_apply.py site content_dir
content_dir holds out_*.json files (see tools/README in repo root README).
"""
import re, json, sys, html, pathlib, datetime

ROOT = pathlib.Path(sys.argv[1]); CONTENT = pathlib.Path(sys.argv[2])
BASE = "https://akdenizdental.com"
TODAY = datetime.date.today().isoformat()
LANGS = ["en", "ru", "pl", "de", "ro"]
HREFLANG = {"en": ["en", "en-GB", "en-IE"], "de": ["de", "de-DE", "de-AT", "de-CH"],
            "pl": ["pl", "pl-PL"], "ro": ["ro", "ro-RO", "ro-MD"], "ru": ["ru", "ru-RU"]}
OG_LOCALE = {"en": "en_GB", "de": "de_DE", "pl": "pl_PL", "ro": "ro_RO", "ru": "ru_RU"}
IN_LANG = {"en": "en-GB", "de": "de-DE", "pl": "pl-PL", "ro": "ro-RO", "ru": "ru-RU"}
FAQ_HEAD = {"en": "Frequently Asked Questions", "de": "Häufig gestellte Fragen", "pl": "Najczęściej zadawane pytania",
            "ro": "Întrebări frecvente", "ru": "Часто задаваемые вопросы"}
# Duplicate / broken pages -> 301 targets
REMOVE = {
    "de/research-style-1": "/de/clinic-gallery", "pl/research-style-1": "/pl/clinic-gallery",
    "ro/research-style-1": "/ro/clinic-gallery", "ru/research-style-1": "/ru/clinic-gallery",
    "ro/what-are-screwless-dental-implants-screw-implant-or-bonding": "/ro/dental-implants",
    "pl/what-are-screwless-dental-implants-screw-implant-or-bonding": "/pl/dental-implants",
}
CLINIC = {
    "@type": "Dentist", "@id": BASE + "/#clinic", "name": "Akdeniz Dental Clinic", "url": BASE + "/",
    "logo": BASE + "/images/logo.png", "telephone": "+90 541 248 35 62", "email": "info@akdenizdental.com",
    "address": {"@type": "PostalAddress", "streetAddress": "Çaybaşı, 1358. Sk. Premier Plaza D:1 B Blok",
                "addressLocality": "Muratpaşa", "addressRegion": "Antalya", "postalCode": "07100", "addressCountry": "TR"},
    "geo": {"@type": "GeoCoordinates", "latitude": 36.889666919959765, "longitude": 30.722741645473576},
    "openingHoursSpecification": [{"@type": "OpeningHoursSpecification",
        "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"], "opens": "09:00", "closes": "19:00"}],
    "sameAs": ["https://www.instagram.com/akdenizdentalclinic/", "https://www.facebook.com/akdenizdentalclinic",
               "https://www.youtube.com/@AntalyaAkdenizDentalClinic", "https://www.trustpilot.com/review/akdenizdental.com",
               "https://www.google.com/maps?cid=17203087416811821981"],
}

def split(rel):
    return rel.split("/", 1) if rel.split("/")[0] in LANGS[1:] else ("en", rel)

def url_of(rel):
    return BASE + "/" if rel == "index" else f"{BASE}/{rel}"

def esc(s): return html.escape(s, quote=True)
def plain(s): return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()

def ld(obj): return '\t<script type="application/ld+json">\n' + json.dumps(obj, ensure_ascii=False, indent=1) + "\n\t</script>\n"

# ---------- load content ----------
content = {}
for f in sorted(CONTENT.glob("out_*.json")):
    for row in json.loads(f.read_text("utf-8")):
        content[row["path"]] = row

# ---------- remove duplicates ----------
for rel in REMOVE:
    p = ROOT / (rel + ".html")
    if p.exists(): p.unlink()

pages = sorted(str(p.relative_to(ROOT))[:-5] for p in ROOT.rglob("*.html"))
by_slug = {}
for rel in pages:
    lang, slug = split(rel); by_slug.setdefault(slug, {})[lang] = rel

report = []
for rel in pages:
    lang, slug = split(rel)
    f = ROOT / (rel + ".html"); t = f.read_text("utf-8"); orig = t
    url = url_of(rel); c = content.get(rel, {})
    # html lang
    t = re.sub(r'(<html[^>]*\blang=")[^"]*(")', rf'\g<1>{lang}\2', t, count=1)
    # canonical
    t = re.sub(r'\s*<link rel="canonical"[^>]*>', "", t)
    # hreflang (rebuild reciprocal cluster with country targeting)
    t = re.sub(r'\s*<link rel="alternate" hreflang="[^"]*"[^>]*>', "", t)
    t = re.sub(r'\s*<!-- Hreflang -->', "", t)
    links = [f'\t<link rel="canonical" href="{url}">', "\t<!-- Hreflang -->"]
    group = by_slug[slug]
    for l in LANGS:
        if l in group:
            for code in HREFLANG[l]:
                links.append(f'\t<link rel="alternate" hreflang="{code}" href="{url_of(group[l])}">')
    links.append(f'\t<link rel="alternate" hreflang="x-default" href="{url_of(group.get("en", group[lang]))}">')
    t = re.sub(r'(<title>.*?</title>)', lambda m: m.group(1) + "\n\n" + "\n".join(links), t, count=1, flags=re.S)
    # title / description / OG / Twitter
    if c.get("title"):
        t = re.sub(r"<title>.*?</title>", f"<title>{esc(c['title'])}</title>", t, count=1, flags=re.S)
        for prop in ['property="og:title"', 'name="twitter:title"']:
            t = re.sub(rf'(<meta\s+{prop}\s+content=")[^"]*(")', lambda m: m.group(1) + esc(c["title"]) + m.group(2), t, flags=re.S)
    if c.get("description"):
        for prop in ['name="description"', 'property="og:description"', 'name="twitter:description"']:
            t = re.sub(rf'(<meta\s+{prop}\s+content=")[^"]*(")', lambda m: m.group(1) + esc(c["description"]) + m.group(2), t, flags=re.S)
    t = re.sub(r'(<meta property="og:url" content=")[^"]*(")', rf"\g<1>{url}\2", t)
    t = re.sub(r'(<meta property="og:locale" content=")[^"]*(")', rf"\g<1>{OG_LOCALE[lang]}\2", t)
    # boilerplate sidebar/footer headings -> styled paragraphs (keeps look, removes heading noise)
    t = re.sub(r'<h2 class="widget-title">(.*?)</h2>', r'<p class="h2 widget-title">\1</p>', t, flags=re.S)
    t = re.sub(r'<h2>(\s*(?:Wie können wir Ihnen weiterhelfen\?|Jak możemy Ci pomóc ?\?|Cum vă putem ajuta\?|Чем мы можем вам помочь\?)\s*)</h2>',
               r'<p class="h2">\1</p>', t)
    # H1
    new_h1 = c.get("h1")
    if slug == "index" and lang != "en":
        t = re.sub(r'<h1 class="slider-hero-title">(.*?)</h1>', r'<div class="slider-hero-title">\1</div>', t, count=1, flags=re.S)
        if new_h1:
            t = t.replace('<h4 class="pbmit-subtitle">', f'<h1 class="pbmit-subtitle">{esc(new_h1)}</h1>\n\t\t\t\t\t<h4 class="pbmit-subtitle">', 1)
    elif new_h1:
        h1s = list(re.finditer(r"<h1([^>]*)>(.*?)</h1>", t, re.S))
        if h1s:
            first = h1s[0]
            t = t[:first.start()] + f"<h1{first.group(1)}>{esc(new_h1)}</h1>" + t[first.end():]
            # demote extra H1s
            head, tail = t[:first.start() + 10], t[first.start() + 10:]
            tail = re.sub(r"<h1([^>]*)>(.*?)</h1>", r"<h2\1>\2</h2>", tail, flags=re.S)
            t = head + tail
        else:
            t = re.sub(r'<h2 class="pbmit-title">.*?</h2>', f'<h1 class="pbmit-title">{esc(new_h1)}</h1>', t, count=1, flags=re.S)
    # H2 changes (exact text match)
    for ch in c.get("h2_changes", []):
        done = False
        for m in re.finditer(r"<h2([^>]*)>(.*?)</h2>", t, re.S):
            if plain(m.group(2)) == ch["old"].strip():
                t = t[:m.start()] + f"<h2{m.group(1)}>{esc(ch['new'])}</h2>" + t[m.end():]; done = True; break
        if not done: report.append(f"H2 not found {rel}: {ch['old'][:60]}")
    # internal links to removed duplicate pages
    t = t.replace('href="research-style-1.html"', 'href="clinic-gallery.html"').replace('href="research-style-1"', 'href="clinic-gallery"')
    if lang in ("pl", "ro"):
        t = re.sub(r'href="what-are-screwless-dental-implants-screw-implant-or-bonding(\.html)?"', r'href="dental-implants\1"', t)
    # broken mailto
    t = t.replace('href="info@akdenizdental.com"', 'href="mailto:info@akdenizdental.com"')
    # ---- structured data ----
    extra = []
    faq = c.get("faq") or []
    if faq and "FAQPage" not in t:
        items = []
        for i, qa in enumerate(faq):
            items.append(f'''								<div class="accordion-item">
									<h3 class="accordion-header" id="adfaq-h{i}">
										<button class="accordion-button{'' if i == 0 else ' collapsed'}" type="button" data-bs-toggle="collapse" data-bs-target="#adfaq-c{i}" aria-expanded="{'true' if i == 0 else 'false'}" aria-controls="adfaq-c{i}">{esc(qa['q'])}</button>
									</h3>
									<div id="adfaq-c{i}" class="accordion-collapse collapse{' show' if i == 0 else ''}" aria-labelledby="adfaq-h{i}" data-bs-parent="#adfaq">
										<div class="accordion-body">{esc(qa['a'])}</div>
									</div>
								</div>''')
        section = f'''		<!-- FAQ (SEO) -->
		<section class="section-lgt ad-faq" id="faq">
			<div class="container">
				<div class="row"><div class="col-md-12"><div class="pbmit-heading-subheading text-center">
					<h2 class="pbmit-title">{FAQ_HEAD[lang]}</h2>
				</div></div></div>
				<div class="row"><div class="col-12">
							<div class="accordion accordion-style-1" id="adfaq">
{chr(10).join(items)}
							</div>
				</div></div>
			</div>
		</section>
'''
        t = t.replace("<footer", section + "\t\t<footer", 1)
        extra.append({"@context": "https://schema.org", "@type": "FAQPage", "@id": url + "#faq", "inLanguage": IN_LANG[lang],
                      "mainEntity": [{"@type": "Question", "name": qa["q"], "acceptedAnswer": {"@type": "Answer", "text": qa["a"]}} for qa in faq]})
    elif "accordion-header" in t and "FAQPage" not in t:
        # visible accordion without schema -> build FAQPage from it
        qs = []
        for m in re.finditer(r'<button class="accordion-button[^>]*>(.*?)</button>.*?<div class="accordion-body">(.*?)</div>', t, re.S):
            q, a = plain(m.group(1)), plain(m.group(2))
            if q and a: qs.append({"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}})
        if qs:
            extra.append({"@context": "https://schema.org", "@type": "FAQPage", "@id": url + "#faq", "inLanguage": IN_LANG[lang], "mainEntity": qs})
    if not re.search(r'"@type":\s*"(WebPage|MedicalWebPage|Article|BlogPosting|ProfilePage|AboutPage|ContactPage|CollectionPage)"', t):
        title_now = plain((re.findall(r"<title>(.*?)</title>", t, re.S) or [""])[0])
        desc_now = html.unescape((re.findall(r'<meta\s+name="description"\s+content="([^"]*)"', t, re.S) or [""])[0])
        extra.append({"@context": "https://schema.org", "@graph": [CLINIC, {
            "@type": "MedicalWebPage" if slug not in ("index", "contact-us", "blog", "clinic-gallery", "our-team", "our-history") else "WebPage",
            "@id": url + "#webpage", "url": url, "name": title_now, "description": desc_now, "inLanguage": IN_LANG[lang],
            "isPartOf": {"@type": "WebSite", "@id": BASE + "/#website", "name": "Akdeniz Dental Clinic", "url": BASE + "/"},
            "about": {"@id": BASE + "/#clinic"}, "publisher": {"@id": BASE + "/#clinic"}, "dateModified": TODAY}]})
    if extra:
        t = t.replace("</head>", "".join(ld(o) for o in extra) + "</head>", 1)
    if t != orig: f.write_text(t, "utf-8")

# ---------- sitemap with hreflang alternates ----------
out = ['<?xml version="1.0" encoding="UTF-8"?>',
       '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
for rel in pages:
    lang, slug = split(rel); group = by_slug[slug]
    out.append(f"  <url>\n    <loc>{url_of(rel)}</loc>\n    <lastmod>{TODAY}</lastmod>")
    for l in LANGS:
        if l in group:
            for code in HREFLANG[l]:
                out.append(f'    <xhtml:link rel="alternate" hreflang="{code}" href="{url_of(group[l])}"/>')
    out.append(f'    <xhtml:link rel="alternate" hreflang="x-default" href="{url_of(group.get("en", group[lang]))}"/>')
    out.append("  </url>")
out.append("</urlset>")
(ROOT / "sitemap.xml").write_text("\n".join(out) + "\n", "utf-8")
print("pages", len(pages), "content rows", len(content))
for r in report: print(r)
