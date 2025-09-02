import { clientsClaim } from 'workbox-core';
import { precacheAndRoute, cleanupOutdatedCaches } from 'workbox-precaching';
import { registerRoute, NavigationRoute } from 'workbox-routing';
import { createHandlerBoundToURL } from 'workbox-precaching';

// Take control of all pages immediately
clientsClaim();

// Precache all assets
precacheAndRoute(self.__WB_MANIFEST);

// Clean up old caches
cleanupOutdatedCaches();

// Handle navigation requests
registerRoute(new NavigationRoute(createHandlerBoundToURL('/index.html')));

// Skip waiting when requested
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