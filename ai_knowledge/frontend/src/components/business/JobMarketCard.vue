<template>
  <div class="job-market-card">
    <div class="job-header">
      <h3>{{ job.name }}</h3>
      <el-tag :type="job.is_core ? 'danger' : 'info'" size="small">
        {{ job.is_core ? '核心必学' : '推荐掌握' }}
      </el-tag>
    </div>
    <div class="job-salary">💰 薪资范围: {{ job.salary }}</div>
    <div class="job-skills">
      <strong>关键技能:</strong>
      <div class="skill-tags">
        <el-tag 
          v-for="(skill, index) in job.skills" 
          :key="index" 
          size="small" 
          effect="plain"
        >
          {{ skill }}
        </el-tag>
      </div>
    </div>
    <div v-if="job.description" class="job-description">
      <strong>岗位描述:</strong>
      <p>{{ job.description }}</p>
    </div>
  </div>
</template>

<script setup>
defineProps({
  job: {
    type: Object,
    required: true
  }
})
</script>

<style scoped>
.job-market-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  transition: all 0.3s ease;
}

.job-market-card:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.job-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.job-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.job-salary {
  font-size: 14px;
  color: #67c23a;
  font-weight: 500;
  margin-bottom: 12px;
}

.job-skills {
  margin-bottom: 12px;
}

.job-skills strong {
  font-size: 13px;
  color: #606266;
}

.skill-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.job-description {
  border-top: 1px solid #ebeef5;
  padding-top: 12px;
}

.job-description strong {
  font-size: 13px;
  color: #606266;
}

.job-description p {
  font-size: 13px;
  color: #909399;
  line-height: 1.6;
  margin: 8px 0 0 0;
}
</style>