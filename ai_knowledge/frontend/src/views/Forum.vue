<template>
  <div class="forum-container" :style="containerStyle">
    <!-- 背景层已移到 MainLayout 中 -->
    <el-card class="forum-header">
      <div class="header-action">
        <h3>🔥 校园热议</h3>
        <div class="header-buttons">
          <el-button type="primary" size="small" round @click="showCreateDialog = true">发布帖子</el-button>
          <el-button size="small" round @click="navigateToMyContent">
            <el-icon><User /></el-icon>
            我的
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 发布帖子对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      title="发布帖子"
      width="80%"
      :before-close="handleClose"
    >
      <el-form :model="newPost" label-width="80px">
        <el-form-item label="帖子标题">
          <el-input v-model="newPost.title" placeholder="请输入帖子标题" maxlength="100" show-word-limit />
        </el-form-item>
        <el-form-item label="帖子分类">
          <el-select v-model="newPost.category" placeholder="请选择分类">
            <el-option label="讨论" value="讨论" />
            <el-option label="求助" value="求助" />
            <el-option label="分享" value="分享" />
            <el-option label="通知" value="通知" />
          </el-select>
        </el-form-item>
        <el-form-item label="帖子内容">
          <el-input
            v-model="newPost.content"
            type="textarea"
            placeholder="请输入帖子内容"
            :rows="8"
            maxlength="5000"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="上传图片">
          <el-upload
            class="avatar-uploader"
            action="/api/forum/upload"
            :headers="{
              Authorization: `Bearer ${typeof localStorage !== 'undefined' ? localStorage.getItem('token') || '' : ''}`
            }"
            :show-file-list="true"
            :on-success="handleImageUpload"
            :on-error="handleUploadError"
            :auto-upload="true"
            accept="image/*"
          >
            <el-button size="small" type="primary">点击上传</el-button>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showCreateDialog = false">取消</el-button>
          <el-button type="primary" @click="createPost" :loading="creatingPost">发布</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 帖子详情对话框 -->
    <el-dialog
      v-model="showPostDialog"
      :title="currentPost?.title || '帖子详情'"
      width="80%"
      :before-close="handleClose"
    >
      <div v-if="currentPost" class="post-detail">
        <div class="post-meta">
          <el-tag size="small" :type="getTagType(currentPost.category)">{{ currentPost.category }}</el-tag>
          <span class="post-author">{{ currentPost.username }}</span>
          <span class="post-time">{{ formatTime(currentPost.create_time) }}</span>
        </div>
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
              <div v-for="item in commentItems" :key="item.id" :class="['comment-item']" :style="{ marginLeft: item.depth * 30 + 'px' }">
                <div class="comment-avatar-wrap">
                  <el-avatar :size="item.depth > 0 ? 36 : 40" :src="item.avatar || ''">
                    {{ (item.username || '用户').charAt(0) }}
                  </el-avatar>
                </div>
                <div class="comment-body">
                  <div class="comment-header">
                    <div class="comment-user-info">
                      <span class="comment-username">{{ item.username }}</span>
                      <span v-if="item.replyTo" class="reply-to">→ {{ item.replyTo }}</span>
                    </div>
                    <span class="comment-time">{{ formatTime(item.create_time) }}</span>
                  </div>
                  <div class="comment-content">
                    {{ item.content }}
                  </div>
                  <div class="comment-actions">
                    <el-button size="small" @click="replyComment(item)">回复</el-button>
                  </div>
                </div>
              </div>
              <div v-if="commentItems.length === 0" class="no-comments">
                <el-empty description="暂无评论，快来发表第一条评论吧" />
              </div>
              <!-- 展开更多评论 -->
              <div v-if="hasMoreComments" class="load-more">
                <el-button type="text" @click="loadMoreComments">
                  展开更多评论 ({{ totalCommentCount - displayCount }}条)
                </el-button>
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

    <div class="post-list">
      <el-skeleton :loading="loading" animated>
        <template #template>
          <el-card shadow="hover" class="post-item">
            <div class="post-tag">
              <el-tag size="small" type="info">加载中...</el-tag>
            </div>
            <h4><el-skeleton-item variant="h3" style="width: 80%" /></h4>
            <div class="post-footer">
              <span class="author"><el-skeleton-item variant="text" style="width: 60px" /></span>
              <span class="time"><el-skeleton-item variant="text" style="width: 100px" /></span>
            </div>
          </el-card>
        </template>
      </el-skeleton>
      <el-card v-for="post in posts" :key="post.id" shadow="hover" class="post-item" @click="showPostDetail(post.id)">
        <div class="post-tag">
          <el-tag size="small" :type="getTagType(post.category)">{{ post.category }}</el-tag>
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
      <div v-if="!loading && posts.length === 0" class="no-data">
        <el-empty description="暂无帖子" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { sanitizeHtml } from '../utils/sanitize'
