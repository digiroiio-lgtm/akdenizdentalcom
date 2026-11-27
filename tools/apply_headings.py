"""Apply H1 / H2 rewrites. Idempotent. Usage: python3 tools/apply_headings.py headings.json
Each entry: {"path", "h1": new or "", "h2_changes": [{"old","new"}], "h2_add": "" or text}
h2_add is inserted as a section heading before the first paragraph of the main content (after the H1 title bar).
"""
import sys, re, json, html, pathlib
SITE = pathlib.Path(__file__).resolve().parent.parent / "site"
def plain(s): return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()
def esc(s): return html.escape(s, quote=False)

rows = json.loads(pathlib.Path(sys.argv[1]).read_text("utf-8")); stats = dict(h1=0, h2=0, add=0, miss=[])
for r in rows:
    f = SITE / (r["path"] + ".html"); t = f.read_text("utf-8")
    head, rest = t.split("</header>", 1); body, foot = rest.split("<footer", 1)
    if r.get("h1"):
        m = re.search(r"<h1([^>]*)>(.*?)</h1>", body, re.S)
        if m and plain(m.group(2)) != r["h1"]:
            body = body[:m.start()] + f"<h1{m.group(1)}>{esc(r['h1'])}</h1>" + body[m.end():]; stats["h1"] += 1
    for ch in r.get("h2_changes", []):
        for m in re.finditer(r"<h2([^>]*)>(.*?)</h2>", body, re.S):
            if plain(m.group(2)) == ch["old"].strip():
                body = body[:m.start()] + f"<h2{m.group(1)}>{esc(ch['new'])}</h2>" + body[m.end():]; stats["h2"] += 1; break
        else:
            if ch["new"] not in plain(body): stats["miss"].append((r["path"], ch["old"][:40]))
    add = r.get("h2_add")
    if add and esc(add) not in body:
        h1 = re.search(r"</h1>", body)
        start = h1.end() if h1 else 0
        p = re.search(r"<p[ >]", body[start:])
        if p:
            i = start + p.start()
            body = body[:i] + f'<h2 class="pbmit-title ad-h2-added">{esc(add)}</h2>\n' + body[i:]; stats["add"] += 1
        else: stats["miss"].append((r["path"], "h2_add"))
    t2 = head + "</header>" + body + "<footer" + foot
    if t2 != t: f.write_text(t2, "utf-8")
print(stats)
