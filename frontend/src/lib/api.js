import axios from 'axios';
import config from '../config'; // Import the new config file

const api = axios.create({
  baseURL: config.API_BASE_URL,
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
