"""Fix duplicate homepage H2s and phone-number H2s. Idempotent. Usage: python3 tools/h2_fixes.py site"""
import re, sys, pathlib
ROOT = pathlib.Path(sys.argv[1])
ALT = {  # replacement titles for 2nd, 3rd occurrence of the testimonials H2 on homepages
    "index": ("Happy Patients", ["Real Patient Stories from Antalya"]),
    "de/index": ("Glückliche Patienten", ["Echte Patientengeschichten aus Antalya", "Das Lächeln unserer Patienten"]),
    "pl/index": ("Szczęśliwi Pacjenci", ["Prawdziwe historie pacjentów z Antalyi", "Uśmiechy naszych pacjentów"]),
    "ro/index": ("Pacienți Fericiți", ["Povești reale ale pacienților din Antalya"]),
    "ru/index": ("Счастливые пациенты", ["Реальные истории пациентов из Антальи", "Улыбки наших пациентов"]),
}
for rel, (title, alts) in ALT.items():
    f = ROOT / (rel + ".html"); t = f.read_text("utf-8")
    pat = re.compile(r'(<h2 class="pbmit-title">)\s*' + re.escape(title) + r'\s*(</h2>)')
    hits = list(pat.finditer(t))
    if not hits: print("no testimonials h2 in", rel, "(check title)"); 
    for m, new in reversed(list(zip(hits[1:], alts))):
        t = t[:m.start()] + m.group(1) + new + m.group(2) + t[m.end():]
    f.write_text(t, "utf-8")
n = 0
for f in ROOT.rglob("*.html"):
    t = f.read_text("utf-8"); o = t
    t = re.sub(r'<h2 class="vc_custom_heading">(\s*\+?90[\d\s()]+)</h2>', r'<p class="h2 vc_custom_heading">\1</p>', t)
    if f.name == "dental-implant-removal.html" and f.parent.name == "ro":
        t = t.replace('<h2 class="pbmit-title">Întrebări frecvente</h2>', '<h2 class="pbmit-title">Întrebări frecvente despre îndepărtarea implanturilor</h2>')
    if f.name == "all-on-4-dental-implants-abroad.html" and f.parent.name == "de":
        t = t.replace("<h2>All-on-4 Zahnimplantate in der Türkei</h2>\n\t\t\t\t<p>Die Türkei gehört", "<h2>Vorteile von All-on-4 Zahnimplantaten in der Türkei</h2>\n\t\t\t\t<p>Die Türkei gehört")
    if t != o: f.write_text(t, "utf-8"); n += 1
print("files changed", n)
