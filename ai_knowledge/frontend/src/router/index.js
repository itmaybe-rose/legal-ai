// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/login.vue'
import Home from '../views/Home.vue'
import Forum from '../views/Forum.vue'
import Profile from '../views/Profile.vue'
import MainLayout from '../layouts/MainLayout.vue'
import Planner from '../views/planner.vue'

const routes = [
  { path: '/login', component: Login },
  {
    path: '/',
    component: MainLayout,
    redirect: '/home',
    children: [
      { path: '/home', component: Home },
      { path: '/forum', component: Forum },
      { path: '/profile', component: Profile },
      { path: '/planner', component: Planner }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 修改路由守卫
router.beforeEach((to, from, next) => {
  // 1. 从本地存储读取 Token（页面刷新时，这里能读到之前存的值）
  const token = localStorage.getItem('token');
  const username = localStorage.getItem('username');

  const isLoginPage = to.path === '/login';

  // 场景1: 已登录，且要去登录页 -> 拦截去主页
  if (token && isLoginPage) {
    next('/home');
  }
  // 场景2: 未登录，且不去登录页 -> 拦截去登录
  else if (!token && !isLoginPage) {
    next('/login');
  }
  // 场景3: 其他情况（未登录去登录页，或已登录去其他页）-> 放行
  else {
    next();
  }
})

export default router