import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { VitePWA } from 'vite-plugin-pwa'

/**
 * En développement, le serveur Vite proxifie /api et /storage vers le backend
 * Laravel (http://127.0.0.1:8000 par défaut, c'est-à-dire `php artisan serve`).
 *
 * La cible est modifiable sans toucher au code :
 *   API_PROXY_TARGET=http://localhost:8000 npm run dev
 */
const proxy = {
  '/api': {
    target: process.env.API_PROXY_TARGET || 'http://127.0.0.1:8000',
    changeOrigin: true,
  },
  // Images téléversées depuis l'admin (disque « public » de Laravel,
  // servis par /storage/... après `php artisan storage:link`)
  '/storage': {
    target: process.env.API_PROXY_TARGET || 'http://127.0.0.1:8000',
    changeOrigin: true,
  },
}

export default defineConfig(({ command }) => {
  // En dev, Vite sert les fichiers à la volée : rien à précharger dans
  // dev-dist (d'où l'avertissement Workbox) → globPatterns vide en dev,
  // préchargement complet de l'app shell lors du build de production.
  const isBuild = command === 'build'

  return {
    plugins: [
      vue(),

      /* ------------------------------------------------------------------
       | PWA — Dar Lila installable comme une application               |
       |                                                                   |
       | • App shell préchargée (build) : ouverture quasi instantanée,    |
       |   même en 3G faible.                                             |
       | • API catalogue (GET) : réseau d'abord, cache en repli — la      |
       |   boutique reste consultable hors-ligne / connexion lente.       |
       | • Images (Bunny CDN inclus) : cache prioritaire, 150 max,        |
       |   expiration 30 jours, auto-nettoyage par le navigateur.         |
       | • Les commandes (POST /api/orders) et l'admin ne sont JAMAIS     |
       |   mis en cache.                                                   |
       | • Mise à jour automatique (autoUpdate) : les clients reçoivent   |
       |   la nouvelle version au rechargement suivant.                   |
       ------------------------------------------------------------------ */
      VitePWA({
        registerType: 'autoUpdate',
        includeAssets: ['apple-touch-icon.png'],
        manifest: {
          id: '/',
          name: 'Planet Kids — Khemici Shop',
          short_name: 'Planet Kids',
          description:
            "Poussettes, cosmétiques bébé et habillement enfant — livrés dans toute l'Algérie. Commandez en un clic via WhatsApp.",
          lang: 'fr',
          dir: 'auto',
          theme_color: '#2d3590',
          background_color: '#ffffff',
          display: 'standalone',
          orientation: 'portrait',
          start_url: '/',
          scope: '/',
          icons: [
            { src: '/pwa-192x192.png', sizes: '192x192', type: 'image/png' },
            { src: '/pwa-512x512.png', sizes: '512x512', type: 'image/png' },
            { src: '/pwa-512-maskable.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
          ],
          screenshots: [
            {
              src: '/pwa-screenshot-boutique.png',
              sizes: '390x844',
              type: 'image/png',
              form_factor: 'narrow',
              label: 'La boutique Planet Kids',
            },
            {
              src: '/pwa-screenshot-lots.png',
              sizes: '390x844',
              type: 'image/png',
              form_factor: 'narrow',
              label: 'Nos lots à prix réduit',
            },
          ],
        },
        workbox: {
          clientsClaim: true,
          skipWaiting: true,
          globPatterns: isBuild
            ? ['**/*.{js,css,html,svg,woff2,png,webp}']
            : [],
          navigateFallback: '/index.html',
          navigateFallbackDenylist: [/^\/api\//, /^\/storage\//],
          maximumFileSizeToCacheInBytes: 4 * 1024 * 1024,
          runtimeCaching: [
            {
              // Catalogue public (produits, lots, réglages…) : réseau d'abord,
              // cache en repli après 4 s de réseau sans réponse.
              urlPattern: ({ url, request }) =>
                request.method === 'GET'
                && url.pathname.startsWith('/api/')
                && !url.pathname.startsWith('/api/admin/')
                && !url.pathname.startsWith('/api/auth/'),
              handler: 'NetworkFirst',
              options: {
                cacheName: 'darlila-api',
                networkTimeoutSeconds: 4,
                expiration: { maxEntries: 60, maxAgeSeconds: 86400 },
                cacheableResponse: { statuses: [0, 200] },
              },
            },
            {
              // Toutes les images (produits, Bunny CDN…) : cache prioritaire
              urlPattern: ({ request }) => request.destination === 'image',
              handler: 'CacheFirst',
              options: {
                cacheName: 'darlila-images',
                expiration: { maxEntries: 150, maxAgeSeconds: 2592000 }, // 30 jours
                cacheableResponse: { statuses: [0, 200] },
              },
            },
          ],
        },
        // Service worker actif aussi en développement (localhost) pour
        // tester l'expérience d'installation ; HMR inchangé.
        devOptions: {
          enabled: true,
          type: 'module',
        },
      }),
    ],
    server: {
      host: '0.0.0.0',
      port: 5173,
      proxy,
      allowedHosts: true,
    },
    preview: {
      host: '0.0.0.0',
      port: 4173,
      proxy,
      allowedHosts: true,
    },
  }
})