import { ref, computed, onMounted } from 'vue'
import { useBackground } from '../composables/useBackground'
import axios from '../utils/axios'
import { Star, View, User, ChatDotRound } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'

const router = useRouter()

// 跳转到我的内容页面
const navigateToMyContent = () => {
  router.push('/my-content')
}

const sanitize = (html) => sanitizeHtml(html)

// 使用背景设置
const { containerStyle } = useBackground()

// 帖子数据
const posts = ref([])
const loading = ref(true)

// 发布帖子相关
const showCreateDialog = ref(false)
const newPost = ref({ title: '', content: '', category: '讨论' })
const creatingPost = ref(false)

// 帖子详情相关
const showPostDialog = ref(false)
const currentPost = ref(null)
const comments = ref([])
const newComment = ref({ content: '' })

// 评论分页：默认显示5条评论（包含回复）
const displayCount = ref(5)
const pageSize = 5

// 回复评论相关
const showReplyDialog = ref(false)
const replyTarget = ref(null)
const replyContent = ref('')

// 展平的评论列表（支持嵌套回复）
const commentItems = computed(() => {
  const items = []
  
  // 递归展开评论和回复
  const flattenComments = (commentList, parentUsername = null, depth = 0) => {
    commentList.forEach(comment => {
      // 添加评论
      items.push({
        ...comment,
        isReply: depth > 0,
        replyTo: parentUsername,
        depth: depth
      })
      
      // 如果有回复，递归展开（最多显示5条每层）
      if (comment.replies && comment.replies.length > 0) {
        const repliesToShow = comment.replies.slice(0, 5)
        flattenComments(repliesToShow, comment.username, depth + 1)
      }
    })
  }
  
  // 展开所有评论
  flattenComments(comments.value)
  
  // 只返回当前显示数量内的评论
  return items.slice(0, displayCount.value)
})

// 计算总评论数（包含所有层级的回复，每层最多5条）
const totalCommentCount = computed(() => {
  const countReplies = (commentList) => {
    return commentList.reduce((count, comment) => {
      const replyCount = comment.replies && comment.replies.length > 5 ? 5 : (comment.replies?.length || 0)
      return count + 1 + countReplies(comment.replies?.slice(0, 5) || [])
    }, 0)
  }
  return countReplies(comments.value)
})

// 是否有更多评论
const hasMoreComments = computed(() => {
  return totalCommentCount.value > displayCount.value
})

// 加载更多评论
const loadMoreComments = () => {
  displayCount.value += pageSize
}



// 获取帖子数据
const fetchPosts = async () => {
  try {
    loading.value = true
    const response = await axios.get('/api/forum/posts')
    posts.value = response.data
  } catch (error) {
    console.error('获取帖子失败，使用模拟数据:', error)
    // 使用模拟数据作为fallback
    posts.value = mockPosts
  } finally {
    loading.value = false
  }
}

// 获取帖子详情
const showPostDetail = async (postId) => {
  try {
    const response = await axios.get(`/api/forum/posts/${postId}`)
    currentPost.value = response.data
    showPostDialog.value = true
    // 获取评论
    await fetchComments(postId)
  } catch (error) {
    console.error('获取帖子详情失败:', error)
    ElMessage.error('获取帖子详情失败')
    showPostDialog.value = false
  }
}

// 获取评论
const fetchComments = async (postId) => {
  try {
    console.log('开始获取评论，postId:', postId)
    const response = await axios.get(`/api/forum/posts/${postId}/comments`)
    console.log('获取评论成功，response.data:', response.data)
    // 处理后端返回的分页数据结构
    const rawComments = response.data.value || response.data || []
    // 构建嵌套评论结构
    comments.value = buildCommentTree(rawComments)
    // 重置显示数量
    displayCount.value = pageSize
    console.log('嵌套评论数据:', comments.value)
  } catch (error) {
    console.error('获取评论失败:', error)
    comments.value = []
    displayCount.value = pageSize
  }
}

