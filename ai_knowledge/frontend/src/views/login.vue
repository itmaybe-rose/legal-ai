<template>
  <div class="login-container">
    <!-- 登录/注册卡片 -->
    <el-card class="box-card" shadow="always">
      <!-- 动态标题 -->
      <h2 class="title">{{ isLogin ? '欢迎回来 👋' : '加入我们要 👋' }}</h2>
      <p class="subtitle">{{ isLogin ? '请输入您的账号信息以登录' : '请输入您的账号信息以注册' }}</p>

      <!-- 表单区域 -->
      <el-form :model="form" :rules="rules" ref="loginForm" label-position="top">
        
        <!-- 用户名 -->
        <el-form-item label="用户名" prop="username">
          <el-input 
            v-model="form.username" 
            placeholder="请输入用户名" 
            prefix-icon="User"
          />
        </el-form-item>

        <!-- 密码 -->
        <el-form-item label="密码" prop="password">
          <el-input 
            v-model="form.password" 
            type="password" 
            placeholder="请输入密码" 
            prefix-icon="Lock"
            show-password
          />
        </el-form-item>

        <!-- 提交按钮 -->
        <el-form-item>
          <el-button 
            type="primary" 
            @click="submitForm" 
            :loading="loading" 
            class="submit-btn"
          >
            {{ isLogin ? '立即登录' : '立即注册' }}
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 底部切换链接 -->
      <div class="footer-link">
        <span>{{ isLogin ? '还没有账号？' : '已有账号？' }}</span>
        <a @click="toggleMode">
          {{ isLogin ? '去注册' : '去登录' }}
        </a>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import axios from '../utils/axios'
import { useRouter } from 'vue-router'
// 1. 引入 jwt-decode
import { jwtDecode } from 'jwt-decode' 
const router = useRouter()
const loading = ref(false)
const isLogin = ref(true) // true为登录模式，false为注册模式

// 表单数据
const form = reactive({
  username: '',
  password: ''
})

// 表单验证规则
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const loginForm = ref(null)

// 切换模式
const toggleMode = () => {
  isLogin.value = !isLogin.value
  // 切换时清空表单
  form.username = ''
  form.password = ''
}

// 提交表单
const submitForm = () => {
  loginForm.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        // 根据模式选择不同的接口
        const url = isLogin.value 
          ? '/api/users/login' 
          : '/api/users/register'

         // --- 核心修改点：使用 URLSearchParams 适配 FastAPI 的 Form ---
        const formData = new URLSearchParams()
        formData.append('username', form.username)
        formData.append('password', form.password)

        const res = await axios.post(url, formData)

        if (isLogin.value) {
            // 1. 获取 Token
          const token = res.data.access_token
          const refreshToken = res.data.refresh_token
          
          if (token) {
            // 2. 存储 Token
            localStorage.setItem('token', token)
            if (refreshToken) {
              localStorage.setItem('refresh_token', refreshToken)
            }
            
            // 2. 【新增】立即从数据库拉取用户信息
          // 注意：这里必须等 Token 存进去后再调用，因为拉取接口需要验证 Token
          try {
            const infoRes = await axios.get('/api/profile', {
              headers: {
                'Authorization': `Bearer ${token}`
              }
            })

            // 3. 将拉取到的数据存入 LocalStorage
            // 这样 Profile 页面加载时就能读到了
            localStorage.setItem('userProfile', JSON.stringify(infoRes.data))
            // 存储用户名到 localStorage
            localStorage.setItem('username', infoRes.data.username)
            
            // 4. 存储用户角色信息
            localStorage.setItem('userInfo', JSON.stringify({ role: infoRes.data.role }))
            
            ElMessage.success('登录成功！')
            router.push('/profile') // 跳转到个人中心

          } catch (infoError) {
            console.error("自动拉取用户信息失败", infoError)
            // 即使拉取失败，也允许登录，只是个人信息可能是空的
            ElMessage.warning('登录成功，但获取个人信息失败，请稍后在个人中心完善')
            // 存储用户名和默认角色
            localStorage.setItem('username', form.username)
            localStorage.setItem('userInfo', JSON.stringify({ role: 0 }))
            router.push('/profile')
          }
          }
            
        } else {
          // 注册成功逻辑
          ElMessage.success('注册成功，请登录！')
          toggleMode() // 自动切换到登录模式
        }
      } catch (error) {
        // 错误已由 axios 拦截器统一显示
        console.error('登录/注册失败:', error)
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style scoped>
/* 整体背景：漂亮的渐变色 */
.login-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  background-attachment: fixed;
}

/* 卡片样式 */
.box-card {
  width: 400px;
  padding: 40px;
  border-radius: 15px;
  border: none;
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
  background: rgba(255, 255, 255, 0.8);
}

.title {
  margin: 0;
  text-align: center;
  color: #333;
  font-weight: 700;
}

.subtitle {
  text-align: center;
  color: #999;
  margin-bottom: 30px;
  font-size: 14px;
}

/* 按钮样式 */
.submit-btn {
  width: 100%;
  padding: 12px;
  font-size: 16px;
  margin-top: 10px;
}

/* 底部链接 */
.footer-link {
  text-align: center;
  margin-top: 20px;
  font-size: 14px;
  color: #666;
}

.footer-link a {
  color: #667eea;
  cursor: pointer;
  text-decoration: none;
  font-weight: bold;
  margin-left: 5px;
}

.footer-link a:hover {
  color: #764ba2;
}
</style>