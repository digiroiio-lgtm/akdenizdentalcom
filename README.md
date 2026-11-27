# akdenizdental.com — 1:1 klon

Canlı sitenin (akdenizdental.com) birebir statik kopyası: 5 dil (EN, RU, PL, DE, RO), 151 sayfa, tüm görseller/CSS/JS.

## Yapı
- `site/` — yayınlanan dosyalar (canlı sitedeki yollarla aynı; `sayfa.html` → `/sayfa`)
- `vercel.json` — Vercel ayarı (`.html` uzantısız temiz URL'ler)
- `tools/mirror.py` — canlı siteden yeniden indirme script'i
- `tools/cfemail.py` — Cloudflare'in gizlediği e-posta adreslerini düz metne çevirir

## Yeniden indirme
```bash
python3 tools/mirror.py urls.txt site   # urls.txt: sitemap'teki URL listesi
python3 tools/cfemail.py site
```

## Notlar
- İletişim formları submit-form.com'a gider; sunucu tarafı kod yok.
- Canlı sitede de 404 veren birkaç tema dosyası (revolution slider ikonları vb.) klonda da yok.

## SEO / GEO düzenlemeleri
- `seo-content/out_*.json` — dil başına yeni title, description, H1, H2 ve SSS içerikleri
- `tools/seo_apply.py` — bu içerikleri + teknik düzeltmeleri siteye uygular (hreflang, canonical, og etiketleri, şema, sitemap, kopya sayfalar)
- `site/robots.txt` AI tarayıcılarına açık, `site/llms.txt` AI asistanları için klinik özeti
- Script'i yalnızca orijinal (ham) dosyalar üzerinde bir kez çalıştırın: `python3 tools/seo_apply.py site seo-content`
