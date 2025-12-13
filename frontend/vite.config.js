import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173
  },
  preview: {
    host: true,
    allowedHosts: ["bingo-frontend-production.up.railway.app"],
    port: process.env.PORT ? Number(process.env.PORT) : 5173,
  }
})