import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
    plugins: [react()],
    server: {
        port: 3001,
        host: '0.0.0.0',
        proxy: {
            '/api': {
                target: process.env.API_PROXY_TARGET || 'http://localhost:8000',
                changeOrigin: true
            },
            '/health': {
                target: process.env.API_PROXY_TARGET || 'http://localhost:8000',
                changeOrigin: true
            },
            '/ready': {
                target: process.env.API_PROXY_TARGET || 'http://localhost:8000',
                changeOrigin: true
            },
            '/metrics': {
                target: process.env.API_PROXY_TARGET || 'http://localhost:8000',
                changeOrigin: true
            },
            '/ws': {
                target: process.env.API_PROXY_TARGET || 'http://localhost:8000',
                ws: true,
                changeOrigin: true
            }
        }
    },
    build: {
        outDir: 'dist',
        sourcemap: true
    }
})
