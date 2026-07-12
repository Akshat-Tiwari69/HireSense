import axios from "axios";

// Simple: use VITE_API_BASE_URL if set, otherwise default to localhost:5000
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:5000";

export const api = axios.create({
  baseURL: API_BASE_URL,
});

// Authentication is header-only: attach the stored bearer token and the
// assessment token used by candidate-facing routes.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("authToken");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  const assessmentToken = sessionStorage.getItem("assessmentToken");
  if (assessmentToken) {
    config.headers["X-Assessment-Token"] = assessmentToken;
  }
  return config;
});
