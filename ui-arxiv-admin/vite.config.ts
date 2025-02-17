import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  base: '/admin-console/',
  server: {
    port: 21511,
    host: '0.0.0.0',
    allowedHosts: ['0.0.0.0', '127.0.0.1', 'localhost', 'localhost.arxiv.org'],
  },
  plugins: [react()],
  build: {
    outDir: 'dist',
    rollupOptions: {
      input: 'index.html',
    },
  },  
});
