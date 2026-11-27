"""Give images descriptive file names / proper folders, update every reference, add 301 redirects.
Idempotent: skips entries whose source no longer exists. Usage: python3 tools/rename_images.py
Mapping is kept in tools/image_renames.json (old -> new, paths relative to site/).
"""
import json, re, shutil, pathlib
REPO = pathlib.Path(__file__).resolve().parent.parent; SITE = REPO / "site"
MAP_FILE = REPO / "tools" / "image_renames.json"

T = "images/treatments/"
RENAMES = {
    # treatment images living in the blog folder -> images/treatments/ (also fixes "implnats" typo)
    "images/blog/all-on-4-dental-implants-before-and-after-turkey-1.jpg": T + "all-on-4-full-arch-before-after-case-1.jpg",
    "images/blog/all-on-4-dental-implants-before-and-after-turkey-2.jpg": T + "all-on-4-full-arch-before-after-case-2.jpg",
    "images/blog/all-on-4-dental-implants-before-and-after-turkey-3.jpg": T + "all-on-4-full-arch-before-after-case-3.jpg",
    "images/blog/all-on-4-dental-implnats-before-after-turkey-4.jpg": T + "all-on-4-full-arch-before-after-case-4.jpg",
    "images/blog/all-on-6-dental-implnats-before-after-turkey-1.jpg": T + "all-on-6-full-arch-before-after-case-1.jpg",
    "images/blog/all-on-6-dental-implnats-before-after-turkey-2.jpg": T + "all-on-6-full-arch-before-after-case-2.jpg",
    "images/blog/all-on-4-dental-implants-turkey.jpg": T + "all-on-4-dental-implants-diagram.jpg",
    "images/blog/dental-implant-crown.jpg": T + "dental-implant-crown.jpg",
    "images/blog/dental-implants-abutment-screw.jpg": T + "dental-implant-abutment-screw.jpg",
    "images/blog/dental-implants-abutment.jpg": T + "dental-implant-abutment.jpg",
    "images/blog/dental-implants-body.jpg": T + "dental-implant-body.jpg",
    "images/blog/parts-of-dental-implants.jpg": T + "parts-of-a-dental-implant.jpg",
    "images/blog/types-of-dental-implants.jpg": T + "types-of-dental-implants.jpg",
    # text-free localized copies of those
    "images/blog/clean/inline-all-on-4-dental-implants-before-and-after-turkey-1.webp": T + "all-on-4-full-arch-before-after-case-1.webp",
    "images/blog/clean/inline-all-on-4-dental-implants-before-and-after-turkey-2.webp": T + "all-on-4-full-arch-before-after-case-2.webp",
    "images/blog/clean/inline-all-on-4-dental-implants-before-and-after-turkey-3.webp": T + "all-on-4-full-arch-before-after-case-3.webp",
    "images/blog/clean/inline-all-on-4-dental-implnats-before-after-turkey-4.webp": T + "all-on-4-full-arch-before-after-case-4.webp",
    "images/blog/clean/inline-all-on-6-dental-implnats-before-after-turkey-1.webp": T + "all-on-6-full-arch-before-after-case-1.webp",
    "images/blog/clean/inline-all-on-6-dental-implnats-before-after-turkey-2.webp": T + "all-on-6-full-arch-before-after-case-2.webp",
    "images/blog/clean/inline-all-on-4-diagram.webp": T + "all-on-4-dental-implants-diagram.webp",
    "images/blog/clean/inline-parts-of-dental-implants.webp": T + "parts-of-a-dental-implant.webp",
    "images/blog/clean/inline-types-of-dental-implants.webp": T + "types-of-dental-implants.webp",
    "images/blog/clean/inline-dental-implants-abutment.webp": T + "dental-implant-abutment.webp",
    "images/blog/clean/inline-dental-implants-body.webp": T + "dental-implant-body.webp",
    "images/blog/clean/inline-emax-laminate-veneer-diagram.webp": T + "e-max-laminate-veneer-diagram.webp",
    # generic theme names
    "images/homepage-1/team/team-1.jpg": "images/homepage-1/team/dr-ali-burak-bozkurt.jpg",
    "images/homepage-1/team/team-2.jpg": "images/homepage-1/team/dr-mustafa-akca.jpg",
    "images/homepage-1/team/team-3.jpg": "images/homepage-1/team/dr-mehmet-onur-merey.jpg",
    "images/homepage-1/team/team-5.jpg": "images/homepage-1/team/dr-omer-isen.jpg",
    "images/homepage-1/img-02.png": "images/homepage-1/akdeniz-dental-dentists-antalya.png",
    "images/homepage-1/img-013.jpg": "images/homepage-1/patient-video-testimonial.jpg",
    "images/icon/setp-01.jpg": "images/icon/step-1-contact-akdeniz-dental.jpg",
    "images/icon/setp-02.jpg": "images/icon/step-2-online-consultation.jpg",
    "images/icon/setp-03.jpg": "images/icon/step-3-travel-to-antalya.jpg",
    "images/icon/setp-04.jpg": "images/icon/step-4-treatment-in-antalya.jpg",
}
for i, slug in enumerate(["dental-implants", "all-on-4", "all-on-6", "hollywood-smile", "zirconium-crowns", "e-max"], 1):
    RENAMES[f"images/homepage-1/service/service-0{i}.jpg"] = f"images/homepage-1/service/{slug}-antalya.jpg"
    RENAMES[f"images/homepage-1/service/service-0{i}b.jpg"] = f"images/homepage-1/service/{slug}-antalya-treatment.jpg"
for n in range(1, 11):
    RENAMES[f"images/homepage-1/portfolio/youtube-thumbnail{n}.jpg"] = f"images/homepage-1/portfolio/patient-video-testimonial-{n}.jpg"

done = json.loads(MAP_FILE.read_text()) if MAP_FILE.exists() else {}
pairs = {}
for old, new in RENAMES.items():
    for suffix in ("", "-480"):  # move responsive siblings too
        o = old.replace(".webp", f"{suffix}.webp") if suffix else old
        n = new.replace(".webp", f"{suffix}.webp") if suffix else new
        if suffix and not old.endswith(".webp"): continue
        if (SITE / o).exists():
            (SITE / n).parent.mkdir(parents=True, exist_ok=True)
            shutil.move(SITE / o, SITE / n); pairs[o] = n
done.update(pairs)
MAP_FILE.write_text(json.dumps(done, indent=1))

# update references in pages, css, specs
files = list(SITE.rglob("*.html")) + list(SITE.rglob("*.css")) + list((REPO / "covers").rglob("*.json")) + [SITE / "llms.txt"]
changed = 0
for f in files:
    t = f.read_text("utf-8"); o = t
    for old, new in pairs.items():
        t = t.replace(old, new)
    if t != o: f.write_text(t, "utf-8"); changed += 1

# 301 redirects for public, previously-live image URLs (not for our new clean copies)
vj = REPO / "vercel.json"; cfg = json.loads(vj.read_text())
red = cfg.setdefault("redirects", []); have = {r["source"] for r in red}
for old, new in done.items():
    if "/clean/" in old: continue
    if "/" + old not in have:
        red.append({"source": "/" + old, "destination": "/" + new, "permanent": True})
vj.write_text(json.dumps(cfg, indent=2) + "\n")
print("moved", len(pairs), "files; updated", changed, "files; redirects", len(red))
