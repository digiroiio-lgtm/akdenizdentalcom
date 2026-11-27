import re, sys, pathlib
def dec(h):
    k = int(h[:2], 16); return "".join(chr(int(h[i:i+2], 16) ^ k) for i in range(2, len(h), 2))
root = pathlib.Path(sys.argv[1]); n = 0
for f in root.rglob("*.html"):
    t = f.read_text("utf-8"); o = t
    t = re.sub(r'<(span|a)[^>]*class="__cf_email__"[^>]*data-cfemail="([0-9a-f]+)"[^>]*>\[email[^<]*protected\]</\1>', lambda m: dec(m.group(2)), t)
    t = re.sub(r'(?:https://akdenizdental\.com)?/cdn-cgi/l/email-protection#([0-9a-f]+)', lambda m: "mailto:" + dec(m.group(1)), t)
    t = re.sub(r'<script[^>]*cdn-cgi/scripts/[^>]*email-decode\.min\.js[^>]*></script>\s*', '', t)
    if t != o: f.write_text(t, "utf-8"); n += 1
print("files changed", n)
