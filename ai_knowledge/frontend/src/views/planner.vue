<template>
  <div class="planner-container">
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
      <!-- <el-avatar :size="40" :icon="UserFilled" class="user-avatar" /> -->
    </div>

    <!-- 主要内容区 -->
     <div class="content">
      <!-- 2. 基础信息输入 -->
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

       <!-- 5. 图谱区域改造 -->
      <div class="section graph-section">
        <h2 class="section-title">知识图谱可视化</h2>
        <!-- X6 画布容器 -->
        <div ref="container" class="graph-canvas"></div>
      </div>

      <!-- 6. 侧边栏抽屉 -->
      <el-drawer
        v-model="drawerVisible"
        :title="selectedNode?.label"
        direction="rtl"
        size="350px"
      >
        <div v-if="selectedNode" class="drawer-content">
          <div class="resource-section">
            <h4>📚 推荐书籍</h4>
            <el-card 
              v-for="(book, i) in selectedNode.resources.books" 
              :key="i" 
              shadow="hover" 
              class="resource-card"
            >
              <div class="book-title">{{ book.title }}</div>
              <div class="book-author">{{ book.author }}</div>
            </el-card>
          </div>

          <div class="resource-section">
            <h4>📺 视频教程</h4>
            <div 
              v-for="(video, i) in selectedNode.resources.videos" 
              :key="i" 
              class="video-item"
            >
              <el-link :href="video.url" target="_blank" underline="never">
                <el-icon><VideoCamera /></el-icon>
                {{ video.title }}
              </el-link>
            </div>
          </div>
        </div>
        <div v-else>
          <p>暂无推荐资源</p>
        </div>
      </el-drawer> 


      <!-- 5. 就业风向标 (新增核心功能) -->
      <div class="section" v-if="selectedPlan === 'job' && jobMarketData.length > 0">
        <h2 class="section-title">就业风向标</h2>
        <div class="job-market-grid">
          <div v-for="(job, index) in jobMarketData" :key="index" class="job-market-card">
            <div class="job-header">
              <h3>{{ job.name }}</h3>
              <el-tag :type="job.is_core ? 'danger' : 'info'" size="small">{{ job.is_core ? '核心必学' : '推荐掌握' }}</el-tag>
            </div>
            <div class="job-salary">💰 薪资范围: {{ job.salary }}</div>
            <div class="job-skills">
              <strong>关键技能:</strong> {{ job.skills.join(', ') }}
            </div>
          </div>
        </div>
      </div>


    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import { Trophy, MagicStick, Document, Briefcase, OfficeBuilding, Opportunity, VideoCamera, ArrowLeft, Loading } from '@element-plus/icons-vue'
import axios from '../utils/axios'
import { Graph } from '@antv/x6'
import '@antv/x6-vue-shape'
// 引入 dagre 用于布局计算
import dagre from 'dagre' 

// --- 1. 状态管理 ---
const container = ref(null)
const graph = ref(null)
const major = ref('')
const selectedPlan = ref('job')
const drawerVisible = ref(false)
const selectedNode = ref(null)
const loading = ref(false) // 添加 loading 状态

// 就业风向标数据
const jobMarketData = ref([])

// 返回主页
const goBack = () => {
  // 这里使用 window.location.href 导航回主页
  // 如果你使用了 Vue Router，可以使用 router.push('/')
  window.location.href = '/'
}

const plans = [
  { id: 'study', name: '考研', icon: Document },
  { id: 'job', name: '就业', icon: Briefcase },
  { id: 'exam', name: '考公', icon: OfficeBuilding },
  { id: 'startup', name: '创业', icon: Opportunity }
]



