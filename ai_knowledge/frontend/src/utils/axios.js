import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '../router'

// 创建 axios 实例
const service = axios.create({
  baseURL: '/',
  timeout: 120000
})

// 是否正在刷新 token
let isRefreshing = false
// 等待刷新 token 的请求队列
let refreshSubscribers = []

// 将请求加入等待队列
function subscribeTokenRefresh(callback) {
  refreshSubscribers.push(callback)
}

// 通知所有等待的请求 - token 已刷新
function onTokenRefreshed(newToken) {
  refreshSubscribers.forEach(callback => callback(newToken))
  refreshSubscribers = []
}

// 请求拦截器
service.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  response => {
    const res = response.data
    // 统一响应格式: { code: 0, message: "success", data: ... }
    if (res.code !== undefined && res.code !== 0) {
      ElMessage.error(res.message || '请求失败')
      return Promise.reject(new Error(res.message))
    }
    // 解包，使 response.data 直接指向实际数据
    response.data = res.data
    return response
  },
  async error => {
    const originalRequest = error.config

    // 如果是 429 速率限制
    if (error.response && error.response.status === 429) {
      ElMessage.warning('请求过于频繁，请稍后再试')
      return Promise.reject(error)
    }

    // 处理 401 错误（token 过期）
    if (error.response && error.response.status === 401) {
      const refreshToken = localStorage.getItem('refresh_token')

      // 没有 refresh_token 或已经重试过，直接跳转登录
      if (!refreshToken || originalRequest._retry) {
        localStorage.removeItem('token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('userProfile')
        localStorage.removeItem('userInfo')
        router.push('/login')
        ElMessage.error('登录已过期，请重新登录')
        return Promise.reject(error)
      }

      // 如果正在刷新，将请求加入队列等待
      if (isRefreshing) {
        return new Promise(resolve => {
          subscribeTokenRefresh(newToken => {
            originalRequest.headers['Authorization'] = `Bearer ${newToken}`
            resolve(service(originalRequest))
          })
        })
      }

      // 开始刷新 token
      isRefreshing = true
      originalRequest._retry = true

      try {
        const formData = new URLSearchParams()
        formData.append('refresh_token', refreshToken)

        const res = await service.post('/api/auth/refresh', formData)
        const { access_token, refresh_token: newRefreshToken } = res

        // 存储新 token
        localStorage.setItem('token', access_token)
        localStorage.setItem('refresh_token', newRefreshToken)

        // 通知所有等待的请求
        onTokenRefreshed(access_token)

        // 重试原始请求
        originalRequest.headers['Authorization'] = `Bearer ${access_token}`
        return service(originalRequest)
      } catch (refreshError) {
        // 刷新失败，清除所有 token 并跳转登录
        localStorage.removeItem('token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('userProfile')
        localStorage.removeItem('userInfo')
        router.push('/login')
        ElMessage.error('登录已过期，请重新登录')
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
        refreshSubscribers = []
      }
    }

    // 其他错误处理 - 适配统一错误格式
    const detail = error.response?.data?.detail
    const errorMsg = typeof detail === 'object' ? detail?.message : detail
    ElMessage.error(errorMsg || '操作失败')
    return Promise.reject(error)
  }
)

export default service