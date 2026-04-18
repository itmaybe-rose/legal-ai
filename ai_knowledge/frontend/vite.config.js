import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0', // 允许通过IP地址访问
    port: 5173, // Vite默认端口
    // 配置代理，把 /api 开头的请求转发给 Python 后端
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000', // 你的 Python 后端地址
        changeOrigin: true,
      },
      '/login': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/register': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      }
    }
  }
})
