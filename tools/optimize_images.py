"""Optimize content images on every page (between </header> and <footer>). Idempotent.
- JPG/PNG -> WebP sibling (kept only if smaller), 480w WebP for images wider than 600px, srcset/sizes
- width/height from the real file, loading="lazy" + decoding="async" (first content image: eager + fetchpriority=high)
- alt texts: fill empty / generic / wrong-language alts from tools/image_alts.json {src: {lang: alt}}
- ImageObject JSON-LD (<script id="ad-images">) for the page's content images
Usage: python3 tools/optimize_images.py
"""
import re, json, html, pathlib
from PIL import Image

REPO = pathlib.Path(__file__).resolve().parent.parent; SITE = REPO / "site"; BASE = "https://akdenizdental.com"
LANGS = ["en", "de", "pl", "ro", "ru"]; IN_LANG = {"en": "en-GB", "de": "de-DE", "pl": "pl-PL", "ro": "ro-RO", "ru": "ru-RU"}
ALTS = json.loads((REPO / "tools" / "image_alts.json").read_text("utf-8")) if (REPO / "tools" / "image_alts.json").exists() else {}
CYR = re.compile(r"[а-яА-ЯёЁ]")
EN_WORDS = re.compile(r"\b(the|and|of|for|with|before|after|dental|teeth|tooth|implants?|veneers?|crowns?|smile|treatment|clinic|patient)\b", re.I)
SKIP = ("flag-", "whatsapp", "revolution/", "images/blog/og/", ".svg", ".gif")

def split(rel): return rel.split("/", 1) if rel.split("/")[0] in LANGS[1:] else ("en", rel)
def bad_alt(alt, lang):
    if not alt or len(alt) < 8 or re.fullmatch(r"(image|img|photo|logo|leczenia|contact|antalya|inlay|onlay|krone|crown)", alt, re.I): return True
    if lang == "ru": return not CYR.search(alt) and bool(EN_WORDS.search(alt))
    if CYR.search(alt): return True
    if lang != "en" and len(EN_WORDS.findall(alt)) >= 2 and not re.search(r"[äöüßąćęłńóśźżăâîșț]", alt, re.I): return True
    return False

dims = {}
def size_of(p):
    if p not in dims:
        with Image.open(SITE / p) as im: dims[p] = im.size
    return dims[p]

def ensure_webp(path):
    """returns (best_path, small_path_or_None)"""
    src = SITE / path; ext = src.suffix.lower()
    if ext in (".jpg", ".jpeg", ".png"):
        w = src.with_suffix(".webp")
        if not w.exists():
            with Image.open(src) as im:
                im = im.convert("RGBA") if im.mode in ("RGBA", "LA", "P") else im.convert("RGB")
                im.save(w, "WEBP", quality=82, method=6)
        if w.stat().st_size < src.stat().st_size: path = str(w.relative_to(SITE))
        else: w.unlink()
    p = SITE / path; small = None
    if p.suffix.lower() == ".webp":
        w0, h0 = size_of(path)
        if w0 > 600:
            s = p.with_name(p.stem + "-480.webp")
            if not s.exists():
                with Image.open(p) as im: im.resize((480, round(h0 * 480 / w0)), Image.LANCZOS).save(s, "WEBP", quality=80, method=6)
            small = str(s.relative_to(SITE))
    return path, small

def set_attr(tag, name, value):
    if re.search(rf'\s{name}="[^"]*"', tag): return re.sub(rf'(\s{name}=")[^"]*(")', lambda m: m.group(1) + value + m.group(2), tag, count=1)
    return tag[:-1].rstrip("/").rstrip() + f' {name}="{value}">'

