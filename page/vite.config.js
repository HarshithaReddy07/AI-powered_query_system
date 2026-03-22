import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  define: {
    // Polyfill for libraries that expect a Node-like global
    global: 'window',
  },
});
