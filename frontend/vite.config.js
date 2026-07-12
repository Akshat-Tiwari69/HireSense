import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react(),
  ],
  server: {
    host: '0.0.0.0',
    port: 5173,
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
      "events": "events/",
      "util": "util/",
    },
    extensions: ['.js', '.jsx', '.json'],
  },
  define: {
    // Polyfill for simple-peer (expects Node.js global)
    global: 'globalThis',
    'process.env': '{}',
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: undefined,
      },
    },
  },
  ssr: {
    noExternal: [],
  },
})
