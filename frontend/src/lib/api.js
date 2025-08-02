import axios from 'axios';

const api = axios.create({
  baseURL: process.env.NODE_ENV === 'production'
    ? 'http://rizwanm42.pythonanywhere.com' // <-- Use your PythonAnywhere URL here
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
