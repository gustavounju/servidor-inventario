// Service Worker — Inventario GOLD
// Maneja instalación PWA

self.addEventListener('push', (event) => {
    let data = {};
    try { data = event.data ? event.data.json() : {}; } catch (_) { data = {}; }
    const accentMarkers = {
        blue: '🟦',
        mint: '🟩',
        amber: '🟧',
        rose: '🟥',
        violet: '🟪'
    };
    const marker = accentMarkers[data.accent] || '🟦';
    const isTask = data.kind === 'new_task' || Boolean(data.task_id);
    const title = data.title || (isTask ? `${marker} Nueva tarea` : 'Inventario');
    const lines = Array.isArray(data.lines) ? data.lines : [];
    const formattedBody = lines.length
        ? lines
            .filter((line) => line && line.value)
            .slice(0, 8)
            .map((line) => `${line.icon || '•'} ${line.label || 'Dato'}: ${line.value}`)
            .join('\n')
        : (data.body || 'Hay una actualización de tareas.');
    const options = {
        body: formattedBody,
        icon: '/static/icon-192.png',
        badge: '/static/icon-192.png',
        tag: data.task_id ? `task-${data.task_id}` : 'inventario-notification',
        renotify: true,
        silent: false,
        requireInteraction: isTask,
        vibrate: isTask ? [180, 80, 180, 80, 260] : [120, 80, 120],
        data: {
            url: data.url || '/tecnicos',
            task_id: data.task_id || null,
            kind: data.kind || 'notification'
        },
        actions: isTask ? [
            { action: 'open', title: 'Abrir tarea' },
            { action: 'tecnicos', title: 'Panel técnicos' }
        ] : []
    };
    event.waitUntil(self.registration.showNotification(title, options));
});

// Al hacer clic en la notificación (lanzada por el cliente interno)
self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    const action = event.action || 'open';
    const url = action === 'tecnicos' ? '/tecnicos' : (event.notification.data?.url || '/tecnicos');
    const targetUrl = new URL(url, self.location.origin).href;
    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
            for (const client of clientList) {
                if ((client.url.includes('/mobile') || client.url.includes('/tecnicos')) && 'focus' in client) {
                    if (action !== 'tecnicos' && 'navigate' in client) {
                        return client.navigate(targetUrl).then((navigatedClient) => {
                            return navigatedClient ? navigatedClient.focus() : client.focus();
                        });
                    }
                    return client.focus();
                }
            }
            if (clients.openWindow) return clients.openWindow(targetUrl);
        })
    );
});

// Lifecycle
self.addEventListener('install', (event) => { self.skipWaiting(); });
self.addEventListener('activate', (event) => { event.waitUntil(self.clients.claim()); });
self.addEventListener('fetch', (event) => {
    event.respondWith(fetch(event.request));
});
