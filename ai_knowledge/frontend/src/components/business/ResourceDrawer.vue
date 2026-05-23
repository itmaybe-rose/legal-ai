<template>
  <el-drawer
    :model-value="visible"
    @update:model-value="$emit('update:visible', $event)"
    :title="title"
    direction="rtl"
    size="350px"
  >
    <div v-if="loading" class="loading-state">
      <el-skeleton style="width: 100%" animated>
        <template #template>
          <el-skeleton-item variant="p" style="width: 80%" />
          <el-skeleton-item variant="p" style="width: 60%" />
        </template>
      </el-skeleton>
      <el-skeleton style="width: 100%" animated>
        <template #template>
          <el-skeleton-item variant="p" style="width: 70%" />
          <el-skeleton-item variant="p" style="width: 50%" />
        </template>
      </el-skeleton>
      <p class="loading-text">正在获取学习资源...</p>
    </div>
    
    <div v-else class="drawer-content">
      <!-- 学习进度板块 -->
      <div class="section">
        <div class="section-header">
          <h4 class="section-title">✅ 学习进度</h4>
        </div>
        <div class="progress-card">
          <div class="progress-header">
            <span class="progress-label">掌握状态</span>
            <el-tag :type="progressStatus === 'completed' ? 'success' : 'warning'">
              {{ progressStatus === 'completed' ? '已掌握' : '学习中' }}
            </el-tag>
          </div>
          <el-progress 
            :percentage="progress" 
            :status="progress === 100 ? 'success' : 'active'"
            :show-text="false"
          />
          <div class="progress-text">{{ progress }}% 完成</div>
          <el-button 
            size="small" 
            :type="progress === 100 ? 'default' : 'primary'"
            @click="handleToggleProgress"
            class="progress-btn"
          >
            {{ progress === 100 ? '标记未完成' : '标记已掌握' }}
          </el-button>
        </div>
      </div>

      <!-- 视频教程板块 -->
      <div class="section">
        <div class="section-header">
          <h4 class="section-title">📺 视频教程</h4>
        </div>
        <div v-if="videos.length > 0" class="video-list">
          <div 
            v-for="(video, index) in videos" 
            :key="index" 
            class="video-item"
          >
            <el-link :href="video.url" target="_blank" underline="never">
              <el-icon><VideoCamera /></el-icon>
              {{ video.title }}
            </el-link>
          </div>
        </div>
        <div v-else class="empty-video">
          <el-icon :size="32" class="empty-icon"><VideoCamera /></el-icon>
          <p>暂无相关视频教程</p>
        </div>
      </div>
    </div>
  </el-drawer>
</template>

<script setup>
import { computed } from 'vue'
import { VideoCamera } from '@element-plus/icons-vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  title: {
    type: String,
    default: ''
  },
  videos: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  progress: {
    type: Number,
    default: 0
  }
})

const emit = defineEmits(['update:visible', 'toggle-progress'])

const progressStatus = computed(() => {
  return props.progress === 100 ? 'completed' : 'in-progress'
})

const handleToggleProgress = () => {
  emit('toggle-progress')
}
</script>

<style scoped>
.drawer-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.section {
  background: #fafafa;
  border-radius: 12px;
  padding: 16px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
  color: #303133;
}

.progress-card {
  background: #fff;
  padding: 16px;
  border-radius: 8px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.progress-label {
  font-size: 14px;
  color: #606266;
}

.progress-text {
  text-align: right;
  font-size: 12px;
  color: #909399;
  margin-top: 8px;
}

.progress-btn {
  width: 100%;
  margin-top: 12px;
}

.video-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.video-item {
  padding: 12px;
  background: #fff;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.video-item:hover {
  background: #e9ecef;
  transform: translateX(-2px);
}

.empty-video {
  text-align: center;
  padding: 24px 0;
  color: #909399;
}

.empty-icon {
  color: #c0c4cc;
  margin-bottom: 8px;
}

.loading-state {
  padding: 20px;
}

.loading-text {
  text-align: center;
  color: #909399;
  margin-top: 16px;
}
</style>
