<template>
  <div class="life-container" :style="containerStyle">
    <!-- 背景层已移到 MainLayout 中 -->
    <div class="back-header">
      <el-button type="primary" link @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
        返回主页
      </el-button>
    </div>
    <h1 class="page-title">济南租房水电费分析</h1>
    
    <!-- 用户输入表单 -->
    <div class="input-section">
      <el-card class="input-card">
        <template #header>
          <div class="card-header">
            <span>参数设置</span>
          </div>
        </template>
        <el-form :model="userInput" class="input-form">
          <el-form-item label="区域" required>
            <el-select v-model="userInput.district" placeholder="选择区域" style="width: 100%">
              <el-option label="历下区" value="历下区"></el-option>
              <el-option label="市中区" value="市中区"></el-option>
              <el-option label="历城区" value="历城区"></el-option>
              <el-option label="长清区" value="长清区"></el-option>
              <el-option label="高新区" value="高新区"></el-option>
              <el-option label="天桥区" value="天桥区"></el-option>
            </el-select>
          </el-form-item>
          <el-form-item label="居住时长" required>
            <el-input-number v-model="userInput.duration" :min="1" :max="12" :step="1" style="width: 100%" />
            <span class="unit">个月</span>
          </el-form-item>
          <el-form-item label="房屋面积" required>
            <el-input-number v-model="userInput.area" :min="10" :max="200" :step="5" style="width: 100%" />
            <span class="unit">㎡</span>
          </el-form-item>
          <el-form-item label="房屋性质" required>
            <el-radio-group v-model="userInput.housingType">
              <el-radio label="A">A类：正规住宅（民水民电，有暖气）</el-radio>
              <el-radio label="B">B类：商业公寓（商水商电，无暖气/自采暖）</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="calculateCost" style="width: 100%">分析方案</el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>
    
    <!-- 区域标签提示 -->
    <div class="district-tip" v-if="districtTip">
      <el-alert
        :title="districtTip"
        type="warning"
        show-icon
        :closable="false"
      />
    </div>
    
    <!-- 分析结果 -->
    <div class="result-section" v-if="showResult">
      <!-- 水电费预警 -->
      <div class="warning-section">
        <h2 class="section-title">水电费预警</h2>
        <el-card class="warning-card">
          <div class="warning-content">
            <el-icon class="warning-icon"><WarningFilled /></el-icon>
            <p>{{ warningMessage }}</p>
          </div>
        </el-card>
      </div>

     
      
      <!-- 方案对比 -->
      <div class="comparison-section">
        <h2 class="section-title">方案对比</h2>
        <div class="comparison-cards">
          <el-card :class="['comparison-card', { 'recommended': plan.recommended }]" v-for="plan in plans" :key="plan.id">
            <template #header>
              <div class="card-header">
                <el-icon v-if="plan.recommended" class="recommended-icon"><Check /></el-icon>
                <span>{{ plan.name }}</span>
              </div>
            </template>
            <div class="plan-content">
              <div class="plan-scenario">
                <span class="label">适用场景：</span>
                <span>{{ plan.scenario }}</span>
              </div>
              <div class="plan-cost">
                <span class="label">费用构成：</span>
                <ul>
                  <li v-for="(item, index) in plan.costBreakdown" :key="index">{{ item }}</li>
                </ul>
              </div>
              <div class="plan-total">
                <span class="label">总成本估算：</span>
                <span class="total-price">¥{{ plan.totalCost.toFixed(2) }}</span>
              </div>
              <div class="plan-comfort">
                <span class="label">舒适度：</span>
                <div class="comfort-stars">
                  <el-icon v-for="i in 5" :key="i" :class="['star-icon', { 'active': i <= plan.comfort }]"><Star /></el-icon>
                </div>
              </div>
              <div class="plan-evaluation">
                <span class="label">评价：</span>
                <span>{{ plan.evaluation }}</span>
              </div>
            </div>
          </el-card>
        </div>
      </div>
      
      <!-- 最终建议 -->
      <div class="suggestion-section">
        <h2 class="section-title">最终建议</h2>
        <el-card class="suggestion-card">
          <div class="suggestion-content">
            <h3>{{ suggestion.title }}</h3>
            <p>{{ suggestion.content }}</p>
            <div class="suggestion-reason">
            <h4>理由:</h4>
            <ul>
              <li v-for="(reason, index) in suggestion.reasons" :key="index" v-html="sanitize(reason)"></li>
            </ul>
          </div>
            <div class="suggestion-operation">
              <h4>操作建议：</h4>
              <p>{{ suggestion.operation }}</p>
            </div>
          </div>
        </el-card>
      </div>
        <!-- 费用趋势图 -->
      <div class="trend-section">
        <h2 class="section-title">费用趋势</h2>
        <el-card class="trend-card">
          <div class="trend-chart">
            <div ref="chartRef" class="chart-container"></div>
          </div>
        </el-card>
      </div>
     
    </div>
  </div>