// --- 2. 核心：注册自定义节点 ---
// --- 2. 核心：注册自定义节点 (修复版) ---
const registerCustomNode = () => {
  const COLORS = {
    core: { bg: '#fef0f0', border: '#f56c6c', text: '#c0392b' },
    high: { bg: '#fdf6ec', border: '#e6a23c', text: '#d35400' },
    default: { bg: '#ecf5ff', border: '#409eff', text: '#2c3e50' }
  }

  Graph.registerNode(
    'custom-rect',
    {
      inherit: 'rect',
      width: 180,
      height: 60,
      // --- 1. 定义默认的属性 ---
      attrs: {
        body: {
          rx: 12,
          ry: 12,
          strokeWidth: 2,
          fill: '#ecf5ff',
          stroke: '#409eff',
          // 增加阴影 (X6 支持 filter 实现阴影)
          filter: {
            name: 'dropShadow',
            args: {
              dx: 2,
              dy: 2,
              blur: 4,
              color: '#ccc'
            }
          }
        },
        // --- 2. 重点：这里必须定义 label 的默认样式 ---
        // 2. 【关键修复】文本标签样式
        label: {
          // 使用 $data.label 可以直接映射 data 中的 label 字段
          text: '$data/label', 
          fill: '#333', // 默认文字颜色
          fontSize: 14,
          fontWeight: 'bold',
          textAnchor: 'middle', // 水平居中
          textVerticalAnchor: 'middle', // 垂直居中
        }
      },
      // 3. 动态属性钩子：根据数据动态改变样式
      // ✅ 正确写法
      propHooks: (metadata) => {
        // --- 1. 防御性检查：确保必要的属性存在 ---
        // 如果 metadata.attrs 不存在，创建一个
        if (!metadata.attrs) {
          metadata.attrs = {}
        }
        // 如果 metadata.attrs.body 不存在，创建一个（防止报错）
        if (!metadata.attrs.body) {
          metadata.attrs.body = {}
        }
        // 如果 metadata.attrs.label 不存在，创建一个（防止文字消失）
        if (!metadata.attrs.label) {
          metadata.attrs.label = {}
        }

        // --- 2. 从 metadata.data 中获取数据，而不是从 node.getData() ---
        // 因为 propHooks 只有一个参数 metadata，没有 node 参数
        const data = metadata.data || {}
        const type = data.type
        const level = data.level // 修正：之前可能用了错误的字段名

        // --- 3. 定义颜色逻辑 ---
        let colors = { bg: '#ecf5ff', stroke: '#409eff', fill: '#2c3e50' }

        if (level === 'core' || type === 'core') {
          colors = { bg: '#fef0f0', stroke: '#f56c6c', fill: '#c0392b' }
        } else if (level === 'high' || type === 'important') {
          colors = { bg: '#fdf6ec', stroke: '#e6a23c', fill: '#d35400' }
        }

        // --- 4. 安全地赋值给 attrs ---
        // 修正属性名：X6 中边框颜色通常用 stroke，背景用 fill
        metadata.attrs.body.fill = colors.bg
        metadata.attrs.body.stroke = colors.stroke
        metadata.attrs.label.fill = colors.fill

        // --- 5. 关键修复：确保文字显示 ---
        // 强制将 data.label 的值同步到 attrs.label.text
        // 这是节点不显示文字的最根本原因
        if (data.label) {
          metadata.attrs.label.text = data.label
        }

        return metadata
      }
    }
  )
}

/**
 * 将后端的嵌套树结构转换为 X6 的 nodes + edges 结构
 * @param {Array} treeData - 后端返回的 skill_tree 数组
 * @returns {Object} - 包含 nodes 和 edges 的对象
 */
const transformTreeData = (treeData) => {
  const nodes = []
  const edges = []
  let idCounter = 0

  // 定义颜色映射表 (根据后端的 level 字段)
  const COLOR_MAP = {
    core: { bg: '#fef0f0', border: '#f56c6c', text: '#c0392b' }, // 红色系：核心
    high: { bg: '#fdf6ec', border: '#e6a23c', text: '#d35400' }, // 橙色系：进阶
    low:  { bg: '#f0f9eb', border: '#67c23a', text: '#228B22' }  // 绿色系：了解
  }

  // 递归遍历函数
  const traverse = (items, parentId = null) => {
    items.forEach(item => {
      const nodeId = item.id || `node-${idCounter++}`

      // 获取对应的颜色 (默认为灰色)
      const level = item.level?.toLowerCase() || 'low'
      const colors = COLOR_MAP[level] || COLOR_MAP.low

      // 1. 创建节点
      const nodeLabel = item.label || item.name || 'Node' // 获取节点标签文本
      nodes.push({
        id: nodeId,
        shape: 'custom-rect', // 使用我们注册好的自定义节点
        label: nodeLabel, // 直接设置 label 属性
        data: { 
          ...item,
          level: item.level, // 传递给节点样式钩子
          label: nodeLabel // 同时在 data 中也存储一份
        },
        // 注意：这里不需要 x/y，因为 applyDagreLayout 会自动计算位置
        // 初始位置随便给一个，或者不写
      })

      // 2. 创建边 (如果存在父节点)
      if (parentId) {
        edges.push({
          source: parentId,
          target: nodeId,
          attrs: { line: { stroke: '#909399', strokeWidth: 1 } }
        })
      }

      // 3. 递归处理子节点
      if (item.children && item.children.length > 0) {
        traverse(item.children, nodeId)
      }
    })
  }

  // 开始遍历
  traverse(treeData)
  return { nodes, edges }
}

