// Service Worker — Inventario GOLD
// Maneja instalación PWA

self.addEventListener('push', (event) => {
    let data = {};
    try { data = event.data ? event.data.json() : {}; } catch (_) { data = {}; }
    const title = data.title || 'Inventario';
    const options = {
        body: data.body || 'Hay una actualización de tareas.',
        icon: '/static/icon-192.png',
        badge: '/static/icon-192.png',
        tag: data.task_id ? `task-${data.task_id}` : 'inventario-notification',
        renotify: true,
        silent: false,
        vibrate: [120, 80, 120],
        data: { url: data.url || '/tecnicos' }
    };
    event.waitUntil(self.registration.showNotification(title, options));
});

// Al hacer clic en la notificación (lanzada por el cliente interno)
self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    const url = event.notification.data?.url || '/mobile';
    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
            for (const client of clientList) {
                if ((client.url.includes('/mobile') || client.url.includes('/tecnicos')) && 'focus' in client) {
                    return client.focus();
                }
            }
            if (clients.openWindow) return clients.openWindow(url);
        })
    );
});

// Lifecycle
self.addEventListener('install', (event) => { self.skipWaiting(); });
self.addEventListener('activate', (event) => { event.waitUntil(self.clients.claim()); });
self.addEventListener('fetch', (event) => {
    event.respondWith(fetch(event.request));
});
