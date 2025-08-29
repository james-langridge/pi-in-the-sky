const CACHE_NAME = 'pi-camera-v1';
const urlsToCache = [
  '/',
  '/js/api.js',
  '/js/controls.js'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', event => {
  // Skip caching for video feed and API endpoints
  if (event.request.url.includes('/video_feed') || 
      event.request.url.includes('/health') ||
      event.request.url.includes('/presets') ||
      event.request.url.includes('/apply_preset') ||
      event.request.url.includes('/api/')) {
    return;
  }

  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Cache hit - return response
        if (response) {
          return response;
        }
        return fetch(event.request);
      })
  );
});

self.addEventListener('activate', event => {
  const cacheWhitelist = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

// Push notification handling
self.addEventListener('push', event => {
  if (!event.data) {
    console.log('Push event but no data');
    return;
  }

  let notification;
  try {
    notification = event.data.json();
  } catch (e) {
    notification = {
      title: 'Pi Camera Alert',
      body: event.data.text()
    };
  }

  const options = {
    body: notification.body || 'Motion detected',
    icon: notification.icon || '/icon-192.png',
    badge: notification.badge || '/badge-72.png',
    vibrate: [200, 100, 200],
    data: notification.data || {},
    requireInteraction: false,
    actions: [
      { action: 'view', title: 'View Camera' },
      { action: 'dismiss', title: 'Dismiss' }
    ]
  };

  event.waitUntil(
    self.registration.showNotification(
      notification.title || 'Motion Detected',
      options
    )
  );
});

// Handle notification clicks
self.addEventListener('notificationclick', event => {
  event.notification.close();

  if (event.action === 'view' || !event.action) {
    // Open the camera interface
    event.waitUntil(
      clients.matchAll({ type: 'window', includeUncontrolled: true })
        .then(clientList => {
          // Check if there's already a window open
          for (let client of clientList) {
            if (client.url.includes(self.location.origin) && 'focus' in client) {
              return client.focus();
            }
          }
          // Open a new window if none found
          if (clients.openWindow) {
            return clients.openWindow('/');
          }
        })
    );
  }
});