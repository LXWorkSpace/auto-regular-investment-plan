<template>
  <div class="plan-detail-container">
    <el-page-header :icon="null" @back="goBack" title="返回计划列表">
      <template #content>
        <span class="page-header-title">投资计划详情</span>
      </template>
    </el-page-header>
    
    <div class="plan-content" v-loading="plansStore.loading">
      <el-alert
        v-if="!plan"
        type="info"
        :closable="false"
        show-icon
        title="无法加载计划"
        description="找不到该投资计划，请返回计划列表重新选择。"
      />
      
      <template v-else>
        <el-row :gutter="20">
          <el-col :span="16">
            <el-card shadow="hover" class="plan-card">
              <template #header>
                <div class="card-header">
                  <h2>投资计划概览</h2>
                  <el-tag 
                    v-if="plan.circuit_breaker_triggered" 
                    type="danger"
                    size="large"
                    effect="dark"
                  >
                    风险预警已触发
                  </el-tag>
                </div>
              </template>
              
              <div class="plan-overview">
                <div class="plan-info">
                  <div class="info-item">
                    <span class="label">生成时间:</span>
                    <span class="value">{{ plansStore.formattedGeneratedAt(plan) }}</span>
                  </div>
                  <div class="info-item">
                    <span class="label">月度总投资:</span>
                    <span class="value">¥{{ plan.total_monthly_amount.toLocaleString() }}</span>
                  </div>
                  <div class="info-item">
                    <span class="label">资金池金额:</span>
                    <span class="value">¥{{ plan.buffer_amount.toLocaleString() }}</span>
                    <el-tooltip content="资金池可用于在市场大幅下跌时加仓或应对紧急情况" placement="top">
                      <el-icon class="info-icon"><el-icon-info-filled /></el-icon>
                    </el-tooltip>
                  </div>
                  <div class="info-item">
                    <span class="label">持仓再平衡:</span>
                    <span class="value">
                      <el-tag :type="plan.rebalance_required ? 'warning' : 'success'" size="small">
                        {{ plan.rebalance_required ? '建议再平衡' : '无需再平衡' }}
                      </el-tag>
                    </span>
                  </div>
                </div>
              </div>

              <el-divider content-position="left">投资分配</el-divider>
              
              <div class="plans-distribution">
                <div ref="pieChartRef" class="chart-container"></div>
              </div>
            </el-card>
          </el-col>
          
          <el-col :span="8">
            <el-card shadow="hover" class="summary-card">
              <template #header>
                <div class="card-header">
                  <h3>投资概要</h3>
                </div>
              </template>
              
              <div class="summary-content">
                <el-statistic title="资产数量" :value="plan.recommendations.length">
                  <template #suffix>个</template>
                </el-statistic>
                <el-divider />
                <el-statistic 
                  title="本月应投资" 
                  :value="calculateTotalInvestment()"
                  :precision="2"
                >
                  <template #prefix>¥</template>
                </el-statistic>
                <el-divider />
                <div class="next-investment">
                  <h4>最近投资日期</h4>
                  <div class="date-list">
                    <el-tag 
                      v-for="date in getNextInvestmentDates()" 
                      :key="date"
                      type="success"
                      class="date-tag"
                    >
                      {{ date }}
                    </el-tag>
                  </div>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
        
        <el-card shadow="hover" class="recommendations-card">
          <template #header>
            <div class="card-header">
              <h2>投资建议明细</h2>
            </div>
          </template>
          
          <el-table :data="plan.recommendations" style="width: 100%" :border="true">
            <el-table-column label="资产" min-width="150">
              <template #default="scope">
                <div class="asset-cell">
                  <div class="asset-name">{{ scope.row.asset.name }}</div>
                  <div class="asset-code">{{ scope.row.asset.code }}</div>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="类型" prop="asset.type" width="120" />
            <el-table-column label="目标权重" width="100">
              <template #default="scope">
                {{ formatPercentage(scope.row.asset.weight) }}
              </template>
            </el-table-column>
            <el-table-column label="投资系数" width="330">
              <template #default="scope">
                <div class="coefficients">
                  <el-tooltip content="基于PE/PB分位的估值系数" placement="top">
                    <el-tag 
                      :type="getCoefficientType(scope.row.valuation_coefficient)"
                      effect="plain"
                    >
                      估值: {{ formatCoefficient(scope.row.valuation_coefficient) }}
                    </el-tag>
                  </el-tooltip>
                  <el-tooltip content="基于均线的趋势系数" placement="top">
                    <el-tag 
                      :type="getCoefficientType(scope.row.trend_coefficient)"
                      effect="plain"
                    >
                      趋势: {{ formatCoefficient(scope.row.trend_coefficient) }}
                    </el-tag>
                  </el-tooltip>
                  <el-tooltip content="基于ATR的波动系数" placement="top">
                    <el-tag 
                      :type="getCoefficientType(scope.row.volatility_coefficient)"
                      effect="plain"
                    >
                      波动: {{ formatCoefficient(scope.row.volatility_coefficient) }}
                    </el-tag>
                  </el-tooltip>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="投资频率" width="120">
              <template #default="scope">
                {{ scope.row.recommended_frequency }}
              </template>
            </el-table-column>
            <el-table-column label="投资金额" width="180">
              <template #default="scope">
                <div class="amount-cell">
                  <div>月度: ¥{{ scope.row.monthly_amount.toLocaleString(undefined, {maximumFractionDigits: 0}) }}</div>
                  <div>单次: ¥{{ scope.row.single_amount.toLocaleString(undefined, {maximumFractionDigits: 0}) }}</div>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="投资日期" min-width="250">
              <template #default="scope">
                <div class="dates-list">
                  <el-tag 
                    v-for="date in scope.row.investment_dates" 
                    :key="date"
                    size="small"
                    class="date-tag"
                  >
                    {{ date }}
                  </el-tag>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
        
        <el-card shadow="hover" class="tips-card">
          <template #header>
            <div class="card-header">
              <h2>投资提示</h2>
            </div>
          </template>
          
          <div class="tips-content">
            <el-alert
              v-if="plan.circuit_breaker_triggered"
              type="error"
              :closable="false"
              show-icon
              title="风险预警"
              description="系统检测到当前市场处于高估高位，建议谨慎投资，可考虑减少投入金额或暂停定投。"
              class="tip-alert"
            />
            
            <el-alert
              v-if="plan.rebalance_required"
              type="warning"
              :closable="false"
              show-icon
              title="建议再平衡"
              description="当前投资组合与目标权重偏差较大，建议适当调整持仓结构。"
              class="tip-alert"
            />
            
            <el-alert
              type="info"
              :closable="false"
              show-icon
              title="投资建议"
              description="系统建议按照上述日期和金额进行定投，投资前请确认交易日，如遇非交易日请顺延至下一交易日。"
              class="tip-alert"
            />
            
            <el-alert
              type="success"
              :closable="false"
              show-icon
              title="策略说明"
              description="本系统根据估值水平、市场趋势和波动率自动调整投资策略，无需人为干预，每月生成一次计划即可。"
              class="tip-alert"
            />
          </div>
        </el-card>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePlansStore } from '../store/plans'
