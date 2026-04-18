<template>
  <div class="profile-container">
    <!-- 状态 1：未进入设置页，显示概览 -->
    <div v-if="!isEditing">
      <el-card class="user-card" shadow="hover">
        <div class="user-info">
          <!-- 头像区域 -->
          <div class="avatar-box">
            <el-avatar :size="100" :src="userInfo.avatar" :icon="!userInfo.avatar ? 'UserFilled' : ''" />
          </div>
          <div class="details">
            <h3>{{ userInfo.name || '未登录/未完善' }}</h3>
            <p>{{ userInfo.major || '点击设置完善档案' }}</p>
          </div>
        </div>
      </el-card>

      <!-- 设置入口 -->
      <el-menu class="setting-menu">
        <el-menu-item index="1" @click="isEditing = true">
          <el-icon><Setting /></el-icon>
          <span>个人设置 / 信息录入</span>
        </el-menu-item>
        <el-menu-item index="2">
          <el-icon><Document /></el-icon>
          <span>我的课程表</span>
        </el-menu-item>
      </el-menu>
    </div>

    <!-- 状态 2：进入设置页，显示表单和退出按钮 -->
    <div v-else>
      <div class="back-header">
        <el-button text @click="isEditing = false">
          <el-icon><ArrowLeft /></el-icon> 返回
        </el-button>
        <span class="title">个人设置</span>
      </div>

      <el-card class="form-card">
        <el-form :model="userInfo" label-width="80px">

          <!-- 👇 表单里的头像上传组件 -->
          <el-form-item label="头像">
            <div class="avatar-uploader">
              <el-upload
                ref="uploadRef"
                class="avatar-uploader"
                action="#"
                :show-file-list="false"
                :auto-upload="false"
                :on-change="handleFileChange"
              >
                <img v-if="userInfo.avatar" :src="userInfo.avatar" class="avatar-preview" />
                <el-icon v-else class="avatar-uploader-icon"><Plus /></el-icon>
              </el-upload>
            </div>
          </el-form-item>

          <el-form-item label="昵称">
            <el-input v-model="userInfo.name" placeholder="请输入你的昵称" />
          </el-form-item>
          <el-form-item label="专业">
            <el-select v-model="userInfo.major"  placeholder="输入专业名称搜索"  filterable style="width: 100%">
  <!-- 👇 这里的 item 就是后端传回来的 { name: 'xxx' } -->
  <!-- 注意 :key 和 :value 必须是 item.name，不能只是 item -->
            <el-option 
              v-for="item in majorOptions" 
              :key="item.name" 
              :label="item.name" 
              :value="item.name" 
  />
</el-select>
          </el-form-item>
          <el-form-item label="年级">
            <el-radio-group v-model="userInfo.grade">
              <el-radio label="大一" />
              <el-radio label="大二" />
              <el-radio label="大三" />
              <el-radio label="大四" />
            </el-radio-group>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="saveInfo">保存信息</el-button>
          </el-form-item>
        </el-form>
      </el-card>
  </div>

      <!-- 退出登录按钮：放在表单下方，醒目且安全 -->
      <div class="logout-area">
        <el-button type="danger" plain style="width: 100%" @click="handleLogout">
          退出登录
        </el-button>
      </div>

    </div>
    
</template>
 
<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Setting, Document, UserFilled, ArrowLeft,Camera,Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import axios from '../utils/axios'



const router = useRouter()
const isEditing = ref(false) // 控制是否显示编辑模式
const fileInput = ref() // 获取隐藏 input 的引用
const uploadRef = ref() // 上传组件引用
const selectedFile = ref(null) // 保存选中的文件
// 模拟用户信息
const userInfo = reactive({
  name: '',
  major: '',
  grade: '大一',
  avatar: ''
})
// 👇 在这里添加：用来存从后端获取的专业列表
const majorOptions = ref([])

// 页面加载时，尝试从 localStorage 恢复数据
const loadUserInfo = () => {
  const saved = localStorage.getItem('userProfile')
  console.log('LocalStorage userProfile:', saved)
  if (saved) {
    try {
      const data = JSON.parse(saved)
      // 将保存的数据复制到 userInfo 中
      userInfo.name = data.name || ''
      userInfo.major = data.major || ''
      userInfo.grade = data.grade || '大一'
      userInfo.avatar = data.avatar || ''
      console.log('Loaded userInfo:', userInfo)
    } catch (e) {
      console.error('读取用户信息失败', e)
    }
  } else {
    console.log('No userProfile in localStorage')
  }
}

