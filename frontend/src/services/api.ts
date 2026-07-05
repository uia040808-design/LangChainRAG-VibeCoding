/**
 * Axios 实例 + 拦截器配置
 *
 * Axios 是前端最常用的HTTP请求库。
 * "拦截器"就像安检站：每个请求发出前、每个响应到达后，都会经过拦截器处理。
 */
import axios from 'axios'

// 创建Axios实例，所有请求共享这个配置
const api = axios.create({
  baseURL: '/api',  // 所有请求都从 /api 开始（Vite代理转发到后端）
  timeout: 30000,   // 超时时间30秒
  headers: {
    'Content-Type': 'application/json',
  },
})

// ===== 请求拦截器 =====
// 每次发送请求前，自动从localStorage取出Token附加到请求头
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// ===== 响应拦截器 =====
// 如果返回401（未登录/Token过期），自动跳转到登录页
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      // 如果不在登录页则跳转
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export default api
