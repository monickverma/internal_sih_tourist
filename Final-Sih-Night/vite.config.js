import { defineConfig } from 'vite'
import tailwindcss from '@tailwindcss/vite'

import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(),tailwindcss()],
  server: {
    // Dev: forward /api to the local FastAPI server (uvicorn api.index:app --port 8000)
    proxy: { '/api': 'http://127.0.0.1:8000' },
  },
})
