import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import router from './router' //挂载路由
// 引入 Element Plus 及其样式
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

createApp(App).use(router).use(ElementPlus).mount('#app')
