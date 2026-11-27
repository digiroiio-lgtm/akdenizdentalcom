"""Add meaningful H2 sections to thin pages (doctors, gallery, before-after, lab, about).
Idempotent: skips pages that already contain the marker 'ad-h2'.
Usage: python3 tools/h2_add.py site
"""
import re, sys, html, pathlib

ROOT = pathlib.Path(sys.argv[1])
LANGS = ["en", "de", "pl", "ro", "ru"]
DOCTORS = ["ali-burak-bozkurt", "ali-burak-kacmaz", "ayse-boharali", "ayse-kuskacmaz", "duygu-kolay-toklu", "funda-ozen",
           "mehmet-buyuktarakci", "mehmet-onur-merey", "mustafa-akca", "omer-isen", "ozer-ilhan", "selen-elif-merey"]

T = {
    "en": dict(
        doc1="About {n}: Education and Background", doc2="{n} – Areas of Expertise at Akdeniz Dental, Antalya",
        gallery=("Inside Akdeniz Dental Clinic in Antalya", "Take a look inside our dental clinic in Antalya, Turkey – the treatment rooms, patient areas and equipment our team works with every day."),
        before_after=("Before and After Dental Treatment Results in Antalya", "Real smile transformations of patients treated at Akdeniz Dental Clinic in Antalya, Turkey."),
        lab=("Akdeniz Dental Lab: Our Dental Laboratory in Antalya", "At Akdeniz Dental Lab, dental technicians work closely with our dentists on crowns, veneers and implant prostheses for our patients."),
        about=("Why Patients Choose Akdeniz Dental in Antalya", None),
        cta=("Plan Your Dental Treatment in Antalya, Turkey", "Contact us to get a personalised treatment plan and help with arranging your visit to Antalya.", "Contact us"),
    ),
    "de": dict(
        doc1="Über {n}: Ausbildung und Werdegang", doc2="{n} – Fachgebiete bei Akdeniz Dental in Antalya",
        gallery=("Einblicke in die Zahnklinik Akdeniz Dental in Antalya", "Werfen Sie einen Blick in unsere Zahnklinik in Antalya, Türkei – Behandlungsräume, Patientenbereiche und die Ausstattung, mit der unser Team täglich arbeitet."),
        before_after=("Vorher-Nachher-Ergebnisse unserer Zahnbehandlungen in Antalya", "Echte Ergebnisse von Patientinnen und Patienten, die bei Akdeniz Dental in Antalya, Türkei, behandelt wurden."),
        lab=("Akdeniz Dental Lab: Unser Dentallabor in Antalya", "Im Akdeniz Dental Lab arbeiten Zahntechniker eng mit unseren Zahnärzten an Kronen, Veneers und Implantatprothesen für unsere Patienten."),
        about=("Warum Patienten Akdeniz Dental in Antalya wählen", None),
        cta=("Planen Sie Ihre Zahnbehandlung in Antalya, Türkei", "Kontaktieren Sie uns für einen persönlichen Behandlungsplan und Unterstützung bei der Planung Ihrer Reise nach Antalya.", "Kontakt aufnehmen"),
    ),
    "pl": dict(
        doc1="{n} – wykształcenie i droga zawodowa", doc2="{n} – specjalizacja w klinice Akdeniz Dental w Antalyi",
        gallery=("Wnętrze kliniki Akdeniz Dental w Antalyi", "Zobacz, jak wygląda nasza klinika stomatologiczna w Antalyi w Turcji – gabinety, strefy dla pacjentów i sprzęt, z którego codziennie korzysta nasz zespół."),
        before_after=("Efekty leczenia przed i po w Antalyi", "Prawdziwe metamorfozy uśmiechu pacjentów leczonych w klinice Akdeniz Dental w Antalyi w Turcji."),
        lab=("Akdeniz Dental Lab – nasze laboratorium protetyczne w Antalyi", "W Akdeniz Dental Lab technicy dentystyczni ściśle współpracują z naszymi lekarzami przy koronach, licówkach i protezach na implantach."),
        about=("Dlaczego pacjenci wybierają Akdeniz Dental w Antalyi", None),
        cta=("Zaplanuj leczenie stomatologiczne w Antalyi w Turcji", "Skontaktuj się z nami, aby otrzymać indywidualny plan leczenia i pomoc w organizacji przyjazdu do Antalyi.", "Skontaktuj się z nami"),
    ),
    "ro": dict(
        doc1="Despre {n}: formare și parcurs profesional", doc2="{n} – domenii de expertiză la Akdeniz Dental, Antalya",
        gallery=("În interiorul clinicii Akdeniz Dental din Antalya", "Aruncați o privire în clinica noastră stomatologică din Antalya, Turcia – cabinetele, spațiile pentru pacienți și echipamentele cu care lucrează echipa noastră în fiecare zi."),
        before_after=("Rezultate înainte și după tratament dentar în Antalya", "Transformări reale ale zâmbetului pacienților tratați la clinica Akdeniz Dental din Antalya, Turcia."),
        lab=("Akdeniz Dental Lab: laboratorul nostru dentar din Antalya", "La Akdeniz Dental Lab, tehnicienii dentari colaborează îndeaproape cu medicii noștri la coroane, fațete și proteze pe implanturi."),
        about=("De ce aleg pacienții Akdeniz Dental din Antalya", None),
        cta=("Planificați tratamentul dentar în Antalya, Turcia", "Contactați-ne pentru un plan de tratament personalizat și ajutor în organizarea vizitei în Antalya.", "Contactați-ne"),
    ),
    "ru": dict(
        doc1="{n}: образование и профессиональный путь", doc2="{n}: специализация в клинике Akdeniz Dental в Анталье",
        gallery=("Клиника Akdeniz Dental в Анталье изнутри", "Посмотрите, как выглядит наша стоматологическая клиника в Анталье, Турция: кабинеты, зоны для пациентов и оборудование, с которым ежедневно работает наша команда."),
        before_after=("Результаты лечения до и после в Анталье", "Реальные преображения улыбок пациентов, прошедших лечение в клинике Akdeniz Dental в Анталье, Турция."),
        lab=("Akdeniz Dental Lab: наша зуботехническая лаборатория в Анталье", "В Akdeniz Dental Lab зубные техники тесно работают с нашими стоматологами над коронками, винирами и протезами на имплантах."),
        about=("Почему пациенты выбирают Akdeniz Dental в Анталье", None),
        cta=("Спланируйте лечение зубов в Анталье, Турция", "Свяжитесь с нами, чтобы получить индивидуальный план лечения и помощь в организации поездки в Анталью.", "Связаться с нами"),
    ),
}

