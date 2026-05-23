<template>
  <div class="graph-wrapper">
    <!-- 搜索框 -->
    <div class="search-bar">
      <el-input 
        v-model="searchQuery" 
        placeholder="搜索知识点..." 
        prefix-icon="Search"
        clearable
        @input="onSearchInput"
        @change="handleSearch"
        class="search-input"
      />
    </div>
    
    <!-- 图例 -->
    <div class="legend">
      <div class="legend-item">
        <span class="legend-color core"></span>
        <span>核心必学</span>
      </div>
      <div class="legend-item">
        <span class="legend-color high"></span>
        <span>进阶掌握</span>
      </div>
      <div class="legend-item">
        <span class="legend-color low"></span>
        <span>了解即可</span>
      </div>
    </div>

    <!-- 图谱容器 -->
    <div ref="container" class="graph-container" :style="{ height: height + 'px' }">
      <div v-if="!graphReady" class="loading-overlay">
        <el-icon :size="48" class="loading-icon"><Loading /></el-icon>
        <p>图谱加载中...</p>
      </div>
      
      <!-- 空状态 -->
      <div v-if="graphReady && props.nodes.length === 0" class="empty-state">
        <el-icon :size="64" class="empty-icon"><Failed /></el-icon>
        <p>暂无数据，请先生成知识图谱</p>
      </div>
    </div>

    <!-- 操作提示 -->
    <div class="tips">
      <span class="tip-item">🖱️ 点击节点查看详情</span>
      <span class="tip-item">🔍 搜索定位节点</span>
      <span class="tip-item">🔄 拖拽移动节点</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, nextTick, computed } from 'vue'
import { Graph } from '@antv/x6'
import { Loading, Failed, Search } from '@element-plus/icons-vue'
import dagre from 'dagre'

const props = defineProps({
  nodes: {
    type: Array,
    default: () => []
  },
  edges: {
    type: Array,
    default: () => []
  },
  height: {
    type: Number,
    default: 500
  }
})

const emit = defineEmits(['node-click'])

const container = ref(null)
const graph = ref(null)
const graphReady = ref(false)
const searchQuery = ref('')
const progressMap = ref({})
let nodeRegistered = false

// 搜索结果高亮
const highlightNodes = computed(() => {
  if (!searchQuery.value) return []
  const query = searchQuery.value.toLowerCase()
  return props.nodes.filter(node => 
    node.label.toLowerCase().includes(query)
  ).map(n => n.id)
})

const handleSearch = () => {
  if (!graph.value) {
    console.log('graph.value 不存在')
    return
  }
  
  console.log('handleSearch 被调用, searchQuery:', searchQuery.value)
  console.log('当前节点数:', graph.value.getNodes().length)
  
  // 先重置所有节点样式
  graph.value.getNodes().forEach(node => {
    node.attr('body/stroke', '#409eff')
    node.attr('body/strokeWidth', 2)
  })
  
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    console.log('搜索关键词:', query)
    
    let matchCount = 0
    let firstMatch = null
    
    graph.value.getNodes().forEach(node => {
      const label = node.getLabel?.() || ''
      console.log('检查节点, label:', label)
      if (label && label.toLowerCase().includes(query)) {
        console.log('匹配成功!')
        node.attr('body/stroke', '#f56c6c')
        node.attr('body/strokeWidth', 4)
        matchCount++
        if (!firstMatch) {
          firstMatch = node
        }
      }
    })
    
    console.log('匹配到的节点数:', matchCount)
    
    if (firstMatch) {
      nextTick(() => {
        graph.value.zoomToFit({ padding: 50, maxScale: 1.5 })
      })
    }
  }
}

const onSearchInput = (val) => {
  console.log('onSearchInput 被调用, val:', val)
  handleSearch()
}

