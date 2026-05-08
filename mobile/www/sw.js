const CACHE_NAME = 'gojo-sentinel-v1';
const ASSETS = [
  './',
  './index.html',
  './styles.css',
  './app.js',
  './chart.js',
  './logo_final.png',
  './fonts.css'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(ASSETS))
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request).then(response => {
      return response || fetch(event.request);
    })
  );
});
