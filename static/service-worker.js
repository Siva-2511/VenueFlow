const CACHE_NAME = 'venueflow-v1';
const urlsToCache = [
  '/login',
  '/user',
  '/static/css/style.css',
  '/static/js/main.js',
  '/static/favicon.ico'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        return Promise.allSettled(urlsToCache.map(url => {
          return cache.add(url).catch(err => console.warn('SW cache.add failed for:', url, err));
        }));
      })
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => response || fetch(event.request))
  );
});
