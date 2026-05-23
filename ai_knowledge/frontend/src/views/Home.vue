<template>
  <div class="home-container" :style="containerStyle">
    <!-- 背景层已移到 MainLayout 中 -->
    <!-- 欢迎卡片 -->
    <div class="home-header">
      <el-card shadow="hover" class="welcome-card">
        <div class="welcome-text">
          <!-- <h1></h1> -->
          <p class="daily-quote">{{ dailyQuote }}</p>
        </div>
      </el-card>
    </div>

    <!-- 倒计时 -->
    <el-card shadow="hover" class="countdown-card">
      <div class="countdown-header">
        <h3>距离{{ countdownTitle }}还有</h3>
        <el-button type="primary" link @click="showCountdownDialog = true" class="edit-button">
          <el-icon><Calendar /></el-icon> 编辑
        </el-button>
      </div>
      <div class="countdown">
        <div class="countdown-item">
          <span class="countdown-number">{{ days }}</span>
          <span class="countdown-label">天</span>
        </div>
        <div class="countdown-item">
          <span class="countdown-number">{{ hours }}</span>
          <span class="countdown-label">时</span>
        </div>
        <div class="countdown-item">
          <span class="countdown-number">{{ minutes }}</span>
          <span class="countdown-label">分</span>
        </div>
        <div class="countdown-item">
          <span class="countdown-number">{{ seconds }}</span>
          <span class="countdown-label">秒</span>
        </div>
      </div>
    </el-card>

    <!-- 倒计时设置对话框 -->
    <el-dialog
      v-model="showCountdownDialog"
      title="设置倒计时"
      width="400px"
    >
      <div class="countdown-setting">
        <div class="setting-item">
          <label>倒计时标题：</label>
          <el-input v-model="countdownConfig.title" placeholder="例如：学期结束" style="width: 100%" />
        </div>
        <div class="setting-item">
          <label>目标日期：</label>
          <el-date-picker
            v-model="countdownConfig.targetDate"
            type="datetime"
            placeholder="选择日期和时间"
            style="width: 100%"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DD HH:mm:ss"
          />
        </div>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showCountdownDialog = false">取消</el-button>
          <el-button type="primary" @click="saveCountdownConfig">保存</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 功能入口网格 -->
    <el-row :gutter="16" class="menu-grid">
      <el-col :span="12" v-for="item in menuItems" :key="item.name">
        <el-card shadow="hover" class="menu-card" @click="handleClick(item.path)">
          <div class="card-content">
            <el-icon :size="30" :color="item.color"><component :is="item.icon" /></el-icon>
            <span>{{ item.name }}</span>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 退出按钮 -->
    <!-- <div class="action-area">
      <el-button type="danger" plain style="width: 100%" @click="logout">
        退出登录
      </el-button>
    </div> -->


  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Reading, House, School, Calendar } from '@element-plus/icons-vue'
import { useBackground } from '../composables/useBackground'
import { ElDialog, ElDatePicker, ElButton } from 'element-plus'
import axios from './../utils/axios'
const router = useRouter()

// 使用背景设置
const { containerStyle, countdownConfig } = useBackground()

const menuItems = [
  { name: '学业规划', icon: Reading, path: '/planner', color: '#409eff'},
  { name: '租房攻略', icon: House, path: '/life', color: '#67c23a' },
  
]

// --- 1. 准备你的名言库 ---
const quotes = [
  "一想全是问题，一做全是答案 💪",
  "每天进步一点点 🌱",
  "允许一切发生 🍃",
  "凡事发生，皆有利于我 ✨",
  "追随自己内心，不必强求 ❤️",
  "星光不问赶路人 🌟",
  "越努力，越幸运 🍀",
  "保持热爱，奔赴山海 🌊"
]

// --- 2. 根据日期计算名言 ---
// 使用日期作为种子，保证同一天内刷新页面名言不变
const getDailyQuote = () => {
  const now = new Date()
  // 获取今年的第几天作为索引 (简单算法)
  const start = new Date(now.getFullYear(), 0, 0)
  const diff = now - start
  const oneDay = 1000 * 60 * 60 * 24
  const dayIndex = Math.floor(diff / oneDay)
  
  // 使用索引对名言数量取余，确保循环播放
  const quoteIndex = dayIndex % quotes.length
  return quotes[quoteIndex]
}

const dailyQuote = ref(getDailyQuote())

// --- 3. 倒计时功能 ---
const days = ref(0)
const hours = ref(0)
const minutes = ref(0)
const seconds = ref(0)
const showCountdownDialog = ref(false)

