// Exists only to make the app installable (Chrome's installability check
// requires a registered service worker with a fetch handler). Deliberately
// does no caching -- this app changes multiple times a day right now, so a
// cached app shell would just serve stale UI. Pure passthrough to network.
self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (event) => event.waitUntil(self.clients.claim()));
self.addEventListener("fetch", (event) => event.respondWith(fetch(event.request)));
