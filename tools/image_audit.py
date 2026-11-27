"""Internal image audit (content images only: between </header> and <footer>).
Usage: python3 tools/image_audit.py site [--json out.json]
"""
import re, sys, json, html, pathlib, collections
from PIL import Image

ROOT = pathlib.Path(sys.argv[1]); LANGS = ["en", "de", "pl", "ro", "ru"]
CYR = re.compile(r"[а-яА-ЯёЁ]")
EN_WORDS = re.compile(r"\b(the|and|of|for|with|before|after|dental|teeth|tooth|implants?|veneers?|crowns?|smile|treatment|clinic|patient)\b", re.I)
GENERIC_ALT = re.compile(r"^(image|img|photo|picture|logo|icon|banner|leczenia|\d+|[\w-]+\.(jpe?g|png|webp))$", re.I)
GENERIC_FILE = re.compile(r"(^img[-_]?\d|^image\d|^team-\d|^setp-\d|^service-\d|^portfolio-\d|^clinic-\d|^dsc|^img_|^photo|^untitled|^\d+$|^youtube-thumbnail\d)", re.I)
TYPE_DIRS = {"treatment": {"dental-implants", "all-on-4", "all-on-6", "hollywood-smile", "zirconium-crowns", "e-max"}}

def split(rel): return rel.split("/", 1) if rel.split("/")[0] in LANGS[1:] else ("en", rel)

def alt_lang_ok(alt, lang):
    if not alt: return True
    if lang == "ru": return bool(CYR.search(alt)) or not EN_WORDS.search(alt)
    if CYR.search(alt): return False
    if lang == "en": return True
    # non-English page: English stop-words with no local diacritics = probably English alt
    return not (len(EN_WORDS.findall(alt)) >= 2 and not re.search(r"[äöüßąćęłńóśźżăâîșț]", alt, re.I))