</template>

<script setup>
import { sanitizeHtml } from '../utils/sanitize'
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { WarningFilled, Check, Star, ArrowLeft } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { useBackground } from '../composables/useBackground'

const sanitize = (html) => sanitizeHtml(html)

// 使用背景设置
const { containerStyle } = useBackground()

const router = useRouter()

const goBack = () => {
  router.push('/')
}

// 响应式数据
const userInput = ref({
  district: '',
  duration: 2,
  area: 60,
  housingType: 'A'
})

const showResult = ref(false)
const warningMessage = ref('')
const districtTip = ref('')
const plans = ref([])
const suggestion = ref({})
const trendData = ref([])
const chartRef = ref(null)
let chart = null

// 区域标签库
const districtTags = {
  '高新区': '该区域多为商业公寓，电费1.2元/度，严禁全天开空调取暖',
  '历下区': '该区域多为集中供暖，请务必确认房租是否包含暖气费',
  '市中区': '该区域多为集中供暖，请务必确认房租是否包含暖气费',
  '历城区': '该区域多为正规住宅，民水民电，有集中供暖',
  '长清区': '该区域多为正规住宅，民水民电，有集中供暖',
  '天桥区': '该区域多为正规住宅，民水民电，有集中供暖'
}

// 监听区域变化，显示区域标签
watch(() => userInput.value.district, (newDistrict) => {
  districtTip.value = districtTags[newDistrict] || ''
})

// 组件挂载时初始化图表
// 注意：图表容器位于条件渲染块中，在showResult为true时才会渲染
// 因此不需要在onMounted中初始化图表，而是在calculateCost函数中初始化

// 初始化图表
const initChart = () => {
  // 延迟执行，确保DOM已经更新
  setTimeout(() => {
    if (chartRef.value) {
      try {
        chart = echarts.init(chartRef.value)
        console.log('图表初始化成功')
      } catch (error) {
        console.error('图表初始化失败:', error)
      }
    } else {
      console.warn('图表容器未找到')
    }
  }, 100)
}

