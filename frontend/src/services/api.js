import axios from "axios";

// API base URL configuration
// Priority:
// 1) Explicit VITE_API_BASE_URL
// 2) Same-origin relative API path (recommended for HTTPS deployments)
const getApiBaseUrl = () => {
  if (import.meta.env.VITE_API_BASE_URL) {
    console.log(" Using VITE_API_BASE_URL:", import.meta.env.VITE_API_BASE_URL);
    return import.meta.env.VITE_API_BASE_URL;
  }

  return "/";
};

const API_BASE_URL = getApiBaseUrl();
console.log(" API Base URL set to:", API_BASE_URL);

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
