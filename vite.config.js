import { defineConfig } from 'vite';

export default defineConfig({
  root: 'ui',
  build: {
    outDir: '../dist',
    emptyOutDir: true,
    rollupOptions: {
      input: {
        main: 'ui/index.html'
      }
    }
  },
  server: {
    proxy: {
      '/api': 'http://localhost:8080',
      '/video_feed': 'http://localhost:8080',
      '/health': 'http://localhost:8080',
      '/presets': 'http://localhost:8080',
      '/apply_preset': 'http://localhost:8080',
      '/manifest.json': 'http://localhost:8080',
      '/service-worker.js': 'http://localhost:8080'
    }
  }
});