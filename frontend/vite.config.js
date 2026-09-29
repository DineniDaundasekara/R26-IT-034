import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const backendTarget = env.VITE_BACKEND_TARGET || env.VITE_API_URL || 'http://127.0.0.1:8000';


  return {
    plugins: [react()],
    server: {
      port: parseInt(env.PORT || '3000', 10),
      host: '0.0.0.0',
      proxy: {
        '/api': {
          target: backendTarget,
          changeOrigin: true
        }
      }
    }
  };
});