onMounted(async () => {
  loadUserInfo()
  await fetchUserInfo()
  
  // 👇 在这里添加：获取专业列表
  // 注意：这里假设你的后端接口是 /api/options
  try {
    const token = localStorage.getItem('token')
    const res = await axios.get('/api/options', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    
    // 关键点：后端返回的是 [{name: '计算机'}, ...] 这种数组
    // 我们直接赋值给 majorOptions
    majorOptions.value = res.data.majors 
    
  } catch (error) {
    console.error('获取专业列表失败', error)
    // 容错：如果后端挂了，给个默认值防止页面报错
    majorOptions.value = [
      { name: '计算机科学与技术' }, 
      { name: '软件工程' }
    ]
  }
})

// 定义 saveToLocal 函数
const saveToLocal = () => {
  localStorage.setItem('userProfile', JSON.stringify(userInfo))
}

// 4. 处理表单内图片变化（编辑页）
const handleFileChange = (file) => {
  // 保存选中的文件
  selectedFile.value = file.raw
  // 使用 FileReader 进行本地预览
  const reader = new FileReader()
  reader.onload = (e) => {
    userInfo.avatar = e.target.result // 将图片转为 Base64 并赋值
  }
  reader.readAsDataURL(file.raw)
}

// 6. 页面加载时，从后端获取最新用户信息
const fetchUserInfo = async () => {
  try {
    const token = localStorage.getItem('token')
    console.log('Token:', token)
    if (!token) {
      console.log('No token found, redirecting to login')
      router.push('/login')
      return
    }
    
    console.log('Fetching user info...')
    const response = await axios.get('/api/profile', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    
    console.log('Response data:', response.data)
    if (response.data) {
      userInfo.name = response.data.name || ''
      userInfo.major = response.data.major || ''
      userInfo.grade = response.data.grade || '大一'
      userInfo.avatar = response.data.avatar || ''
      console.log('Updated userInfo:', userInfo)
      // 保存到本地存储
      // 添加完整的后端域名
      userInfo.avatar = response.data.avatar ? response.data.avatar : ''
      console.log('Updated userInfo:', userInfo)
      // 保存到本地存储
      localStorage.setItem('userProfile', JSON.stringify(userInfo))
      console.log('Saved to localStorage')
    }
  } catch (error) {
    console.error('获取用户信息失败', error)
  }
}




// --- 👇 重点修改：保存信息函数 ---
const saveInfo = async () => {
  try {
    // 1. 准备发送给后端的数据
    const token = localStorage.getItem('token')
    console.log('Token:', token)
    
    //创建formData对象，而不是普通的JSON对象
    const formData = new FormData()
    formData.append('name', userInfo.name)
    formData.append('major', userInfo.major)
    formData.append('grade', userInfo.grade)
    
    // 如果有选中的文件，添加到formData
    if (selectedFile.value) {
      console.log('Selected file:', selectedFile.value)
      formData.append('avatar_file', selectedFile.value)
    }
    
    // 2. 发送 POST 请求
    console.log('Saving info...')
    const response = await axios.post(
      '/api/profile', // 你的后端接口地址
      formData,
      {
        headers: {
          'Authorization': `Bearer ` + token, // 👈 带上 Token，后端才知道是谁在保存
          'Content-Type': 'multipart/form-data'
        }
      }
    )

    console.log('Response data:', response.data)
    // 3. 后端返回成功
    if (response.data) {
      // 更新头像URL
      if (response.data.avatar_url) {
        console.log('Updating avatar URL:', response.data.avatar_url)
        userInfo.avatar = response.data.avatar_url
         // 添加完整的后端域名
        userInfo.avatar = response.data.avatar_url
      }
      // 保存到本地
      localStorage.setItem('userProfile', JSON.stringify(userInfo))
      console.log('Saved to localStorage')
      ElMessage.success('信息保存成功！')
      isEditing.value = false
    }

  } catch (error) {
    console.error(error)
    ElMessage.error('保存失败，请检查后端服务或登录状态')
  }
}

// --- 新增：退出登录逻辑 ---
const handleLogout = () => {
  // 1. 清除 Token
  localStorage.removeItem('token')
  // 2. 清除用户信息（可选，为了安全）
  // localStorage.removeItem('userProfile')
  // 3. 跳转
  router.push('/login')
}

// 组件挂载后执行：读取数据
onMounted(async () => {
  loadUserInfo()
  // 从后端获取最新用户信息
  await fetchUserInfo()
  // 确保头像URL正确
  console.log('Current avatar URL:', userInfo.avatar)
})
</script>

<style scoped>
.profile-container { padding: 20px; }

/* 概览页样式 */
.user-card { margin-bottom: 20px; }
.user-info { display: flex; align-items: center; gap: 20px; }
.details h3 { margin: 0 0 8px 0; font-size: 20px; }
.details p { margin: 0; color: #909399; }
.setting-menu { border-radius: 8px; overflow: hidden; }

/* 编辑页样式 */
.back-header { display: flex; align-items: center; margin-bottom: 20px; }
.back-header .title { margin-left: 10px; font-weight: bold; font-size: 18px; }
.form-card { margin-bottom: 20px; }

/* 退出按钮区域 */
.logout-area { margin-top: 30px; }

/* 概览页头像样式 */
.avatar-box {
  position: relative;
  cursor: pointer;
  border-radius: 50%;
  overflow: hidden;
}
.avatar-mask {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s;
  color: white;
  font-size: 30px;
}
.avatar-box:hover .avatar-mask {
  opacity: 1;
}

/* 编辑页上传样式 */
.avatar-uploader {
  width: 100px;
  height: 100px;
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  overflow: hidden;
}
.avatar-uploader .avatar-preview {
  width: 100px;
  height: 100px;
  display: block;
  object-fit: cover;
}
.avatar-uploader-icon {
  font-size: 28px;
  color: #8c939d;
  width: 100px;
  height: 100px;
  line-height: 100px;
  text-align: center;
}
</style>