// Minimal service worker for PWA installation and push notifications
// No caching since the app requires network connectivity anyway

self.addEventListener('install', event => {
  // Immediately activate
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  // Clean up any old caches from previous versions
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          console.log('Removing old cache:', cacheName);
          return caches.delete(cacheName);
        })
      );
    }).then(() => {
      // Take control of all clients immediately
      return clients.claim();
    })
  );
});

// No fetch handling - let all requests go to network
// The app is useless offline anyway since it needs camera stream

// Push notification handling for motion detection
self.addEventListener('push', event => {
  const options = {
    body: 'Motion detected!',
    icon: '/icon-192.png',
    badge: '/icon-192.png',
    vibrate: [200, 100, 200],
    tag: 'motion-alert',
    renotify: true,
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    }
  };

  if (event.data) {
    const data = event.data.json();
    options.body = data.body || options.body;
    if (data.title) {
      event.waitUntil(
        self.registration.showNotification(data.title, options)
      );
      return;
    }
  }

  event.waitUntil(
    self.registration.showNotification('Pi Camera Alert', options)
  );
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  
  // Open the app when notification is clicked
  event.waitUntil(
    clients.matchAll({ type: 'window' }).then(clientList => {
      // Focus if already open
      for (const client of clientList) {
        if (client.url === '/' && 'focus' in client) {
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