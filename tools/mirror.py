import re, sys, os, urllib.request, urllib.parse, collections
BASE = "https://akdenizdental.com"
urls_file, out = sys.argv[1], sys.argv[2]
seen, failed = set(), []
q = collections.deque()

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 site-mirror"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read(), r.headers.get_content_type()

def local_path(path):
    path = urllib.parse.unquote(path.split("?")[0].split("#")[0])
    if path in ("", "/"): return "index.html"
    p = path.lstrip("/")
    if p.endswith("/"): p += "index.html"
    if not os.path.splitext(p)[1]: p += ".html"
    return p

def enqueue(abs_url):
    u = urllib.parse.urlparse(abs_url)
    if u.netloc not in ("akdenizdental.com", "www.akdenizdental.com"): return
    if u.path.startswith("/cdn-cgi/"): return
    key = local_path(u.path)
    if key in seen: return
    seen.add(key); q.append((BASE + urllib.parse.quote(urllib.parse.unquote(u.path)), key))

for line in open(urls_file):
    if line.strip(): enqueue(line.strip())
enqueue(BASE + "/robots.txt"); enqueue(BASE + "/sitemap.xml")

ATTR = re.compile(r'''(?:src|href|data-src|data-bg|data-lazyload|poster|content)\s*=\s*["']([^"']+)["']''', re.I)
SRCSET = re.compile(r'''srcset\s*=\s*["']([^"']+)["']''', re.I)
CSSURL = re.compile(r'''url\(\s*['"]?([^'")]+)['"]?\s*\)''', re.I)
JSSTR = re.compile(r'''["']((?:\.\./|/)?(?:images|img|assets|revolution|fonts|css|js|video)/[^"'\s]+)["']''')

while q:
    url, key = q.popleft()
    try:
        data, ctype = fetch(url)
    except Exception as e:
        failed.append((url, str(e))); continue
    dest = os.path.join(out, key)
    os.makedirs(os.path.dirname(dest) or out, exist_ok=True)
    open(dest, "wb").write(data)
    if key.endswith((".html", ".css", ".js", ".xml")):
        text = data.decode("utf-8", "ignore")
        refs = ATTR.findall(text) + CSSURL.findall(text) + JSSTR.findall(text)
        for s in SRCSET.findall(text): refs += [p.strip().split(" ")[0] for p in s.split(",")]
        for r in refs:
            r = r.strip()
            if r.startswith(("data:", "mailto:", "tel:", "javascript:", "#", "{")) or not r: continue
            if key.endswith(".js") and not r.startswith(("/", "../", "images", "img", "assets", "revolution", "fonts", "css", "js", "video")): continue
            base_url = BASE + "/" + key
            enqueue(urllib.parse.urljoin(base_url, r))
print("saved", len(seen) - len(failed), "failed", len(failed))
for f in failed: print("FAIL", *f)
