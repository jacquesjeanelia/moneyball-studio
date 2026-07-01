import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { fileURLToPath, URL } from 'node:url'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'charts': ['recharts'],
          'query': ['@tanstack/react-query'],
        },
      },
    },
  },
  server: {
    port: 5173,
    proxy: {
      // Dev convenience: proxy API calls to the local backend so the app
      // works with a relative base URL out of the box.
      '/api': {
        target: process.env.VITE_PROXY_TARGET || 'http://127.0.0.1:8011',
        changeOrigin: true,
      },
    },
  },
  preview: {
    port: 4173,
  },
})
