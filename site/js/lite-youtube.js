/* Lightweight YouTube embeds: load the real player only when the visitor clicks. */
document.addEventListener('click', function (e) {
  var b = e.target.closest('.ad-yt');
  if (!b || b.querySelector('iframe')) return;
  var f = document.createElement('iframe');
  f.src = 'https://www.youtube.com/embed/' + b.dataset.id + '?autoplay=1&rel=0';
  f.title = b.getAttribute('aria-label') || 'YouTube video';
  f.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share';
  f.referrerPolicy = 'strict-origin-when-cross-origin';
  f.allowFullscreen = true;
  b.innerHTML = ''; b.appendChild(f);
});
