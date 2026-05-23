import { ref, onMounted, onUnmounted } from 'vue'
import { ElNotification } from 'element-plus'

const notifiedCourses = ref(new Set())

export function useNotification() {
  const checkNotificationPermission = () => {
    if (!('Notification' in window)) {
      console.warn('浏览器不支持通知')
      return false
    }
    return Notification.permission === 'granted'
  }

  const requestNotificationPermission = async () => {
    if (!('Notification' in window)) {
      console.warn('浏览器不支持通知')
      return false
    }

    if (Notification.permission === 'granted') {
      return true
    }

    if (Notification.permission !== 'denied') {
      const permission = await Notification.requestPermission()
      return permission === 'granted'
    }

    return false
  }

  const showBrowserNotification = (title, options = {}) => {
    if (checkNotificationPermission()) {
      const notification = new Notification(title, {
        icon: '/favicon.ico',
        badge: '/favicon.ico',
        ...options
      })

      notification.onclick = () => {
        window.focus()
        notification.close()
      }

      setTimeout(() => notification.close(), 10000)
    }
  }

  const showCourseReminder = (course) => {
    const courseKey = `${course.id}-${course.name}-${Date.now()}`

    if (notifiedCourses.value.has(courseKey)) {
      return false
    }

    notifiedCourses.value.add(courseKey)
    setTimeout(() => {
      notifiedCourses.value.delete(courseKey)
    }, 60000)

    const title = `${course.name} 即将开始！🔈请注意单双周`
    const body = `时间: ${course.time_start} - ${course.time_end}\n教室: ${course.classroom}\n教师: ${course.teacher || '未知'}`

    showBrowserNotification(title, {
      body,
      tag: `course-${course.id}`,
      requireInteraction: true
    })

    ElNotification({
      title: `${course.name} 即将开始！🔈请注意单双周`,
      message: `时间: ${course.time_start} - ${course.time_end}\n教室: ${course.classroom}`,
      type: 'warning',
      duration: 0,
      position: 'top-right'
    })

    return true
  }

  const showElNotification = (title, message, type = 'info') => {
    ElNotification({
      title,
      message,
      type,
      position: 'top-right'
    })
  }

  return {
    checkNotificationPermission,
    requestNotificationPermission,
    showBrowserNotification,
    showCourseReminder,
    showElNotification
  }
}

let reminderInterval = null

export function startCourseReminder(checkFn, intervalMs = 60000) {
  stopCourseReminder()

  reminderInterval = setInterval(async () => {
    try {
      const upcomingCourses = await checkFn()
      if (upcomingCourses && upcomingCourses.length > 0) {
        const { showCourseReminder } = useNotification()
        upcomingCourses.forEach(course => {
          showCourseReminder(course)
        })
      }
    } catch (error) {
      console.error('检查课程提醒失败:', error)
    }
  }, intervalMs)

  return reminderInterval
}

export function stopCourseReminder() {
  if (reminderInterval) {
    clearInterval(reminderInterval)
    reminderInterval = null
  }
}