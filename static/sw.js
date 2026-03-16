// Minimal Service Worker for PWA requirements
// All external Web Push logic has been removed to ensure privacy
self.addEventListener('install', (event) => {
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(self.clients.claim());
});
