import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/send_message': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/send_message_streaming': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/api/v1/data-analysis/chat-stream': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      // Unified streaming now handled via /api/unified/chat-stream
      '/upload': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/run_analysis': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/get_visualization': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: '../app/static/react',
    emptyOutDir: true,
  },
})
