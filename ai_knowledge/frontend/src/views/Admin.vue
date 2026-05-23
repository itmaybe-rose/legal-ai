<template>
  <div class="admin-container">
    <div class="admin-header">
      <h2>后台管理系统</h2>
      <p class="subtitle">管理所有系统功能</p>
    </div>

    <el-tabs v-model="activeTab" class="admin-tabs" type="border-card">
      <!-- 系统概览 -->
      <el-tab-pane label="系统概览" name="dashboard">
        <div class="tab-content">
          <div class="stats-grid">
            <div class="stat-card">
              <div class="stat-icon user-icon">U</div>
              <div class="stat-info">
                <span class="stat-value">{{ dashboard.total_users }}</span>
                <span class="stat-label">总用户数</span>
                <span class="stat-today">今日 +{{ dashboard.today_users }}</span>
              </div>
            </div>
            <div class="stat-card">
              <div class="stat-icon post-icon">P</div>
              <div class="stat-info">
                <span class="stat-value">{{ dashboard.total_posts }}</span>
                <span class="stat-label">总帖子数</span>
                <span class="stat-today">今日 +{{ dashboard.today_posts }}</span>
              </div>
            </div>
            <div class="stat-card">
              <div class="stat-icon comment-icon">C</div>
              <div class="stat-info">
                <span class="stat-value">{{ dashboard.total_comments }}</span>
                <span class="stat-label">总评论数</span>
                <span class="stat-today">今日 +{{ dashboard.today_comments }}</span>
              </div>
            </div>
            <div class="stat-card">
              <div class="stat-icon like-icon">L</div>
              <div class="stat-info">
                <span class="stat-value">{{ dashboard.total_likes }}</span>
                <span class="stat-label">总点赞数</span>
              </div>
            </div>
          </div>

          <div class="dashboard-section">
            <h3>活跃用户 Top 10</h3>
            <el-table :data="dashboard.active_users" style="width: 100%" stripe>
              <el-table-column type="index" label="排名" width="60" />
              <el-table-column prop="name" label="用户名" />
              <el-table-column prop="post_count" label="发帖数" width="100" />
              <el-table-column prop="comment_count" label="评论数" width="100" />
              <el-table-column prop="score" label="积分" width="100" />
            </el-table>
          </div>
        </div>
      </el-tab-pane>

      <!-- 用户管理 -->
      <el-tab-pane label="用户管理" name="users">
        <div class="tab-content">
          <div class="action-bar">
            <el-button type="primary" @click="refreshUsers" :icon="'Refresh'">刷新列表</el-button>
            <el-input v-model="userKeyword" placeholder="搜索用户名/昵称/专业" clearable style="width: 250px" @keyup.enter="refreshUsers" />
          </div>
          <el-table :data="users" style="width: 100%" stripe v-loading="loading.users">
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="username" label="用户名" width="100" />
            <el-table-column prop="name" label="昵称" width="100">
              <template #default="{ row }">{{ row.name || '-' }}</template>
            </el-table-column>
            <el-table-column prop="major" label="专业" />
            <el-table-column prop="grade" label="年级" width="80" />
            <el-table-column prop="post_count" label="帖子" width="60" />
            <el-table-column prop="comment_count" label="评论" width="60" />
            <el-table-column prop="score" label="积分" width="70" />
            <el-table-column prop="role" label="角色" width="100">
              <template #default="{ row }">
                <el-select v-model="row.role" @change="updateUserRole(row.id, row.role)" size="small">
                  <el-option label="学生" :value="0" />
                  <el-option label="管理员" :value="1" />
                </el-select>
              </template>
            </el-table-column>
            <el-table-column prop="create_time" label="注册时间" width="170">
              <template #default="{ row }">{{ formatTime(row.create_time) }}</template>
            </el-table-column>
            <el-table-column label="操作" width="80" fixed="right">
              <template #default="{ row }">
                <el-popconfirm title="确定删除此用户吗？" @confirm="deleteUser(row.id)">
                  <template #reference>
                    <el-button type="danger" size="small" text>删除</el-button>
                  </template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
          <div class="pagination-info">共 {{ userTotal }} 条记录</div>
        </div>
      </el-tab-pane>

      <!-- 帖子管理 -->
      <el-tab-pane label="帖子管理" name="posts">
        <div class="tab-content">
          <div class="action-bar">
            <el-button type="primary" @click="refreshPosts" :icon="'Refresh'">刷新列表</el-button>
            <el-input v-model="postKeyword" placeholder="搜索帖子标题/内容" clearable style="width: 250px" @keyup.enter="refreshPosts" />
            <el-select v-model="postStatusFilter" placeholder="状态筛选" clearable style="width: 120px" @change="refreshPosts">
              <el-option label="正常" :value="0" />
              <el-option label="审核中" :value="1" />
              <el-option label="违规" :value="2" />
            </el-select>
          </div>
          <el-table :data="posts" style="width: 100%" stripe v-loading="loading.posts">
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="author" label="作者" width="100" />
            <el-table-column prop="title" label="标题" min-width="180">
              <template #default="{ row }">
                <span class="post-title-text">{{ row.title }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="category" label="分类" width="80" />
            <el-table-column prop="view_count" label="浏览" width="60" />
            <el-table-column prop="like_count" label="点赞" width="60" />
            <el-table-column prop="comment_count" label="评论" width="60" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 0 ? 'success' : row.status === 1 ? 'warning' : 'danger'" size="small">
                  {{ row.status === 0 ? '正常' : row.status === 1 ? '审核' : '违规' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="状态操作" width="180">
              <template #default="{ row }">
                <el-button size="small" :type="row.status !== 0 ? 'success' : ''" @click="updatePostStatus(row.id, 0)" :disabled="row.status === 0">正常</el-button>
                <el-button size="small" :type="row.status !== 1 ? 'warning' : ''" @click="updatePostStatus(row.id, 1)" :disabled="row.status === 1">审核</el-button>
                <el-button size="small" :type="row.status !== 2 ? 'danger' : ''" @click="updatePostStatus(row.id, 2)" :disabled="row.status === 2">违规</el-button>
              </template>
            </el-table-column>
            <el-table-column label="删除" width="60" fixed="right">
              <template #default="{ row }">
                <el-popconfirm title="确定删除此帖子吗？" @confirm="deletePost(row.id)">
                  <template #reference>
                    <el-button type="danger" size="small" text>删除</el-button>
                  </template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
          <div class="pagination-info">共 {{ postTotal }} 条记录</div>
        </div>
      </el-tab-pane>

      <!-- 评论管理 -->
      <el-tab-pane label="评论管理" name="comments">
        <div class="tab-content">
          <div class="action-bar">
            <el-button type="primary" @click="refreshComments" :icon="'Refresh'">刷新列表</el-button>
            <el-input v-model="commentKeyword" placeholder="搜索评论内容" clearable style="width: 250px" @keyup.enter="refreshComments" />
          </div>
          <el-table :data="comments" style="width: 100%" stripe v-loading="loading.comments">
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="author" label="评论人" width="100" />
            <el-table-column prop="post_title" label="所属帖子" min-width="180">
              <template #default="{ row }">
                <span class="post-title-text">{{ row.post_title }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="content" label="评论内容" min-width="250">
              <template #default="{ row }">{{ row.content }}</template>
            </el-table-column>
            <el-table-column prop="create_time" label="评论时间" width="170">
              <template #default="{ row }">{{ formatTime(row.create_time) }}</template>
            </el-table-column>
            <el-table-column label="操作" width="80" fixed="right">
              <template #default="{ row }">
                <el-popconfirm title="确定删除此评论吗？" @confirm="deleteComment(row.id)">
                  <template #reference>
                    <el-button type="danger" size="small" text>删除</el-button>
                  </template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
          <div class="pagination-info">共 {{ commentTotal }} 条记录</div>
        </div>
      </el-tab-pane>

      <!-- 专业管理 -->
      <el-tab-pane label="专业管理" name="majors">
        <div class="tab-content">
          <div class="action-bar">
            <el-button type="primary" @click="showAddMajorDialog = true" :icon="'Plus'">添加专业</el-button>
          </div>
          <el-table :data="majors" style="width: 100%" stripe v-loading="loading.majors">
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="name" label="专业名称" />
            <el-table-column prop="college" label="所属学院" />
            <el-table-column label="操作" width="80">
              <template #default="{ row }">
                <el-popconfirm title="确定删除此专业吗？" @confirm="deleteMajor(row.id)">
                  <template #reference>
                    <el-button type="danger" size="small" text>删除</el-button>
                  </template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>

      <!-- 分类统计 -->
      <el-tab-pane label="分类统计" name="categories">
        <div class="tab-content">
          <div class="category-chart">
            <div class="category-card" v-for="cat in categories" :key="cat.name">
              <div class="category-name">{{ cat.name }}</div>
              <div class="category-count">{{ cat.count }} 篇帖子</div>
              <el-progress :percentage="getCategoryPercent(cat.count)" :color="categoryColors[cat.name]" />
            </div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 添加专业对话框 -->
    <el-dialog v-model="showAddMajorDialog" title="添加专业" width="400px">
      <el-form :model="majorForm" label-width="80px">
        <el-form-item label="专业名称" required>
          <el-input v-model="majorForm.name" placeholder="请输入专业名称" />
        </el-form-item>
        <el-form-item label="所属学院">
          <el-input v-model="majorForm.college" placeholder="请输入所属学院" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddMajorDialog = false">取消</el-button>
        <el-button type="primary" @click="addMajor" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from '../utils/axios'
import { ElMessage } from 'element-plus'

const activeTab = ref('dashboard')

// 加载状态
const loading = ref({ users: false, posts: false, comments: false, majors: false })
const submitting = ref(false)

// 系统概览
const dashboard = ref({
  total_users: 0, total_posts: 0, total_comments: 0, total_likes: 0,
  today_users: 0, today_posts: 0, today_comments: 0,
  active_users: []
})

// 用户管理
const users = ref([])
const userTotal = ref(0)
const userKeyword = ref('')

// 帖子管理
const posts = ref([])
const postTotal = ref(0)
const postKeyword = ref('')
const postStatusFilter = ref(null)

// 评论管理
const comments = ref([])
const commentTotal = ref(0)
const commentKeyword = ref('')

// 专业管理
const majors = ref([])
const showAddMajorDialog = ref(false)
const majorForm = ref({ name: '', college: '' })

// 分类统计
const categories = ref([])
const categoryColors = { '讨论': '#409eff', '求助': '#e6a23c', '分享': '#67c23a', '通知': '#f56c6c' }

const getCategoryPercent = (count) => {
  const max = Math.max(...categories.value.map(c => c.count), 1)
  return Math.round((count / max) * 100)
}

const formatTime = (time) => {
  if (!time) return '-'
  const d = new Date(time)
  return d.toLocaleString('zh-CN', { hour12: false })
}

// 加载概览数据
const refreshDashboard = async () => {
  try {
    const res = await axios.get('/api/admin/dashboard')
    dashboard.value = res.data
  } catch (error) {
    console.error('获取概览数据失败:', error)
  }
}

// 加载用户列表
const refreshUsers = async () => {
  loading.value.users = true
  try {
    const params = { keyword: userKeyword.value }
    const response = await axios.get('/api/admin/users', { params })
    users.value = response.data.users || []
    userTotal.value = response.data.total || 0
  } catch (error) {
    console.error('获取用户列表失败:', error)
  } finally {
    loading.value.users = false
  }
}

// 更新用户角色
const updateUserRole = async (userId, role) => {
  try {
    const formData = new FormData()
    formData.append('role', role)
    await axios.put(`/api/admin/users/${userId}/role`, formData)
    ElMessage.success('角色更新成功')
  } catch (error) {
    console.error('更新用户角色失败:', error)
    ElMessage.error('更新失败')
  }
}

// 删除用户
const deleteUser = async (userId) => {
  try {
    await axios.delete(`/api/admin/users/${userId}`)
    ElMessage.success('用户已删除')
    refreshUsers()
  } catch (error) {
    console.error('删除用户失败:', error)
    ElMessage.error('删除失败')
  }
}

// 加载帖子列表
const refreshPosts = async () => {
  loading.value.posts = true
  try {
    const params = { keyword: postKeyword.value }
    if (postStatusFilter.value !== null && postStatusFilter.value !== '') {
      params.status = postStatusFilter.value
    }
    const response = await axios.get('/api/admin/posts', { params })
    posts.value = response.data.posts || []
    postTotal.value = response.data.total || 0
  } catch (error) {
    console.error('获取帖子列表失败:', error)
  } finally {
    loading.value.posts = false
  }
}

// 更新帖子状态
const updatePostStatus = async (postId, status) => {
  try {
    const formData = new FormData()
    formData.append('status', status)
    await axios.put(`/api/admin/posts/${postId}/status`, formData)
    ElMessage.success('状态更新成功')
    refreshPosts()
  } catch (error) {
    console.error('更新帖子状态失败:', error)
    ElMessage.error('更新失败')
  }
}

// 删除帖子
const deletePost = async (postId) => {
  try {
    await axios.delete(`/api/admin/posts/${postId}`)
    ElMessage.success('帖子已删除')
    refreshPosts()
  } catch (error) {
    console.error('删除帖子失败:', error)
    ElMessage.error('删除失败')
  }
}

// 加载评论列表
const refreshComments = async () => {
  loading.value.comments = true
  try {
    const params = { keyword: commentKeyword.value }
    const response = await axios.get('/api/admin/comments', { params })
    comments.value = response.data.comments || []
    commentTotal.value = response.data.total || 0
  } catch (error) {
    console.error('获取评论列表失败:', error)
  } finally {
    loading.value.comments = false
  }
}

// 删除评论
const deleteComment = async (commentId) => {
  try {
    await axios.delete(`/api/admin/comments/${commentId}`)
    ElMessage.success('评论已删除')
    refreshComments()
  } catch (error) {
    console.error('删除评论失败:', error)
    ElMessage.error('删除失败')
  }
}

// 加载专业列表
const refreshMajors = async () => {
  loading.value.majors = true
  try {
    const response = await axios.get('/api/admin/majors')
    majors.value = response.data.majors || []
  } catch (error) {
    console.error('获取专业列表失败:', error)
  } finally {
    loading.value.majors = false
  }
}

// 添加专业
const addMajor = async () => {
  if (!majorForm.value.name) {
    ElMessage.warning('请输入专业名称')
    return
  }
  submitting.value = true
  try {
    const formData = new FormData()
    formData.append('name', majorForm.value.name)
    formData.append('college', majorForm.value.college)
    await axios.post('/api/admin/majors', formData)
    ElMessage.success('专业添加成功')
    showAddMajorDialog.value = false
    majorForm.value = { name: '', college: '' }
    refreshMajors()
  } catch (error) {
    console.error('添加专业失败:', error)
  } finally {
    submitting.value = false
  }
}

// 删除专业
const deleteMajor = async (majorId) => {
  try {
    await axios.delete(`/api/admin/majors/${majorId}`)
    ElMessage.success('专业已删除')
    refreshMajors()
  } catch (error) {
    console.error('删除专业失败:', error)
    ElMessage.error('删除失败')
  }
}

// 加载分类统计
const refreshCategories = async () => {
  try {
    const response = await axios.get('/api/admin/categories')
    categories.value = response.data.categories || []
  } catch (error) {
    console.error('获取分类统计失败:', error)
  }
}

// 切换 tab 时加载对应数据
const handleTabChange = (tab) => {
  switch (tab) {
    case 'dashboard': refreshDashboard(); break
    case 'users': refreshUsers(); break
    case 'posts': refreshPosts(); break
    case 'comments': refreshComments(); break
    case 'majors': refreshMajors(); break
    case 'categories': refreshCategories(); break
  }
}

onMounted(() => {
  refreshDashboard()
  refreshUsers()
  refreshPosts()
  refreshMajors()
  refreshCategories()
})
</script>

<style scoped>
.admin-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}

.admin-header {
  margin-bottom: 24px;
  text-align: center;
}

.admin-header h2 {
  color: #303133;
  margin-bottom: 6px;
  font-size: 24px;
}

.subtitle {
  color: #909399;
  font-size: 14px;
}

.admin-tabs {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.tab-content {
  margin-top: 20px;
  min-height: 300px;
}

.action-bar {
  margin-bottom: 16px;
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

.pagination-info {
  margin-top: 12px;
  color: #909399;
  font-size: 13px;
}

.post-title-text {
  color: #303133;
  font-weight: 500;
}

/* 概览统计卡片 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: transform 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: bold;
  color: #fff;
}

.user-icon { background: linear-gradient(135deg, #409eff, #337ecc); }
.post-icon { background: linear-gradient(135deg, #67c23a, #529b2e); }
.comment-icon { background: linear-gradient(135deg, #e6a23c, #cf9236); }
.like-icon { background: linear-gradient(135deg, #f56c6c, #d95353); }

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  line-height: 1.2;
}

.stat-label {
  font-size: 13px;
  color: #909399;
}

.stat-today {
  font-size: 12px;
  color: #67c23a;
  margin-top: 4px;
}

.dashboard-section {
  margin-top: 20px;
}

.dashboard-section h3 {
  margin-bottom: 12px;
  color: #303133;
  font-size: 16px;
}

/* 分类统计 */
.category-chart {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.category-card {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 20px;
}

.category-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 6px;
}

.category-count {
  font-size: 13px;
  color: #909399;
  margin-bottom: 12px;
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .category-chart {
    grid-template-columns: 1fr;
  }
}
</style>