<template>
  <div class="home-container">
    <!-- 欢迎卡片 -->
    <el-card shadow="hover" class="welcome-card">
      <div class="welcome-text">
        <!-- <h1></h1> -->
        <p class="daily-quote">{{ dailyQuote }}</p>
      </div>
    </el-card>

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
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Reading, House, Coordinate, School } from '@element-plus/icons-vue'
const router = useRouter()
const menuItems = [
  { name: '学业规划', icon: Reading, path: '/planner', color: '#409eff'},
  { name: '租房攻略', icon: House, path: '/life', color: '#67c23a' },
  { name: '出行助手', icon: Coordinate, path: '/travel', color: '#e6a23c' },
  { name: '校园生活', icon: School, path: '/campus', color: '#f56c6c' },
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
.home-container { padding: 20px; }

.welcome-card {
  margin-bottom: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 10px;
  transition: all 0.3s ease;
}
.welcome-text h1 { margin: 0; font-size: 24px; }
.welcome-text p { margin: 5px 0 0; opacity: 0.9; }

.menu-grid { margin-bottom: 30px; }
.menu-card { cursor: pointer; margin-bottom: 15px; 
border-radius: 10px;
filter:  drop-shadow(0 0 10px rgba(0,0,0,0.1));
}
.card-content {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 500;
  color: #303133;
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
</style>