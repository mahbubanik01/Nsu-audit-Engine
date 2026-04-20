import axios from 'axios';

// Pull from environment or fallback to defaults
const API_KEY = import.meta.env.VITE_NSU_API_KEY || 'dev_secret_key';

// Capacitor-aware API URL:
// When running as a native Android app, localhost doesn't work.
// Use 10.0.2.2 for Android emulator, or your deployed server URL.
function getApiUrl(): string {
  // 0. Manual Override (useful for pasting Cloudflare Tunnel URL in UI)
  if (typeof window !== 'undefined') {
    const manualUrl = localStorage.getItem('NSU_API_OVERRIDE');
    if (manualUrl) return manualUrl;
  }

  // 1. Check for explicit environment variable (REQUIRED for Cloudflare Tunnel to bypass Vercel limits)
  const envUrl = import.meta.env.VITE_API_BASE_URL;
  if (envUrl) return envUrl;

  // 2. Capacitor-specific logic for native Android app
  const isNative = typeof (window as any)?.Capacitor !== 'undefined' 
    && (window as any).Capacitor?.isNativePlatform?.();

  if (isNative) {
    // Android emulator uses 10.0.2.2. For real devices, the Tunnel URL must be provided in env.
    return 'http://10.0.2.2:8000';
  }

  // 3. Vercel deployment detection
  // If we are in a browser and not on localhost, we are likely on Vercel.
  // Use the current origin so Vercel routes `/api/v1/...` to the serverless backend.
  if (typeof window !== 'undefined' && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
    return window.location.origin;
  }

  // 4. Fallback to local machine for local Vite dev server
  return 'http://localhost:8000';
}

const API_URL = getApiUrl();

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'X-API-Key': API_KEY,
  },
});

// Intercept requests to dynamically inject the Bearer token for protected routes
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('nsu_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});
