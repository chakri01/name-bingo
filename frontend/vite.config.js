import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
  },
  preview: {
    host: '0.0.0.0',
    port: parseInt(process.env.PORT) || 5173,
    strictPort: true,  // Fail if port is already in use
  }
})