// --- 3. 初始化画布 ---
const setupGraph = () => {
  const containerEl = container.value
  if (!containerEl) return

  registerCustomNode()

  if (graph.value) {
    graph.value.off('node:click') // 解绑旧事件
    graph.value.off('node:tap') // 解绑触摸事件
    graph.value.dispose() // 销毁旧实例
  }  

  // 动态计算初始高度
  const windowHeight = window.innerHeight
  const containerHeight = windowHeight * 0.6 // 与resize时保持一致
  const minHeight = window.innerWidth < 768 ? 300 : 400
  const finalHeight = Math.max(containerHeight, minHeight)

  graph.value = new Graph({
    container: containerEl,
    width: containerEl.clientWidth,
    height: finalHeight,
    background: { color: '#f9fbfd' },
    grid: { size: 10, visible: false },
    panning: true,
    selecting:{
      enabled: true,
      multiple: false,
    },
    scroller: {
    enabled: true,
    pageVisible: false,
    pageBreak: false,
  },
    mousewheel:{
    enabled: true,
    zoomAtMousePosition: true,
    modifiers: 'ctrl', // Mac 触控板通常需要按住 Ctrl 才能缩放
    minScale: 0.5,
    maxScale: 2,
    },
    connecting: { router: 'manhattan',
       connector: { 
          name: 'rounded', 
          args: { radius: 20 } // 圆角曲线
  }
     } // 使用曼哈顿路由，线条更直

  })

  // 绑定点击事件和触摸事件
  const handleNodeClick = ({ cell }) => {
    console.log('Node clicked:', new Date().toISOString())
    const data = cell.getData()
    console.log('Node data:', data)
    selectedNode.value = {
      label: data.label,
      resources: {
        books: [{ title: `《${data.label} 权威指南》`, author: '专家' }],
        videos: [{ title: `B站：${data.label} 教程`, url: '#' }]
      }
    }
    console.log('Selected node:', selectedNode.value)
    console.log('Before setting drawerVisible:', drawerVisible.value)
    drawerVisible.value = true
    console.log('After setting drawerVisible:', drawerVisible.value)
  }
  
  // 绑定鼠标点击事件
  graph.value.on('node:click', handleNodeClick)
  
  // 绑定触摸事件，支持移动端
  graph.value.on('node:tap', handleNodeClick)
}

// --- 4. 核心：使用 Dagre 进行自动布局 ---
// 这是 X6 官方文档推荐的标准写法
const applyDagreLayout = (nodes, edges) => {
  const graphInstance = graph.value
  if (!graphInstance) return

  // 执行布局
  const dagreGraph = new dagre.graphlib.Graph()
  dagreGraph.setGraph({
    rankdir: 'TB',
    ranksep: 120,
    nodesep: 50,
    edgesep: 20
  })
  dagreGraph.setDefaultEdgeLabel(() => ({}))

  // 获取 X6 节点对象
  const x6Nodes = graphInstance.getNodes()
  if (!x6Nodes.length) return

  // 添加节点到 Dagre 图中
  x6Nodes.forEach((node) => {
    const nodeId = node.id
    dagreGraph.setNode(nodeId, { 
      width: 180, // 必须和注册节点的 width 一致
      height: 60   // 必须和注册节点的 height 一致
    })
  })

  // 添加边到 Dagre 图中
  const x6Edges = graphInstance.getEdges()
  x6Edges.forEach((edge) => {
    const source = edge.getSource().id
    const target = edge.getTarget().id
    if (source && target) {
      dagreGraph.setEdge(source, target)
    }
  })

  // 执行布局
  dagre.layout(dagreGraph)

  // 更新坐标
  x6Nodes.forEach((node) => {
    const nodeId = node.id
    const nodeWithPosition = dagreGraph.node(nodeId)
    if (nodeWithPosition) {
      // 设置位置 (居中)
      node.position(nodeWithPosition.x - 90, nodeWithPosition.y - 30)
    }
  })

  // 强制刷新和适应
  nextTick(() => {
    graphInstance.zoomToFit({ padding: 80 }) // 增加 padding 防止被裁剪
    // X6 没有 refresh 方法，使用 centerContent 来确保内容居中
    graphInstance.centerContent()
  })
}

