<template>
  <div class="profile-container" :style="containerStyle">
    <!-- 背景层已移到 MainLayout 中 -->
    <el-card class="profile-card">
      <template #header>
        <div class="profile-header">
          <el-button text @click="goBack">
            <el-icon><ArrowLeft /></el-icon> 返回
          </el-button>
          <h2 style="color: black;">我的内容</h2>
        </div>
      </template>
      
      <el-tabs v-model="activeTab" class="profile-tabs" @tab-change="handleTabChange">
        <!-- 我的帖子 -->
        <el-tab-pane label="我的帖子" name="posts">
          <div v-if="loadingPosts" class="loading-container">
            <el-skeleton :rows="3" animated />
          </div>
          <div v-else-if="userPosts.length === 0" class="no-data">
            <el-empty description="暂无帖子" />
          </div>
          <div v-else class="posts-list">
            <el-card 
              v-for="post in userPosts" 
              :key="post.id" 
              shadow="hover" 
              class="post-item"
              @click="showPostDetail(post.id)"
            >
              <div class="post-tag">
                <el-tag size="small" :type="getTagType(post.category)">{{ post.category }}</el-tag>
                <el-tag v-if="post.status === 1" size="small" type="warning">审核中</el-tag>
                <el-tag v-else-if="post.status === 2" size="small" type="danger">违规</el-tag>
              </div>
              <h4>{{ post.title }}</h4>
              <div class="post-excerpt" v-if="post.content">{{ getExcerpt(post.content) }}</div>
              <div class="post-footer">
                <span class="time">{{ formatTime(post.create_time) }}</span>
                <div class="post-stats">
                  <span class="stat-item">
                    <el-icon><View /></el-icon>
                    {{ post.view_count }}
                  </span>
                  <span class="stat-item">
                    <el-icon><Star /></el-icon>
                    {{ post.like_count }}
                  </span>
                </div>
              </div>
              <div class="post-actions">
                <el-button size="small" @click.stop="editPost(post)">
                  <el-icon><Edit /></el-icon>
                  编辑
                </el-button>
                <el-button size="small" type="danger" @click.stop="deletePost(post.id)">
                  <el-icon><Delete /></el-icon>
                  删除
                </el-button>
              </div>
            </el-card>
          </div>
        </el-tab-pane>
        
        <!-- 我的点赞 -->
        <el-tab-pane label="我的点赞" name="likes">
          <div v-if="loadingLikes" class="loading-container">
            <el-skeleton :rows="3" animated />
          </div>
          <div v-else-if="userLikes.length === 0" class="no-data">
            <el-empty description="暂无点赞" />
          </div>
          <div v-else class="posts-list">
            <el-card 
              v-for="post in userLikes" 
              :key="post.id" 
              shadow="hover" 
              class="post-item"
              @click="showPostDetail(post.id)"
            >
              <div class="post-tag">
                <el-tag size="small" :type="getTagType(post.category)">{{ post.category }}</el-tag>
                <el-tag v-if="post.status === 1" size="small" type="warning">审核中</el-tag>
                <el-tag v-else-if="post.status === 2" size="small" type="danger">违规</el-tag>
              </div>
              <h4>{{ post.title }}</h4>
              <div class="post-excerpt" v-if="post.content">{{ getExcerpt(post.content) }}</div>
              <div class="post-footer">
                <span class="author">{{ post.username }}</span>
                <span class="time">{{ formatTime(post.create_time) }}</span>
                <div class="post-stats">
                  <span class="stat-item">
                    <el-icon><View /></el-icon>
                    {{ post.view_count }}
                  </span>
                  <span class="stat-item">
                    <el-icon><Star /></el-icon>
                    {{ post.like_count }}
                  </span>
                </div>
              </div>
            </el-card>
          </div>
        </el-tab-pane>
      </el-tabs>
      
      <!-- 帖子详情对话框 -->
      <el-dialog
        v-model="showPostDetailDialog"
        :title="currentPost?.title || '帖子详情'"
        width="80%"
        :before-close="handlePostDetailClose"
      >
        <div v-if="currentPost" class="post-detail">
          <div class="post-meta">
            <el-tag size="small" :type="getTagType(currentPost.category)">{{ currentPost.category }}</el-tag>
            <span class="post-author">{{ currentPost.username }}</span>
            <span class="post-time">{{ formatTime(currentPost.create_time) }}</span>
          </div>
          <el-alert
            v-if="currentPost.status === 1"
            title="审核中"
            type="warning"
            :description="currentPost.status_message || '你的帖子正在审核中，审核通过后将对其他用户可见'"
            show-icon
            :closable="false"
            class="status-alert"
          />
          <el-alert
            v-if="currentPost.status === 2"
            title="违规"
            type="error"
            :description="currentPost.status_message || '你的帖子因违反社区规定已被设为违规状态，仅你自己可见'"
            show-icon
            :closable="false"
            class="status-alert"
          />
          <div class="post-content" v-html="sanitize(currentPost.content)"></div>
          <div class="post-actions">
            <el-button size="small" @click="likePost(currentPost.id)">
              <el-icon><Star /></el-icon>
              {{ currentPost.like_count }} 点赞
            </el-button>
            <el-button size="small">
              <el-icon><View /></el-icon>
              {{ currentPost.view_count }} 浏览
            </el-button>
          </div>
          <div class="comments-section">
            <h4>评论 ({{ comments.length }})</h4>
            <div class="comment-form">
              <el-input
                v-model="newComment.content"
                type="textarea"
                placeholder="写下你的评论..."
                :rows="3"
                maxlength="500"
                show-word-limit
              />
              <div class="comment-actions">
                <el-button type="primary" size="small" @click="addComment">发表评论</el-button>
              </div>
            </div>
            <div class="comment-list">
              <div v-for="comment in comments" :key="comment.id" :class="['comment-item', { 'comment-reply': comment.parent_id }]">
                <div class="comment-avatar-wrap">
                  <el-avatar :size="40" :src="comment.avatar || ''">
                    {{ (comment.username || '用户').charAt(0) }}
                  </el-avatar>
                </div>
                <div class="comment-body">
                  <div v-if="comment.parent_id" class="reply-info">
                    <el-icon><ChatDotRound /></el-icon>
                    回复 {{ getParentCommentAuthor(comment.parent_id) }}
                  </div>
                  <div class="comment-header">
                    <span class="comment-username">{{ comment.username }}</span>
                    <span class="comment-time">{{ formatTime(comment.create_time) }}</span>
                  </div>
                  <div class="comment-content">{{ comment.content }}</div>
                  <div class="comment-reply">
                    <el-button size="small" @click="replyComment(comment)">回复</el-button>
                  </div>
                </div>
              </div>
              <div v-if="comments.length === 0" class="no-comments">
                <el-empty description="暂无评论，快来发表第一条评论吧" />
              </div>
            </div>
          </div>
        </div>
      </el-dialog>

      <!-- 回复评论对话框 -->
      <el-dialog
        v-model="showReplyDialog"
        :title="`回复 ${replyTarget?.username || ''}`"
        width="60%"
      >
        <el-input
          v-model="replyContent"
          type="textarea"
          placeholder="写下你的回复..."
          :rows="3"
          maxlength="300"
          show-word-limit
        />
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="showReplyDialog = false">取消</el-button>
            <el-button type="primary" @click="submitReply">回复</el-button>
          </span>
        </template>
      </el-dialog>

      <!-- 编辑帖子对话框 -->
      <el-dialog
        v-model="showEditDialog"
        title="编辑帖子"
        width="80%"
      >
        <el-form :model="editPostForm" label-width="80px">
          <el-form-item label="帖子标题">
            <el-input v-model="editPostForm.title" placeholder="请输入帖子标题" maxlength="100" show-word-limit />
          </el-form-item>
          <el-form-item label="帖子分类">
            <el-select v-model="editPostForm.category" placeholder="请选择分类">
              <el-option label="讨论" value="讨论" />
              <el-option label="求助" value="求助" />
              <el-option label="分享" value="分享" />
              <el-option label="通知" value="通知" />
            </el-select>
          </el-form-item>
          <el-form-item label="帖子内容">
            <el-input
              v-model="editPostForm.content"
              type="textarea"
              placeholder="请输入帖子内容"
              :rows="8"
              maxlength="5000"
              show-word-limit
            />
          </el-form-item>
        </el-form>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="showEditDialog = false">取消</el-button>
            <el-button type="primary" @click="updatePost" :loading="updatingPost">保存</el-button>
          </span>
        </template>
      </el-dialog>
    </el-card>
  </div>
