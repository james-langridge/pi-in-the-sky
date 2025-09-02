import { clientsClaim } from 'workbox-core';

// Auto-update behavior - immediately activate and take control
self.skipWaiting();
clientsClaim();

// No caching - service worker exists only for PWA installation and push notifications

// Handle skip waiting message (for manual update if needed)
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});


// Push notification handling - matching the old implementation
self.addEventListener('push', event => {
  console.log('[ServiceWorker] Push notification received', event);

  const options = {
    body: 'Motion detected!',
    icon: '/pwa-192x192.png',
    badge: '/pwa-64x64.png',
    vibrate: [200, 100, 200],
    tag: 'motion-alert',
    renotify: true,
    requireInteraction: false,
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    }
  };

  if (event.data) {
    try {
      const data = event.data.json();
      options.body = data.body || options.body;
      if (data.title) {
        event.waitUntil(
          self.registration.showNotification(data.title, options)
        );
        return;
      }
    } catch (e) {
      console.error('[ServiceWorker] Error parsing push data:', e);
    }
  }

  event.waitUntil(
    self.registration.showNotification('Pi Camera Alert', options)
  );
});

// Notification click handling - matching the old implementation
self.addEventListener('notificationclick', event => {
  console.log('[ServiceWorker] Notification click received');
  event.notification.close();

  event.waitUntil(
    clients.matchAll({
      type: 'window',
      includeUncontrolled: true
    }).then(clientList => {
      // Focus if already open
      for (const client of clientList) {
        if (client.url.includes(self.registration.scope) && 'focus' in client) {
          return client.focus();
        }
      }
      // Open new window if not open
      if (clients.openWindow) {
        return clients.openWindow('/');
      }
    })
  );
});