import { 
  InfoFilled as ElIconInfoFilled 
} from '@element-plus/icons-vue'
import * as echarts from 'echarts/core'
import { PieChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent
} from 'echarts/components'
import { LabelLayout } from 'echarts/features'
import { CanvasRenderer } from 'echarts/renderers'

// 注册必需的组件
echarts.use([
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  PieChart,
  CanvasRenderer,
  LabelLayout
])

const route = useRoute()
const router = useRouter()
const plansStore = usePlansStore()
const pieChartRef = ref(null)
let pieChart = null

// 计算属性
const plan = computed(() => plansStore.currentPlan)

// 方法
const goBack = () => {
  router.push('/plans')
}

const formatPercentage = (value) => {
  return `${(value * 100).toFixed(0)}%`
}

const formatCoefficient = (value) => {
  return value.toFixed(2)
}

const getCoefficientType = (value) => {
  if (value > 1.2) return 'success'
  if (value < 0.8) return 'danger'
  return 'info'
}

const calculateTotalInvestment = () => {
  if (!plan.value || !plan.value.recommendations) return 0
  return plan.value.recommendations.reduce((sum, rec) => sum + rec.single_amount, 0)
}

const getNextInvestmentDates = () => {
  if (!plan.value || !plan.value.recommendations) return []
  
  // 收集所有日期并去重
  const allDates = []
  plan.value.recommendations.forEach(rec => {
    if (rec.investment_dates && rec.investment_dates.length > 0) {
      rec.investment_dates.forEach(date => {
        if (!allDates.includes(date)) {
          allDates.push(date)
        }
      })
    }
  })
  
  // 排序日期
  allDates.sort()
  
  // 只返回未来30天内的日期
  const now = new Date()
  const thirtyDaysLater = new Date()
  thirtyDaysLater.setDate(now.getDate() + 30)
  
  return allDates.filter(dateStr => {
    const date = new Date(dateStr)
    return date >= now && date <= thirtyDaysLater
  })
}

