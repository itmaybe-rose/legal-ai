<template>
  <div class="schedule-container">
    <div class="schedule-header">
      <el-button class="back-btn" @click="goBack" circle>
        <el-icon size="18"><ArrowLeft /></el-icon>
      </el-button>
      <h2>📅 My Schedule</h2>
      <div class="header-actions">
        <el-upload
          class="upload-btn"
          action="#"
          :auto-upload="false"
          :on-change="handleScheduleUpload"
          accept="image/*"
          capture="environment"
        >
          <el-button type="primary" size="small" :loading="isUploading">
            <el-icon><Camera /></el-icon>
            {{ isUploading ? 'AI Recognizing...' : '📸 Upload Schedule' }}
          </el-button>
        </el-upload>
        <el-button size="small" @click="showAddDialog = true">
          <el-icon><Plus /></el-icon>
          Add Course
        </el-button>
      </div>
    </div>

    <div class="reminder-bar">
      <div class="reminder-left">
        <el-icon class="reminder-icon"><Opportunity /></el-icon>
        <span>🔔 Course Reminder</span>
      </div>
      <div class="reminder-right">
        <el-switch
          v-model="reminderEnabled"
          @change="handleReminderToggle"
          active-text="On"
          inactive-text="Off"
        />
        <el-select
          v-if="reminderEnabled"
          v-model="reminderMinutes"
          @change="handleReminderMinutesChange"
          size="small"
          style="width: 100px; margin-left: 10px;"
        >
          <el-option :value="10" label="10 min" />
          <el-option :value="20" label="20 min" />
          <el-option :value="30" label="30 min" />
        </el-select>
      </div>
    </div>

    <div class="test-mode-toggle">
      <el-switch
        v-model="isTestMode"
        active-text="Test Mode"
        inactive-text="Normal Mode"
        size="small"
      />
    </div>

    <div v-if="isTestMode" class="test-mode-bar">
      <div class="test-mode-header">
        <el-icon><Setting /></el-icon>
        <span>🎯 Test Mode</span>
      </div>
      <div class="test-mode-content">
        <div class="test-item">
          <label>Day:</label>
          <el-select v-model="testDay" size="small">
            <el-option :value="1" label="Mon" />
            <el-option :value="2" label="Tue" />
            <el-option :value="3" label="Wed" />
            <el-option :value="4" label="Thu" />
            <el-option :value="5" label="Fri" />
            <el-option :value="6" label="Sat" />
            <el-option :value="7" label="Sun" />
          </el-select>
        </div>
        <div class="test-item">
          <label>Time:</label>
          <el-time-picker
            v-model="testTime"
            format="HH:mm"
            size="small"
          />
        </div>
        <el-button size="small" type="primary" @click="testReminder">
          Test Reminder
        </el-button>
      </div>
    </div>

    <div class="ai-tip">
      <el-icon class="ai-icon"><Sparkles /></el-icon>
      <span>✨ Upload your schedule image and AI will automatically recognize the courses!</span>
    </div>

    <div class="schedule-content">
      <div class="time-column">
        <div class="time-header"></div>
        <div class="time-cell">08:30</div>
        <div class="time-cell">10:00</div>
        <div class="time-cell">10:20</div>
        <div class="time-cell">11:50</div>
        <div class="time-cell">14:00</div>
        <div class="time-cell">15:30</div>
        <div class="time-cell">15:50</div>
        <div class="time-cell">17:20</div>
        <div class="time-cell">18:40</div>
        <div class="time-cell">20:10</div>
        <div class="time-cell">21:30</div>
      </div>

      <div class="schedule-grid">
        <div class="day-header">
          <div class="day-cell">Mon</div>
          <div class="day-cell">Tue</div>
          <div class="day-cell">Wed</div>
          <div class="day-cell">Thu</div>
          <div class="day-cell">Fri</div>
          <div class="day-cell">Sat</div>
          <div class="day-cell">Sun</div>
        </div>
        <div class="schedule-body">
          <div class="period-row" v-for="period in 11" :key="period">
            <div
              class="course-cell"
              v-for="day in 7"
              :key="day"
              @click="handleCellClick(day, period)"
            >
              <div
                v-for="course in getCourseAt(day, period)"
                :key="course.id"
                class="course-item"
                :style="{ backgroundColor: course.color }"
                @click.stop="showCourseDetail(course)"
              >
                <span class="course-name">{{ course.name }}</span>
                <span class="course-info">{{ course.classroom }}</span>
                <el-icon class="delete-icon" @click.stop="deleteCourse(course.id)">
                  <Delete />
                </el-icon>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="courses.length === 0" class="empty-state">
      <el-icon class="empty-icon"><Calendar /></el-icon>
      <p>No courses scheduled</p>
      <p class="empty-hint">Click the button above to upload or add courses</p>
    </div>

    <el-dialog v-model="showAddDialog" title="Add Course" :width="dialogWidth">
      <el-form :model="newCourse" label-width="80px">
        <el-form-item label="Course Name">
          <el-input v-model="newCourse.name" placeholder="Enter course name" />
        </el-form-item>
        <el-form-item label="Day">
          <el-select v-model="newCourse.day_of_week">
            <el-option label="Monday" :value="1" />
            <el-option label="Tuesday" :value="2" />
            <el-option label="Wednesday" :value="3" />
            <el-option label="Thursday" :value="4" />
            <el-option label="Friday" :value="5" />
            <el-option label="Saturday" :value="6" />
            <el-option label="Sunday" :value="7" />
          </el-select>
        </el-form-item>
        <el-form-item label="Period">
          <el-select v-model="newCourse.period">
            <el-option label="Period 1-2 (08:30-10:00)" :value="'1-2'" />
            <el-option label="Period 3-4 (10:00-11:50)" :value="'3-4'" />
            <el-option label="Period 5-6 (14:00-15:30)" :value="'5-6'" />
            <el-option label="Period 7-8 (16:00-17:20)" :value="'7-8'" />
            <el-option label="Period 9-10 (18:40-20:10)" :value="'9-10'" />
          </el-select>
        </el-form-item>
        <el-form-item label="Classroom">
          <el-input v-model="newCourse.classroom" placeholder="Enter classroom" />
        </el-form-item>
        <el-form-item label="Teacher">
          <el-input v-model="newCourse.teacher" placeholder="Enter teacher name" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">Cancel</el-button>
        <el-button type="primary" @click="addCourse">Confirm</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showDetailDialog" title="Course Detail">
      <div v-if="selectedCourse" class="course-detail">
        <h3>{{ selectedCourse.name }}</h3>
        <div class="detail-row">
          <span class="label">Time: </span>
          <span>{{ getDayText(selectedCourse.day_of_week) }} Period {{ selectedCourse.period }}</span>
        </div>
        <div class="detail-row">
          <span class="label">Classroom: </span>
          <span>{{ selectedCourse.classroom || 'Not set' }}</span>
        </div>
        <div class="detail-row">
          <span class="label">Teacher: </span>
          <span>{{ selectedCourse.teacher || 'Not set' }}</span>
        </div>
        <div class="detail-row">
          <span class="label">Time Range: </span>
          <span>{{ selectedCourse.time_start || '--:--' }} - {{ selectedCourse.time_end || '--:--' }}</span>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Camera, Plus, Delete, Calendar, Opportunity, Setting, ArrowLeft } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { scheduleApi } from '../services/api'