img_info = {}
def info(path):
    if path not in img_info:
        p = ROOT / path
        if not p.exists(): img_info[path] = None
        else:
            try:
                with Image.open(p) as im: w, h = im.size
            except Exception: w = h = 0
            img_info[path] = dict(kb=p.stat().st_size // 1024, w=w, h=h, ext=p.suffix.lower())
    return img_info[path]

rows = []; used = set(); pages_imgs = collections.Counter()
for f in sorted(ROOT.rglob("*.html")):
    rel = str(f.relative_to(ROOT))[:-5]; lang, slug = split(rel)
    if slug == "thank-you": continue
    t = f.read_text("utf-8")
    if "</header>" not in t: continue
    head = t.split("</header>", 1)[0]
    body = t.split("</header>", 1)[1].split("<footer", 1)[0]
    body_nc = re.sub(r"<!--.*?-->", "", body, flags=re.S)
    has_imgobj = '"ImageObject"' in t
    og = re.findall(r'<meta\s+property="og:image"\s+content="([^"]*)"', head)
    for i, m in enumerate(re.finditer(r"<img\b([^>]*)>", body_nc, re.S)):
        a = m.group(1)
        src = (re.findall(r'\bsrc="([^"]*)"', a) or [""])[0]
        if not src or src.startswith(("http", "data:", "//")): continue
        path = re.sub(r"^(\.\./)+", "", src.split("?")[0]).lstrip("/")
        if "flag-" in path or "whatsapp" in path: continue
        used.add(path); pages_imgs[rel] += 1
        alt_m = re.search(r'\balt="([^"]*)"', a); alt = html.unescape(alt_m.group(1)).strip() if alt_m else None
        inf = info(path)
        rows.append(dict(page=rel, lang=lang, slug=slug, idx=i, src=path, alt=alt,
            has_alt=alt_m is not None, alt_empty=alt_m is not None and not alt, alt_generic=bool(alt and (GENERIC_ALT.match(alt) or len(alt) < 8)),
            alt_lang_ok=alt_lang_ok(alt or "", lang), alt_long=bool(alt and len(alt) > 140),
            wh=bool(re.search(r'\bwidth="\d+"', a) and re.search(r'\bheight="\d+"', a)),
            lazy='loading="lazy"' in a, srcset="srcset=" in a, missing=inf is None,
            modern=bool(inf and inf["ext"] in (".webp", ".avif")), kb=inf["kb"] if inf else 0, w=inf["w"] if inf else 0,
            generic_file=bool(GENERIC_FILE.search(pathlib.Path(path).stem)),
            in_figure=bool(re.search(r"<figure[^>]*>(?:(?!</figure>).)*$", body_nc[:m.start()], re.S)),
            imgobj=has_imgobj, og=bool(og and "logo" not in og[0])))

# orphan image files (never referenced anywhere)
all_html = "".join(p.read_text("utf-8") for p in ROOT.rglob("*.html")) + "".join(p.read_text("utf-8") for p in ROOT.rglob("*.css"))
img_files = [p for p in (ROOT / "images").rglob("*") if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg", ".avif")]
orphans = [str(p.relative_to(ROOT)) for p in img_files if p.name not in all_html]
orphan_kb = sum((ROOT / o).stat().st_size for o in orphans) // 1024

N = len(rows); U = {r["src"] for r in rows}
def pct(k, neg=False): return round(100 * sum((not r[k]) if neg else r[k] for r in rows) / max(1, N), 1)
uniq = [dict(src=s, **img_info[s]) for s in U if img_info.get(s)]
big = sorted([u for u in uniq if u["kb"] > 200], key=lambda u: -u["kb"])
huge_px = [u for u in uniq if u["w"] > 1600]
sitemap = (ROOT / "sitemap.xml").read_text("utf-8")
first_lazy = [r for r in rows if r["idx"] == 0 and r["lazy"]]
summary = {
    "img_occurrences": N, "unique_images": len(U), "pages_with_images": len(pages_imgs),
    "alt_missing_%": pct("has_alt", True), "alt_empty_%": pct("alt_empty"), "alt_generic_%": pct("alt_generic"),
    "alt_wrong_language_%": round(100 * sum(1 for r in rows if not r["alt_lang_ok"]) / N, 1),
    "width_height_%": pct("wh"), "lazy_%": pct("lazy"), "srcset_%": pct("srcset"), "modern_format_unique_%": round(100 * sum(u["ext"] in (".webp", ".avif") for u in uniq) / max(1, len(uniq)), 1),
    "missing_files": sorted({r["src"] for r in rows if r["missing"]}),
    "over_200kb": [(u["src"], u["kb"]) for u in big[:15]], "over_200kb_count": len(big),
    "over_1600px": [(u["src"], u["w"]) for u in huge_px[:10]],
    "generic_filenames_%": round(100 * sum(r["generic_file"] for r in rows) / N, 1),
    "treatment_images_in_blog_folder": sorted({r["src"] for r in rows if r["slug"] in TYPE_DIRS["treatment"] and "/blog/" in r["src"]}),
    "in_figure_or_caption_%": pct("in_figure"),
    "pages_with_ImageObject_%": round(100 * sum(1 for p in pages_imgs if any(r["imgobj"] for r in rows if r["page"] == p)) / max(1, len(pages_imgs)), 1),
    "pages_with_real_og_image_%": round(100 * sum(1 for p in pages_imgs if any(r["og"] for r in rows if r["page"] == p)) / max(1, len(pages_imgs)), 1),
    "image_sitemap": "<image:image>" in sitemap,
    "first_image_lazy_count": len(first_lazy),
    "orphan_files": len(orphans), "orphan_kb": orphan_kb,
    "total_unique_kb": sum(u["kb"] for u in uniq),
}
by_lang = {}
for l in LANGS:
    rs = [r for r in rows if r["lang"] == l]
    if rs: by_lang[l] = dict(n=len(rs), alt_missing=sum(not r["has_alt"] or r["alt_empty"] for r in rs), alt_generic=sum(r["alt_generic"] for r in rs),
                             alt_wrong_lang=sum(not r["alt_lang_ok"] for r in rs), no_wh=sum(not r["wh"] for r in rs), no_srcset=sum(not r["srcset"] for r in rs))
summary["by_lang"] = by_lang
summary["examples_wrong_lang"] = [(r["page"], r["alt"][:60]) for r in rows if not r["alt_lang_ok"]][:8]
summary["examples_generic"] = [(r["page"], r["alt"]) for r in rows if r["alt_generic"]][:8]
summary["examples_missing_alt"] = [(r["page"], r["src"]) for r in rows if not r["has_alt"] or r["alt_empty"]][:8]
print(json.dumps(summary, ensure_ascii=False, indent=1))
if "--json" in sys.argv:
    json.dump(dict(summary=summary, rows=rows, orphans=orphans), open(sys.argv[sys.argv.index("--json") + 1], "w"), ensure_ascii=False, indent=1)
