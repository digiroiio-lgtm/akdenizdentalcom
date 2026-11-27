"""Point the header language switcher to the SAME page in the other language (fallback: that language's homepage)
and align <meta name="content-language"> with the page language. Idempotent.
Usage: python3 tools/lang_switch.py site
"""
import re, sys, pathlib
ROOT = pathlib.Path(sys.argv[1])
LANGS = ["en", "de", "pl", "ro", "ru"]
FLAG = {"uk": "en", "de": "de", "pl": "pl", "ro": "ro", "ru": "ru"}

def split(rel): return rel.split("/", 1) if rel.split("/")[0] in LANGS[1:] else ("en", rel)
pages = {str(p.relative_to(ROOT))[:-5] for p in ROOT.rglob("*.html")}

def href_for(cur_lang, target_lang, slug):
    up = "" if cur_lang == "en" else "../"
    if target_lang == "en":
        return up + ("" if slug == "index" else slug) if (slug in pages) else (up or "./")
    tgt = f"{target_lang}/{slug}"
    return up + (tgt if tgt in pages else f"{target_lang}/index")

sw = cl = 0
for rel in sorted(pages):
    lang, slug = split(rel); f = ROOT / (rel + ".html"); t = f.read_text("utf-8"); o = t
    def fix_menu(m):
        def fix_a(a):
            flag = re.search(r"flag-(uk|de|pl|ro|ru)\.png", a.group(0))
            if not flag: return a.group(0)
            h = href_for(lang, FLAG[flag.group(1)], slug) or "./"
            return re.sub(r'href="[^"]*"', f'href="{h}"', a.group(0), count=1)
        return re.sub(r'<a [^>]*class="dropdown-item"[^>]*>.*?</a>', fix_a, m.group(0), flags=re.S)
    t = re.sub(r'<div class="dropdown-menu[^"]*">.*?</div>', fix_menu, t, flags=re.S)
    if t != o: sw += 1
    t2 = re.sub(r'(<meta name="content-language" content=")[^"]*(")', rf"\g<1>{lang}\2", t)
    if t2 != t: cl += 1
    if t2 != o: f.write_text(t2, "utf-8")
print("switcher updated", sw, "content-language fixed", cl)
