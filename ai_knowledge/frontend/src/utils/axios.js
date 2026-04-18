import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '../router'

// 创建 axios 实例
const service = axios.create({
  baseURL: '/',
  timeout: 120000
})

// 响应拦截器
service.interceptors.response.use(
  response => {
    return response
  },
  error => {
    // 处理 401 错误
    if (error.response && error.response.status === 401) {
      // 清除本地存储的 token 和用户信息
      localStorage.removeItem('token')
      localStorage.removeItem('userProfile')

      // 显示错误提示
      ElMessage.error('登录已过期，请重新登录')

      // 跳转到登录页面
      router.push('/login')
    }

    // 其他错误处理
    ElMessage.error(error.response?.data?.detail || '操作失败')
    return Promise.reject(error)
  }
)

export default service
