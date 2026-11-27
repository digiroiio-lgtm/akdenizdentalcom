"""Content fixes applied after seo_apply.py (prices, typos, wrong copy).

Price policy: clinic/Turkey prices are shown in GBP on English pages and in EUR on
DE/PL/RO/RU pages. EUR figures are the ones already used on the German pages
(Hollywood smile 2,500-4,800 EUR, zirconium crown 230-430 EUR, All-on-6 3,000-5,000 EUR
per jaw, All-on-4 at the clinic 3,500-7,000 EUR per arch). UK comparisons stay in GBP.

Usage: python3 tools/content_fixes.py site
Each replacement must match at least once, otherwise the script stops.
"""
import sys, pathlib

ROOT = pathlib.Path(sys.argv[1])

FIXES = {
    # ---- EN ----
    "hollywood-smile.html": [
        (r"Hollywood smile cost in Turkey ranges from \$2,500 to \$4,800. This is", "Hollywood smile cost in Turkey ranges from €2,500 to €4,800. This is"),
        ("significantly lower than the cost of Hollywood smile in other countries, such as\n\t\t\t\t\t\t\t\t\t\tthe United States, where the cost can range from \\$6,000 to \\$10,000.",
         "significantly lower than the cost of Hollywood smile in the UK, where the cost\n\t\t\t\t\t\t\t\t\t\tusually ranges from £6,000 to £10,000."),
    ],
    # ---- DE ----
    "de/hollywood-smile.html": [
        ("<strong>Türkei:</strong>500 € bis 4.800 €", "<strong>Türkei:</strong> 2.500 € bis 4.800 €"),
        ("<strong>Deutschland, Österreich und Schweiz:</strong>000 € bis 10.000 €", "<strong>Deutschland, Österreich und Schweiz:</strong> 6.000 € bis 10.000 €"),
    ],
    # ---- PL ----
    "pl/hollywood-smile.html": [
        (r"Koszt hollywoodzkiego uśmiechu w Turcji waha się od 2.500 do 4.800 dolarów. Jest to znacznie niższy koszt niż koszt hollywoodzkiego uśmiechu w innych krajach, takich jak Stany Zjednoczone, gdzie koszt może wynosić od \$6,000 do \$10,000.",
         "Koszt hollywoodzkiego uśmiechu w Turcji waha się od 2 500 do 4 800 euro. Jest to znacznie mniej niż w Wielkiej Brytanii, gdzie koszt wynosi zwykle od 6 000 do 10 000 funtów."),
        ("€2,500 do €4,800", "2 500 do 4 800 euro"),
    ],
    "pl/zirconium-crowns.html": [
        ("wahają się od 250 do 450 USD za pojedynczą koronę cyrkonową. Cena ta mieści się w przedziale 900-1300 GBP w Wielkiej Brytanii.",
         "wahają się od 230 do 430 euro za pojedynczą koronę cyrkonową. W Wielkiej Brytanii ta sama korona kosztuje zwykle 900–1300 funtów."),
        ("od 250 do 450 USD", "od 230 do 430 euro"),
        ("900–1300 GBP", "900–1300 funtów"),
    ],
    "pl/all-on-6.html": [
        ("od 3 000 do 5 000 dolarów", "od 3 000 do 5 000 euro"),
        ("od $3,000 do $5,000 za szczękę", "od 3 000 do 5 000 euro za szczękę"),
    ],
    "pl/all-on-4.html": [
        ("od 3 000 do 6 000 funtów", "od 3 500 do 7 000 euro"),
        ("od 3000 do 6000 funtów", "od 3 500 do 7 000 euro"),
    ],
    "pl/all-on-4-dental-implants-abroad.html": [
        ("od 3 000 do 6 000 funtów", "od 3 500 do 7 000 euro"),
        ("od 3000 do 6000 funtów", "od 3 500 do 7 000 euro"),
    ],
    # ---- RO ----
    "ro/hollywood-smile.html": [
        ("Costul zâmbetului hollywoodian în Turcia variază de la $2.500 la $4.800. Acesta este semnificativ mai mic decât costul zâmbetului hollywoodian în alte țări, cum ar fi Statele Unite, unde costul poate varia între \u00a0$6.000 și $10.000.",
         "Costul zâmbetului hollywoodian în Turcia variază între 2.500 € și 4.800 €. Acesta este semnificativ mai mic decât în Marea Britanie, unde costul variază de regulă între 6.000 și 10.000 de lire sterline."),
    ],
    "ro/zirconium-crowns.html": [
        ("variază între 250 și 450 USD pentru o singură coroană din zirconiu. Acest preț este în intervalul 900-1300 GBP în Marea Britanie.",
         "variază între 230 € și 430 € pentru o singură coroană din zirconiu. În Marea Britanie, aceeași coroană costă de regulă 900–1300 de lire sterline."),
        ("costă între 250 și 450 USD, potrivit acestei pagini, față de 900–1300 GBP în Marea Britanie.",
         "costă între 230 € și 430 €, față de 900–1300 de lire sterline în Marea Britanie."),
    ],
    "ro/all-on-4-dental-implants-abroad.html": [
        ("costă de regulă între 3.000 și 6.000 de lire sterline pe arcadă, potrivit comparației de pe această pagină. În Marea Britanie, același tratament variază între 12.000 și 20.000 GBP pe arcadă.",
         "costă de regulă între 3.500 € și 7.000 € pe arcadă. În Marea Britanie, același tratament variază între 12.000 și 20.000 de lire sterline pe arcadă."),
        ("variază între 3.000 și 6.000 de lire sterline pe arcada.", "variază între 3.500 € și 7.000 € pe arcadă."),
        ("variind între 3.000 GBP și 6.000 GBP per arcada.", "variind între 3.500 € și 7.000 € pe arcadă."),
        ("între 12.000 GBP și 20.000 GBP per arcada", "între 12.000 și 20.000 de lire sterline pe arcadă"),
    ],
    "ro/all-on-4.html": [
        ("din 19978", "din 1998"),
    ],
}

total = 0
for rel, pairs in FIXES.items():
    f = ROOT / rel
    t = f.read_text("utf-8")
    for old, new in pairs:
        n = t.count(old)
        if n == 0 and new in t:
            continue  # already applied
        if n == 0:
            sys.exit(f"NOT FOUND in {rel}: {old[:70]}")
        t = t.replace(old, new)
        total += n
    f.write_text(t, "utf-8")
print("replacements", total)
