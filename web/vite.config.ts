/// <reference types="vitest" />
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig(({ mode }) => ({
  base: mode === 'ha' ? '/scheduled_scenes_panel/' : '/',
  build: mode === 'ha' ? {
    outDir: fileURLToPath(new URL('../custom_components/scheduled_scenes/frontend/dist', import.meta.url)),
    emptyOutDir: true,
  } : undefined,
  plugins: [
    vue(),
    tailwindcss(),
  ],
  test: {
    environment: 'happy-dom',
    globals: true,
    include: ['src/**/*.{test,spec}.ts'],
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,
    watch: {
      usePolling: true,
      interval: 300,
      ignored: ['**/node_modules/**', '**/.git/**', '**/dist/**', '**/.dev/**'],
    },
  },
}))
