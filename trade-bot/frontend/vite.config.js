import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'https://trade-bot-production-7ac0.up.railway.app',
        changeOrigin: true
      }
    }
  }
})