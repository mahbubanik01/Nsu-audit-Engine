import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'edu.northsouth.auditengine',
  appName: 'NSU Audit Engine',
  webDir: 'dist',
  server: {
    // For development: point to your local FastAPI server
    // Remove this block for production builds
    // androidScheme: 'https',
    cleartext: true, // Allow HTTP for local dev
  },
  plugins: {
    CapacitorHttp: {
      enabled: true, // Use native HTTP for better CORS handling on Android
    },
  },
  android: {
    allowMixedContent: true, // Allow HTTP + HTTPS during dev
  },
};

export default config;
