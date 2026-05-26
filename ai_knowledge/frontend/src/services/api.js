import axios from '../utils/axios'

// 规划相关API
export const planApi = {
  generatePlan: (major, goal, job = null) => {
    const formData = new FormData()
    formData.append('major', major)
    formData.append('goal', goal)
    if (job) formData.append('job', job)
    return axios.post('/api/generate_plan', formData)
  },

  recommendBooks: (course) => {
    const formData = new FormData()
    formData.append('course', course)
    return axios.post('/api/recommend_books', formData)
  }
}

// 用户相关API
export const userApi = {
  login: (username, password) => {
    return axios.post('/api/users/login', { username, password })
  },

  register: (username, password) => {
    return axios.post('/api/users/register', { username, password })
  },

  getProfile: () => {
    return axios.get('/api/users/profile')
  },

  updateProfile: (data) => {
    return axios.put('/api/users/profile', data)
  }
}

// 论坛相关API
export const forumApi = {
  getPosts: (page = 1, limit = 10) => {
    return axios.get(`/api/forum/posts?page=${page}&limit=${limit}`)
  },

  createPost: (title, content) => {
    return axios.post('/api/forum/posts', { title, content })
  },

  getPostDetail: (id) => {
    return axios.get(`/api/forum/posts/${id}`)
  },

  addComment: (postId, content, parentId = null) => {
    return axios.post('/api/forum/comments', { post_id: postId, content, parent_id: parentId })
  },

  likePost: (postId) => {
    return axios.post(`/api/forum/posts/${postId}/like`)
  }
}

// 生活相关API
export const lifeApi = {
  getHeatingPlan: (district, housingType, area, duration, isCommercial) => {
    return axios.post('/api/life/heating_plan', {
      district,
      housing_type: housingType,
      area,
      duration,
      is_commercial: isCommercial
    })
  }
}

// 课程表相关API
export const scheduleApi = {
  uploadSchedule: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return axios.post('/api/user/upload-schedule', formData, {
      headers: { 'Content-Type': undefined }
    })
  },

  getSchedule: () => {
    return axios.get('/api/user/schedule')
  },

  addCourse: (data) => {
    return axios.post('/api/user/schedule/course', data)
  },

  deleteCourse: (courseId) => {
    return axios.delete(`/api/user/schedule/course/${courseId}`)
  },

  getUpcomingCourses: (minutes = 20, testTime = null, testDay = null) => {
    const params = { minutes }
    if (testTime) params.test_time = testTime
    if (testDay) params.test_day = testDay
    return axios.get('/api/user/schedule/upcoming', { params })
  },

  getReminderSettings: () => {
    return axios.get('/api/user/settings/reminder')
  },

  updateReminderSettings: (enabled, minutes) => {
    return axios.put('/api/user/settings/reminder', { enabled, minutes })
  }
}

export default {
  plan: planApi,
  user: userApi,
  forum: forumApi,
  life: lifeApi,
  schedule: scheduleApi
}