// 保存倒计时配置到后端
const saveCountdownConfig = async () => {
  try {
    // 保存到本地存储
    localStorage.setItem('countdownConfig', JSON.stringify(countdownConfig.value))

    // 保存到后端
    const token = localStorage.getItem('token')
    if (token) {
      const data = {
        countdownConfig: {
          title: countdownConfig.value.title,
          targetDate: countdownConfig.value.targetDate
        }
      }

      await axios.put('/api/user/settings', data)
    }

    showCountdownDialog.value = false
    updateCountdown()
  } catch (error) {
      console.error('保存倒计时配置失败', error)
      console.error('错误详情:', error.response?.data)
      showCountdownDialog.value = false
      updateCountdown()
    }
}

// 倒计时标题
const countdownTitle = computed(() => {
  return countdownConfig.value.title || '学期结束'
})

// 获取目标日期
const getTargetDate = () => {
  return new Date(countdownConfig.value.targetDate)
}

const updateCountdown = () => {
  const now = new Date()
  const targetDate = getTargetDate()
  const timeLeft = targetDate - now
  
  if (timeLeft <= 0) {
    days.value = 0
    hours.value = 0
    minutes.value = 0
    seconds.value = 0
    return
  }
  
  days.value = Math.floor(timeLeft / (1000 * 60 * 60 * 24))
  hours.value = Math.floor((timeLeft % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60))
  minutes.value = Math.floor((timeLeft % (1000 * 60 * 60)) / (1000 * 60))
  seconds.value = Math.floor((timeLeft % (1000 * 60)) / 1000)
}

let countdownInterval = null

onMounted(async () => {
  updateCountdown()
  countdownInterval = setInterval(updateCountdown, 1000)
})

onUnmounted(() => {
  if (countdownInterval) {
    clearInterval(countdownInterval)
  }
})



const handleClick = (path) => {
  // 这里只是演示，实际你可以跳转到对应页面
  router.push(path)
}

const logout = () => {
  localStorage.removeItem('token')
  router.push('/')
}
</script>

<style scoped>
.home-container { padding: 20px; min-height: 100vh; position: relative; }

.welcome-card {
  margin-bottom: 20px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.8), rgba(118, 75, 162, 0.8));
  color: white;
  border-radius: 10px;
  transition: all 0.3s ease;
}
.welcome-text h1 { margin: 0; font-size: 24px; }
.welcome-text p { margin: 5px 0 0; opacity: 0.9; }

/* 倒计时样式 */
.countdown-card {
  margin-bottom: 20px;
  border-radius: 10px;
  transition: all 0.3s ease;
  padding: 20px;
  background: rgba(255, 255, 255, 0.8);
}

.countdown-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.countdown-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 500;
}

.edit-button {
  font-size: 14px;
  padding: 0;
}

/* 倒计时设置对话框样式 */
.countdown-setting {
  padding: 10px 0;
}

.setting-item {
  margin-bottom: 20px;
}

.setting-item label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
}

.countdown {
  display: flex;
  justify-content: center;
  gap: 20px;
  flex-wrap: wrap;
}

.countdown-item {
  text-align: center;
  background: #f0f0f0;
  padding: 10px;
  border-radius: 8px;
  min-width: 80px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.countdown-number {
  display: block;
  font-size: 24px;
  font-weight: bold;
  line-height: 1;
}

.countdown-label {
  display: block;
  font-size: 12px;
  margin-top: 5px;
  opacity: 0.8;
}

.menu-grid { margin-bottom: 30px; }
.menu-card { cursor: pointer; margin-bottom: 15px; 
border-radius: 10px;
filter:  drop-shadow(0 0 10px rgba(0,0,0,0.1));
background: rgba(255, 255, 255, 0.8);
}
.card-content {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 500;
  color: inherit;
  /* border-radius: 10px; */
}
/* 优化名言的样式 */
.daily-quote {
  margin: 10px 0 0;
  font-size: 16px;
  font-family: 'Courier New', Courier, monospace;
  opacity: 0.95;
  font-weight: 300;
  letter-spacing: 0.5px;
  /* 增加一点文字阴影让它在渐变背景上更清晰 */
  text-shadow: 0 1px 2px rgba(0,0,0,0.1);
}

/* 响应式样式 */
@media (max-width: 768px) {
  .home-container {
    padding: 10px;
  }
  
  .countdown {
    gap: 10px;
  }
  
  .countdown-item {
    min-width: 60px;
    padding: 8px;
  }
  
  .countdown-number {
    font-size: 18px;
  }
  
  .countdown-label {
    font-size: 10px;
  }
}
</style>