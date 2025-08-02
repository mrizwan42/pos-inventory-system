import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.PROD 
    ? 'http://your-username.pythonanywhere.com' // <-- HARDCODED PRODUCTION URL
    : 'http://localhost:5000', // Fallback for local development
} );

// Add a request interceptor to include the token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export default api;
