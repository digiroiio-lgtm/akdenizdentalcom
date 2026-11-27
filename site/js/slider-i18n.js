/**
 * Slider i18n Typography & Localization Helper
 * Ensures structured spans (<span class="slider-title-line1">, <span class="slider-title-line2">)
 * and Bodoni Moda italic highlights remain intact without text overlapping.
 */
(function (global) {
  'use strict';

  var translations = {
    en: {
      eyebrow: "DENTAL CARE IN ANTALYA",
      title: '<span class="slider-title-line1">Your smile.</span><span class="slider-title-line2"><em class="slider-title-italic">Your confidence.</em></span>',
      description: 'Personalised dental care, with support at every step of your journey.',
      ctaPrimary: "Get Your Treatment Plan",
      ctaSecondary: "Explore Patient Results",
      tagline: "Real patient. Real smile.",
      whatsappPhone: "+905412483562"
    },
    tr: {
      eyebrow: "ANTALYA'DA DİŞ TEDAVİSİ",
      title: '<span class="slider-title-line1">Gülüşünüz.</span><span class="slider-title-line2"><em class="slider-title-italic">Özgüveniniz.</em></span>',
      description: 'Tedavi yolculuğunuzun her adımında tam destekle kişiselleştirilmiş diş sağlığı hizmeti.',
      ctaPrimary: "Tedavi Planınızı Alın",
      ctaSecondary: "Hasta Sonuçlarını İnceleyin",
      tagline: "Gerçek hasta. Gerçek gülüş.",
      whatsappPhone: "+905412483562"
    },
    de: {
      eyebrow: "ZAHNMEDIZIN IN ANTALYA",
      title: '<span class="slider-title-line1">Ihr Lächeln.</span><span class="slider-title-line2"><em class="slider-title-italic">Ihr Selbstvertrauen.</em></span>',
      description: 'Individuelle Zahnpflege mit persönlicher Betreuung bei jedem Schritt Ihrer Reise.',
      ctaPrimary: "Behandlungsplan anfordern",
      ctaSecondary: "Patientenergebnisse ansehen",
      tagline: "Echte Patienten. Echtes Lächeln.",
      whatsappPhone: "+905077854049"
    },
    pl: {
      eyebrow: "STOMATOLOGIA W ANTALYI",
      title: '<span class="slider-title-line1">Twój uśmiech.</span><span class="slider-title-line2"><em class="slider-title-italic">Twoja pewność siebie.</em></span>',
      description: 'Spersonalizowana opieka stomatologiczna ze wsparciem na każdym etapie leczenia.',
      ctaPrimary: "Uzyskaj plan leczenia",
      ctaSecondary: "Zobacz efekty pacjentów",
      tagline: "Prawdziwy pacjent. Prawdziwy uśmiech.",
      whatsappPhone: "+905077854049"
    },
    ro: {
      eyebrow: "STOMATOLOGIE ÎN ANTALYA",
      title: '<span class="slider-title-line1">Zâmbetul tău.</span><span class="slider-title-line2"><em class="slider-title-italic">Încrederea ta.</em></span>',
      description: 'Îngrijire dentară personalizată, cu sprijin continuu la fiecare pas al călătoriei tale.',
      ctaPrimary: "Obține planul de tratament",
      ctaSecondary: "Descoperă rezultatele",
      tagline: "Pacient real. Zâmbet real.",
      whatsappPhone: "+905077854049"
    },
    ru: {
      eyebrow: "СТОМАТОЛОГИЯ В АНТАЛЬЕ",
      title: '<span class="slider-title-line1">Ваша улыбка.</span><span class="slider-title-line2"><em class="slider-title-italic">Ваша уверенность.</em></span>',
      description: 'Индивидуальный стоматологический уход с заботой на каждом этапе вашего пути.',
      ctaPrimary: "Получить план лечения",
      ctaSecondary: "Результаты пациентов",
      tagline: "Реальный пациент. Реальная улыбка.",
      whatsappPhone: "+905077854049"
    }
  };

  function detectLocale() {
    var htmlLang = (document.documentElement.lang || 'en').toLowerCase().substring(0, 2);
    var path = window.location.pathname.toLowerCase();
    if (path.indexOf('/de') !== -1) return 'de';
    if (path.indexOf('/pl') !== -1) return 'pl';
    if (path.indexOf('/ro') !== -1) return 'ro';
    if (path.indexOf('/ru') !== -1) return 'ru';
    if (path.indexOf('/tr') !== -1) return 'tr';
    if (translations[htmlLang]) return htmlLang;
    return 'en';
  }

  global.AkdenizSliderI18n = {
    get: function (lang) {
      return translations[lang] || translations.en;
    },
    getCurrent: function () {
      return this.get(detectLocale());
    },
    data: translations
  };

})(typeof window !== 'undefined' ? window : this);
