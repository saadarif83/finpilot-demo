// Minimal service worker: no offline caching logic needed for a live demo,
// this just needs to exist and register for the browser to consider the
// app "installable" as a PWA.
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (event) => event.waitUntil(self.clients.claim()));
self.addEventListener('fetch', () => {}); // pass-through, no caching