def esc(s): return html.escape(s, quote=False)

def intro_block(h, p):
    return (f'\n\t\t\t\t\t<div class="pbmit-heading-subheading text-center ad-h2">\n\t\t\t\t\t\t<h2 class="pbmit-title">{esc(h)}</h2>\n'
            f'\t\t\t\t\t\t<div class="pbmit-heading-content"><p>{esc(p)}</p></div>\n\t\t\t\t\t</div>')

def cta_section(lang):
    h, p, btn = T[lang]["cta"]
    return (f'\t\t<!-- CTA (SEO) -->\n\t\t<section class="section-md ad-h2 ad-cta">\n\t\t\t<div class="container">\n'
            f'\t\t\t\t<div class="pbmit-heading-subheading text-center">\n\t\t\t\t\t<h2 class="pbmit-title">{esc(h)}</h2>\n'
            f'\t\t\t\t\t<div class="pbmit-heading-content"><p>{esc(p)}</p></div>\n'
            f'\t\t\t\t\t<a href="contact-us.html" class="pbmit-btn">{esc(btn)}</a>\n\t\t\t\t</div>\n\t\t\t</div>\n\t\t</section>\n')

def add_cta(t, lang):
    if "ad-cta" in t or "<footer" not in t: return t
    return t.replace("<footer", cta_section(lang) + "\t\t<footer", 1)

changed = []
for lang in LANGS:
    pre = "" if lang == "en" else lang + "/"
    # doctors
    for d in DOCTORS:
        f = ROOT / f"{pre}{d}.html"
        if not f.exists(): continue
        t = f.read_text("utf-8")
        if "ad-h2" in t: continue
        m = re.search(r'<div class="card-body">(.*?)</div>', t, re.S)
        name = re.search(r"<h3>\s*(Dr\.?[^<]+?)\s*</h3>", t)
        if not m or not name: print("skip doctor", f); continue
        n = re.sub(r"\s+", " ", name.group(1)).strip()
        body = m.group(1)
        ps = list(re.finditer(r"<p[ >]", body))
        if not ps: print("no bio p", f); continue
        h1 = f'<h2 class="ad-h2">{esc(T[lang]["doc1"].format(n=n))}</h2>\n\t\t\t\t\t\t'
        h2 = f'<h2 class="ad-h2">{esc(T[lang]["doc2"].format(n=n))}</h2>\n\t\t\t\t\t\t'
        if len(ps) >= 2:
            i2 = ps[len(ps) // 2].start()
            body = body[:i2] + h2 + body[i2:]
        body = body[:ps[0].start()] + h1 + body[ps[0].start():]
        t = t[:m.start(1)] + body + t[m.end(1):]
        if len(ps) < 2: t = add_cta(t, lang)
        f.write_text(t, "utf-8"); changed.append(str(f))
    # gallery / before-after / lab: intro H2 at top of the grid + CTA section
    for slug, key in [("clinic-gallery", "gallery"), ("before-after", "before_after"), ("akdeniz-dental-lab", "lab")]:
        f = ROOT / f"{pre}{slug}.html"
        if not f.exists(): continue
        t = f.read_text("utf-8")
        if "ad-h2" in t: continue
        h, p = T[lang][key]
        t2 = re.sub(r'(<section class="section-lg">\s*<div class="container">)', lambda m: m.group(1) + intro_block(h, p), t, count=1)
        if t2 == t: print("no grid anchor", f); continue
        t2 = add_cta(t2, lang)
        f.write_text(t2, "utf-8"); changed.append(str(f))
    # about pages: H2 before the checklist + CTA section
    f = ROOT / f"{pre}our-history.html"
    if f.exists():
        t = f.read_text("utf-8")
        if "ad-h2" not in t:
            h = T[lang]["about"][0]
            t2 = re.sub(r'(\n(\s*)<div class="row">\s*<div class="col-md-6">\s*<ul class="list-group)',
                        lambda m: f'\n{m.group(2)}<h2 class="pbmit-title h3 ad-h2">{esc(h)}</h2>' + m.group(1), t, count=1)
            if t2 == t: print("no checklist anchor", f)
            t2 = add_cta(t2, lang)
            f.write_text(t2, "utf-8"); changed.append(str(f))
print("pages changed", len(changed))
