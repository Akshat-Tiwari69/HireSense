import axios from "axios";
import { clearStaffSession, getStaffSession } from "./session";

const configuredBaseUrl = String(import.meta.env.VITE_API_BASE_URL || '').trim();

// Same-origin is the production-safe default. Vite proxies /api and /socket.io
// to the local backend during development.
export const API_BASE_URL = configuredBaseUrl.replace(/\/$/, '');

export const isRelativeApiUrl = (url) => {
  if (typeof url !== 'string' || !url.trim()) return false;
  const value = url.trim();
  if (/^(?:[a-z][a-z\d+.-]*:)?\/\//i.test(value)) return false;
  if (/^(?:data|blob|javascript):/i.test(value)) return false;
  const normalized = value.startsWith('/') ? value : `/${value}`;
  return normalized === '/api' || normalized.startsWith('/api/');
};

export const api = axios.create({
  baseURL: API_BASE_URL,
});

api.interceptors.request.use((config) => {
  if (!isRelativeApiUrl(config.url)) {
    throw new TypeError('API requests must use a relative /api URL');
  }

  const normalizedUrl = config.url.startsWith('/') ? config.url : `/${config.url}`;
  const isIntervieweeRequest = normalizedUrl.startsWith('/api/interviewee/');
  const staffSession = getStaffSession();

  if (staffSession?.token && !isIntervieweeRequest) {
    config.headers.Authorization = `Bearer ${staffSession.token}`;
  }

  const assessmentToken = window.sessionStorage.getItem('assessmentToken');
  if (assessmentToken && isIntervieweeRequest) {
    config.headers["X-Assessment-Token"] = assessmentToken;
  }

  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (
      error?.response?.status === 401
      && error?.config?.headers?.Authorization
    ) {
      clearStaffSession();
      window.dispatchEvent(new CustomEvent('hiresense:session-expired'));
    }
    return Promise.reject(error);
  },
);
