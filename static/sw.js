// Minimal Service Worker for PWA requirements
// All external Web Push logic has been removed to ensure privacy

// Required 'install' event
self.addEventListener('install', (event) => {
    self.skipWaiting();
});

// Required 'activate' event
self.addEventListener('activate', (event) => {
    event.waitUntil(self.clients.claim());
});

// Required 'fetch' event for Chrome installability
// This satisfies the requirement of having a fetch handler, even if it just uses the network.
self.addEventListener('fetch', (event) => {
    // Default network behavior
    event.respondWith(fetch(event.request));
});
