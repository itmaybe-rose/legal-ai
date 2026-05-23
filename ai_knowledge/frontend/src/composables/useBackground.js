import { computed, inject, watch, ref } from 'vue'
import axios from 'axios'

// 背景设置的可复用逻辑
export function useBackground() {
  // 注入全局背景状态
  const backgroundState = inject('backgroundState')

  // 创建本地的响应式引用，当全局状态准备好时会被更新
  const localBackgroundImage = ref('')
  const localFontColor = ref('#303133')
  const localOpacity = ref(0.8)
  const localCountdownConfig = ref({
    title: '学期结束',
    targetDate: '2026-06-30 23:59:59'
  })

  // 从本地存储加载设置作为后备
  const loadFromLocalStorage = () => {
    const savedBackground = localStorage.getItem('homeBackground')
    const savedFontColor = localStorage.getItem('homeFontColor')
    const savedOpacity = localStorage.getItem('homeOpacity')
    const savedCountdownConfig = localStorage.getItem('countdownConfig')

    if (savedBackground) {
      localBackgroundImage.value = savedBackground
    }
    if (savedFontColor) {
      localFontColor.value = savedFontColor
    }
    if (savedOpacity) {
      localOpacity.value = parseFloat(savedOpacity)
    }
    if (savedCountdownConfig) {
      localCountdownConfig.value = JSON.parse(savedCountdownConfig)
    }
  }

  // 初始化时从本地存储加载
  loadFromLocalStorage()

  // 监听本地引用变化，更新到全局状态
  watch(localBackgroundImage, (newVal) => {
    if (backgroundState?.backgroundImage) {
      backgroundState.backgroundImage.value = newVal
    }
  })

  watch(localFontColor, (newVal) => {
    if (backgroundState?.fontColor) {
      backgroundState.fontColor.value = newVal
    }
  })

  watch(localOpacity, (newVal) => {
    if (backgroundState?.opacity) {
      backgroundState.opacity.value = newVal
    }
  })

  watch(localCountdownConfig, (newVal) => {
    if (backgroundState?.countdownConfig) {
      backgroundState.countdownConfig.value = newVal
    }
  }, { deep: true })

  // 监听全局状态变化，当全局状态准备好时更新本地引用
  if (backgroundState) {
    watch(() => backgroundState.backgroundImage?.value, (newVal) => {
      if (newVal !== undefined && newVal !== '') {
        localBackgroundImage.value = newVal
      }
    }, { immediate: true })

    watch(() => backgroundState.fontColor?.value, (newVal) => {
      if (newVal !== undefined && newVal !== '') {
        localFontColor.value = newVal
      }
    }, { immediate: true })

    watch(() => backgroundState.opacity?.value, (newVal) => {
      if (newVal !== undefined && newVal !== '') {
        localOpacity.value = newVal
      }
    }, { immediate: true })

    watch(() => backgroundState.countdownConfig?.value, (newVal) => {
      if (newVal && typeof newVal === 'object') {
        localCountdownConfig.value = newVal
      }
    }, { immediate: true, deep: true })
  }

  // 保存设置到后端
  const saveSettings = async () => {
    try {
      const token = localStorage.getItem('token')
      if (!token) return

      loading.value = true
      const data = {
        homeBackground: localBackgroundImage.value,
        homeFontColor: localFontColor.value,
        homeOpacity: localOpacity.value.toString(),
        countdownConfig: localCountdownConfig.value
      }

      await axios.put('/api/user/settings', data, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })
    } catch (error) {
      console.error('保存用户设置失败', error)
      console.error('错误详情:', error.response?.data)
    } finally {
      loading.value = false
    }
  }

  // 处理图片上传
  const handleImageChange = async (file) => {
    try {
      const token = localStorage.getItem('token')
      if (!token) return

      // 1. 立即用 FileReader 生成 base64 预览
      const reader = new FileReader()
      reader.onload = (e) => {
        localBackgroundImage.value = e.target.result
      }
      reader.readAsDataURL(file.raw)

      loading.value = true
      const formData = new FormData()
      formData.append('file', file.raw)

      const response = await axios.post('/api/user/upload-background', formData, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      })

      // 2. 上传成功后，更新为后端返回的正式 URL
      localBackgroundImage.value = response.data.url
      await saveSettings()
    } catch (error) {
      console.error('上传背景图片失败', error)
    } finally {
      loading.value = false
    }
  }

  // 移除背景图片
  const removeBackground = () => {
    localBackgroundImage.value = ''
    saveSettings()
  }

  // 计算容器样式
  const containerStyle = computed(() => {
    return {
      color: localFontColor.value
    }
  })

  // 计算背景层样式
  const backgroundLayerStyle = computed(() => {
    if (localBackgroundImage.value) {
      return {
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundImage: `url(${localBackgroundImage.value})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
        zIndex: -9999,
        pointerEvents: 'none',
        opacity: localOpacity.value
      }
    }

    return {
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: '#f0f2f5',
      zIndex: -9999,
      pointerEvents: 'none',
      opacity: 1
    }
  })

  const loading = ref(false)
  const isLoaded = ref(true)

  return {
    backgroundImage: localBackgroundImage,
    fontColor: localFontColor,
    opacity: localOpacity,
    countdownConfig: localCountdownConfig,
    isLoaded,
    loading,
    saveSettings,
    handleImageChange,
    removeBackground,
    containerStyle,
    backgroundLayerStyle
  }
}