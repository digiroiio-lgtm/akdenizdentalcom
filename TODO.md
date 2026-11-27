# Yapılacaklar (TODO)

Durum etiketleri: ⏸️ Beklemede · ⏳ Devam ediyor · ✅ Tamam

---

## ⏸️ Canlıya alma: DNS kayıtlarının Cloudflare'de Vercel'e aktarılması
**Durum:** Beklemede (kullanıcı kararıyla ertelendi — henüz canlıya alınmayacak)
**Eklenme:** 2026-11-27

Vercel tarafı hazır, sadece DNS değişikliği bekliyor. Bu adım yapılana kadar akdenizdental.com eski sunucuda (Plesk + Cloudflare) çalışmaya devam eder.

### Hazır olanlar
- Vercel projesi: `akdenizdentalcom` (team: tortilla), production deploy READY
- Domainler projeye eklendi ve doğrulandı: `akdenizdental.com` (ana) ve `www.akdenizdental.com` (→ ana domaine 308 yönlendirme)
- DNS değişmediği sürece bunların canlı siteye etkisi yok

### Yapılacak adımlar (Cloudflare → akdenizdental.com → DNS → Records)
1. Değişiklikten önce mevcut DNS kayıtlarının ekran görüntüsünü al (geri dönüş için).
2. `@` (akdenizdental.com) **A** kaydı → `76.76.21.21` (fazla A kayıtları silinir, tek kayıt). Proxy: **DNS only** (gri bulut).
3. `www` → **CNAME** `cname.vercel-dns.com`. Proxy: **DNS only**.
4. **MX / TXT / mail kayıtlarına dokunulmaz** (info@akdenizdental.com e-postaları).
5. Kaydet; 5–30 dk içinde yayılır.

### Geçiş sonrası kontrol listesi
- [ ] SSL sertifikası aktif (https)
- [ ] Eski URL'ler: `/dental-implants.html` → `/dental-implants`, `/ru/index` 200, eski görsel adresleri → `images/treatments/...` (301)
- [ ] Form gönderimi → 5 dilde teşekkür sayfası
- [ ] reCAPTCHA canlı domainde hatasız görünüyor ("Invalid domain for site key" yok) ve form gönderimi kabul ediliyor. Site anahtarı akdenizdental.com için tanımlı; test adresi (vercel.app) listede olmadığı için testte hata vermesi normal. Gerekirse Google reCAPTCHA admin → Domains listesine domain eklenir.
- [ ] JivoChat, WhatsApp butonu, GA4/GTM, Meta Pixel, Yandex Metrika çalışıyor
- [ ] 5 dilde örnek sayfalar masaüstü + mobil (Playwright)
- [ ] `python3 tools/site_report.py site`, `tools/hreflang_audit.py`, `tools/image_audit.py` temiz
- [ ] Search Console: sitemap.xml gönderimi + kritik sayfaların indekslenmesi (mülke erişim gerekli)
- [ ] Eski sunucu 1–2 hafta yedek olarak açık kalır, sonra kapatılır

### Geri dönüş
Cloudflare'de eski A kayıtlarını (ekran görüntüsündeki) geri koymak yeterli.

---

## ⏸️ PR'ı main'e birleştirme
**Durum:** Beklemede — production şu an `claude/peaceful-curie-uwnz7e` dalından yayında. Canlıya alma kararıyla birlikte değerlendirilecek.
PR: https://github.com/digiroiio-lgtm/akdenizdentalcom/pull/1

## ⏸️ Search Console erişimi
**Durum:** Beklemede — bağlı hesabın akdenizdental.com mülküne erişimi yok. Erişim verilince sitemap gönderimi, indeksleme ve 7 günlük hata raporu.
