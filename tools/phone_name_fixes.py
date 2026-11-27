"""Unify phone numbers and the surname spelling across all pages.
Usage: python3 tools/phone_name_fixes.py site seo-content"""
import re, sys, pathlib
S = r"[\s()\-.]*"
PHONES = {  # old groups -> new groups (after the 90 country code)
    ("541", "248", "35", "30"): ("541", "248", "35", "62"),
    ("507", "705", "40", "49"): ("507", "785", "40", "49"),
    ("505", "926", "40", "49"): ("507", "785", "40", "49"),
    ("507", "452", "40", "49"): ("507", "785", "40", "49"),
    ("554", "987", "40", "49"): ("507", "785", "40", "49"),
}
NAMES = {"Büyüktarakcı": "Büyüktarakçı", "BÜYÜKTARAKCI": "BÜYÜKTARAKÇI"}
counts = {}
for d in sys.argv[1:]:
    for f in pathlib.Path(d).rglob("*"):
        if f.suffix not in (".html", ".json", ".txt", ".xml"): continue
        t = f.read_text("utf-8"); o = t
        for old, new in PHONES.items():
            pat = re.compile(r"(?:(?<=90)|(?<!\d))" + S.join(f"({g})" if i == 0 else g for i, g in enumerate(old)).replace(S, "(" + S + ")") + r"(?!\d)")
            def rep(m, new=new):
                seps = m.groups()[1:]
                return new[0] + seps[0] + new[1] + seps[1] + new[2] + seps[2] + new[3]
            t, n = pat.subn(rep, t); counts[old] = counts.get(old, 0) + n
        for a, b in NAMES.items():
            counts[a] = counts.get(a, 0) + t.count(a); t = t.replace(a, b)
        if t != o: f.write_text(t, "utf-8")
for k, v in counts.items(): print(k, v)
