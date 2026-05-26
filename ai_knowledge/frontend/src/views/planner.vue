<template>
  <div class="planner-container" :style="containerStyle">
    <!-- 顶部标题 -->
    <div class="header">
      <div class="header-left">
        <el-button type="text" @click="goBack" class="back-button">
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
      </div>
      <div class="title">
        <el-icon class="logo"><Trophy /></el-icon>
        <h1>学业领航员</h1>
        <span class="subtitle">AI 驱动的个性化成长路径</span>
      </div>
    </div>

    <!-- 主要内容区 -->
    <div class="content">
      <!-- 基础信息输入 -->
      <div class="section">
        <div class="input-group">
          <el-input v-model="major" placeholder="请输入专业 (如: 计算机科学)" class="major-input" />
          <el-button type="primary" class="generate-btn" @click="generateKnowledgeTree" :loading="loading" :disabled="loading">
            <el-icon v-if="!loading"><MagicStick /></el-icon>
            {{ loading ? 'AI生成中...' : '生成专属图谱' }}
          </el-button>
        </div>
      </div>

      <!-- 未来意向规划 -->
      <div class="section">
        <h2 class="section-title">未来意向规划</h2>
        <div class="plan-options">
          <el-button 
            v-for="plan in plans" 
            :key="plan.id"
            :class="['plan-btn', { active: selectedPlan === plan.id }]"
            @click="selectedPlan = plan.id"
          >
            <el-icon>
              <component :is="plan.icon" />
            </el-icon>
            {{ plan.name }}
          </el-button>
        </div>
      </div>

      <!-- 图谱区域 -->
      <div class="section graph-section">
        <h2 class="section-title">知识图谱可视化</h2>
        <KnowledgeGraph 
          :nodes="graphNodes" 
          :edges="graphEdges" 
          :height="graphHeight"
          @node-click="handleNodeClick"
        />
      </div>

      <!-- 资源抽屉 -->
      <ResourceDrawer
        :visible="drawerVisible"
        @update:visible="drawerVisible = $event"
        :title="selectedNodeData?.label || ''"
        :videos="currentVideos"
        :loading="nodeLoading"
        :progress="currentProgress"
        @toggle-progress="handleToggleProgress"
      />

      <!-- 就业风向标 -->
      <div class="section" v-if="selectedPlan === 'job' && jobMarketData.length > 0">
        <h2 class="section-title">就业风向标</h2>
        <div class="job-market-grid">
          <JobMarketCard 
            v-for="(job, index) in jobMarketData" 
            :key="index" 
            :job="job" 
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { Trophy, MagicStick, Document, Briefcase, OfficeBuilding, Opportunity, ArrowLeft } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useBackground } from '../composables/useBackground'
import { planApi } from '../services/api'
import KnowledgeGraph from '../components/business/KnowledgeGraph.vue'
import ResourceDrawer from '../components/business/ResourceDrawer.vue'
import JobMarketCard from '../components/business/JobMarketCard.vue'

// 使用背景设置
const { containerStyle } = useBackground()

// 状态管理
const major = ref('')
const selectedPlan = ref('job')
const drawerVisible = ref(false)
const selectedNodeData = ref(null)
const loading = ref(false)
const nodeLoading = ref(false)
const graphNodes = ref([])
const graphEdges = ref([])
const jobMarketData = ref([])
const currentVideos = ref([])
const graphHeight = ref(500)
const progressMap = ref({})
const currentProgress = ref(0)

// 返回主页
const goBack = () => {
  window.location.href = '/'
}

const plans = [
  { id: 'study', name: '考研', icon: Document },
  { id: 'job', name: '就业', icon: Briefcase },
  { id: 'exam', name: '考公', icon: OfficeBuilding },
  { id: 'startup', name: '创业', icon: Opportunity }
]

// 生成B站搜索链接
const generateBilibiliLink = (courseName) => {
  let keyword = courseName
  if (!keyword.includes('教程') && !keyword.includes('课程') && !keyword.includes('学习')) {
    keyword += ' 教程'
  }
  return `https://search.bilibili.com/all?keyword=${encodeURIComponent(keyword)}`
}

// 转换树数据为图谱格式
const transformTreeData = (tree) => {
  const nodes = []
  const edges = []
  let nodeId = 0

  const traverse = (item, parentId = null) => {
    const id = `node-${nodeId++}`
    const level = item.level || item.type || 'low'
    
    const colorMap = {
      core: { bg: '#fef0f0', border: '#f56c6c', text: '#c0392b' },
      high: { bg: '#fdf6ec', border: '#e6a23c', text: '#d35400' },
      low: { bg: '#ecf5ff', border: '#409eff', text: '#2c3e50' }
    }
    
    const colors = colorMap[level] || colorMap.low

    nodes.push({
      id,
      shape: 'custom-node',
      x: 0,
      y: 0,
      label: item.label || item.name,
      attrs: {
        body: {
          fill: colors.bg,
          stroke: colors.border,
          strokeWidth: 2
        },
        label: {
          fill: colors.text
        }
      },
      data: {
        label: item.label || item.name,
        level: level,
        description: item.description
      },
      ports: {
        items: [
          { id: 'port-top', group: 'top' },
          { id: 'port-bottom', group: 'bottom' }
        ]
      }
    })

    if (parentId) {
      edges.push({
        id: `edge-${parentId}-${id}`,
        source: { cell: parentId, port: 'port-bottom' },
        target: { cell: id, port: 'port-top' },
        attrs: {
          line: {
            stroke: '#d9d9d9',
            strokeWidth: 2,
            targetMarker: {
              name: 'classic',
              size: 8
            }
          }
        }
      })
    }

    if (item.children && item.children.length > 0) {
      item.children.forEach(child => traverse(child, id))
    }
  }

  tree.forEach(item => traverse(item))
  return { nodes, edges }
}



