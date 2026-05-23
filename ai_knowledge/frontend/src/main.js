import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import router from './router' //挂载路由
// 引入 Element Plus 及其样式
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

// 注册 Service Worker 和推送通知
if ('serviceWorker' in navigator && 'PushManager' in window) {
  navigator.serviceWorker.register('/sw.js')
    .then(async (registration) => {
      console.log('Service Worker 注册成功')

      const permission = await Notification.requestPermission()
      if (permission === 'granted') {
        const response = await fetch('/api/push/public-key')
        const { public_key } = await response.json()

        const subscription = await registration.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: urlBase64ToUint8Array(public_key)
        })

        await fetch('/api/push/subscribe', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(subscription)
        })

        console.log('已订阅推送通知')
      }
    })
    .catch(err => console.error('Service Worker 注册失败:', err))
}

function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - base64String.length % 4) % 4)
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/')
  const rawData = window.atob(base64)
  return Uint8Array.from([...rawData].map(char => char.charCodeAt(0)))
}

createApp(App).use(router).use(ElementPlus).mount('#app')