// --- 5. 渲染逻辑 ---
const renderGraph = (nodes, edges) => { // 接收两个参数
  if (!graph.value) return
  graph.value.clearCells()

  // 从 transformTreeData 传入的已经是处理好的数据
  graph.value.fromJSON({ nodes, edges })
  
  // 不需要重新绑定点击事件，因为在 setupGraph 中已经绑定过了
  
  // 调用布局
  applyDagreLayout(nodes, edges)
}

// 确认工作岗位选择


// --- 6. 业务逻辑：连接后端 ---
const generateKnowledgeTree = async () => {
  if (!major.value) return
  
  // 无论选择什么目标，都直接生成知识图谱
  loading.value = true // 显示加载状态
  try {
    // 1. 调用后端 API
    const formData = new FormData()
    formData.append('major', major.value)
    formData.append('goal', selectedPlan.value)
    
    const response = await axios.post('/api/generate_plan', formData)

    console.log('后端返回数据:', response.data)

    // 2. 提取 skill_tree 数据
    const backendTree = response.data.skill_tree 
    if (!Array.isArray(backendTree) || backendTree.length === 0) {
      console.error('后端返回的数据格式错误:', response.data)
      throw new Error('后端返回的技能树数据为空或格式不正确')
    }
    // 3. 转换数据结构并渲染图谱
    if (response.data && response.data.skill_tree) {
      const { nodes, edges } = transformTreeData(response.data.skill_tree)
      renderGraph(nodes, edges)
    } else {
      console.error('数据格式错误：缺少 skill_tree')
    }

    // 4. 如果选择的是就业目标，获取就业风向标数据
    if (selectedPlan.value === 'job' && response.data.job_market) {
      jobMarketData.value = response.data.job_market
    } else {
      jobMarketData.value = []
    }

  } catch (error) {
    console.error('获取数据失败:', error)
  } finally {
    loading.value = false // 无论成功失败，都要关闭加载状态
  }
}

// --- 7. 生命周期 ---
onMounted(() => {
  setupGraph()
})

// 监听窗口大小变化
const handleResize = () => {
  if (graph.value && container.value) {
    // 动态计算高度，适配不同屏幕尺寸
    const containerEl = container.value
    const windowHeight = window.innerHeight
    const containerHeight = windowHeight * 0.6 // 适配屏幕高度的60%
    
    // 最小高度限制
    const minHeight = window.innerWidth < 768 ? 300 : 400
    const finalHeight = Math.max(containerHeight, minHeight)
    
    // 调整图谱大小
    graph.value.resize(containerEl.clientWidth, finalHeight)
    
    // 重新布局和适应
    applyDagreLayout()
  }
}

// 添加resize事件监听器
window.addEventListener('resize', handleResize)

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  if (graph.value) graph.value.dispose()
})
</script>

