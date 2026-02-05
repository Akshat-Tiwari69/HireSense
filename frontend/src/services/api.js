import axios from "axios";

// Dynamic API base URL configuration
// If accessed via localhost, use localhost:5000 (for you)
// If accessed via network IP, use <network-ip>:5000 (for others)
const getApiBaseUrl = () => {
  // Check if there's an environment variable set
  if (import.meta.env.VITE_API_BASE_URL) {
    console.log("🔧 Using VITE_API_BASE_URL:", import.meta.env.VITE_API_BASE_URL);
    return import.meta.env.VITE_API_BASE_URL;
  }

  // Get the current hostname (e.g., "localhost" or "10.39.35.52")
  const hostname = window.location.hostname;
  console.log("🌐 Detected hostname:", hostname);

  // If accessing via localhost, use localhost backend
  if (hostname === "localhost" || hostname === "127.0.0.1") {
    console.log("✅ Using localhost backend: http://localhost:5000");
    return "http://localhost:5000";
  }

  // If accessing via network IP, use the same IP for backend
  const networkUrl = `http://${hostname}:5000`;
  console.log("✅ Using network backend:", networkUrl);
  return networkUrl;
};

const API_BASE_URL = getApiBaseUrl();
console.log("📡 API Base URL set to:", API_BASE_URL);

// Export for use in other components (e.g., Socket.IO connections)
export { API_BASE_URL };

export const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: false,
});

// Attach token if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("authToken");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
