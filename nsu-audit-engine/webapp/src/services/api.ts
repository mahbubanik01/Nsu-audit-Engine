import axios from 'axios';

// Pull from environment or fallback to defaults
const API_KEY = import.meta.env.VITE_NSU_API_KEY || 'dev_secret_key';

// Capacitor-aware API URL:
// When running as a native Android app, localhost doesn't work.
// Use 10.0.2.2 for Android emulator, or your deployed server URL.
function getApiUrl(): string {
  const envUrl = import.meta.env.VITE_API_BASE_URL;

  // If explicitly set in env, use it
  if (envUrl) return envUrl;

  // Check if running inside Capacitor native shell
  const isNative = typeof (window as any)?.Capacitor !== 'undefined' 
    && (window as any).Capacitor?.isNativePlatform?.();

  if (isNative) {
    // Android emulator uses 10.0.2.2 to reach host machine's localhost
    return 'http://10.0.2.2:8000';
  }

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