import { useNotification, startCourseReminder, stopCourseReminder } from '../composables/useNotification'

const courses = ref([])
const showAddDialog = ref(false)
const showDetailDialog = ref(false)
const selectedCourse = ref(null)
const selectedFile = ref(null)
const isUploading = ref(false)
const reminderEnabled = ref(true)
const reminderMinutes = ref(20)
const isTestMode = ref(false)
const testDay = ref(1)
const testTime = ref(null)

const router = useRouter()
const goBack = () => {
  router.back()
}

let reminderInterval = null
const { requestNotificationPermission, checkNotificationPermission, showCourseReminder } = useNotification()

const newCourse = ref({
  name: '',
  day_of_week: 1,
  period: '1-2',
  classroom: '',
  teacher: ''
})

const dialogWidth = computed(() => {
  const screenWidth = window.innerWidth
  if (screenWidth < 768) return '90%'
  return '400px'
})

const getCourseAt = (day, period) => {
  const periodMap = {
    1: ['1', '1节', '1-2', '1-2节'],
    2: ['1', '1节', '1-2', '1-2节'],
    3: ['3', '3节', '3-4', '3-4节'],
    4: ['3', '3节', '3-4', '3-4节'],
    5: ['5', '5节', '5-6', '5-6节'],
    6: ['5', '5节', '5-6', '5-6节'],
    7: ['7', '7节', '7-8', '7-8节'],
    8: ['7', '7节', '7-8', '7-8节'],
    9: ['9', '9节', '9-10', '9-10节', '9-11', '9-11节'],
    10: ['9', '9节', '9-10', '9-10节', '9-11', '9-11节'],
    11: ['9', '9节', '9-10', '9-10节', '9-11', '9-11节']
  }
  const matched = courses.value.filter(c =>
    Number(c.day_of_week) === day && periodMap[period]?.includes(c.period)
  )
  return matched
}

