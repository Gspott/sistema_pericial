const CACHE_NAME = "sistema-pericial-v5";
const STATIC_ASSETS = [
    "/favicon.ico",
    "/apple-touch-icon.png",
    "/manifest.json",
    "/static/mobile.css",
    "/static/pwa.js",
    "/static/icon-192.png",
    "/static/icon-512.png"
];

self.addEventListener("install", (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
    );
    self.skipWaiting();
});

self.addEventListener("activate", (event) => {
    event.waitUntil(
        caches.keys().then((keys) =>
            Promise.all(
                keys
                    .filter((key) => key !== CACHE_NAME)
                    .map((key) => caches.delete(key))
            )
        )
    );
    self.clients.claim();
});

self.addEventListener("fetch", (event) => {
    const request = event.request;

    if (request.method !== "GET") {
        return;
    }

    const url = new URL(request.url);

    if (request.mode === "navigate") {
        event.respondWith(fetch(request));
        return;
    }

    const isCacheableAsset =
        url.pathname.startsWith("/static/") ||
        url.pathname.startsWith("/uploads/") ||
        url.pathname === "/favicon.ico" ||
        url.pathname === "/apple-touch-icon.png" ||
        url.pathname === "/manifest.json";

    if (isCacheableAsset) {
        event.respondWith(
            caches.match(request).then((cached) => {
                return (
                    cached ||
                    fetch(request).then((response) => {
                        if (response.ok) {
                            const responseClone = response.clone();
                            caches.open(CACHE_NAME).then((cache) => cache.put(request, responseClone));
                        }
                        return response;
                    })
                );
            })
        );
        return;
    }

    event.respondWith(fetch(request));
});
