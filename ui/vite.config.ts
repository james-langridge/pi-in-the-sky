import { VitePWA } from 'vite-plugin-pwa';
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vitejs.dev/config/
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
      '/video_feed': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
      '/presets': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
      '/apply_preset': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
      '/photos': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
    }
  },
  plugins: [react(), tailwindcss(), VitePWA({
    strategies: 'injectManifest',
    srcDir: 'public',
    filename: 'sw.js',
    registerType: 'autoUpdate',
    injectRegister: 'auto',
    injectManifest: {
      injectionPoint: undefined // No precaching needed
    },

    pwaAssets: {
      disabled: false,
      config: true,
    },
    manifest: {
      name: 'Pi Camera Stream',
      short_name: 'PiCam',
      description: 'Remote camera control and streaming for Raspberry Pi',
      theme_color: '#1f2937',
      background_color: '#111827',
      display: 'standalone',
      orientation: 'any',
      scope: '/',
      start_url: '/',
      icons: [
        {
          src: '/icon-192.png',
          sizes: '192x192',
          type: 'image/png'
        },
        {
          src: '/icon-512.png',
          sizes: '512x512',
          type: 'image/png'
        }
      ]
    },

    devOptions: {
      enabled: false,
      navigateFallback: 'index.html',
      suppressWarnings: true,
      type: 'module',
    },
  })],
})
