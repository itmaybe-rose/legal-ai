<template>
  <div class="global-container">
    <div class="background-layer" :style="backgroundLayerStyle"></div>
    <el-container class="layout-container" direction="vertical">
      <!-- 1. 顶部 Header -->
      <el-header class="app-header">
        <div class="header-content">
          <h2>智汇校园</h2>
        </div>
      </el-header>

      <!-- 2. 中间主要内容区 -->
      <el-main class="app-main view-wrapper">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>

      <!-- 3. 底部导航栏 -->
      <!-- 底部导航栏 (替换原来的退出按钮区域) -->
      <nav class="bottom-nav">
        <!-- 滑块：通过 :style 动态控制位置和宽度 -->
        <div
          class="slider"
          :style="{
            transform: `translateX(${activeIndex * 100}%)`,
            width: `${100 / navItems.length}%`
          }"
        ></div>

        <!-- 导航项 -->
        <button
          v-for="(item, index) in navItems"
          :key="item.name"
          class="nav-item"
          :class="{ active: activeIndex === index }"
          @click="handleNav(index, item.path)"
        >
          <!-- 图标 -->
          <el-icon :size="24" class="nav-icon">
            <component :is="item.icon" />
          </el-icon>
          <!-- 文字 -->
          <span class="nav-text">{{ item.name }}</span>
        </button>
      </nav>
    </el-container>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Location, User, Menu, Setting } from '@element-plus/icons-vue'
import { useBackground } from '../composables/useBackground'

const { backgroundLayerStyle } = useBackground()

const router = useRouter()
const route = useRoute()

// 获取用户角色
const getUserRole = () => {
  try {
    const userInfo = localStorage.getItem('userInfo')
    if (userInfo) {
      const info = JSON.parse(userInfo)
      return info.role || 0
    }
    return 0
  } catch (error) {
    return 0
  }
}

// 新增：底部导航栏数据
const navItems = computed(() => {
  const baseItems = [
    { name: '主页', icon: Menu, path: '/home' },
    { name: '论坛', icon: Location, path: '/forum' }, // 对应你图片中间的图标
    { name: '我的', icon: User, path: '/profile' },
  ]
  
  // 如果是管理员，添加管理入口
  if (getUserRole() === 1) {
    baseItems.push({ name: '管理', icon: Setting, path: '/admin' })
  }
  
  return baseItems
})

// 当前激活的索引
const activeIndex = ref(0)

// 根据当前路由设置activeIndex
const setActiveIndexByRoute = () => {
  const currentPath = route.path
  const index = navItems.value.findIndex(item => item.path === currentPath)
  if (index !== -1) {
    activeIndex.value = index
  }
}

// 导航处理
const handleNav = (index, path) => {
  activeIndex.value = index
  router.push(path)
}

// 组件挂载时设置
onMounted(() => {
  setActiveIndexByRoute()
})

// 监听路由变化
watch(() => route.path, () => {
  setActiveIndexByRoute()
})
</script>

<style scoped>
/* 全局容器 */
.global-container {
  position: relative;
  width: 100%;
  min-height: 100vh;
  overflow: hidden;
}

/* 样式保持不变 */
.layout-container {    /* 关键修复：确保高度占满屏幕 */
  height: 100vh;
  /* 移除之前的 padding，交给内部组件处理 */
  padding: 0;
  overflow: hidden; }
/* 头部样式 */
.app-header {
  height: 60px;
  background: linear-gradient(135deg, #7aa0c6 0%, #a072b5 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  /* 防止被压缩 */
  flex-shrink: 0;
  /* filter: blur(2px); */
  backdrop-filter: blur(2px);
}
.header-content h2 { margin: 0; color: white; font-size: 20px; font-weight: 500; }
.app-main { padding: 0; overflow-y: auto; padding-bottom: 70px; }
/* .app-footer { height: 60px; padding: 0; background-color: #fff; border-top: 1px solid #e6e6e6; display: flex; justify-content: center; }
.footer-menu { width: 100%; border-right: none; justify-content: center; }
.el-menu--horizontal > .el-menu-item { height: 60px; line-height: 60px; font-size: 14px; color: #606266; }
.el-menu-item.is-active { background-color: #ecf5ff; color: #409eff; } */
/* 导航按钮 */
/* --- 底部导航栏核心样式 --- */
.bottom-nav {
  /* 1. 固定在底部 */
  position: fixed;
  bottom: 20px; /* 距离底部一点距离，更像卡片 */
  left: 50%;
  transform: translateX(-50%); /* 水平居中 */

  /* 2. 尺寸与外观 */
  width: 90%; /* 宽度占屏幕 90% */
  max-width: 400px; /* 最大宽度限制 */
  height: 60px;

  /* 3. 胶囊形状 */
  background-color: #f0f2f5; /* 浅灰底色 */
  border-radius: 30px; /* 大圆角 */
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08); /* 悬浮阴影 */

  /* 4. 布局 */
  display: flex;
  align-items: center;
  justify-content: space-around;

  /* 5. 关键修复：隐藏溢出 */
  /* 这会让蓝色的滑块在左右两端变成圆角 */
  overflow: hidden;

  /* 6. 层级 */
  z-index: 100;
}

/* 滑块样式 */
.slider {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  background-color: #409eff; /* 激活时的蓝色背景 */
  border-radius: 30px; /* 与父容器一致的圆角 */
  transition: transform 0.3s cubic-bezier(0.645, 0.045, 0.355, 1); /* 丝滑动画 */
  z-index: 1; /* 在按钮下面 */
}

/* 导航按钮 */
.nav-item {
  position: relative;
  z-index: 2; /* 确保文字在滑块之上 */
  background: transparent;
  border: none;
  outline: none;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  cursor: pointer;
  padding: 0;
  margin: 0;
}

/* 图标和文字颜色 */
.nav-icon, .nav-text {
  transition: color 0.3s;
  color: #aeb4bc; /* 未选中时的灰色 */
}

/* 激活状态文字变白 */
.nav-item.active .nav-icon,
.nav-item.active .nav-text {
  color: #ffffff;
}
</style>