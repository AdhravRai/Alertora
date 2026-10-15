/* ==========================================================================
   ALERTORA AI — Service Worker (Offline Emergency Protocols & Survival Hub)
   Provides offline access to verified emergency instructions, first aid,
   hotlines, and survival checklists without treating live forecasts as static truth.
   ========================================================================== */

const CACHE_NAME = "alertora-offline-v2.6.0";

const STATIC_EMERGENCY_ASSETS = [
  "/",
  "/index.html",
  "/css/styles.css",
  "/js/mockData.js",
  "/js/api.js",
  "/js/app.js"
];

// 1. Install Event: Pre-cache core static emergency resources
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log("[ALERTORA SW] Pre-caching static emergency protocols & assets...");
      return cache.addAll(STATIC_EMERGENCY_ASSETS);
    }).then(() => {
      return self.skipWaiting();
    })
  );
});

// 2. Activate Event: Clean up outdated cache versions
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            console.log("[ALERTORA SW] Clearing obsolete cache:", key);
            return caches.delete(key);
          }
        })
      );
    }).then(() => {
      return self.clients.claim();
    })
  );
});

// 3. Fetch Event: Cache-First for static assets; Network-First with staleness for data
self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);

  // Never touch real-time Server-Sent Events (SSE)
  if (url.pathname.includes("/api/events/stream")) {
    return;
  }

  // Handle external CDN assets (Tailwind, Fonts, Leaflet) gracefully
  if (url.origin !== self.location.origin) {
    event.respondWith(
      caches.match(event.request).then((cached) => {
        return (
          cached ||
          fetch(event.request).then((networkRes) => {
            if (networkRes.status === 200) {
              const resClone = networkRes.clone();
              caches.open(CACHE_NAME).then((cache) => cache.put(event.request, resClone));
            }
            return networkRes;
          }).catch(() => {
            // Return empty or cached fallback if CDN offline
            return cached || new Response("", { status: 408, statusText: "Offline" });
          })
        );
      })
    );
    return;
  }

  // Dynamic API Endpoints: Network-First with Safe Offline Fallback
  // (Do NOT claim dynamic forecasts are live when served from cache)
  if (url.pathname.startsWith("/api/")) {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          if (response && response.status === 200 && event.request.method === "GET") {
            const resClone = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, resClone));
          }
          return response;
        })
        .catch(async () => {
          const cached = await caches.match(event.request);
          if (cached) {
            // Append header indicating cached/stale data
            const headers = new Headers(cached.headers);
            headers.set("X-Alertora-Data-Status", "CACHED_OFFLINE");
            return new Response(await cached.blob(), {
              status: cached.status,
              statusText: cached.statusText,
              headers: headers
            });
          }
          return new Response(
            JSON.stringify({
              offline: true,
              status: "OFFLINE",
              message: "Network offline. Displaying cached emergency safety protocols.",
              timestamp: new Date().toISOString()
            }),
            {
              headers: { "Content-Type": "application/json", "X-Alertora-Data-Status": "OFFLINE" }
            }
          );
        })
    );
    return;
  }

  // Core Static Emergency App Assets: Cache-First Strategy
  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached) {
        // Fetch in background to update cache for next visit
        fetch(event.request).then((networkRes) => {
          if (networkRes && networkRes.status === 200) {
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, networkRes));
          }
        }).catch(() => {/* Offline, background update ignored */});
        return cached;
      }
      return fetch(event.request).then((networkRes) => {
        if (networkRes && networkRes.status === 200) {
          const resClone = networkRes.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, resClone));
        }
        return networkRes;
      });
    })
  );
});
