import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 8100
  },
  preview: {
    // Render sirve la app por dominio distinto; permitir el host del preview
    allowedHosts: ['sistemagestioncanchasmobile-1.onrender.com', 'sistemagestioncanchasmobile-2.onrender.com', 'sistemagestioncanchasmobile.onrender.com']

  }
});

