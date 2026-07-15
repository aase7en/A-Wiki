// A-Wiki Live Dashboard Service Worker — progressive enhancement for offline use.
// Strategy: cache-first for static assets (HTML, JS CDN), network-first for API.
// Cache name bumped on each dashboard version change.
const CACHE_NAME = 'awiki-dashboard-v1';
const STATIC_ASSETS = [
  '/',
  '/dashboard',
  // vis-network CDN is cached on first load (not precached to avoid blocking).
];

// Install: precache the static shell.
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
      .then(() => self.skipWaiting())
      .catch(() => {/* ignore precache failures — SW still installs */})
  );
});

// Activate: clean old caches.
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(
      keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))
    )).then(() => self.clients.claim())
  );
});

// Fetch: route by request type.
self.addEventListener('fetch', (event) => {
  const req = event.request;
  const url = new URL(req.url);

  // Skip non-GET (POST/PUT — never cache writes).
  if (req.method !== 'GET') return;

  // SSE (EventSource) — never cache, always live.
  if (url.pathname === '/events') return;

  // API calls: network-first, fallback to cache (stale data better than nothing offline).
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(req).then((resp) => {
        // Cache successful API responses for offline fallback.
        if (resp.ok) {
          const clone = resp.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(req, clone)).catch(() => {});
        }
        return resp;
      }).catch(() => caches.match(req).then((cached) => cached || new Response(
        JSON.stringify({ error: 'offline', message: 'ไม่สามารถเชื่อมต่อได้ — ออฟไลน์' }),
        { status: 503, headers: { 'Content-Type': 'application/json' } }
      )))
    );
    return;
  }

  // Static assets (HTML, CDN JS): cache-first, fallback to network.
  event.respondWith(
    caches.match(req).then((cached) => {
      if (cached) return cached;
      return fetch(req).then((resp) => {
        // Cache same-origin + CDN responses for offline.
        if (resp.ok && (url.origin === self.location.origin || url.hostname.includes('unpkg.com'))) {
          const clone = resp.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(req, clone)).catch(() => {});
        }
        return resp;
      });
    })
  );
});