const initPieChart = () => {
  if (!pieChartRef.value || !plan.value) return
  
  // 销毁之前的图表实例
  if (pieChart) {
    pieChart.dispose()
  }
  
  // 初始化图表
  pieChart = echarts.init(pieChartRef.value)
  
  // 准备数据
  const data = plan.value.recommendations.map(rec => ({
    name: rec.asset.name,
    value: rec.monthly_amount
  }))
  
  // 设置图表选项
  const option = {
    title: {
      text: '资产分配',
      left: 'center'
    },
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      data: data.map(item => item.name)
    },
    series: [
      {
        name: '月度投资额',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: false,
          position: 'center'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: '18',
            fontWeight: 'bold'
          }
        },
        labelLine: {
          show: false
        },
        data: data
      }
    ]
  }
  
  // 设置图表
  pieChart.setOption(option)
  
  // 添加窗口大小变化时的自适应
  window.addEventListener('resize', function() {
    pieChart.resize()
  })
}

// 生命周期钩子
onMounted(async () => {
  const planId = route.params.id
  if (planId) {
    await plansStore.loadPlanById(planId)
  }
})

// 监视plan变化，初始化图表
watch(plan, () => {
  // 使用nextTick确保DOM已更新
  setTimeout(() => {
    initPieChart()
  }, 0)
}, { immediate: true })
</script>

<style scoped>
.plan-detail-container {
  padding: 20px;
}

.page-header-title {
  font-size: 18px;
  font-weight: bold;
}

.plan-content {
  margin-top: 20px;
}

.plan-card, .recommendations-card, .tips-card, .summary-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2, .card-header h3 {
  margin: 0;
}

.plan-overview {
  margin-bottom: 20px;
}

.plan-info {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.info-item {
  display: flex;
  align-items: center;
}

.label {
  min-width: 120px;
  color: #606266;
}

.value {
  font-weight: bold;
}

.info-icon {
  margin-left: 5px;
  color: #909399;
}

.chart-container {
  height: 300px;
  width: 100%;
}

.coefficients {
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
}

.asset-cell {
  display: flex;
  flex-direction: column;
}

.asset-code {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

.amount-cell {
  display: flex;
  flex-direction: column;
}

.dates-list {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.date-tag {
  margin-bottom: 5px;
}

.tip-alert {
  margin-bottom: 15px;
}

.summary-content {
  padding: 15px 0;
}

.next-investment {
  padding: 10px 0;
}

.next-investment h4 {
  margin-top: 0;
  margin-bottom: 10px;
  color: #606266;
}

.date-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
</style> 