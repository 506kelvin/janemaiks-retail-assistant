import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';
const TIMEOUT = parseInt(import.meta.env.VITE_API_TIMEOUT || '15000', 10);

const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: TIMEOUT,
});

if (import.meta.env.DEV) {
  console.log('[JaneMaiks API] Base URL:', BASE_URL);
}

api.interceptors.request.use((config) => {
  if (import.meta.env.DEV) {
    console.log(`[JaneMaiks API] ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`);
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === 'ECONNABORTED') {
      return Promise.reject(new Error('Request timed out. Please check your connection.'));
    }
    if (!error.response) {
      return Promise.reject(new Error('Unable to reach the server. Please try again.'));
    }
    return Promise.reject(error);
  }
);

export { api };

export const productApi = {
  list: (params) => api.get('/products/', { params }),
  listAll: () => api.get('/products/all'),
  get: (id) => api.get(`/products/${id}`),
  create: (data) => api.post('/products/', data),
  update: (id, data) => api.put(`/products/${id}`, data),
  delete: (id) => api.delete(`/products/${id}`),
  categories: () => api.get('/products/categories/list'),
  suppliers: () => api.get('/products/suppliers/list'),
};

export const pricingApi = {
  calculate: (data) => api.post('/pricing/calculate', data),
  batch: (productIds) => api.get('/pricing/batch', { params: { product_ids: productIds } }),
  suggest: (data) => api.post('/pricing/suggest', data),
  getProductPricing: (productId) => api.get(`/pricing/product/${productId}`),
  round: (data) => api.post('/pricing/round', data),
  calculateFull: (data) => api.post('/pricing/calculate-full', data),
};

export const chatApi = {
  query: (data) => api.post('/chat/query', data),
  history: (sessionId) => api.get('/chat/history', { params: { session_id: sessionId } }),
};

export const inventoryApi = {
  list: (lowStockOnly = false) => api.get('/inventory/', { params: { low_stock_only: lowStockOnly } }),
  get: (productId) => api.get(`/inventory/${productId}`),
  addTransaction: (data) => api.post('/inventory/transactions', data),
  transactions: (productId) => api.get('/inventory/transactions/list', { params: { product_id: productId } }),
  updateThreshold: (productId, threshold) =>
    api.put(`/inventory/threshold/${productId}`, null, { params: { threshold } }),
};

export const analyticsApi = {
  dashboard: () => api.get('/analytics/dashboard'),
};

export default api;
