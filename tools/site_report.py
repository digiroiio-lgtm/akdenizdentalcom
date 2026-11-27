"""Internal QA + H1/H2 scoring. Usage: python3 tools/site_report.py site"""
import re, json, sys, html, pathlib, collections, urllib.parse
ROOT = pathlib.Path(sys.argv[1]); BASE = "https://akdenizdental.com"
LANGS = ["en", "de", "pl", "ro", "ru"]
GEO = {"en": r"antalya|turkey", "de": r"antalya|türkei", "pl": r"antaly|turcj", "ro": r"antalya|turcia", "ru": r"анталь|анталии|анталию|турци"}
CYR = re.compile(r"[а-яА-ЯёЁ]")
DOCTORS = {"ali-burak-bozkurt","ali-burak-kacmaz","ayse-boharali","ayse-kuskacmaz","duygu-kolay-toklu","funda-ozen","mehmet-buyuktarakci","mehmet-onur-merey","mustafa-akca","omer-isen","ozer-ilhan","selen-elif-merey"}
TREAT = {"dental-implants","all-on-4","all-on-6","hollywood-smile","zirconium-crowns","e-max"}
CORE = {"index","our-history","our-team","before-after","faq","services","contact-us","clinic-gallery","akdeniz-dental-lab","blog","dental-finance-turkey"}
def plain(s): return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()
def split(rel): return rel.split("/", 1) if rel.split("/")[0] in LANGS[1:] else ("en", rel)
def url_of(rel): return BASE + "/" if rel == "index" else f"{BASE}/{rel}"
def typ(slug): return "Doktor" if slug in DOCTORS else "Tedavi" if slug in TREAT else "Ana" if slug in CORE else "Blog"

pages = {}
for f in sorted(ROOT.rglob("*.html")):
    rel = str(f.relative_to(ROOT))[:-5]; lang, slug = split(rel)
    if slug == "thank-you": continue
    t = f.read_text("utf-8")
    body = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", t, flags=re.S)
    pages[rel] = dict(lang=lang, slug=slug, t=t,
        title=plain((re.findall(r"<title>(.*?)</title>", t, re.S) or [""])[0]),
        desc=html.unescape((re.findall(r'<meta\s+name="description"\s+content="([^"]*)"', t, re.S) or [""])[0]),
        h1=[plain(x) for x in re.findall(r"<h1[^>]*>(.*?)</h1>", body, re.S)],
        h2=[plain(x) for x in re.findall(r"<h2(?![^>]*accordion-header)[^>]*>(.*?)</h2>", body, re.S)])

def wrong_script(text, lang): return bool(CYR.search(text)) != (lang == "ru")

def h1_score(p):
    s, notes = 0, []
    if len(p["h1"]) == 1: s += 40
    else: notes.append(f"{len(p['h1'])} H1")
    h = p["h1"][0] if p["h1"] else ""
    if 20 <= len(h) <= 70: s += 20
    elif h: notes.append(f"H1 uzunluk {len(h)}")
    if h and (re.search(GEO[p["lang"]], h, re.I) or p["slug"] in DOCTORS and "Dr" in h): s += 20
    elif h: notes.append("H1'de konum yok")
    if h and not wrong_script(h, p["lang"]): s += 20
    elif h: notes.append("H1 yanlış dil")
    return s, notes

def h2_score(p):
    h2 = [x for x in p["h2"] if x]; s, notes = 0, []
    if len(h2) >= 2: s += 30
    elif len(h2) == 1: s += 15; notes.append("tek H2")
    else: notes.append("H2 yok")
    if h2 and not any(wrong_script(x, p["lang"]) for x in h2): s += 20
    elif h2: notes.append("yanlış dil H2")
    if len(set(h2)) == len(h2): s += 20
    else: notes.append("tekrar H2")
    if h2:
        avg = sum(len(x) for x in h2) / len(h2)
        if 15 <= avg <= 90: s += 15
        else: notes.append(f"ort. uzunluk {avg:.0f}")
        if any(x.endswith("?") for x in h2) or any(re.search(GEO[p["lang"]], x, re.I) for x in h2): s += 15
        else: notes.append("soru/konum H2 yok")
    return s, notes

