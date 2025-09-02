// Minimal service worker - no caching, just for PWA installation and push notifications
// Version: 1.0.3 - Update this to force service worker update

// Install event
self.addEventListener('install', event => {
  console.log('[ServiceWorker] Installing v1.0.3');
  // Skip waiting to activate immediately
  self.skipWaiting();
});

// Activate event
self.addEventListener('activate', event => {
  console.log('[ServiceWorker] Activating');
  event.waitUntil(
      // Clean up any old caches from previous versions
      caches.keys().then(cacheNames => {
        return Promise.all(
            cacheNames.map(cacheName => {
              console.log('[ServiceWorker] Removing old cache:', cacheName);
              return caches.delete(cacheName);
            })
        );
      }).then(() => {
        // Take control of all clients immediately
        return clients.claim();
      })
  );
});

// Handle messages from the app
self.addEventListener('message', event => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    console.log('[ServiceWorker] Received skip waiting message');
    self.skipWaiting();
  }

  if (event.data && event.data.type === 'CLIENTS_CLAIM') {
    console.log('[ServiceWorker] Claiming clients');
    self.clients.claim();
  }
});

// Push notification handling
self.addEventListener('push', event => {
  const options = {
    body: 'Motion detected!',
    icon: '/icon-192.png',
    badge: '/icon-192.png',
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

// Notification click handling
self.addEventListener('notificationclick', event => {
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
