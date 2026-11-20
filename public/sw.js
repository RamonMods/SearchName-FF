/* --- Service worker do SearchName (PWA): HTML sempre da rede, assets do cache. --- */
const CACHE = "searchname-v2";
const ASSETS = [
  "./",
  "./index.html",
  "./search/",
  "./search/index.html",
  "./styles.css",
  "./site.css",
  "./search/search.css",
  "./app.js",
  "./search/search.js",
  "./manifest.json",
  "./assets/favicon.svg",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(ASSETS)).catch(() => {})
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;

  const url = new URL(req.url);

  /* --- API de busca: sempre rede, nunca cache. --- */
  if (url.pathname === "/search" && url.searchParams.has("name")) {
    return;
  }

  /* --- navegação: rede primeiro, cache só como reserva offline. --- */
  if (req.mode === "navigate") {
    event.respondWith(
      fetch(req)
        .then((resp) => {
          if (resp.ok && url.origin === self.location.origin) {
            const copia = resp.clone();
            caches.open(CACHE).then((c) => c.put(req, copia));
          }
          return resp;
        })
        .catch(() => caches.match(req).then((cached) => cached || caches.match("./index.html")))
    );
    return;
  }

  /* --- assets: cache primeiro, com atualização em segundo plano. --- */
  event.respondWith(
    caches.match(req).then((cached) => {
      const rede = fetch(req)
        .then((resp) => {
          if (resp.ok && url.origin === self.location.origin) {
            const copia = resp.clone();
            caches.open(CACHE).then((c) => c.put(req, copia));
          }
          return resp;
        })
        .catch(() => cached);
      return cached || rede;
    })
  );
});
