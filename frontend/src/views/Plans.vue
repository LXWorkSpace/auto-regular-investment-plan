<template>
  <div class="plans-container">
    <el-card shadow="hover" class="plans-card">
      <template #header>
        <div class="card-header">
          <h2>投资计划列表</h2>
          <div>
            <el-button 
              type="primary" 
              @click="generatePlan" 
              :loading="plansStore.generating"
            >
              生成新计划
            </el-button>
          </div>
        </div>
      </template>
      
      <div v-loading="plansStore.loading">
        <el-alert
          v-if="plansStore.plans.length === 0"
          type="info"
          :closable="false"
          show-icon
          title="暂无投资计划"
          description="您还没有生成任何投资计划，请点击上方按钮生成第一个计划。"
        />
        
        <el-timeline v-else>
          <el-timeline-item
            v-for="plan in plansStore.plans"
            :key="plan.id"
            :timestamp="plansStore.formattedGeneratedAt(plan)"
            placement="top"
            :type="getTimelineItemType(plan)"
            :hollow="true"
            :size="plan === plansStore.latestPlan ? 'large' : 'normal'"
          >
            <el-card class="plan-item-card">
              <div class="plan-item-content">
                <div class="plan-item-info">
                  <h3>
                    {{ plan === plansStore.latestPlan ? '最新投资计划' : '历史投资计划' }}
                    <el-tag 
                      v-if="plan.circuit_breaker_triggered" 
                      type="danger"
                      effect="dark"
                      size="small"
                    >
                      风险预警
                    </el-tag>
                  </h3>
                  <div class="plan-details">
                    <div class="detail-item">
                      <span class="label">月度总投资:</span>
                      <span class="value">¥{{ plan.total_monthly_amount.toLocaleString() }}</span>
                    </div>
                    <div class="detail-item">
                      <span class="label">资产数量:</span>
                      <span class="value">{{ plan.recommendations?.length || 0 }} 个</span>
                    </div>
                    <div class="detail-item">
                      <span class="label">资金池金额:</span>
                      <span class="value">¥{{ plan.buffer_amount.toLocaleString() }}</span>
                    </div>
                  </div>
                  
                  <div class="assets-distribution" v-if="plan.recommendations">
                    <h4>资产分布:</h4>
                    <div class="asset-tags">
                      <el-tag 
                        v-for="rec in getTopRecommendations(plan)"
                        :key="rec.asset.code"
                        effect="plain"
                        class="asset-tag"
                      >
                        {{ rec.asset.name }} {{ formatPercentage(rec.monthly_amount / plan.total_monthly_amount) }}
                      </el-tag>
                      <el-tag v-if="plan.recommendations.length > 5" type="info" class="asset-tag">
                        其他 {{ plan.recommendations.length - 5 }} 项...
                      </el-tag>
                    </div>
                  </div>
                </div>
                
                <div class="plan-item-actions">
                  <el-button 
                    type="primary" 
                    @click="viewPlanDetail(plan)"
                    :icon="View"
                  >
                    查看详情
                  </el-button>
                </div>
              </div>
            </el-card>
          </el-timeline-item>
        </el-timeline>
      </div>
    </el-card>
    
    <el-dialog
      v-model="generateDialogVisible"
      title="生成新投资计划"
      width="500px"
      center
    >
      <div class="generate-dialog-content">
        <p>生成新的投资计划将基于当前的市场数据和您的投资配置。</p>
        <p>确认要生成新的投资计划吗？</p>
        
        <div class="warning-box" v-if="canGenerateWarning">
          <el-alert
            type="warning"
            :closable="false"
            show-icon
            title="注意"
            description="您今天已经生成过投资计划，一般建议每月生成一次计划，是否仍要继续？"
          />
        </div>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="generateDialogVisible = false">取消</el-button>
          <el-button 
            type="primary" 
            @click="confirmGeneratePlan"
            :loading="plansStore.generating"
          >
            确认生成
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { usePlansStore } from '../store/plans'
import { ElMessage } from 'element-plus'
import { View } from '@element-plus/icons-vue'

const router = useRouter()
const plansStore = usePlansStore()
const generateDialogVisible = ref(false)

// 计算属性
const canGenerateWarning = computed(() => {
  const latestPlan = plansStore.latestPlan
  if (!latestPlan) return false
  
  // 检查最近的计划是否是今天生成的
  const today = new Date()
  const generatedDate = new Date(latestPlan.generated_at)
  
  return (
    today.getDate() === generatedDate.getDate() &&
    today.getMonth() === generatedDate.getMonth() &&
    today.getFullYear() === generatedDate.getFullYear()
  )
})

// 方法
const generatePlan = () => {
  generateDialogVisible.value = true
}

const confirmGeneratePlan = async () => {
  try {
    await plansStore.generatePlan()
    generateDialogVisible.value = false
    
    // 如果生成成功，跳转到详情页
    if (plansStore.currentPlan) {
      ElMessage.success('投资计划生成成功')
      router.push(`/plans/${plansStore.currentPlan.id}`)
    }
  } catch (error) {
    ElMessage.error('生成计划失败，请稍后重试')
  }
}

const viewPlanDetail = (plan) => {
  router.push(`/plans/${plan.id}`)
}

const getTimelineItemType = (plan) => {
  if (plan === plansStore.latestPlan) {
    return 'primary'
  }
  if (plan.circuit_breaker_triggered) {
    return 'danger'
  }
  return ''
}

const formatPercentage = (value) => {
  return `${(value * 100).toFixed(0)}%`
}

const getTopRecommendations = (plan) => {
  // 按月度金额降序排序并返回前5个
  return [...plan.recommendations]
    .sort((a, b) => b.monthly_amount - a.monthly_amount)
    .slice(0, 5)
}

// 生命周期钩子
onMounted(async () => {
  await plansStore.loadPlans()
})
</script>

<style scoped>
.plans-container {
  padding: 20px;
}

.plans-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2 {
  margin: 0;
}

.plan-item-card {
  margin-bottom: 10px;
}

.plan-item-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.plan-item-info {
  flex: 1;
}

.plan-item-info h3 {
  margin-top: 0;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.plan-details {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  margin-bottom: 15px;
}

.detail-item {
  display: flex;
  align-items: center;
}

.label {
  color: #606266;
  margin-right: 5px;
}

.value {
  font-weight: bold;
}

.assets-distribution h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #606266;
}

.asset-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.asset-tag {
  margin-bottom: 5px;
}

.plan-item-actions {
  display: flex;
  flex-direction: column;
  justify-content: center;
  height: 100%;
}

.generate-dialog-content {
  text-align: center;
}

.warning-box {
  margin-top: 20px;
}
</style> 