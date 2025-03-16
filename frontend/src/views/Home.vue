<template>
  <div class="home-container">
    <el-row :gutter="20">
      <el-col :span="24">
        <el-card shadow="hover" class="welcome-card">
          <h2>欢迎使用自动定投策略提醒系统</h2>
          <p class="subtitle">基于估值择时、趋势跟踪和波动率适配的智能定投策略</p>
          <el-divider />
          <div class="features">
            <div class="feature">
              <el-icon class="feature-icon"><el-icon-data-analysis /></el-icon>
              <h3>估值择时</h3>
              <p>基于PE/PB分位数判断市场估值水平，低估时加码，高估时减码</p>
            </div>
            <div class="feature">
              <el-icon class="feature-icon"><el-icon-trend-charts /></el-icon>
              <h3>趋势跟踪</h3>
              <p>基于200日均线判断市场趋势，避免逆势操作，顺应市场趋势</p>
            </div>
            <div class="feature">
              <el-icon class="feature-icon"><el-icon-alarm-clock /></el-icon>
              <h3>波动率适配</h3>
              <p>根据ATR波动率自动调整投资频率，波动小时频繁小额投入，波动大时降低频率集中投入</p>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="mt-20">
      <el-col :span="12">
        <el-card shadow="hover" class="action-card">
          <template #header>
            <div class="card-header">
              <h3>快速操作</h3>
            </div>
          </template>
          <div class="quick-actions">
            <el-button type="primary" @click="navigateTo('/config')" :icon="Setting">
              设置投资配置
            </el-button>
            <el-button type="success" @click="navigateTo('/market')" :icon="DataLine">
              查看市场数据
            </el-button>
            <el-button type="warning" @click="generatePlan" :loading="plansStore.generating" :icon="Document">
              生成投资计划
            </el-button>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card shadow="hover" class="latest-plan-card" v-loading="plansStore.loading">
          <template #header>
            <div class="card-header">
              <h3>最新投资计划</h3>
              <el-button class="button" text @click="navigateTo('/plans')" v-if="latestPlan">
                查看全部计划
              </el-button>
            </div>
          </template>
          <div v-if="latestPlan" class="latest-plan">
            <p>生成时间: {{ plansStore.formattedGeneratedAt(latestPlan) }}</p>
            <p>月度总投资: ¥{{ latestPlan.total_monthly_amount?.toLocaleString() }}</p>
            <p>资金池金额: ¥{{ latestPlan.buffer_amount?.toLocaleString() }}</p>
            <p>推荐方案数量: {{ latestPlan.recommendations?.length || 0 }}</p>
            <el-button type="primary" @click="navigateTo(`/plans/${latestPlan.id}`)" plain>
              查看详情
            </el-button>
          </div>
          <el-empty 
            v-else 
            description="暂无投资计划" 
            :image-size="100"
          >
            <el-button type="primary" @click="generatePlan">
              立即生成
            </el-button>
          </el-empty>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { usePlansStore } from '../store/plans'
import { 
  Setting, 
  DataLine, 
  Document,
  DataAnalysis as ElIconDataAnalysis,
  TrendCharts as ElIconTrendCharts,
  AlarmClock as ElIconAlarmClock
} from '@element-plus/icons-vue'

const router = useRouter()
const plansStore = usePlansStore()

// 计算属性
const latestPlan = computed(() => plansStore.latestPlan)

// 方法
const navigateTo = (path) => {
  router.push(path)
}

const generatePlan = async () => {
  await plansStore.generatePlan()
  if (plansStore.currentPlan) {
    router.push(`/plans/${plansStore.currentPlan.id}`)
  }
}

// 生命周期钩子
onMounted(async () => {
  await plansStore.loadPlans()
})
</script>

<style scoped>
.home-container {
  padding: 20px;
}

.mt-20 {
  margin-top: 20px;
}

.welcome-card {
  text-align: center;
}

.subtitle {
  color: #606266;
  font-size: 16px;
  margin-top: 10px;
}

.features {
  display: flex;
  justify-content: space-around;
  margin-top: 20px;
  flex-wrap: wrap;
}

.feature {
  flex: 1;
  min-width: 250px;
  padding: 15px;
  text-align: center;
}

.feature-icon {
  font-size: 48px;
  color: #409EFF;
  margin-bottom: 10px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
}

.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.latest-plan {
  line-height: 1.8;
}
</style> 