# ---- internal tests ----
issues = collections.Counter(); examples = collections.defaultdict(list)
def fail(k, ex): issues[k] += 1; len(examples[k]) < 3 and examples[k].append(ex)
titles = collections.Counter(p["title"] for p in pages.values()); descs = collections.Counter(p["desc"] for p in pages.values())
by_slug = collections.defaultdict(dict)
for rel, p in pages.items(): by_slug[p["slug"]][p["lang"]] = rel
sitemap = set(re.findall(r"<loc>([^<]+)</loc>", (ROOT / "sitemap.xml").read_text()))
for rel, p in pages.items():
    t = p["t"]; u = url_of(rel)
    canon = re.findall(r'<link rel="canonical" href="([^"]+)"', t)
    if canon != [u]: fail("Canonical kendini göstermiyor", rel)
    hre = dict((c, h) for c, h in re.findall(r'hreflang="([^"]+)" href="([^"]+)"', t))
    for l, other in by_slug[p["slug"]].items():
        if url_of(other) not in hre.values(): fail("hreflang eksik dil", f"{rel}→{l}")
    if "x-default" not in hre: fail("x-default yok", rel)
    for c, h in hre.items():
        tr = h.replace(BASE + "/", "") or "index"
        if tr not in pages: fail("hreflang olmayan sayfaya gidiyor", f"{rel}→{h}")
    if u not in sitemap: fail("Sitemap'te yok", rel)
    if titles[p["title"]] > 1: fail("Tekrar eden title", rel)
    if descs[p["desc"]] > 1: fail("Tekrar eden description", rel)
    if not 30 <= len(p["title"]) <= 65: fail("Title uzunluğu", f"{rel} ({len(p['title'])})")
    if not 110 <= len(p["desc"]) <= 165: fail("Description uzunluğu", f"{rel} ({len(p['desc'])})")
    for m in re.findall(r'<script type="application/ld\+json">(.*?)</script>', t, re.S):
        try: json.loads(m)
        except Exception: fail("Bozuk JSON-LD", rel)
    if 'name="robots" content="noindex' in t: fail("Yanlışlıkla noindex", rel)
    for h in re.findall(r'<a[^>]+href="([^"#?]+)"', t):
        if h.startswith(("mailto:", "tel:", "javascript:", "whatsapp:")) or (h.startswith(("http", "//")) and "akdenizdental.com" not in h): continue
        if "onlinepax" in h or "trustpilot" in h: continue
        path = urllib.parse.urlparse(urllib.parse.urljoin(u if rel != "index" else BASE + "/index", h)).path.lstrip("/")
        path = path[:-5] if path.endswith(".html") else path
        path = path or "index"
        if not ((ROOT / (path + ".html")).exists() or (ROOT / path).is_file()): fail("Kırık iç link", f"{rel}→{h}")
for s in sitemap:
    tr = s.replace(BASE + "/", "") or "index"
    if tr not in pages: fail("Sitemap'te olmayan sayfa", s)

# ---- output ----
out = {"langs": {}, "missing": {}, "pages": [], "issues": dict(issues), "examples": dict(examples)}
all_slugs = sorted(by_slug)
for l in LANGS:
    ps = [p for p in pages.values() if p["lang"] == l]
    c = collections.Counter(typ(p["slug"]) for p in ps)
    h1s = [h1_score(p)[0] for p in ps]; h2s = [h2_score(p)[0] for p in ps]
    out["langs"][l] = dict(total=len(ps), types=dict(c), h1=round(sum(h1s)/len(h1s)), h2=round(sum(h2s)/len(h2s)),
                           h1_full=sum(1 for x in h1s if x == 100), h2_full=sum(1 for x in h2s if x == 100))
    out["missing"][l] = [s for s in all_slugs if l not in by_slug[s]]
for rel, p in sorted(pages.items()):
    a, an = h1_score(p); b, bn = h2_score(p)
    out["pages"].append(dict(path=rel, lang=p["lang"], type=typ(p["slug"]), h1=a, h2=b, notes=an + bn, h1_text=p["h1"][:1], nh2=len(p["h2"])))
print(json.dumps(out, ensure_ascii=False, indent=1))