// 更新图表
const updateChart = (months, centralHeatingData, airConditionerData, heatingBlanketData) => {
  // 确保图表容器存在
  if (!chartRef.value) {
    console.warn('图表容器未找到')
    return
  }
  
  // 确保图表已经初始化
  if (!chart) {
    try {
      chart = echarts.init(chartRef.value)
      console.log('图表初始化成功')
    } catch (error) {
      console.error('图表初始化失败:', error)
      return
    }
  }
  
  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: function(params) {
        let result = `居住${params[0].name}个月<br/>`
        params.forEach(item => {
          result += `${item.marker}${item.seriesName}: ¥${item.value.toFixed(2)}<br/>`
        })
        return result
      }
    },
    legend: {
      data: ['集中供暖', '空调', '电热毯+空调'],
      top: 0
    },
    grid: {
      left: '10%',
      right: '10%',
      bottom: '15%',
      top: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: ['1', '2', '3', '4', '5', '6'],
      name: '居住月数',
      nameLocation: 'middle',
      nameGap: 30
    },
    yAxis: {
      type: 'value',
      name: '总费用 (元)',
      nameLocation: 'middle',
      nameGap: 40
    },
    series: [
      {
        name: '集中供暖',
        type: 'line',
        data: centralHeatingData,
        itemStyle: {
          color: '#409eff'
        },
        lineStyle: {
          width: 3
        }
      },
      {
        name: '空调',
        type: 'line',
        data: airConditionerData,
        itemStyle: {
          color: '#f56c6c'
        },
        lineStyle: {
          width: 3
        }
      },
      {
        name: '电热毯+空调',
        type: 'line',
        data: heatingBlanketData,
        itemStyle: {
          color: '#67c23a'
        },
        lineStyle: {
          width: 3
        }
      }
    ]
  }
  
  try {
    chart.setOption(option)
  } catch (error) {
    console.error('图表更新失败:', error)
  }
}

