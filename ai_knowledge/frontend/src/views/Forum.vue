<template>
  <div class="forum-container">
    <el-card class="forum-header">
      <div class="header-action">
        <h3>🔥 校园热议</h3>
        <el-button type="primary" size="small" round>发布帖子</el-button>
      </div>
    </el-card>

    <div class="post-list">
      <el-card v-for="i in 5" :key="i" shadow="hover" class="post-item">
        <div class="post-tag">
          <el-tag size="small" type="info">求助</el-tag>
        </div>
        <h4>济南最近降温了，图书馆占座攻略有人知道吗？</h4>
        <div class="post-footer">
          <span class="author">用户 12345</span>
          <span class="time">10分钟前</span>
        </div>
      </el-card>
    </div>
  </div>
</template>

<style scoped>
.forum-container { padding: 15px; }
.header-action { display: flex; justify-content: space-between; align-items: center; }
.header-action h3 { margin: 0; }

.post-item { margin-bottom: 15px; cursor: pointer; }
.post-tag { margin-bottom: 8px; }
.post-item h4 { margin: 0 0 10px 0; font-size: 16px; color: #303133; }
.post-footer { display: flex; justify-content: space-between; font-size: 12px; color: #909399; }
</style>