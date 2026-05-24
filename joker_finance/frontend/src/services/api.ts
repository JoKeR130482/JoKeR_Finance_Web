import axios from 'axios'
import { useAuthStore } from '../store/authStore'

const API_BASE_URL = '/api/v1'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Interceptor для добавления токена
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

// Interceptor для обработки ошибок авторизации
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth endpoints
export const authApi = {
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),
  register: (email: string, username: string, password: string) =>
    api.post('/auth/register', { email, username, password }),
  refresh: (refreshToken: string) =>
    api.post('/auth/refresh', { refresh_token: refreshToken }),
  getMe: () => api.get('/auth/me'),
}

// Accounts endpoints
export const accountsApi = {
  getAll: (params?: any) => api.get('/accounts/', { params }),
  getById: (id: number) => api.get(`/accounts/${id}`),
  create: (data: any) => api.post('/accounts/', data),
  update: (id: number, data: any) => api.put(`/accounts/${id}`, data),
  delete: (id: number) => api.delete(`/accounts/${id}`),
  merge: (sourceId: number, targetId: number) =>
    api.post('/accounts/merge', { source_account_id: sourceId, target_account_id: targetId }),
  reorder: (ids: number[]) => api.put('/accounts/reorder', { account_ids: ids }),
}

// Transactions endpoints
export const transactionsApi = {
  getAll: (params?: any) => api.get('/transactions/', { params }),
  getById: (id: number) => api.get(`/transactions/${id}`),
  create: (data: any) => api.post('/transactions/', data),
  update: (id: number, data: any) => api.put(`/transactions/${id}`, data),
  delete: (id: number) => api.delete(`/transactions/${id}`),
  bulkDelete: (ids: number[]) => api.post('/transactions/bulk-delete', { transaction_ids: ids }),
}

// Categories endpoints
export const categoriesApi = {
  getAll: (params?: any) => api.get('/categories/', { params }),
  getById: (id: number) => api.get(`/categories/${id}`),
  create: (data: any) => api.post('/categories/', data),
  update: (id: number, data: any) => api.put(`/categories/${id}`, data),
  delete: (id: number) => api.delete(`/categories/${id}`),
}

// Budget endpoints
export const budgetApi = {
  getAll: (month: number, year: number, params?: any) =>
    api.get('/budget/', { params: { month, year, ...params } }),
  create: (data: any) => api.post('/budget/', data),
  update: (id: number, data: any) => api.put(`/budget/${id}`, data),
  copy: (data: any) => api.post('/budget/copy', data),
  getStats: (month: number, year: number) =>
    api.get(`/budget/stats/${month}/${year}`),
}

export default api