// 构建嵌套评论树
const buildCommentTree = (rawComments) => {
  // 创建评论映射
  const commentMap = new Map()
  const rootComments = []
  
  // 先将所有评论放入Map
  rawComments.forEach(comment => {
    commentMap.set(comment.id, { ...comment, replies: [] })
  })
  
  // 构建嵌套结构，回复按时间倒序排列（最新的在最上面）
  rawComments.forEach(comment => {
    if (comment.parent_id && commentMap.has(comment.parent_id)) {
      // 这是一个回复，添加到父评论的replies中
      commentMap.get(comment.parent_id).replies.unshift(commentMap.get(comment.id))
    } else {
      // 这是一个顶级评论
      rootComments.push(commentMap.get(comment.id))
    }
  })
  
  // 顶级评论按时间倒序排列
  return rootComments.sort((a, b) => new Date(b.create_time) - new Date(a.create_time))
}

// 发布帖子
const createPost = async () => {
  if (!newPost.value.title || !newPost.value.content) {
    ElMessage.warning('请填写标题和内容')
    return
  }
  
  try {
    creatingPost.value = true
    const response = await axios.post('/api/forum/posts', newPost.value)
    ElMessage.success('帖子发布成功')
    showCreateDialog.value = false
    // 重置表单
    newPost.value = { title: '', content: '', category: '讨论' }
    // 重新获取帖子列表
    await fetchPosts()
  } catch (error) {
    console.error('发布帖子失败:', error)
    ElMessage.error('发布帖子失败，请先登录')
  } finally {
    creatingPost.value = false
  }
}

// 添加评论
const addComment = async () => {
  if (!newComment.value.content) {
    ElMessage.warning('请输入评论内容')
    return
  }
  
  try {
    const response = await axios.post('/api/forum/comments', {
      post_id: currentPost.value.id,
      content: newComment.value.content
    })
    ElMessage.success('评论发表成功')
    // 重置评论表单
    newComment.value.content = ''
    // 重新获取评论
    await fetchComments(currentPost.value.id)
  } catch (error) {
    console.error('发表评论失败:', error)
    ElMessage.error('发表评论失败，请先登录')
  }
}

// 回复评论
const replyComment = (comment) => {
  replyTarget.value = comment
  showReplyDialog.value = true
}

// 提交回复
const submitReply = async () => {
  if (!replyContent.value) {
    ElMessage.warning('请输入回复内容')
    return
  }
  
  try {
    const response = await axios.post('/api/forum/comments', {
      post_id: currentPost.value.id,
      content: replyContent.value,
      parent_id: replyTarget.value.id
    })
    ElMessage.success('回复发表成功')
    showReplyDialog.value = false
    // 重置回复表单
    replyContent.value = ''
    replyTarget.value = null
    // 重新获取评论
    await fetchComments(currentPost.value.id)
  } catch (error) {
    console.error('发表回复失败:', error)
    ElMessage.error('发表回复失败，请先登录')
  }
}

// 点赞帖子
const likePost = async (postId) => {
  try {
    const response = await axios.post(`/api/forum/posts/${postId}/like`)
    ElMessage.success('点赞成功')
    // 更新本地数据
    if (currentPost.value && currentPost.value.id === postId) {
      currentPost.value.like_count = response.data.like_count
    }
    // 更新列表中的数据
    const post = posts.value.find(p => p.id === postId)
    if (post) {
      post.like_count = response.data.like_count
    }
  } catch (error) {
    console.error('点赞失败:', error)
    ElMessage.error('点赞失败，请先登录')
  }
}

// 处理图片上传
const handleImageUpload = (response, file, fileList) => {
  if (response.url) {
    // 将图片URL插入到内容中
    newPost.value.content += `<img src="${response.url}" style="max-width: 100%; height: auto; margin: 10px 0;" />`
    ElMessage.success('图片上传成功')
  }
}

// 处理上传错误
const handleUploadError = (error, file, fileList) => {
  ElMessage.error('图片上传失败，请先登录')
}

// 处理对话框关闭
const handleClose = (done) => {
  // 重置相关状态
  currentPost.value = null
  comments.value = []
  newComment.value.content = ''
  replyContent.value = ''
  replyTarget.value = null
  // 重置显示数量
  displayCount.value = pageSize
  // 调用 done 回调关闭对话框
  if (done) {
    done()
  }
}