</template>

<script setup>
import { sanitizeHtml } from '../utils/sanitize'
import { ref, onMounted } from 'vue'
import { useBackground } from '../composables/useBackground'
import axios from '../utils/axios'
import { Star, View, Delete, Edit, ArrowLeft, ChatDotRound } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'

const router = useRouter()

const sanitize = (html) => sanitizeHtml(html)

// 返回上一页
const goBack = () => {
  router.back()
}

// 使用背景设置
const { containerStyle } = useBackground()

// 标签页状态
const activeTab = ref('posts')

// 我的帖子数据
const userPosts = ref([])
const loadingPosts = ref(true)

// 我的点赞数据
const userLikes = ref([])
const loadingLikes = ref(true)

// 编辑帖子相关
const showEditDialog = ref(false)
const editPostForm = ref({ id: '', title: '', content: '', category: '' })
const updatingPost = ref(false)

// 帖子详情相关
const showPostDetailDialog = ref(false)
const currentPost = ref(null)
const comments = ref([])
const newComment = ref({ content: '' })

// 回复评论相关
const showReplyDialog = ref(false)
const replyTarget = ref(null)
const replyContent = ref('')

// 获取用户帖子
const fetchUserPosts = async () => {
  try {
    const token = localStorage.getItem('token')
    const response = await axios.get('/api/forum/my-posts', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    userPosts.value = response.data
    console.log('用户帖子:', userPosts.value)
  } catch (error) {
    console.error('获取用户帖子失败', error)
    ElMessage.error('获取用户帖子失败')
  } finally {
    loadingPosts.value = false
  }
}

// 获取用户点赞
const fetchUserLikes = async () => {
  try {
    const token = localStorage.getItem('token')
    const response = await axios.get('/api/forum/likes', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    userLikes.value = response.data
    console.log('用户点赞:', userLikes.value)
  } catch (error) {
    console.error('获取用户点赞失败', error)
    ElMessage.error('获取用户点赞失败')
  } finally {
    loadingLikes.value = false
  }
}

// 编辑帖子
const editPost = (post) => {
  editPostForm.value = {
    id: post.id,
    title: post.title,
    content: post.content,
    category: post.category
  }
  showEditDialog.value = true
}

// 更新帖子
const updatePost = async () => {
  try {
    updatingPost.value = true
    const token = localStorage.getItem('token')
    await axios.put(`/api/forum/posts/${editPostForm.value.id}`, {
      title: editPostForm.value.title,
      content: editPostForm.value.content,
      category: editPostForm.value.category
    }, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    ElMessage.success('帖子更新成功')
    showEditDialog.value = false
    // 重新获取帖子列表
    await fetchUserPosts()
  } catch (error) {
    console.error('更新帖子失败', error)
    ElMessage.error('更新帖子失败')
  } finally {
    updatingPost.value = false
  }
}

// 删除帖子
const deletePost = async (postId) => {
  try {
    const token = localStorage.getItem('token')
    await axios.delete(`/api/forum/posts/${postId}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    ElMessage.success('帖子删除成功')
    // 重新获取帖子列表
    await fetchUserPosts()
  } catch (error) {
    console.error('删除帖子失败', error)
    ElMessage.error('删除帖子失败')
  }
}

// 查看帖子详情
const showPostDetail = async (postId) => {
  try {
    const response = await axios.get(`/api/forum/posts/${postId}`)
    currentPost.value = response.data
    showPostDetailDialog.value = true
    // 获取评论
    await fetchComments(postId)
  } catch (error) {
    console.error('获取帖子详情失败:', error)
    ElMessage.error('获取帖子详情失败')
    showPostDetailDialog.value = false
  }
}

// 获取评论
const fetchComments = async (postId) => {
  try {
    console.log('开始获取评论，postId:', postId)
    const response = await axios.get(`/api/forum/posts/${postId}/comments`)
    console.log('获取评论成功，response.data:', response.data)
    // 处理后端返回的分页数据结构
    comments.value = response.data.value || response.data || []
    console.log('评论数据:', comments.value)
  } catch (error) {
    console.error('获取评论失败:', error)
    comments.value = []
  }
}

// 添加评论
const addComment = async () => {
  if (!newComment.value.content) {
    ElMessage.warning('请输入评论内容')
    return
  }
  
  try {
    const token = localStorage.getItem('token')
    const response = await axios.post('/api/forum/comments', {
      post_id: currentPost.value.id,
      content: newComment.value.content
    }, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    ElMessage.success('评论发表成功')
    newComment.value.content = ''
    await fetchComments(currentPost.value.id)
  } catch (error) {
    console.error('发表评论失败:', error)
    ElMessage.error('发表评论失败，请先登录')
  }
}

// 回复评论
const replyComment = (comment) => {
  replyTarget.value = comment
  replyContent.value = ''
  showReplyDialog.value = true
}

// 提交回复
const submitReply = async () => {
  if (!replyContent.value) {
    ElMessage.warning('请输入回复内容')
    return
  }
  
  try {
    const token = localStorage.getItem('token')
    const response = await axios.post('/api/forum/comments', {
      post_id: currentPost.value.id,
      content: replyContent.value,
      parent_id: replyTarget.value.id
    }, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    ElMessage.success('回复发表成功')
    showReplyDialog.value = false
    replyContent.value = ''
    replyTarget.value = null
    await fetchComments(currentPost.value.id)
  } catch (error) {
    console.error('发表回复失败:', error)
    ElMessage.error('发表回复失败，请先登录')
  }
}

// 点赞帖子
const likePost = async (postId) => {
  try {
    const token = localStorage.getItem('token')
    const response = await axios.post(`/api/forum/posts/${postId}/like`, {}, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    ElMessage.success('点赞成功')
    if (currentPost.value && currentPost.value.id === postId) {
      currentPost.value.like_count = response.data.like_count
    }
    const post = userPosts.value.find(p => p.id === postId)
    if (post) {
      post.like_count = response.data.like_count
    }
    const likedPost = userLikes.value.find(p => p.id === postId)
    if (likedPost) {
      likedPost.like_count = response.data.like_count
    }
  } catch (error) {
    console.error('点赞失败:', error)
    ElMessage.error('点赞失败，请先登录')
  }
}

// 获取父评论作者
const getParentCommentAuthor = (parentId) => {
  const parent = comments.value.find(c => c.id === parentId)
  return parent ? parent.username : '用户'
}

// 处理帖子详情对话框关闭
const handlePostDetailClose = (done) => {
  currentPost.value = null
  comments.value = []
  newComment.value.content = ''
  replyContent.value = ''
  replyTarget.value = null
  if (done) {
    done()
  }
}

// 格式化时间
const formatTime = (timeString) => {
  if (!timeString) return ''
  const date = new Date(timeString)
  
  // 检查是否是有效的日期
  if (isNaN(date.getTime())) {
    return ''
  }
  
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 获取帖子摘要
const getExcerpt = (content) => {
  // 移除 HTML 标签
  const plainText = content.replace(/<[^>]+>/g, '')
  // 截取前 100 个字符
  return plainText.length > 100 ? plainText.substring(0, 100) + '...' : plainText
}

// 获取标签类型
const getTagType = (category) => {
  const typeMap = {
    '讨论': 'info',
    '求助': 'warning',
    '分享': 'success',
    '通知': 'danger'
  }
  return typeMap[category] || 'default'
}

// 监听标签页变化
const handleTabChange = (activeTab) => {
  if (activeTab === 'likes' && userLikes.value.length === 0) {
    loadingLikes.value = true
    fetchUserLikes()
  }
}

// 页面加载时获取数据
onMounted(async () => {
  await fetchUserPosts()
})
</script>

<style scoped>
.profile-container {
  min-height: 100vh;
  padding: 20px;
  position: relative;
}

.background-layer {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 0;
}

.profile-card {
  position: relative;
  z-index: 1;
  max-width: 800px;
  margin: 0 auto;
}

.profile-header {
  display: flex;
  align-items: center;
  gap: 15px;
}

.profile-tabs {
  margin-top: 20px;
}

.posts-list {
  margin-top: 20px;
}

.post-item {
  margin-bottom: 15px;
  cursor: pointer;
}

.post-item:hover {
  transform: translateY(-2px);
  transition: transform 0.3s ease;
}

.post-tag {
  margin-bottom: 10px;
}

.post-excerpt {
  margin: 10px 0;
  color: #666;
  line-height: 1.5;
}

.post-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 15px;
  font-size: 14px;
  color: #999;
}

.post-stats {
  display: flex;
  gap: 15px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 5px;
}

.post-actions {
  margin-top: 15px;
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.loading-container {
  padding: 20px 0;
}

.no-data {
  padding: 40px 0;
  text-align: center;
}

.header-buttons {
  display: flex;
  gap: 10px;
}

/* 帖子详情样式 */
.post-detail {
  padding: 10px 0;
}
.post-meta {
  display: flex; align-items: center; gap: 15px; margin-bottom: 20px;
  font-size: 14px;
}
.post-author {
  font-weight: bold;
}
.post-time {
  color: #666;
}
.post-content {
  margin: 20px 0;
  line-height: 1.6;
  font-size: 15px;
}
.post-content img {
  max-width: 100%;
  height: auto;
  margin: 10px 0;
  border-radius: 4px;
}
.post-actions {
  margin: 20px 0;
  display: flex; gap: 20px;
}

/* 评论区样式 */
.comments-section {
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #eee;
}
.comments-section h4 {
  margin-bottom: 20px;
}
.comment-form {
  margin-bottom: 30px;
}
.comment-actions {
  display: flex; justify-content: flex-end; margin-top: 10px;
}
.comment-item {
  margin-bottom: 15px;
  padding: 15px;
  background: rgba(245, 247, 250, 0.8);
  border-radius: 8px;
  display: flex;
  gap: 12px;
}
.comment-item.comment-reply {
  margin-left: 45px;
  background: rgba(230, 240, 255, 0.8);
  border-left: 3px solid #409eff;
}
.comment-avatar-wrap {
  flex-shrink: 0;
}
.comment-body {
  flex: 1;
  min-width: 0;
}
.reply-info {
  display: flex; align-items: center; gap: 4px;
  margin-bottom: 6px;
  color: #666;
  font-size: 12px;
}
.comment-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 8px;
}
.comment-user {
  display: flex; align-items: center; gap: 8px;
}
.comment-username {
  font-weight: 600;
  font-size: 14px;
  color: #303133;
}
.comment-time {
  color: #909399;
  font-size: 12px;
}
.comment-content {
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
  word-break: break-all;
}
.comment-reply {
  display: flex; justify-content: flex-end;
  margin-top: 10px;
}
.no-comments {
  text-align: center;
  padding: 30px 0;
}

.status-alert {
  margin-bottom: 16px;
}

.post-tag {
  display: flex;
  gap: 6px;
  align-items: center;
}

@media (max-width: 768px) {
  .profile-container {
    padding: 10px;
  }
  
  .profile-card {
    max-width: 100%;
  }
  
  .post-footer {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .post-stats {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>