// 处理节点点击
const handleNodeClick = async (data) => {
  console.log('handleNodeClick 被调用, data:', data)
  console.log('当前 drawerVisible:', drawerVisible.value)
  
  selectedNodeData.value = data
  drawerVisible.value = true
  
  console.log('设置后 drawerVisible:', drawerVisible.value)
  
  nodeLoading.value = true
  
  // 设置当前节点的学习进度
  currentProgress.value = progressMap.value[data.label] || 0
  
  try {
    currentVideos.value = [
      { title: `查看最新${data.label}教程`, url: generateBilibiliLink(data.label) },
      { title: `查找${data.label}实战资源`, url: generateBilibiliLink(`${data.label} 实战`) }
    ]
  } catch (error) {
    console.error('获取资源失败:', error)
  } finally {
    nodeLoading.value = false
  }
}

// 切换学习进度
const handleToggleProgress = () => {
  if (selectedNodeData.value) {
    const label = selectedNodeData.value.label
    progressMap.value[label] = progressMap.value[label] === 100 ? 0 : 100
    currentProgress.value = progressMap.value[label]
  }
}

// 生成知识图谱
const generateKnowledgeTree = async () => {
  if (!major.value) {
    ElMessage.warning('请输入专业名称')
    return
  }

  loading.value = true
  try {
    console.log('开始调用后端API...')
    const response = await planApi.generatePlan(major.value, selectedPlan.value)
    console.log('后端响应:', response.data)
    
    const backendTree = response.data.skill_tree
    console.log('skill_tree数据:', backendTree)
    
    if (!Array.isArray(backendTree) || backendTree.length === 0) {
      throw new Error('后端返回的数据格式错误')
    }

    const { nodes, edges } = transformTreeData(backendTree)
    console.log('转换后的节点:', nodes)
    console.log('转换后的边:', edges)
    
    graphNodes.value = nodes
    graphEdges.value = edges
    console.log('planner: 已设置 graphNodes, 数量:', graphNodes.value.length)

    if (selectedPlan.value === 'job' && response.data.job_market) {
      jobMarketData.value = response.data.job_market
    } else {
      jobMarketData.value = []
    }

    ElMessage.success('知识图谱生成成功！')
  } catch (error) {
    console.error('获取数据失败:', error)
    ElMessage.error('生成知识图谱失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

// 调整图谱高度
const adjustGraphHeight = () => {
  const windowHeight = window.innerHeight
  graphHeight.value = Math.max(windowHeight * 0.5, 400)
}

onMounted(() => {
  adjustGraphHeight()
  window.addEventListener('resize', adjustGraphHeight)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', adjustGraphHeight)
})
</script>

<style scoped>
.planner-container {
  min-height: 100vh;
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding: 10px 0;
}

.header-left {
  flex: 0 0 auto;
}

.back-button {
  font-size: 16px;
  color: #303133;
  font-weight: 500;
}

.title {
  text-align: center;
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.logo {
  font-size: 24px;
  color: #409eff;
  margin-bottom: 4px;
}

.title h1 {
  font-size: 22px;
  margin: 0;
  color: #000000;
  font-weight: 600;
}

.subtitle {
  font-size: 13px;
  color: #303133;
  margin: 0;
  opacity: 0.8;
}

.content {
  max-width: 1200px;
  margin: 0 auto;
}

.section {
  background: rgba(255, 255, 255, 0.9);
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 20px 0;
}

.input-group {
  display: flex;
  gap: 12px;
}

.major-input {
  flex: 1;
  height: 44px;
}

.generate-btn {
  height: 44px;
  padding: 0 24px;
}

.plan-options {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.plan-btn {
  padding: 10px 20px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.plan-btn.active {
  background: #409eff;
  border-color: #409eff;
}

.graph-section {
  padding: 24px;
}

.job-market-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

@media (max-width: 768px) {
  .planner-container {
    padding: 8px;
  }

  .header {
    flex-direction: row;
    padding: 8px 0;
    margin-bottom: 20px;
  }

  .header-left {
    flex: 0 0 55px;
  }

  .back-button {
    font-size: 14px;
    padding: 4px 8px;
  }

  .title {
    flex: 1;
  }

  .logo {
    font-size: 20px;
    margin-bottom: 2px;
  }

  .title h1 {
    font-size: 18px;
    color: #000000;
  }

  .subtitle {
    font-size: 12px;
    color: #303133;
  }

  .input-group {
    flex-direction: column;
  }

  .job-market-grid {
    grid-template-columns: 1fr;
  }
}
</style>