const getDayText = (day) => {
  const days = ['', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
  return days[day] || ''
}

const handleScheduleUpload = async (file) => {
  selectedFile.value = file.raw
  isUploading.value = true

  try {
    ElMessage.info('📸 Uploading image... AI is recognizing your schedule...')

    const response = await scheduleApi.uploadSchedule(selectedFile.value)

    const count = response.data?.courses_count || 0
    ElMessage.success(`🎉 AI recognized ${count} courses! Schedule uploaded successfully!`)
    await loadSchedule()
  } catch (error) {
    console.error('Upload failed', error)
    ElMessage.error('Upload failed, please try again')
  } finally {
    isUploading.value = false
  }
}

const loadSchedule = async () => {
  try {
    const response = await scheduleApi.getSchedule()

    if (response.data && response.data.courses) {
      courses.value = response.data.courses
    }
  } catch (error) {
    console.error('Failed to get schedule', error)
  }
}

const addCourse = async () => {
  if (!newCourse.value.name.trim()) {
    ElMessage.warning('Please enter course name')
    return
  }

  try {
    const response = await scheduleApi.addCourse({
      name: newCourse.value.name,
      day_of_week: newCourse.value.day_of_week,
      period: newCourse.value.period,
      classroom: newCourse.value.classroom,
      teacher: newCourse.value.teacher
    })

    if (response.data.course) {
      courses.value.push(response.data.course)
    }

    ElMessage.success('Course added successfully!')
    showAddDialog.value = false

    newCourse.value = {
      name: '',
      day_of_week: 1,
      period: '1-2',
      classroom: '',
      teacher: ''
    }
  } catch (error) {
    console.error('Failed to add course', error)
    ElMessage.error('Failed to add course, please try again')
  }
}

const deleteCourse = async (courseId) => {
  try {
    await scheduleApi.deleteCourse(courseId)

    courses.value = courses.value.filter(c => c.id !== courseId)
    ElMessage.success('Course deleted successfully!')
  } catch (error) {
    console.error('Failed to delete course', error)
    ElMessage.error('Failed to delete course, please try again')
  }
}

const showCourseDetail = (course) => {
  selectedCourse.value = course
  showDetailDialog.value = true
}

const handleCellClick = (day, period) => {
  console.log(`Clicked ${getDayText(day)} period ${period}`)
}

const loadReminderSettings = async () => {
  try {
    const response = await scheduleApi.getReminderSettings()
    if (response.data) {
      reminderEnabled.value = response.data.enabled
      reminderMinutes.value = response.data.minutes
    }
  } catch (error) {
    console.error('Failed to load reminder settings', error)
  }
}

const handleReminderToggle = async (enabled) => {
  try {
    await scheduleApi.updateReminderSettings(enabled, reminderMinutes.value)
    ElMessage.success(enabled ? 'Course reminder enabled!' : 'Course reminder disabled')

    if (enabled) {
      await requestNotificationPermission()
      startReminder()
    } else {
      stopReminder()
    }
  } catch (error) {
    console.error('Failed to update reminder settings', error)
    ElMessage.error('Failed to update reminder settings')
  }
}

const handleReminderMinutesChange = async (minutes) => {
  try {
    await scheduleApi.updateReminderSettings(reminderEnabled.value, minutes)
    ElMessage.success(`Reminder time set to ${minutes} minutes before class`)

    if (reminderEnabled.value) {
      stopReminder()
      startReminder()
    }
  } catch (error) {
    console.error('Failed to update reminder minutes', error)
  }
}

const startReminder = async () => {
  stopReminder()

  const hasPermission = checkNotificationPermission()
  if (!hasPermission) {
    const granted = await requestNotificationPermission()
    if (!granted) {
      ElMessage.warning('Notification permission denied. Please enable it in browser settings.')
      return
    }
  }

  reminderInterval = startCourseReminder(async () => {
    try {
      const response = await scheduleApi.getUpcomingCourses(reminderMinutes.value)
      return response.data?.courses || []
    } catch (error) {
      console.error('Failed to check upcoming courses', error)
      return []
    }
  }, 60000)

  console.log('Course reminder started')
}

const stopReminder = () => {
  stopCourseReminder()
  reminderInterval = null
  console.log('Course reminder stopped')
}

const testReminder = async () => {
  if (!testTime.value || !testDay.value) {
    ElMessage.warning('Please select both day and time')
    return
  }

  try {
    const timeStr = testTime.value instanceof Date
      ? testTime.value.toTimeString().slice(0, 5)
      : testTime.value

    const response = await scheduleApi.getUpcomingCourses(reminderMinutes.value, timeStr, testDay.value)

    const upcomingCourses = response.data?.courses || []

    if (upcomingCourses.length > 0) {
      ElMessage.info(`Found ${upcomingCourses.length} upcoming course(s) for testing`)
      upcomingCourses.forEach(course => {
        showCourseReminder(course)
      })
    } else {
      ElMessage.info('No upcoming courses found for the selected time')
    }
  } catch (error) {
    console.error('Test reminder failed', error)
    ElMessage.error('Test reminder failed')
  }
}

onMounted(async () => {
  await loadSchedule()
  await loadReminderSettings()

  if (reminderEnabled.value) {
    await startReminder()
  }
})

onUnmounted(() => {
  stopReminder()
})
</script>

<style scoped>
.schedule-container {
  padding: 20px;
  min-height: 100vh;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 12px;
  margin: 10px;
}

.schedule-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 10px;
}

