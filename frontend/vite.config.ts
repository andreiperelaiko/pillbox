import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react(),
    {
      name: 'spa-fallback',
      configureServer(server) {
        const fallback = (req: { url?: string }, _res: unknown, next: () => void) => {
          const url = (req.url ?? '').split('?')[0];
          if (url.indexOf('/api') === 0 || url.indexOf('/@') === 0 || url.indexOf('/node_modules') === 0 || /\.[a-z0-9]+$/i.test(url)) {
            return next();
          }
          req.url = '/index.html';
          next();
        };
        const m = server.middlewares as { stack: Array<{ route: string; handle: unknown }> };
        m.stack.unshift({ route: '', handle: fallback });
      },
    },
  ],
  server: {
    proxy: {
      '/api': {
        target: 'https://pi11box.ru',
        changeOrigin: true,
        secure: false,
      },
    },
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
      },
    },
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
          redux: ['@reduxjs/toolkit', 'react-redux'],
        },
      },
    },
  },
  base: '/',
});