// 计算费用
const calculateCost = () => {
  if (!userInput.value.district) {
    ElMessage.error('请选择区域')
    return
  }
  
  const { district, duration, area, housingType } = userInput.value
  
  // 济南真实数据
  const centralHeatingCost = 26.7 // 元/㎡
  const residentialElectricity = 0.55 // 元/度
  const commercialElectricity = 1.2 // 元/度
  
  // 设备能耗模型
  const airConditionerHourly = 1.2 // 度/小时
  const heatingBlanketDaily = 0.5 // 度/天
  
  // 计算不同方案的成本
  const isCommercial = (district === '高新区' || housingType === 'B')
  const electricityPrice = isCommercial ? commercialElectricity : residentialElectricity
  
  // 方案A：集中供暖
  const planA = {
    id: 1,
    name: '方案A：集中供暖',
    scenario: '长租 (>3个月)，正规小区',
    costBreakdown: [
      `暖气费: ${area}㎡ × ${centralHeatingCost} = ${(area * centralHeatingCost).toFixed(2)}元 (一口价)`,
      '辅助电费: 仅照明热水'
    ],
    totalCost: area * centralHeatingCost + 100, // 加上100元辅助电费
    comfort: 5,
    evaluation: '恒温24℃，舒适度最高',
    recommended: false
  }
  
  // 方案B：空调硬扛
  const planB = {
    id: 2,
    name: '方案B：空调硬扛',
    scenario: '短租 (1-2个月)，公寓/无暖气',
    costBreakdown: [
      '暖气费: 0元',
      `电费: 每天开10小时 × ${airConditionerHourly}度 × ${electricityPrice}元(商电) × ${duration * 30}天`
    ],
    totalCost: 10 * airConditionerHourly * electricityPrice * duration * 30,
    comfort: 2,
    evaluation: '干燥/头热脚冷，舒适度低',
    recommended: false
  }
  
  // 方案C：空调+电热毯
  const planC = {
    id: 3,
    name: '方案C：空调+电热毯',
    scenario: '极致省钱，所有房型',
    costBreakdown: [
      '暖气费: 0元',
      '空调: 仅早晚开 (50%时间)',
      `电热毯: 每晚开 (${heatingBlanketDaily}度 × ${duration * 30}天)`
    ],
    totalCost: (5 * airConditionerHourly * electricityPrice * duration * 30) + (heatingBlanketDaily * electricityPrice * duration * 30),
    comfort: 3,
    evaluation: '被窝极暖，舒适度中等',
    recommended: false
  }
  
  // 确定推荐方案
  let recommendedPlan
  if (duration > 3 && housingType === 'A') {
    recommendedPlan = planA
  } else if (isCommercial && duration <= 3) {
    recommendedPlan = planC
  } else if (duration <= 2) {
    recommendedPlan = planC
  } else {
    recommendedPlan = planA
  }
  
  recommendedPlan.recommended = true
  
  // 设置方案
  plans.value = [planA, planB, planC]
  
  // 生成预警信息
  if (isCommercial) {
    warningMessage.value = `⚠️ 注意：${district}大量房源为商水商电（电费约${electricityPrice}元/度）。若使用空调取暖，电费将是普通住宅的 ${(electricityPrice / residentialElectricity).toFixed(1)}倍。`
  } else {
    warningMessage.value = `ℹ️ 提示：${district}多为正规住宅，民水民电（电费约${electricityPrice}元/度），可考虑集中供暖。`
  }
  
  // 生成最终建议
  suggestion.value = {
    title: `针对您"居住${duration}个月"的需求，建议选择【${recommendedPlan.name}】。`,
    content: '',
    reasons: [],
    operation: ''
  }
  
  if (recommendedPlan === planA) {
    suggestion.value.reasons = [
      `集中供暖费（${(area * centralHeatingCost).toFixed(2)}元）对于长租来说单价合理`,
      '舒适度最高，恒温24℃',
      '无需担心电费飙升问题'
    ]
    suggestion.value.operation = '确认房租是否包含暖气费，如不包含，需单独缴纳供暖费用。'
  } else if (recommendedPlan === planB) {
    suggestion.value.reasons = [
      '短租时间较短，集中供暖费用较高',
      '空调取暖方便，无需开通暖气'
    ]
    suggestion.value.operation = '合理控制空调使用时间，避免电费过高。'
  } else if (recommendedPlan === planC) {
    suggestion.value.reasons = [
      `<span style="color: red; font-weight: bold;">集中供暖费（${(area * centralHeatingCost).toFixed(2)}元）对于短租来说单价过高，即使只住${duration}个月，也需要缴纳整个供暖季的费用</span>`,
      `商电公寓全开空调会导致电费爆炸（约${planB.totalCost.toFixed(2)}元）`,
      `<span style="color: green; font-weight: bold;">方案C比纯空调省 ${(planB.totalCost - planC.totalCost).toFixed(2)}元！</span>`
    ]
    suggestion.value.operation = '购买一个定时电热毯（成本约60元），晚上睡觉关掉空调，每月电费可控制在 200元以内。'
  }
  
  // 生成趋势数据
  trendData.value = []
  const months = []
  const centralHeatingData = []
  const airConditionerData = []
  const heatingBlanketData = []
  
  for (let i = 1; i <= 6; i++) {
    // 集中供暖费用：按整个供暖季（4个月）计算，即使只住1-2个月，也需要缴纳整个供暖季的费用
    const centralHeating = area * centralHeatingCost + 100 // 加上100元辅助电费
    const airConditioner = 10 * airConditionerHourly * electricityPrice * i * 30
    const heatingBlanket = (5 * airConditionerHourly * electricityPrice * i * 30) + (heatingBlanketDaily * electricityPrice * i * 30)
    
    months.push(i)
    centralHeatingData.push(centralHeating)
    airConditionerData.push(airConditioner)
    heatingBlanketData.push(heatingBlanket)
    
    trendData.value.push({
      months: i,
      centralHeating: `¥${centralHeating.toFixed(2)}`,
      airConditioner: `¥${airConditioner.toFixed(2)}`,
      heatingBlanket: `¥${heatingBlanket.toFixed(2)}`
    })
  }
  
  showResult.value = true
  
  // 延迟执行，确保图表容器已经渲染完成
  setTimeout(() => {
    // 初始化图表
    if (!chart) {
      initChart()
    }
    // 更新图表
    updateChart(months, centralHeatingData, airConditionerData, heatingBlanketData)
  }, 100)
}
</script>

<style scoped>
.life-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.back-header {
  margin-bottom: 20px;
  text-align: left;
}

