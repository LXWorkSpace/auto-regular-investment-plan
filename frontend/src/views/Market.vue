<template>
  <div class="market-container">
    <el-card shadow="hover" class="market-card">
      <template #header>
        <div class="card-header">
          <h2>市场数据</h2>
          <div>
            <span class="last-updated">
              最后更新时间: {{ marketStore.formattedLastUpdated }}
            </span>
            <el-button 
              type="primary" 
              @click="refreshMarketData" 
              :loading="marketStore.refreshing"
              :disabled="marketStore.refreshing"
            >
              刷新数据
            </el-button>
          </div>
        </div>
      </template>
      
      <div v-loading="marketStore.loading">
        <el-alert
          v-if="Object.keys(marketStore.marketData).length === 0"
          type="info"
          :closable="false"
          show-icon
          title="暂无市场数据"
          description="请先在投资配置中添加资产，然后点击刷新数据按钮获取最新市场数据。"
        />
        
        <el-table
          v-else
          :data="marketStore.marketDataList"
          style="width: 100%"
          border
          stripe
        >
          <el-table-column label="资产代码" prop="code" width="100" />
          <el-table-column label="当前价格" width="120">
            <template #default="scope">
              {{ formatNumber(scope.row.price) }}
            </template>
          </el-table-column>
          <el-table-column label="PE" width="100">
            <template #default="scope">
              {{ scope.row.pe_ratio ? formatNumber(scope.row.pe_ratio) : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="PE分位数" width="120">
            <template #default="scope">
              <div v-if="scope.row.pe_percentile !== null && scope.row.pe_percentile !== undefined">
                <el-progress
                  :percentage="scope.row.pe_percentile * 100"
                  :color="getPercentileColor(scope.row.pe_percentile)"
                />
              </div>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column label="PB" width="100">
            <template #default="scope">
              {{ scope.row.pb_ratio ? formatNumber(scope.row.pb_ratio) : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="偏离200日均线" width="150">
            <template #default="scope">
              <div v-if="scope.row.deviation_percentage !== null && scope.row.deviation_percentage !== undefined">
                {{ formatPercentage(scope.row.deviation_percentage) }}
                <el-tag 
                  :type="getDeviationTagType(scope.row.deviation_percentage)"
                  size="small"
                >
                  {{ getDeviationStatus(scope.row.deviation_percentage) }}
                </el-tag>
              </div>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column label="波动系数" width="120">
            <template #default="scope">
              <div v-if="scope.row.atr_20 && scope.row.atr_baseline">
                {{ formatNumber(scope.row.atr_baseline / scope.row.atr_20) }}
                <el-tag 
                  :type="getVolatilityTagType(scope.row.atr_baseline / scope.row.atr_20)"
                  size="small"
                >
                  {{ getVolatilityStatus(scope.row.atr_baseline / scope.row.atr_20) }}
                </el-tag>
              </div>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column label="建议系数" min-width="250">
            <template #default="scope">
              <div v-if="canCalculateCoefficients(scope.row)" class="coefficients">
                <div class="coefficient">
                  <span class="coefficient-label">估值系数:</span>
                  <span class="coefficient-value">{{ calculateValuationCoefficient(scope.row) }}</span>
                </div>
                <div class="coefficient">
                  <span class="coefficient-label">趋势系数:</span>
                  <span class="coefficient-value">{{ calculateTrendCoefficient(scope.row) }}</span>
                </div>
                <div class="coefficient">
                  <span class="coefficient-label">波动系数:</span>
                  <span class="coefficient-value">{{ calculateVolatilityCoefficient(scope.row) }}</span>
                </div>
              </div>
              <span v-else>数据不足，无法计算</span>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>
    
    <el-card shadow="hover" class="market-card" v-if="Object.keys(marketStore.marketData).length > 0">
      <template #header>
        <div class="card-header">
          <h2>市场状态分析</h2>
        </div>
      </template>
      
      <div v-loading="marketStore.loading">
        <el-row :gutter="20">
          <el-col :span="8" v-for="(asset, index) in marketStore.marketDataList" :key="index">
            <el-card shadow="hover" class="asset-analysis-card">
              <template #header>
                <div class="asset-header">
                  <h3>{{ asset.code }}</h3>
                </div>
              </template>
              
              <div class="asset-analysis">
                <div class="analysis-item">
                  <h4>估值分析</h4>
                  <p>
                    {{ getValuationAnalysis(asset) }}
                  </p>
                </div>
                
                <div class="analysis-item">
                  <h4>趋势分析</h4>
                  <p>
                    {{ getTrendAnalysis(asset) }}
                  </p>
                </div>
                
                <div class="analysis-item">
                  <h4>波动率分析</h4>
                  <p>
                    {{ getVolatilityAnalysis(asset) }}
                  </p>
                </div>
                
                <div class="analysis-item analysis-summary">
                  <h4>投资建议</h4>
                  <p>
                    {{ getInvestmentSuggestion(asset) }}
                  </p>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useMarketStore } from '../store/market'
import { ElMessage } from 'element-plus'

const marketStore = useMarketStore()

// 刷新市场数据
const refreshMarketData = async () => {
  try {
    await marketStore.refreshMarketData()
    ElMessage.success('市场数据已更新')
  } catch (error) {
    ElMessage.error('刷新市场数据失败')
  }
}

// 数字格式化
const formatNumber = (value) => {
  if (value === null || value === undefined) return '-'
  return Number(value).toFixed(2)
}

// 百分比格式化
const formatPercentage = (value) => {
  if (value === null || value === undefined) return '-'
  return `${(value * 100).toFixed(2)}%`
}

// 根据PE/PB分位数获取颜色
const getPercentileColor = (percentile) => {
  if (percentile < 0.3) return '#67C23A' // 低估 - 绿色
  if (percentile > 0.7) return '#F56C6C' // 高估 - 红色
  return '#E6A23C' // 中性 - 黄色
}

// 根据均线偏离度获取状态标签类型
const getDeviationTagType = (deviation) => {
  if (deviation < -0.15) return 'success' // 严重超跌
  if (deviation < -0.05) return 'warning' // 弱势
  if (deviation > 0.05) return 'danger' // 超涨
  return 'info' // 平衡
}

// 根据均线偏离度获取状态文字
const getDeviationStatus = (deviation) => {
  if (deviation < -0.15) return '严重超跌'
  if (deviation < -0.05) return '弱势'
  if (deviation > 0.05) return '超涨'
  return '平衡'
}

// 根据波动系数获取状态标签类型
const getVolatilityTagType = (volatility) => {
  if (volatility > 1.3) return 'success' // 极度平静
  if (volatility >= 0.9 && volatility <= 1.3) return 'info' // 正常波动
  if (volatility >= 0.6 && volatility < 0.9) return 'warning' // 波动加剧
  return 'danger' // 极端动荡
}

// 根据波动系数获取状态文字
const getVolatilityStatus = (volatility) => {
  if (volatility > 1.3) return '极度平静'
  if (volatility >= 0.9 && volatility <= 1.3) return '正常波动'
  if (volatility >= 0.6 && volatility < 0.9) return '波动加剧'
  return '极端动荡'
}

// 检查是否可以计算系数
const canCalculateCoefficients = (asset) => {
  return (
    (asset.pe_percentile !== null && asset.pe_percentile !== undefined) ||
    (asset.pb_percentile !== null && asset.pb_percentile !== undefined) ||
    (asset.deviation_percentage !== null && asset.deviation_percentage !== undefined) ||
    (asset.atr_20 && asset.atr_baseline)
  )
}

// 计算估值系数
const calculateValuationCoefficient = (asset) => {
  // 优先使用PE分位数
  const percentile = asset.pe_percentile !== null && asset.pe_percentile !== undefined 
    ? asset.pe_percentile 
    : asset.pb_percentile

  if (percentile === null || percentile === undefined) {
    return 1.0
  }

  if (percentile < 0.3) {
    // 越低估加成越大
    return (1 + (0.3 - percentile) / 0.3).toFixed(2)
  } else if (percentile > 0.7) {
    // 越高估减仓越多
    return (1 - (percentile - 0.7) / 0.3).toFixed(2)
  } else {
    // 中性区域
    return '1.00'
  }
}

// 计算趋势系数
const calculateTrendCoefficient = (asset) => {
  const deviation = asset.deviation_percentage

  if (deviation === null || deviation === undefined) {
    return '1.00'
  }

  if (deviation < -0.15) {
    // 严重超跌区域
    return '1.50'
  } else if (deviation >= -0.15 && deviation < -0.05) {
    // 弱势区域
    return '1.20'
  } else if (deviation >= -0.05 && deviation <= 0.05) {
    // 平衡区域
    return '1.00'
  } else {
    // 超涨区域
    return '0.80'
  }
}

// 计算波动系数
const calculateVolatilityCoefficient = (asset) => {
  if (!asset.atr_20 || !asset.atr_baseline || asset.atr_20 === 0) {
    return '1.00'
  }

  // 波动系数 = 基准波动率 / 当前ATR
  const volatilityCoefficient = asset.atr_baseline / asset.atr_20

  // 限制系数范围，避免极端值
  const limitedCoefficient = Math.max(0.5, Math.min(volatilityCoefficient, 1.5))
  
  return limitedCoefficient.toFixed(2)
}

// 获取估值分析
const getValuationAnalysis = (asset) => {
  // 优先使用PE分位数
  const percentile = asset.pe_percentile !== null && asset.pe_percentile !== undefined 
    ? asset.pe_percentile 
    : asset.pb_percentile

  if (percentile === null || percentile === undefined) {
    return '无估值数据'
  }

  if (percentile < 0.3) {
    return `当前估值处于低位(${formatPercentage(percentile)})，建议加仓`
  } else if (percentile > 0.7) {
    return `当前估值处于高位(${formatPercentage(percentile)})，建议减仓`
  } else {
    return `当前估值适中(${formatPercentage(percentile)})，建议正常投资`
  }
}

// 获取趋势分析
const getTrendAnalysis = (asset) => {
  const deviation = asset.deviation_percentage

  if (deviation === null || deviation === undefined) {
    return '无趋势数据'
  }

  if (deviation < -0.15) {
    return `当前严重超跌(${formatPercentage(deviation)})，建议加仓`
  } else if (deviation >= -0.15 && deviation < -0.05) {
    return `当前处于弱势(${formatPercentage(deviation)})，建议适度加仓`
  } else if (deviation >= -0.05 && deviation <= 0.05) {
    return `当前处于均线附近(${formatPercentage(deviation)})，建议正常投资`
  } else {
    return `当前处于超涨状态(${formatPercentage(deviation)})，建议减仓`
  }
}

// 获取波动率分析
const getVolatilityAnalysis = (asset) => {
  if (!asset.atr_20 || !asset.atr_baseline) {
    return '无波动率数据'
  }

  const volatilityCoefficient = asset.atr_baseline / asset.atr_20

  if (volatilityCoefficient > 1.3) {
    return '当前波动率极度平静，建议高频小额投入'
  } else if (volatilityCoefficient >= 0.9 && volatilityCoefficient <= 1.3) {
    return '当前波动率正常，建议周投资'
  } else if (volatilityCoefficient >= 0.6 && volatilityCoefficient < 0.9) {
    return '当前波动率加剧，建议双周投资'
  } else {
    return '当前波动率极端，建议月投资并寻找合适时机'
  }
}

// 获取投资建议
const getInvestmentSuggestion = (asset) => {
  if (!canCalculateCoefficients(asset)) {
    return '数据不足，无法给出建议'
  }
  
  const valuationCoef = parseFloat(calculateValuationCoefficient(asset))
  const trendCoef = parseFloat(calculateTrendCoefficient(asset))
  const volatilityCoef = parseFloat(calculateVolatilityCoefficient(asset))
  
  // 综合系数
  const totalCoef = valuationCoef * trendCoef * volatilityCoef
  
  if (totalCoef > 1.5) {
    return `综合评分 ${totalCoef.toFixed(2)}，建议明显加仓`
  } else if (totalCoef > 1.2) {
    return `综合评分 ${totalCoef.toFixed(2)}，建议适度加仓`
  } else if (totalCoef > 0.9) {
    return `综合评分 ${totalCoef.toFixed(2)}，建议正常投资`
  } else if (totalCoef > 0.6) {
    return `综合评分 ${totalCoef.toFixed(2)}，建议减少投入`
  } else {
    return `综合评分 ${totalCoef.toFixed(2)}，建议谨慎投资或观望`
  }
}

// 生命周期钩子
onMounted(async () => {
  await marketStore.loadMarketData()
})
</script>

<style scoped>
.market-container {
  padding: 20px;
}

.market-card {
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

.last-updated {
  margin-right: 15px;
  color: #909399;
}

.coefficients {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.coefficient {
  display: flex;
  align-items: center;
}

.coefficient-label {
  width: 70px;
  color: #606266;
}

.coefficient-value {
  font-weight: bold;
}

.asset-analysis-card {
  margin-bottom: 20px;
  height: 100%;
}

.asset-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.asset-header h3 {
  margin: 0;
}

.asset-analysis {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.analysis-item h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #606266;
}

.analysis-item p {
  margin: 0;
  line-height: 1.5;
}

.analysis-summary {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px dashed #EBEEF5;
}

.analysis-summary h4 {
  color: #409EFF;
}
</style> 