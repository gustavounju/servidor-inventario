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

self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    event.waitUntil(
        clients.matchAll({ type: 'window' }).then((clientList) => {
            for (const client of clientList) {
                if (client.url === '/' && 'focus' in client) {
                    return client.focus();
                }
            }
            if (clients.openWindow) {
                return clients.openWindow(event.notification.data?.url || '/mobile');
            }
        })
    );
});
