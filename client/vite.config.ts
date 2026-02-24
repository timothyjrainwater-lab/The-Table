import { defineConfig } from 'vite';

export default defineConfig({
  root: '.',
  server: {
    port: 3000,
    open: true,
    fs: {
      allow: ['..'],
    },
  },
  build: {
    outDir: 'dist',
  },
  test: {
    environment: 'node',
    include: ['tests/unit/**/*.test.ts'],
    reporters: ['verbose'],
  },
});