.page-title {
  font-size: 28px;
  font-weight: bold;
  margin-bottom: 30px;
  color: #ffffff;
  text-align: center;
}

.input-section {
  margin-bottom: 30px;
}

.input-card {
  transition: all 0.3s ease;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 10px;
}

.input-card:hover {
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
}

.input-form {
  padding: 20px;
}

.input-form .el-form-item {
  margin-bottom: 20px;
}

.unit {
  margin-left: 10px;
  color: #909399;
}

.district-tip {
  margin-bottom: 30px;
}

.result-section {
  margin-top: 40px;
}

.section-title {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 20px;
  color: #303133;
}

.warning-section {
  margin-bottom: 40px;
}

.warning-card {
  border-left: 4px solid #e6a23c;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 10px;
}

.warning-content {
  display: flex;
  align-items: flex-start;
  gap: 15px;
  padding: 20px;
}

.warning-icon {
  font-size: 24px;
  color: #e6a23c;
  margin-top: 2px;
}

.warning-content p {
  margin: 0;
  color: #606266;
  line-height: 1.6;
}

.comparison-section {
  margin-bottom: 40px;
}

.comparison-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 20px;
}

.comparison-card {
  transition: all 0.3s ease;
  border-top: 4px solid #dcdfe6;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 10px;
}

.comparison-card:hover {
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  transform: translateY(-5px);
}

.comparison-card.recommended {
  border-top: 4px solid #67c23a;
  background-color: rgba(240, 249, 235, 0.9);
}

.card-header {
  display: flex;
  align-items: center;
  font-size: 16px;
  font-weight: bold;
  color: #303133;
}

.recommended-icon {
  color: #67c23a;
  margin-right: 8px;
}

.plan-content {
  padding: 20px;
}

.plan-scenario {
  margin-bottom: 15px;
}

.plan-cost {
  margin-bottom: 15px;
}

.plan-cost ul {
  margin: 5px 0 0 20px;
  padding: 0;
}

.plan-cost li {
  margin-bottom: 5px;
  color: #606266;
}

.plan-total {
  margin-bottom: 15px;
}

.plan-comfort {
  margin-bottom: 15px;
}

.comfort-stars {
  display: flex;
  gap: 5px;
}

.star-icon {
  color: #dcdfe6;
  font-size: 16px;
}

.star-icon.active {
  color: #e6a23c;
}

.plan-evaluation {
  margin-bottom: 15px;
}

.label {
  font-weight: bold;
  color: #303133;
  margin-right: 10px;
}

.total-price {
  font-size: 18px;
  font-weight: bold;
  color: #f56c6c;
}

.suggestion-section {
  margin-bottom: 40px;
}

.suggestion-card {
  border-left: 4px solid #409eff;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 10px;
}

.suggestion-content {
  padding: 20px;
}

.suggestion-content h3 {
  margin-top: 0;
  margin-bottom: 15px;
  color: #303133;
}

.suggestion-content p {
  margin-bottom: 20px;
  color: #606266;
  line-height: 1.6;
}

.suggestion-reason h4,
.suggestion-operation h4 {
  margin-top: 0;
  margin-bottom: 10px;
  color: #303133;
}

.suggestion-reason ul {
  margin: 0 0 20px 20px;
  padding: 0;
}

.suggestion-reason li {
  margin-bottom: 5px;
  color: #606266;
}

.trend-section {
  margin-bottom: 40px;
}

.trend-card {
  transition: all 0.3s ease;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 10px;
}

.trend-card:hover {
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
}

.trend-chart {
  padding: 20px 0;
}

.chart-container {
  width: 100%;
  height: 400px;
}

@media (max-width: 768px) {
  .life-container {
    padding: 10px;
  }
  
  .back-header {
    margin-bottom: 15px;
  }
  
  .comparison-cards {
    grid-template-columns: 1fr;
  }
  
  .input-form .el-form-item {
    margin-bottom: 15px;
  }
}
</style>