<template>
  <router-view />
</template>
<!--这样页面才能显示我们定义的路由组件-->
 

<script setup>
import { ref, provide, onMounted, watch } from 'vue'
import axios from './utils/axios'

// 创建全局背景状态
const backgroundImage = ref('')
const fontColor = ref('#303133')
const opacity = ref(0.8)

// 创建全局倒计时配置
const countdownConfig = ref({
  title: '学期结束',
  targetDate: '2026-06-30 23:59:59'
})

// 从本地存储加载设置
const loadSettingsFromLocal = () => {
  const savedBackground = localStorage.getItem('homeBackground')
  const savedFontColor = localStorage.getItem('homeFontColor')
  const savedOpacity = localStorage.getItem('homeOpacity')
  const savedCountdownConfig = localStorage.getItem('countdownConfig')

  if (savedBackground) {
    backgroundImage.value = savedBackground
  }

  if (savedFontColor) {
    fontColor.value = savedFontColor
  }

  if (savedOpacity) {
    opacity.value = parseFloat(savedOpacity)
  }

  if (savedCountdownConfig) {
    countdownConfig.value = JSON.parse(savedCountdownConfig)
  }
}

// 保存设置到本地存储
const saveSettingsToLocal = () => {
  if (backgroundImage.value) {
    localStorage.setItem('homeBackground', backgroundImage.value)
  }
  if (fontColor.value) {
    localStorage.setItem('homeFontColor', fontColor.value)
  }
  if (opacity.value) {
    localStorage.setItem('homeOpacity', opacity.value.toString())
  }
  // 只有当 countdownConfig 不是默认值时才保存，避免覆盖本地存储的设置
  if (countdownConfig.value.title !== '学期结束' || countdownConfig.value.targetDate !== '2026-06-30 23:59:59') {
    localStorage.setItem('countdownConfig', JSON.stringify(countdownConfig.value))
  }
}

// 从后端获取设置
const loadSettings = async () => {
  try {
    const token = localStorage.getItem('token')
    if (!token) {
      loadSettingsFromLocal()
      return
    }

    const response = await axios.get('/api/user/settings', {
      headers: { 'Authorization': `Bearer ${token}` }
    })

    const settings = response.data
    // 只有当后端返回的设置有值时，才更新本地值
    // 这样可以避免后端返回空值时覆盖本地存储的设置
    if (settings.homeBackground && settings.homeBackground !== '') {
      backgroundImage.value = settings.homeBackground
    }
    if (settings.homeFontColor && settings.homeFontColor !== '') {
      fontColor.value = settings.homeFontColor
    }
    if (settings.homeOpacity && settings.homeOpacity !== '') {
      opacity.value = settings.homeOpacity
    }
    // 检查countdownConfig是否是有效的对象，且包含必要的属性
    if (settings.countdownConfig && typeof settings.countdownConfig === 'object' && settings.countdownConfig.title && settings.countdownConfig.targetDate) {
      countdownConfig.value = settings.countdownConfig
    } else {
      // 如果后端没有返回有效的 countdownConfig，使用本地存储的值
      const savedCountdownConfig = localStorage.getItem('countdownConfig')
      if (savedCountdownConfig) {
        countdownConfig.value = JSON.parse(savedCountdownConfig)
      }
    }

    saveSettingsToLocal()
  } catch (error) {
    console.error('获取用户设置失败', error)
    loadSettingsFromLocal()
  }
}

// 监听状态变化，自动保存到本地存储
watch(backgroundImage, saveSettingsToLocal)
watch(fontColor, saveSettingsToLocal)
watch(opacity, saveSettingsToLocal)
watch(countdownConfig, (newVal) => {
  // 只有当 countdownConfig 不是默认值时才保存，避免覆盖本地存储的设置
  if (newVal.title !== '学期结束' || newVal.targetDate !== '2026-06-30 23:59:59') {
    saveSettingsToLocal()
  }
}, { deep: true })

// 提供全局状态
provide('backgroundState', {
  backgroundImage,
  fontColor,
  opacity,
  countdownConfig,
  loadSettings
})

// 初始化加载设置
onMounted(() => {
  loadSettings()
})
</script>