const setupGraph = async () => {
  if (!container.value) return
  
  await nextTick()
  
  const containerEl = container.value
  const width = containerEl.clientWidth
  
  if (width === 0) {
    console.warn('容器宽度为0，延迟重试')
    setTimeout(setupGraph, 100)
    return
  }
  
  if (!nodeRegistered) {
    Graph.registerNode('custom-node', {
      inherit: 'rect',
      width: 180,
      height: 60,
      attrs: {
        body: {
          fill: '#ecf5ff',
          stroke: '#409eff',
          strokeWidth: 2,
          rx: 8,
          ry: 8,
          shadowColor: 'transparent',
          shadowBlur: 0
        },
        label: {
          fill: '#2c3e50',
          fontSize: 14,
          fontWeight: 'bold'
        }
      },
      ports: {
        groups: {
          top: { position: 'top', attrs: { circle: { r: 4, magnet: true, stroke: '#409eff', strokeWidth: 2, fill: '#fff' } } },
          bottom: { position: 'bottom', attrs: { circle: { r: 4, magnet: true, stroke: '#409eff', strokeWidth: 2, fill: '#fff' } } }
        }
      }
    })
    nodeRegistered = true
  }
  
  graph.value = new Graph({
    container: containerEl,
    width: width,
    height: props.height,
    background: { color: '#f9fbfd' },
    grid: { size: 10, visible: false },
    scroller: {
      enabled: true,
      pageVisible: false,
      pageBreak: false,
      touchEnabled: true,
      pannable: true,
      scalable: true,
      minScale: 0.3,
      maxScale: 3
    },
    mousewheel: {
      enabled: true,
      zoomAtMousePosition: true,
      minScale: 0.3,
      maxScale: 3
    },
    connecting: {
      router: 'manhattan',
      connector: {
        name: 'rounded',
        args: { radius: 20 }
      }
    },
    selecting: {
      enabled: true,
      rubberband: true,
      showNodeSelectionBox: true
    },
    highlighting: {
      magnetAvailable: {
        name: 'stroke',
        args: {
          attrs: {
            strokeWidth: 3,
            stroke: '#409eff'
          }
        }
      },
      magnetAdsorbed: {
        name: 'stroke',
        args: {
          attrs: {
            strokeWidth: 3,
            stroke: '#52c41a'
          }
        }
      }
    }
  })
  
  // 点击事件
  graph.value.on('node:click', ({ cell }) => {
    let data = cell.getData() || cell.data
    if (!data) {
      const attrs = cell.getAttrs?.() || {}
      data = {
        label: cell.getLabel?.() || attrs.label || '未知节点',
        level: attrs.level || 'low',
        description: ''
      }
    }
    console.log('KnowledgeGraph 节点点击, data:', data)
    emit('node-click', data)
  })
  
  // 双击事件 - 居中放大
  graph.value.on('node:dblclick', ({ cell }) => {
    const view = cell.findView(graph.value)
    if (view) {
      const rect = view.getBBox()
      graph.value.zoomToFit({
        padding: 80,
        maxScale: 2,
        rect: rect
      })
    }
  })
  
  // 边点击事件
  graph.value.on('edge:click', ({ cell }) => {
    console.log('边被点击:', cell)
  })
  
  // 画布点击事件 - 取消选中
  graph.value.on('blank:click', () => {
    if (graph.value) {
      const selected = graph.value.getSelectedCells()
      selected.forEach(cell => {
        cell.setSelected(false)
      })
    }
  })
  
  graphReady.value = true
  
  if (props.nodes.length > 0) {
    renderGraph()
  }
}

const updateNodeProgress = (label) => {
  // 节点进度更新函数 - 可根据需要扩展实现
  const progress = progressMap.value[label]
  if (progress && graph.value) {
    const node = graph.value.getCellById(label)
    if (node) {
      // 可以在这里添加进度显示逻辑，比如改变节点颜色等
      console.log(`更新节点 ${label} 的进度: ${progress}`)
    }
  }
}

const applyLayout = () => {
  if (!graph.value) return
  
  const dagreGraph = new dagre.graphlib.Graph()
  dagreGraph.setGraph({
    rankdir: 'TB',
    ranksep: 100,
    nodesep: 60,
    edgesep: 20
  })
  dagreGraph.setDefaultEdgeLabel(() => ({}))
  
  const x6Nodes = graph.value.getNodes()
  if (!x6Nodes.length) return
  
  x6Nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: 180, height: 60 })
  })
  
  const x6Edges = graph.value.getEdges()
  x6Edges.forEach((edge) => {
    const source = edge.getSource().id
    const target = edge.getTarget().id
    if (source && target) {
      dagreGraph.setEdge(source, target)
    }
  })
  
  dagre.layout(dagreGraph)
  
  x6Nodes.forEach((node) => {
    const nodeId = node.id
    const nodeWithPosition = dagreGraph.node(nodeId)
    if (nodeWithPosition) {
      node.position(nodeWithPosition.x - 90, nodeWithPosition.y - 30)
    }
  })
  
  nextTick(() => {
    if (graph.value) {
      graph.value.zoomToFit({ padding: 60 })
      graph.value.centerContent()
    }
  })
}

const renderGraph = () => {
  if (!graph.value || !graphReady.value) return
  
  graph.value.clearCells()
  
  if (props.nodes.length > 0) {
    try {
      graph.value.fromJSON({ nodes: props.nodes, edges: props.edges || [] })
      applyLayout()
      
      // 更新进度显示
      props.nodes.forEach(node => {
        if (progressMap.value[node.label]) {
          updateNodeProgress(node.label)
        }
      })
      
      console.log('图谱渲染成功，节点数:', props.nodes.length, '边数:', (props.edges || []).length)
    } catch (error) {
      console.error('图谱渲染失败:', error)
    }
  }
}

watch(() => [props.nodes, props.edges], () => {
  renderGraph()
}, { deep: true })

onMounted(() => {
  setupGraph()
})

onBeforeUnmount(() => {
  if (graph.value) {
    graph.value.dispose()
    graph.value = null
  }
})
</script>

<style scoped>
.graph-wrapper {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.search-bar {
  display: flex;
  justify-content: flex-end;
}

.search-input {
  width: 300px;
}

.legend {
  display: flex;
  gap: 24px;
  padding: 8px 16px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #606266;
}

.legend-color {
  width: 16px;
  height: 16px;
  border-radius: 4px;
}

.legend-color.core {
  background: #fef0f0;
  border: 2px solid #f56c6c;
}

.legend-color.high {
  background: #fdf6ec;
  border: 2px solid #e6a23c;
}

.legend-color.low {
  background: #ecf5ff;
  border: 2px solid #409eff;
}

.graph-container {
  width: 100%;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  position: relative;
  overflow: hidden;
}

.loading-overlay, .empty-state {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.9);
  z-index: 10;
}

.loading-icon, .empty-icon {
  color: #409eff;
}

.loading-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.empty-icon {
  opacity: 0.5;
}

.loading-overlay p, .empty-state p {
  margin-top: 16px;
  color: #606266;
}

.tips {
  display: flex;
  justify-content: center;
  gap: 24px;
  padding: 8px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.tip-item {
  font-size: 13px;
  color: #909399;
}
</style>
