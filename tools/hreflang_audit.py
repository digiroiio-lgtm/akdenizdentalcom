"""Internal hreflang audit with weighted score. Usage: python3 tools/hreflang_audit.py site"""
import re, sys, json, pathlib, collections

ROOT = pathlib.Path(sys.argv[1]); BASE = "https://akdenizdental.com"
LANGS = ["en", "de", "pl", "ro", "ru"]
ISO639 = {"en", "de", "pl", "ro", "ru"}
ISO3166 = {"GB", "IE", "DE", "AT", "CH", "PL", "RO", "MD", "RU"}
REDIRECTED = {r["source"].lstrip("/") for r in json.load(open(ROOT.parent / "vercel.json")).get("redirects", [])}

def split(rel): return rel.split("/", 1) if rel.split("/")[0] in LANGS[1:] else ("en", rel)
def rel_of(url): return url.replace(BASE + "/", "").rstrip("/") or "index"

pages = {}
for f in sorted(ROOT.rglob("*.html")):
    rel = str(f.relative_to(ROOT))[:-5]; t = f.read_text("utf-8")
    lang, slug = split(rel)
    pages[rel] = dict(lang=lang, slug=slug, t=t,
        hre=re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"', t),
        canon=(re.findall(r'<link rel="canonical" href="([^"]+)"', t) or [None])[0],
        html_lang=(re.findall(r'<html[^>]*\blang="([^"]*)"', t) or [""])[0],
        content_lang=re.findall(r'<meta name="content-language" content="([^"]*)"', t),
        noindex='name="robots" content="noindex' in t)
idx = {r: p for r, p in pages.items() if p["slug"] != "thank-you"}

sm = (ROOT / "sitemap.xml").read_text("utf-8")
sm_alt = {}
for block in re.findall(r"<url>(.*?)</url>", sm, re.S):
    loc = re.search(r"<loc>([^<]+)</loc>", block).group(1)
    sm_alt[rel_of(loc)] = sorted(re.findall(r'hreflang="([^"]+)" href="([^"]+)"', block))

CHECKS = [  # key, label, weight
    ("present", "Sayfada hreflang etiketleri var", 10),
    ("self", "Sayfa kendini hreflang'de listeliyor", 10),
    ("reciprocal", "Tüm alternatifler karşılıklı (geri link veriyor)", 15),
    ("xdefault", "x-default var ve İngilizce sürümü gösteriyor", 8),
    ("codes", "Geçerli dil/ülke kodları (ISO 639-1 / 3166-1)", 7),
    ("unique", "Her kod bir kez, tek URL'ye", 5),
    ("targets_ok", "Hedefler var, 200 döner, yönlendirme yok, noindex yok", 12),
    ("canon_match", "Hedeflerin canonical'ı hreflang URL'si ile aynı", 10),
    ("absolute", "Mutlak https URL, tek host", 5),
    ("html_lang", "<html lang> hreflang diliyle uyumlu", 6),
    ("content_lang", "content-language meta çelişkisi yok", 4),
    ("sitemap", "Sitemap hreflang = sayfa hreflang", 8),
]
res = collections.defaultdict(lambda: [0, 0]); ex = collections.defaultdict(list)
def mark(k, ok, rel, why=""):
    res[k][0] += ok; res[k][1] += 1
    if not ok and len(ex[k]) < 4: ex[k].append(f"{rel} {why}".strip())

for rel, p in idx.items():
    h = p["hre"]; codes = [c for c, _ in h]; url_self = BASE + "/" if rel == "index" else f"{BASE}/{rel}"
    mark("present", bool(h), rel)
    mark("self", any(u == url_self for _, u in h), rel)
    bad = []
    for c, u in h:
        tr = rel_of(u)
        if tr in idx and not any(rel_of(x) == rel for _, x in idx[tr]["hre"]): bad.append(tr)
    mark("reciprocal", not bad, rel, ",".join(bad[:2]))
    xd = [u for c, u in h if c == "x-default"]
    en_ver = next((u for c, u in h if c == "en"), None)
    mark("xdefault", len(xd) == 1 and (en_ver is None or xd[0] == en_ver), rel)
    badc = [c for c in codes if c != "x-default" and not (re.fullmatch(r"[a-z]{2}(-[A-Z]{2})?", c) and c[:2] in ISO639 and (len(c) == 2 or c[3:] in ISO3166))]
    mark("codes", not badc, rel, ",".join(badc))
    mark("unique", len(codes) == len(set(codes)), rel)
    badt = [u for _, u in h if rel_of(u) not in pages or rel_of(u) in REDIRECTED or pages[rel_of(u)]["noindex"]]
    mark("targets_ok", not badt, rel, ",".join(badt[:2]))
    badcan = [u for _, u in h if rel_of(u) in pages and pages[rel_of(u)]["canon"] != u]
    mark("canon_match", not badcan, rel, ",".join(badcan[:2]))
    mark("absolute", all(u.startswith(BASE + "/") for _, u in h), rel)
    mark("html_lang", p["html_lang"][:2] == p["lang"], rel, p["html_lang"])
    mark("content_lang", all(c[:2] == p["lang"] for c in p["content_lang"]), rel, ",".join(p["content_lang"]))
    mark("sitemap", sm_alt.get(rel) == sorted(h), rel)

total = sum(w for _, _, w in CHECKS)
score = sum(w * res[k][0] / res[k][1] for k, _, w in CHECKS if res[k][1])
by_slug = collections.defaultdict(set)
for rel, p in idx.items(): by_slug[p["slug"]].add(p["lang"])
full = sum(1 for s, ls in by_slug.items() if len(ls) == 5)

# language switcher: does the flag menu point to the same page in the other language?
sw_ok = sw_tot = 0
for rel, p in idx.items():
    m = re.search(r'dropdown-menu[^>]*>(.*?)</div>', p["t"], re.S)
    if not m: continue
    for href in re.findall(r'href="([^"]+)"', m.group(1)):
        sw_tot += 1
        target = href.replace("../", "").replace(".html", "")
        sw_ok += target.split("/")[-1] == p["slug"]

out = dict(score=round(score / total * 100, 1), pages=len(idx),
           checks=[dict(label=l, weight=w, passed=res[k][0], total=res[k][1], pct=round(100 * res[k][0] / max(1, res[k][1]), 1), examples=ex[k]) for k, l, w in CHECKS],
           clusters=len(by_slug), full_clusters=full,
           cluster_sizes=dict(collections.Counter(len(v) for v in by_slug.values())),
           codes=dict(collections.Counter(c for p in idx.values() for c, _ in p["hre"])),
           switcher_same_page_pct=round(100 * sw_ok / max(1, sw_tot), 1))
print(json.dumps(out, ensure_ascii=False, indent=1))