<style scoped>
/* 沿用之前的样式，并添加新样式 */
.planner-container { padding: 20px; background-color: #f5f7fa; min-height: 100vh; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
.header-left {
  margin-right: 20px;
}
.back-button {
  font-size: 16px;
  color: #409eff;
}
.title { display: flex; align-items: center; gap: 10px; }
.logo { font-size: 32px; color: #409eff; }
.title h1 { margin: 0; font-size: 24px; font-weight: 600; color: #303133; }
.subtitle { font-size: 14px; color: #909399; }

.content { display: flex; flex-direction: column; gap: 20px; }
.section { background-color: #fff; border-radius: 12px; padding: 20px; box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.08); }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.section-title { margin: 0; font-size: 16px; font-weight: 500; color: #303133; }

.input-group { display: flex; gap: 12px; }
.major-input { flex: 1; }
.generate-btn { background-color: #409eff; border-radius: 8px; padding: 0 24px; }

/* 计划选项样式 */
.plan-options { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px;  }
.plan-btn { border-radius: 8px; padding: 12px; display: flex; align-items: center; justify-content: center; gap: 8px; border: 1px solid #dcdfe6; background-color: #fff; width: 100%; margin-left: 0 !important; }

.plan-btn .el-icon {
  font-size: 18px;
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 确保按钮之间没有左边距 */
.plan-options .el-button + .el-button {
  margin-left: 0 !important;
}
.plan-btn.active { border-color: #409eff; background-color: #409eff; color: #fff; }

/* 就业风向标样式 */
.job-market-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .planner-container { padding: 10px; }
  
  .header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .input-group {
    flex-direction: column;
  }
  
  .plan-options {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .job-market-grid {
    grid-template-columns: 1fr;
  }
  
  .graph-canvas {
    height: 400px;
  }
  
  /* 确保画布容器不会溢出 */
  .graph-section {
    overflow: hidden;
  }
}

@media (max-width: 480px) {
  .plan-options {
    grid-template-columns: 1fr;
  }
  
  .graph-canvas {
    height: 300px;
  }
  
  .section {
    padding: 15px;
  }
  
  /* 确保画布容器不会溢出 */
  .graph-section {
    overflow: hidden;
  }
  
  /* 确保计划选项按钮不会溢出 */
  .plan-btn {
    padding: 10px 8px;
    font-size: 14px;
  }
  
  .plan-btn .el-icon {
    font-size: 16px;
  }
}

.job-market-card {
  background-color: #f9f9f9;
  border-radius: 8px;
  padding: 16px;
  border-left: 4px solid #409eff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.job-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.job-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.job-salary {
  color: #67c23a;
  font-size: 14px;
  margin-bottom: 8px;
}

.job-skills {
  color: #606266;
  font-size: 14px;
  line-height: 1.4;
}

/* 技能树样式 */
.skill-tree { background-color: #fafafa; padding: 10px; border-radius: 8px; }
.tree-node { flex: 1; display: flex; align-items: center; justify-content: space-between; font-size: 14px; padding-right: 8px; }
.node-label { margin-left: 8px; }
.node-label.mastered { text-decoration: line-through; color: #909399; }
.mastered-check { transform: scale(0.8); }

/* 资源卡片样式 */
.resource-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }
.resource-card { border: 1px solid #e4e7ed; border-radius: 8px; padding: 16px; transition: all 0.3s; position: relative; overflow: hidden; }
.resource-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.1); transform: translateY(-2px); }
.resource-card.青铜 { border-top: 3px solid #909399; }
.resource-card.黄金 { border-top: 3px solid #e6a23c; }
.resource-card.王者 { border-top: 3px solid #f56c6c; }

.card-header { display: flex; justify-content: space-between; margin-bottom: 8px; }
.job-tag { font-size: 12px; color: #67c23a; font-weight: bold; }
.resource-card h3 { margin: 0 0 8px 0; font-size: 16px; }
.resource-desc { font-size: 12px; color: #606266; margin-bottom: 12px; line-height: 1.5; }
.card-footer { display: flex; justify-content: space-between; align-items: center; font-size: 12px; color: #909399; }

/* 画布容器样式 */
.graph-canvas {
  width: 100%;
  min-height: 400px; /* 最小高度 */
  border: 1px solid #ebeef5;
  border-radius: 8px;
  background-color: #fff;
  overflow: hidden; /* 防止滚动条 */
}

/* 侧边栏内容样式 */
.drawer-content {
  padding: 20px;
}

.resource-section {
  margin-bottom: 20px;
}

.resource-section h4 {
  margin-bottom: 10px;
  color: #303133;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 6px;
}

/* 书籍卡片样式 */
.resource-card {
  margin-bottom: 10px;
  border-radius: 8px;
  border: none;
  background-color: #f9f9f9;
}

.book-title {
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
  display: block;
}

.book-author {
  font-size: 12px;
  color: #999;
}

/* 视频链接样式 */
.video-item {
  padding: 8px 0;
}

.video-item .el-link {
  display: flex;
  align-items: center;
  font-size: 14px;
  color: #606266;
}

.video-item .el-link:hover {
  color: #409EFF;
}

/* 工作岗位选择弹框样式 */
.job-selection {
  max-height: 400px;
  overflow-y: auto;
}

.job-option {
  margin-bottom: 12px;
  width: 100%;
}

.job-info {
  width: 100%;
}

.job-name {
  font-weight: bold;
  margin-bottom: 4px;
}

.job-description {
  font-size: 12px;
  color: #666;
  line-height: 1.4;
  margin-left: 20px;
}

/* 滚动条样式 */
.job-selection::-webkit-scrollbar {
  width: 6px;
}

.job-selection::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.job-selection::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.job-selection::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>