stats = dict(pages=0, webp=0, srcset=0, wh=0, lazy=0, alt=0, schema=0)
for f in sorted(SITE.rglob("*.html")):
    rel = str(f.relative_to(SITE))[:-5]; lang, slug = split(rel)
    t = f.read_text("utf-8")
    if "</header>" not in t or "<footer" not in t: continue
    head, rest = t.split("</header>", 1); body, foot = rest.split("<footer", 1)
    prefix = "" if lang == "en" else "../"
    images = []; first = [True]
    def fix(m):
        tag = m.group(0)
        if "<!--" in tag: return tag
        src = (re.findall(r'\bsrc="([^"]*)"', tag) or [""])[0]
        if not src or src.startswith(("http", "//", "data:")) or any(s in src for s in SKIP): return tag
        path = re.sub(r"^(\.\./)+", "", src)
        if not (SITE / path).exists(): return tag
        orig_path = path
        in_cover = 'class="ad-cover"' in body[max(0, m.start() - 40):m.start()]
        if not in_cover:
            new_path, small = ensure_webp(path)
            if new_path != path:
                tag = tag.replace(src, prefix + new_path); stats["webp"] += 1; path = new_path
            if small and "srcset=" not in tag:
                w0 = size_of(path)[0]
                tag = set_attr(tag, "srcset", f"{prefix}{small} 480w, {prefix}{path} {w0}w")
                tag = set_attr(tag, "sizes", f"(max-width: 600px) 480px, {min(w0, 800)}px"); stats["srcset"] += 1
        w, h = size_of(path)
        if not re.search(r'\swidth="\d+"', tag) or not re.search(r'\sheight="\d+"', tag):
            tag = set_attr(set_attr(tag, "width", str(w)), "height", str(h)); stats["wh"] += 1
        if first[0]:
            tag = re.sub(r'\sloading="lazy"', "", tag)
            if "fetchpriority=" not in tag: tag = set_attr(tag, "fetchpriority", "high")
            first[0] = False
        else:
            if 'loading="' not in tag: tag = set_attr(tag, "loading", "lazy"); stats["lazy"] += 1
        if "decoding=" not in tag: tag = set_attr(tag, "decoding", "async")
        alt = html.unescape((re.findall(r'\balt="([^"]*)"', tag) or [""])[0]).strip()
        key = orig_path if orig_path in ALTS else path
        if key in ALTS and lang in ALTS[key] and (bad_alt(alt, lang) or ALTS[key].get("_force")):
            alt = ALTS[key][lang]; tag = set_attr(tag, "alt", html.escape(alt, quote=True)); stats["alt"] += 1
        images.append((path, alt, w, h))
        return tag
    body2 = re.sub(r"<img\b[^>]*>", fix, body, flags=re.S)
    # ImageObject structured data
    url = BASE + "/" if rel == "index" else f"{BASE}/{rel}"
    seen = set(); objs = []
    for path, alt, w, h in images:
        if path in seen or not alt: continue
        seen.add(path)
        objs.append({"@type": "ImageObject", "contentUrl": f"{BASE}/{path}", "url": f"{BASE}/{path}", "caption": alt, "name": alt,
                     "width": w, "height": h, "inLanguage": IN_LANG[lang], "creditText": "Akdeniz Dental Clinic",
                     "copyrightNotice": "© Akdeniz Dental Clinic", "creator": {"@type": "Organization", "name": "Akdeniz Dental Clinic", "url": BASE + "/"}})
        if len(objs) >= 12: break
    head = re.sub(r'\s*<script type="application/ld\+json" id="ad-images">.*?</script>', "", head, flags=re.S)
    if objs and slug != "thank-you":
        objs[0]["representativeOfPage"] = True
        block = {"@context": "https://schema.org", "@type": "WebPage", "@id": url + "#webpage", "url": url, "primaryImageOfPage": objs[0], "image": objs}
        head = head.replace("</head>", '\t<script type="application/ld+json" id="ad-images">\n' + json.dumps(block, ensure_ascii=False, indent=1) + "\n\t</script>\n</head>", 1)
        stats["schema"] += 1
    new = head + "</header>" + body2 + "<footer" + foot
    if new != t: f.write_text(new, "utf-8"); stats["pages"] += 1
print(stats)
