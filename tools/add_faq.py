"""Add a visible FAQ section + FAQPage JSON-LD to pages that have none. Idempotent (skips pages with FAQPage).
Usage: python3 tools/add_faq.py faq.json [faq2.json ...]   (each: list of {"path", "faq": [{"q","a"}]})
Same markup as tools/seo_apply.py. Inserted before the CTA section if present, else before the footer.
"""
import sys, json, html, pathlib
SITE = pathlib.Path(__file__).resolve().parent.parent / "site"; BASE = "https://akdenizdental.com"
FAQ_HEAD = {"en": "Frequently Asked Questions", "de": "Häufig gestellte Fragen", "pl": "Najczęściej zadawane pytania",
            "ro": "Întrebări frecvente", "ru": "Часто задаваемые вопросы"}
IN_LANG = {"en": "en-GB", "de": "de-DE", "pl": "pl-PL", "ro": "ro-RO", "ru": "ru-RU"}
def esc(s): return html.escape(s, quote=True)

rows = [r for f in sys.argv[1:] for r in json.loads(pathlib.Path(f).read_text("utf-8"))]
done = 0
for r in rows:
    rel = r["path"]; lang = rel.split("/")[0] if rel.split("/")[0] in FAQ_HEAD and "/" in rel else "en"
    f = SITE / (rel + ".html"); t = f.read_text("utf-8")
    if "FAQPage" in t or not r.get("faq"): continue
    items = []
    for i, qa in enumerate(r["faq"]):
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
    anchor = "\t\t<!-- CTA (SEO) -->" if "<!-- CTA (SEO) -->" in t else "<footer"
    t = t.replace(anchor, section + anchor, 1)
    url = BASE + "/" + rel
    ld = {"@context": "https://schema.org", "@type": "FAQPage", "@id": url + "#faq", "inLanguage": IN_LANG[lang],
          "mainEntity": [{"@type": "Question", "name": qa["q"], "acceptedAnswer": {"@type": "Answer", "text": qa["a"]}} for qa in r["faq"]]}
    t = t.replace("</head>", '\t<script type="application/ld+json">\n' + json.dumps(ld, ensure_ascii=False, indent=1) + "\n\t</script>\n</head>", 1)
    f.write_text(t, "utf-8"); done += 1
print("faq added", done, "of", len(rows))
