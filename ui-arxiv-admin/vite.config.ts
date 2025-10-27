import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react-swc';

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
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      input: 'index.html',
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-is'],
          'mui': ['@mui/material', '@mui/icons-material', '@emotion/react', '@emotion/styled'],
          'react-admin': ['react-admin', 'ra-core', 'ra-ui-materialui', 'ra-data-json-server'],
        },
      },
    },
  },
});
