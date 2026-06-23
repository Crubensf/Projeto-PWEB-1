// Service worker — Van Já (PWA, etapa 7)
// v3: network-first para navegação (HTML) — garante que mudanças de CSP/código
// aplicam na hora. Não intercepta requisições cross-origin (tiles de mapa,
// Leaflet, fontes) — deixa o browser buscar direto, sem cache interferindo.
const CACHE = 'vanja-v3';

const ASSETS = [
  '/index.html',
  '/css/style.css',
  '/js/utils.js',
  '/js/app.js',
  '/manifest.json',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(ASSETS).catch(() => {}))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((nomes) =>
        Promise.all(nomes.filter((n) => n !== CACHE).map((n) => caches.delete(n)))
      )
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);

  // Cross-origin (tiles do mapa, unpkg, fontes, API em outra porta): não toca.
  if (url.origin !== self.location.origin) return;

  // API same-origin: sempre rede.
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(fetch(req));
    return;
  }

  // Navegação/HTML: network-first (sempre pega versão fresca; cai no cache offline).
  const isHTML =
    req.mode === 'navigate' ||
    (req.headers.get('accept') || '').includes('text/html');
  if (isHTML) {
    event.respondWith(
      fetch(req)
        .then((resp) => {
          const clone = resp.clone();
          caches.open(CACHE).then((c) => c.put(req, clone));
          return resp;
        })
        .catch(() => caches.match(req).then((c) => c || caches.match('/index.html')))
    );
    return;
  }

  // Demais estáticos same-origin: stale-while-revalidate.
  event.respondWith(
    caches.match(req).then((cached) => {
      const fetchPromise = fetch(req)
        .then((resp) => {
          if (resp.ok) {
            const clone = resp.clone();
            caches.open(CACHE).then((c) => c.put(req, clone));
          }
          return resp;
        })
        .catch(() => cached);
      return cached || fetchPromise;
    })
  );
});
