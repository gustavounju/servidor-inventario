// Service Worker — Inventario GOLD
// Maneja instalación PWA + notificaciones push de Firebase Messaging

importScripts('https://www.gstatic.com/firebasejs/9.23.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/9.23.0/firebase-messaging-compat.js');

// Inicializar Firebase en el SW
firebase.initializeApp({
    apiKey: "AIzaSyC6PcD59xCNoqodWc3j3Xx-RkYaWRbUwHg",
    authDomain: "inventario-gold.firebaseapp.com",
    projectId: "inventario-gold",
    storageBucket: "inventario-gold.firebasestorage.app",
    messagingSenderId: "155956386088",
    appId: "1:155956386088:web:0aac3dcc29079442ff981d"
});

const messaging = firebase.messaging();

// Manejar mensajes en background (navegador cerrado / minimizado)
messaging.onBackgroundMessage((payload) => {
    console.log('[SW] Mensaje en background recibido:', payload);

    const notificationTitle = payload.notification?.title || 'Inventario GOLD';
    const notificationOptions = {
        body: payload.notification?.body || 'Hay una actualización.',
        icon: '/static/icon-192.png',
        badge: '/static/icon-192.png',
        vibrate: [200, 100, 200],
        data: { url: payload.data?.url || '/mobile' },
        actions: [
            { action: 'open', title: 'Ver tarea' }
        ]
    };

    self.registration.showNotification(notificationTitle, notificationOptions);
});

// Al hacer clic en la notificación → abrir /mobile
self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    const url = event.notification.data?.url || '/mobile';
    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
            for (const client of clientList) {
                if (client.url.includes('/mobile') && 'focus' in client) {
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