// 格式化时间
const formatTime = (time) => {
  if (!time) return ''
  const now = new Date()
  const postTime = new Date(time)
  
  // 检查是否是有效的日期
  if (isNaN(postTime.getTime())) {
    return ''
  }
  
  const diff = now - postTime
  
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)
  
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 30) return `${days}天前`
  
  return postTime.toLocaleDateString()
}

// 获取标签类型
const getTagType = (category) => {
  const typeMap = {
    '求助': 'info',
    '分享': 'success',
    '讨论': 'warning',
    '通知': 'danger'
  }
  return typeMap[category] || 'info'
}

// 获取帖子摘要
const getExcerpt = (content) => {
  // 移除HTML标签
  const text = content.replace(/<[^>]*>/g, '')
  // 返回前100个字符
  return text.length > 100 ? text.substring(0, 100) + '...' : text
}

// 获取父评论作者
const getParentCommentAuthor = (parentId) => {
  const parent = comments.value.find(c => c.id === parentId)
  return parent ? parent.username : '用户'
}

// 组件挂载时获取数据
onMounted(() => {
  fetchPosts()
})
</script>

<style scoped>
.forum-container { padding: 15px; min-height: 100vh; }
.header-action { display: flex; justify-content: space-between; align-items: center; }
.header-action h3 { margin: 0; }

.post-item { margin-bottom: 15px; cursor: pointer; transition: transform 0.2s; }
.post-item:hover { transform: translateY(-2px); }
.post-tag { margin-bottom: 8px; }
.post-item h4 { margin: 0 0 10px 0; font-size: 16px; color: inherit; }
.post-excerpt { font-size: 14px; color: #666; margin-bottom: 10px; line-height: 1.4; }
.post-footer { display: flex; justify-content: space-between; align-items: center; font-size: 12px; color: inherit; }
.post-stats { display: flex; gap: 15px; }
.stat-item { display: flex; align-items: center; gap: 4px; }

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

/* 评论区样式 - 支持嵌套回复 */
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
.comment-form-actions {
  display: flex; justify-content: flex-end; margin-top: 10px;
}
.comment-item {
  margin-bottom: 12px;
  padding: 14px;
  background: rgba(245, 247, 250, 0.8);
  border-radius: 8px;
  display: flex;
  gap: 12px;
  transition: all 0.2s ease;
}
.comment-item:not(:first-child) {
  padding: 12px 14px;
  background: rgba(255, 255, 255, 0.9);
  border-left: 3px solid #409eff;
}
.comment-avatar-wrap {
  flex-shrink: 0;
}
.comment-body {
  flex: 1;
  min-width: 0;
}
.comment-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 6px;
}
.comment-user-info {
  display: flex; align-items: center;
}
.comment-username {
  font-weight: 600;
  font-size: 14px;
  color: #303133;
}
.reply-to {
  color: #409eff;
  font-weight: 500;
  font-size: 13px;
  margin-left: 4px;
}
.comment-item:not(:first-child) .comment-username {
  font-weight: 500;
  font-size: 13px;
}
.comment-time {
  color: #909399;
  font-size: 12px;
}
.comment-item:not(:first-child) .comment-time {
  font-size: 11px;
}
.comment-content {
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
  word-break: break-all;
}
.comment-item:not(:first-child) .comment-content {
  font-size: 13px;
  line-height: 1.5;
}
.reply-tag {
  color: #409eff;
  font-weight: 500;
  margin-right: 6px;
}
.comment-actions {
  display: flex; justify-content: flex-end;
  margin-top: 8px;
}
.comment-item:not(:first-child) .comment-actions {
  margin-top: 6px;
}
.comment-actions button {
  padding: 2px 8px;
}
.no-comments {
  text-align: center;
  padding: 30px 0;
}
/* 展开更多评论按钮 */
.load-more {
  text-align: center;
  margin-top: 20px;
  padding-top: 15px;
  border-top: 1px dashed #ddd;
}
.load-more button {
  color: #409eff;
  font-size: 14px;
}

/* 调整卡片背景透明度 */
.forum-header,
.post-item {
  background: rgba(255, 255, 255, 0.8);
  border-radius: 10px;
}

/* 响应式设计 */
@media screen and (max-width: 768px) {
  .forum-container { padding: 10px; }
  .post-item h4 { font-size: 14px; }
  .post-excerpt { font-size: 12px; }
  .el-dialog {
    width: 95% !important;
  }
}
</style>