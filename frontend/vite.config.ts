import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vitejs.dev/config/
export default defineConfig(() => {
  const backendUrl = process.env.VITE_BACKEND_URL || 'http://localhost:8000'
  const wsUrl = backendUrl.replace(/^http/, 'ws')

  return {
    plugins: [react(), tailwindcss()],
    server: {
      port: 5173,
      host: true,
      proxy: {
        '/api': {
          target: backendUrl,
          changeOrigin: true
        },
        '/ws': {
          target: wsUrl,
          ws: true,
          changeOrigin: true
        }
      }
    }
  }
})