.back-btn {
  background: #f5f7fa;
  border: 1px solid #dcdfe6;
  color: #606266;
  transition: all 0.3s ease;
}

.back-btn:hover {
  background: #1e3a5f;
  border-color: #1e3a5f;
  color: #fff;
}

.schedule-header h2 {
  margin: 0;
  font-size: 20px;
  color: #303133;
}

.reminder-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: linear-gradient(135deg, #1e3a5f 0%, #0d9488 100%);
  border-radius: 12px;
  margin-bottom: 15px;
  color: #fff;
  flex-wrap: wrap;
  gap: 10px;
  box-shadow: 0 4px 20px rgba(30, 58, 95, 0.3);
}

.reminder-left {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

.reminder-icon {
  font-size: 18px;
  animation: bell 1s ease-in-out infinite;
}

@keyframes bell {
  0%, 100% { transform: rotate(0deg); }
  25% { transform: rotate(15deg); }
  75% { transform: rotate(-15deg); }
}

.reminder-right {
  display: flex;
  align-items: center;
}

.test-mode-toggle {
  margin-bottom: 15px;
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 6px;
  text-align: right;
}

.test-mode-bar {
  background: linear-gradient(135deg, #312e81 0%, #1e1b4b 100%);
  border-radius: 12px;
  padding: 15px;
  margin-bottom: 15px;
  color: #fff;
  box-shadow: 0 4px 20px rgba(49, 46, 129, 0.3);
}

.test-mode-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  margin-bottom: 12px;
}

.test-mode-content {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
  align-items: center;
}

.test-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.test-mode-bar :deep(.el-select),
.test-mode-bar :deep(.el-time-picker) {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.test-mode-bar :deep(.el-select .el-input__inner),
.test-mode-bar :deep(.el-time-picker .el-input__inner) {
  color: #fff;
  background: transparent;
}

.test-mode-bar :deep(.el-select .el-input__icon),
.test-mode-bar :deep(.el-time-picker .el-input__icon) {
  color: rgba(255, 255, 255, 0.7);
}

.ai-tip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 18px;
  background: linear-gradient(135deg, #537ad5 0%, #5778e7 100%);
  border-radius: 12px;
  margin-bottom: 20px;
  color: #e2e8f0;
  font-size: 14px;
  border: 1px solid rgba(15, 132, 227, 0.2);
}

.ai-icon {
  font-size: 18px;
  opacity: 0.8;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.schedule-content {
  display: flex;
  overflow-x: auto;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  -webkit-overflow-scrolling: touch;
}

.time-column {
  min-width: 50px;
  border-right: 1px solid #e4e7ed;
  flex-shrink: 0;
}

.time-header {
  height: 40px;
  border-bottom: 1px solid #e4e7ed;
}

.time-cell {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  color: #909399;
  border-bottom: 1px solid #e4e7ed;
}

.schedule-grid {
  flex: 1;
  min-width: 300px;
}

.day-header {
  display: flex;
  border-bottom: 1px solid #e4e7ed;
}

.day-cell {
  flex: 1;
  min-width: 60px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 500;
  font-size: 12px;
  color: #606266;
  border-right: 1px solid #e4e7ed;
}

.day-cell:last-child {
  border-right: none;
}

.schedule-body {
  display: flex;
  flex-direction: column;
}

.period-row {
  display: flex;
}

.course-cell {
  flex: 1;
  min-width: 60px;
  height: 60px;
  border-right: 1px solid #e4e7ed;
  border-bottom: 1px solid #e4e7ed;
  position: relative;
  overflow: hidden;
  cursor: pointer;
}

.course-item {
  position: absolute;
  top: 2px;
  left: 2px;
  right: 2px;
  bottom: 2px;
  border-radius: 4px;
  padding: 4px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  cursor: pointer;
}

.course-name {
  font-size: 12px;
  color: #fff;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.3;
}

.course-info {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.8);
  margin-top: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.delete-icon {
  position: absolute;
  top: 2px;
  right: 2px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
  opacity: 0;
  transition: opacity 0.2s;
}

.course-item:hover .delete-icon {
  opacity: 1;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.empty-icon {
  font-size: 64px;
  color: #c0c4cc;
  margin-bottom: 16px;
}

.empty-state p {
  margin: 8px 0;
  color: #909399;
}

.empty-hint {
  font-size: 14px;
}

.course-detail h3 {
  margin: 0 0 16px 0;
  color: #303133;
}

.detail-row {
  margin-bottom: 12px;
  font-size: 14px;
}

.detail-row .label {
  color: #909399;
  margin-right: 8px;
}

@media (max-width: 768px) {
  .schedule-container {
    padding: 10px;
    margin: 5px;
  }

  .schedule-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .reminder-bar {
    flex-direction: column;
    align-items: flex-start;
  }

  .reminder-right {
    margin-top: 10px;
  }

  .test-mode-content {
    flex-direction: column;
    align-items: flex-start;
  }

  .schedule-content {
    font-size: 12px;
  }

  .time-column {
    min-width: 50px;
  }

  .time-cell {
    height: 50px;
    font-size: 10px;
  }

  .day-cell {
    min-width: 70px;
    height: 35px;
    font-size: 11px;
  }

  .course-cell {
    min-width: 70px;
    height: 50px;
  }

  .course-name {
    font-size: 9px;
  }

  .course-info {
    font-size: 8px;
  }
}
</style>