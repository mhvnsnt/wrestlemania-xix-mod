const CACHE = 'wmxix-testbed-v1';
const FILES = [
  'index.html', 'app.js', 'manifest.json',
  'skeleton.json', 'head_000.obj', 'arena_02.obj',
  'anim_idle.json', 'anim_walk.json', 'anim_punch.json',
  'anim_kick.json', 'anim_grapple.json'
];
self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(FILES)).then(() => self.skipWaiting()));
});
self.addEventListener('fetch', e => {
  e.respondWith(caches.match(e.request).then(r => r || fetch(e.request)));
});
