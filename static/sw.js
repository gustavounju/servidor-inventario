// Minimal Service Worker for background notifications
self.addEventListener('install', (event) => {
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(self.clients.claim());
});

self.addEventListener('push', (event) => {
    const data = event.data ? event.data.json() : {};
    const title = data.title || "Inventario GOLD";
    const options = {
        body: data.body || "Nueva notificación",
        icon: '/static/favicon.ico',
        badge: '/static/favicon.ico',
        vibrate: [200, 100, 200],
        tag: 'task-pool-alert',
        renotify: true
    };
    event.waitUntil(self.registration.showNotification(title, options));
});
