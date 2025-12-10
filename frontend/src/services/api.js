import axios from 'axios'
import { useAuthStore } from '../store/authStore'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api'

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Interceptor para agregar token
api.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().token
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Interceptor para manejar errores
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth
export const authAPI = {
  login: (username, password) =>
    api.post('/auth/login', { username, password }),
}

// Menu
export const menuAPI = {
  getAll: (category) =>
    api.get('/menu/', { params: { category } }),
  getById: (id) => api.get(`/menu/${id}`),
  create: (data) => api.post('/menu/', data),
  update: (id, data) => api.put(`/menu/${id}`, data),
  delete: (id) => api.delete(`/menu/${id}`),
  getCategories: () => api.get('/menu/categories'),
}

// Orders
export const ordersAPI = {
  getAll: (filters) => api.get('/orders/', { params: filters }),
  getById: (id) => api.get(`/orders/${id}`),
  getOpen: () => api.get('/orders/open'),
  create: (data) => api.post('/orders/', data),
  addItems: (orderId, items) =>
    api.post(`/orders/${orderId}/items`, { items }),
  updateItem: (orderId, itemId, data) =>
    api.put(`/orders/${orderId}/items/${itemId}`, data),
  removeItem: (orderId, itemId) =>
    api.delete(`/orders/${orderId}/items/${itemId}`),
  complete: (orderId, paymentMethod) =>
    api.put(`/orders/${orderId}/complete`, { payment_method: paymentMethod }),
  cancel: (orderId) => api.put(`/orders/${orderId}/cancel`),
  downloadTicket: (orderId) =>
    api.get(`/orders/${orderId}/ticket`, { responseType: 'blob' }),
}

// Reports
export const reportsAPI = {
  daily: (date) => api.get('/reports/daily', { params: { date } }),
  bestSellers: (days) =>
    api.get('/reports/best-sellers', { params: { days } }),
  salesByCategory: (days) =>
    api.get('/reports/sales-by-category', { params: { days } }),
}

export default api