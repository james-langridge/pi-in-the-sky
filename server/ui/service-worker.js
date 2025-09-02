const CACHE_NAME = 'pi-camera-v1';
const urlsToCache = [
  '/',
  '/app.css',
  '/app.js',
  '/js/api.js',
  '/js/controls.js',
  '/js/motion.js',
  '/manifest.json'
];

// Install event - cache essential files
self.addEventListener('install', event => {
  console.log('[ServiceWorker] Installing new version');
  event.waitUntil(
      caches.open(CACHE_NAME)
          .then(cache => {
            console.log('[ServiceWorker] Caching app shell');
            return cache.addAll(urlsToCache);
          })
          // Don't skip waiting - let the user control when to update
          .then(() => console.log('[ServiceWorker] Install complete'))
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  console.log('[ServiceWorker] Activating new version');
  event.waitUntil(
      caches.keys().then(cacheNames => {
        return Promise.all(
            cacheNames.map(cacheName => {
              if (cacheName !== CACHE_NAME) {
                console.log('[ServiceWorker] Removing old cache:', cacheName);
                return caches.delete(cacheName);
              }
            })
        );
      }).then(() => {
        console.log('[ServiceWorker] Activation complete');
        // Take control of all clients
        return clients.claim();
      })
  );
});

// Fetch event - network first for critical resources
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);

  // Skip caching for video feed and API calls
  if (url.pathname.includes('/video_feed') ||
      url.pathname.includes('/api/') ||
      url.pathname.includes('/health')) {
    event.respondWith(fetch(event.request));
    return;
  }

  // Network-first strategy for CSS/JS files to ensure updates are applied
  if (url.pathname.endsWith('.css') || url.pathname.endsWith('.js')) {
    event.respondWith(
        fetch(event.request)
            .then(fetchResponse => {
              // Clone the response as it can only be consumed once
              const responseToCache = fetchResponse.clone();
              
              // Update cache with new version
              if (fetchResponse.status === 200) {
                caches.open(CACHE_NAME).then(cache => {
                  cache.put(event.request, responseToCache);
                });
              }
              
              return fetchResponse;
            })
            .catch(() => {
              // Fall back to cache if network fails
              return caches.match(event.request);
            })
    );
    return;
  }

  // Cache-first strategy for other assets (manifest, icons)
  event.respondWith(
      caches.match(event.request)
          .then(response => {
            // Return cached version or fetch from network
            return response || fetch(event.request).then(fetchResponse => {
              // Don't cache non-successful responses
              if (!fetchResponse || fetchResponse.status !== 200 || fetchResponse.type === 'opaque') {
                return fetchResponse;
              }

              // Clone the response as it can only be consumed once
              const responseToCache = fetchResponse.clone();

              // Update cache with new version
              caches.open(CACHE_NAME).then(cache => {
                cache.put(event.request, responseToCache);
              });

              return fetchResponse;
            });
          })
          .catch(() => {
            // Offline fallback could go here
            console.log('[ServiceWorker] Fetch failed for:', event.request.url);
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
