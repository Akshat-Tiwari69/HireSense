import axios from "axios";

// Prefer deploy env, fallback to same-origin or local dev.
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  import.meta.env.VITE_API_URL ||
  (typeof window !== "undefined" ? window.location.origin : "http://127.0.0.1:5000");

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
