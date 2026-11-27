import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'fs'
import path from 'path'

// Face detection runs MediaPipe's wasm runtime, which must be served from our
// own origin under the production CSP. Rather than committing ~15 MB of
// binaries, serve them from node_modules in dev and copy them into the build.
const MEDIAPIPE_WASM_DIR = path.resolve(__dirname, 'node_modules/@mediapipe/tasks-vision/wasm')
const MEDIAPIPE_FILES = ['vision_wasm_internal.js', 'vision_wasm_internal.wasm']
const MEDIAPIPE_PUBLIC_PATH = 'mediapipe'

const mediapipeWasm = () => ({
  name: 'hiresense-mediapipe-wasm',
  configureServer(server) {
    server.middlewares.use(`/${MEDIAPIPE_PUBLIC_PATH}`, (req, res, next) => {
      const name = path.basename(new URL(req.url, 'http://localhost').pathname)
      if (!MEDIAPIPE_FILES.includes(name)) return next()
      res.setHeader('Content-Type', name.endsWith('.wasm') ? 'application/wasm' : 'text/javascript')
      fs.createReadStream(path.join(MEDIAPIPE_WASM_DIR, name)).pipe(res)
    })
  },
  generateBundle() {
    for (const name of MEDIAPIPE_FILES) {
      this.emitFile({
        type: 'asset',
        fileName: `${MEDIAPIPE_PUBLIC_PATH}/${name}`,
        source: fs.readFileSync(path.join(MEDIAPIPE_WASM_DIR, name)),
      })
    }
  },
})

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react(),
    mediapipeWasm(),
  ],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:5000',
      '/socket.io': {
        target: 'http://127.0.0.1:5000',
        ws: true,
      },
    },
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
  test: {
    environment: 'jsdom',
    setupFiles: './src/test/setup.js',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json-summary'],
      include: [
        'src/services/session.js',
        'src/services/api.js',
      ],
      thresholds: {
        lines: 80,
        functions: 80,
        branches: 80,
        statements: 80,
      },
    },
  },
})
