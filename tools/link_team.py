"""Link doctor names on <lang>/our-team.html to doctor profile pages that exist in that language.
Doctor identity comes from the card photo (mapping taken from the English team page links).
Usage: python3 tools/link_team.py site"""
import re, sys, pathlib
ROOT = pathlib.Path(sys.argv[1])
SPLIT = r'(?=<article class="pbmit-team-style)'
img2slug = {}
for card in re.split(SPLIT, (ROOT / "our-team.html").read_text("utf-8")):
    im = re.search(r'team/([^"/]+\.(?:jpg|png|webp))', card); a = re.search(r'href="([a-z-]+?)(?:\.html)?"', card)
    if im and a: img2slug[im.group(1)] = a.group(1)
print("map", img2slug)
for lang in ["de", "ro", "ru", "pl"]:
    f = ROOT / lang / "our-team.html"; parts = re.split(SPLIT, f.read_text("utf-8")); n = 0
    for i, card in enumerate(parts):
        im = re.search(r'team/([^"/]+\.(?:jpg|png|webp))', card)
        slug = img2slug.get(im.group(1)) if im else None
        if not slug or not (ROOT / lang / f"{slug}.html").exists(): continue
        def rep(m):
            if "<a" in m.group(2): return m.group(0)
            return f'{m.group(1)}<a href="{slug}.html">{m.group(2).strip()}</a>{m.group(3)}'
        new = re.sub(r'(<h3 class="pbmit-team-title">\s*)(.*?)(\s*</h3>)', rep, card, count=1, flags=re.S)
        if new != card: n += 1; parts[i] = new
    f.write_text("".join(parts), "utf-8"); print(lang, "newly linked", n, "total links", "".join(parts).count('pbmit-team-title">') and len(re.findall(r'pbmit-team-title">\s*<a', "".join(parts))))
