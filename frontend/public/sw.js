// AI WebGen Service Worker
// Version 1.0.0

const CACHE_NAME = 'ai-webgen-v1.0.0';
const STATIC_CACHE = 'ai-webgen-static-v1';
const DYNAMIC_CACHE = 'ai-webgen-dynamic-v1';

// Files to cache immediately
const STATIC_FILES = [
  '/',
  '/static/js/bundle.js',
  '/static/css/main.css',
  '/manifest.json',
  '/android-chrome-192x192.png',
  '/android-chrome-512x512.png',
  '/apple-touch-icon.png',
  '/favicon.ico'
];

// API endpoints to cache
const API_CACHE_PATTERNS = [
  /\/api\/$/,
  /\/api\/create-referral/,
  /\/api\/preview\//
];

// Install event - cache static files
self.addEventListener('install', function(event) {
  console.log('🚀 Service Worker installing...');
  
  event.waitUntil(
    caches.open(STATIC_CACHE).then(function(cache) {
      console.log('📦 Caching static files...');
      return cache.addAll(STATIC_FILES);
    }).then(function() {
      console.log('✅ Static files cached successfully');
      return self.skipWaiting();
    }).catch(function(error) {
      console.error('❌ Failed to cache static files:', error);
    })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', function(event) {
  console.log('🔄 Service Worker activating...');
  
  event.waitUntil(
    caches.keys().then(function(cacheNames) {
      return Promise.all(
        cacheNames.map(function(cacheName) {
          if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE) {
            console.log('🗑️ Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(function() {
      console.log('✅ Service Worker activated');
      return self.clients.claim();
    })
  );
});

// Fetch event - serve cached content when offline
self.addEventListener('fetch', function(event) {
  const requestUrl = new URL(event.request.url);
  
  // Handle API requests
  if (requestUrl.pathname.startsWith('/api/')) {
    event.respondWith(
      handleApiRequest(event.request)
    );
    return;
  }
  
  // Handle static files
  event.respondWith(
    caches.match(event.request).then(function(response) {
      // Return cached version if available
      if (response) {
        return response;
      }
      
      // Fetch from network and cache if successful
      return fetch(event.request).then(function(response) {
        // Only cache successful responses
        if (response.status === 200) {
          const responseClone = response.clone();
          caches.open(DYNAMIC_CACHE).then(function(cache) {
            cache.put(event.request, responseClone);
          });
        }
        return response;
      }).catch(function(error) {
        console.log('🌐 Network request failed:', error);
        
        // Return offline page for navigation requests
        if (event.request.destination === 'document') {
          return caches.match('/').then(function(response) {
            return response || new Response('Application offline', {
              status: 503,
              statusText: 'Service Unavailable'
            });
          });
        }
        
        throw error;
      });
    })
  );
});

// Handle API requests with caching strategy
function handleApiRequest(request) {
  const url = new URL(request.url);
  
  // Cache GET requests for specific endpoints
  if (request.method === 'GET') {
    const shouldCache = API_CACHE_PATTERNS.some(pattern => pattern.test(url.pathname));
    
    if (shouldCache) {
      return caches.open(DYNAMIC_CACHE).then(function(cache) {
        return cache.match(request).then(function(response) {
          if (response) {
            // Return cached response and update in background
            fetch(request).then(function(networkResponse) {
              if (networkResponse.status === 200) {
                cache.put(request, networkResponse.clone());
              }
            }).catch(function() {
              // Ignore network errors when updating cache
            });
            return response;
          }
          
          // No cache, fetch from network
          return fetch(request).then(function(networkResponse) {
            if (networkResponse.status === 200) {
              cache.put(request, networkResponse.clone());
            }
            return networkResponse;
          });
        });
      });
    }
  }
  
  // For non-cacheable requests, just fetch from network
  return fetch(request).catch(function(error) {
    console.log('🌐 API request failed:', error);
    
    // Return a generic error response
    return new Response(JSON.stringify({
      error: 'Application is offline',
      message: 'Please check your internet connection and try again.'
    }), {
      status: 503,
      statusText: 'Service Unavailable',
      headers: {
        'Content-Type': 'application/json'
      }
    });
  });
}

// Handle push notifications (for future use)
self.addEventListener('push', function(event) {
  if (event.data) {
    const data = event.data.json();
    const options = {
      body: data.body || 'Votre site web est prêt !',
      icon: '/android-chrome-192x192.png',
      badge: '/android-chrome-192x192.png',
      vibrate: [200, 100, 200],
      data: data.data || {},
      actions: [
        {
          action: 'view',
          title: 'Voir',
          icon: '/android-chrome-192x192.png'
        },
        {
          action: 'close',
          title: 'Fermer'
        }
      ]
    };
    
    event.waitUntil(
      self.registration.showNotification(data.title || 'AI WebGen', options)
    );
  }
});

// Handle notification clicks
self.addEventListener('notificationclick', function(event) {
  event.notification.close();
  
  if (event.action === 'view') {
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});

// Periodic background sync (for future use)
self.addEventListener('sync', function(event) {
  if (event.tag === 'background-sync') {
    event.waitUntil(
      // Perform background operations
      console.log('🔄 Background sync triggered')
    );
  }
});

// Share target handling (for future use)
self.addEventListener('message', function(event) {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

console.log('🤖 AI WebGen Service Worker loaded successfully');