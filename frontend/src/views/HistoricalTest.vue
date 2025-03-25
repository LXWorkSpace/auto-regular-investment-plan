<template>
  <div class="historical-test-container">
    <el-card shadow="hover" class="test-card">
      <template #header>
        <div class="card-header">
          <h2>历史数据测试</h2>
        </div>
      </template>

      <div class="historical-form">
        <el-form :model="formData" label-position="top">
          <el-form-item label="选择历史日期">
            <el-date-picker
              v-model="formData.date"
              type="date"
              placeholder="选择测试日期"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              :disabled-date="disableFutureDates"
              style="width: 100%"
            />
          </el-form-item>

          <el-form-item>
            <el-button
              type="primary"
              @click="generateHistoricalPlan"
              :loading="loading"
              :disabled="!formData.date"
            >
              生成历史投资计划
            </el-button>
          </el-form-item>
        </el-form>
      </div>

      <div v-if="errorMessage" class="error-message">
        <el-alert :title="errorMessage" type="error" show-icon />
      </div>

      <div v-if="historicalPlan" class="historical-plan">
        <el-divider content-position="left">
          {{ historicalPlan.historical_date }} 的投资计划
        </el-divider>

        <!-- 投资计划概览 -->
        <div class="plan-overview">
          <el-descriptions title="计划概览" :column="2" border>
            <el-descriptions-item label="月度投资总额">
              {{ formatCurrency(historicalPlan.total_monthly_amount) }}
            </el-descriptions-item>
            <el-descriptions-item label="实际投资总额">
              {{ formatCurrency(historicalPlan.actual_investment_amount) }}
            </el-descriptions-item>
            <el-descriptions-item label="资金池使用">
              {{ formatCurrency(historicalPlan.buffer_pool_usage) }}
            </el-descriptions-item>
            <el-descriptions-item label="市场情况">
              <el-tag
                :type="getMarketTagType(historicalPlan.warning_messages)"
                effect="dark"
              >
                {{ getMarketStatusText(historicalPlan.warning_messages) }}
              </el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- 投资建议列表 -->
        <div class="recommendation-list">
          <h3>投资建议明细</h3>
          <el-table :data="historicalPlan.recommendations" style="width: 100%">
            <el-table-column label="资产" min-width="200">
              <template #default="scope">
                <div class="asset-info">
                  <div class="asset-name">{{ scope.row.asset.name }}</div>
                  <div class="asset-code">{{ scope.row.asset.code }}</div>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="估值系数" width="100">
              <template #default="scope">
                <el-tag
                  :type="getValuationTagType(scope.row.valuation_coefficient)"
                >
                  {{ scope.row.valuation_coefficient.toFixed(1) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="趋势系数" width="100">
              <template #default="scope">
                <el-tag :type="getTrendTagType(scope.row.trend_coefficient)">
                  {{ scope.row.trend_coefficient.toFixed(1) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="波动系数" width="100">
              <template #default="scope">
                <el-tag
                  :type="getVolatilityTagType(scope.row.volatility_coefficient)"
                >
                  {{ scope.row.volatility_coefficient.toFixed(1) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="建议频率" width="100">
              <template #default="scope">
                {{ scope.row.recommended_frequency }}次/月
              </template>
            </el-table-column>
            <el-table-column label="单次金额" width="120">
              <template #default="scope">
                {{ formatCurrency(scope.row.single_amount) }}
              </template>
            </el-table-column>
            <el-table-column label="月度总额" width="120">
              <template #default="scope">
                {{ formatCurrency(scope.row.monthly_amount) }}
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- 警告消息 -->
        <div
          v-if="
            historicalPlan.warning_messages &&
            historicalPlan.warning_messages.length > 0
          "
          class="warning-messages"
        >
          <h3>注意事项</h3>
          <el-alert
            v-for="(message, index) in historicalPlan.warning_messages"
            :key="index"
            :title="message"
            type="warning"
            show-icon
            :closable="false"
            style="margin-bottom: 10px"
          />
        </div>
      </div>

      <div
        v-if="!historicalPlan && !errorMessage && !loading"
        class="tip-message"
      >
        <el-empty description="选择历史日期并生成投资计划" />
      </div>
    </el-card>
  </div>
</template>

<script>
import api from "../api";
import { ref, reactive } from "vue";

export default {
  name: "HistoricalTest",
  setup() {
    const formData = reactive({
      date: "",
    });

    const loading = ref(false);
    const historicalPlan = ref(null);
    const errorMessage = ref("");

    // 禁用未来日期
    const disableFutureDates = (time) => {
      return time.getTime() > Date.now();
    };

    // 生成历史投资计划
    const generateHistoricalPlan = async () => {
      if (!formData.date) {
        errorMessage.value = "请选择历史日期";
        return;
      }

      loading.value = true;
      errorMessage.value = "";

      try {
        const result = await api.plans.generateHistorical(formData.date);
        if (result.error) {
          errorMessage.value = result.error;
        } else {
          historicalPlan.value = result;
        }
      } catch (error) {
        console.error("生成历史投资计划出错", error);
        errorMessage.value =
          "生成历史投资计划失败: " + (error.message || "未知错误");
      } finally {
        loading.value = false;
      }
    };

    // 格式化货币
    const formatCurrency = (value) => {
      return "¥" + (value || 0).toFixed(2);
    };

    // 获取估值标签类型
    const getValuationTagType = (value) => {
      if (value >= 1.2) return "success";
      if (value >= 0.8) return "warning";
      return "danger";
    };

    // 获取趋势标签类型
    const getTrendTagType = (value) => {
      if (value >= 1.2) return "success";
      if (value >= 0.8) return "warning";
      return "danger";
    };

    // 获取波动标签类型
    const getVolatilityTagType = (value) => {
      if (value >= 1.2) return "success";
      if (value >= 0.8) return "warning";
      return "danger";
    };

    // 获取市场状态标签类型
    const getMarketTagType = (warnings) => {
      if (!warnings || warnings.length === 0) return "info";

      // 检查是否有极度超跌警告
      const hasExtremeWarning = warnings.some((w) => w.includes("极度超跌"));
      if (hasExtremeWarning) return "danger";

      // 检查是否有价值区间警告
      const hasValueWarning = warnings.some((w) => w.includes("价值区间"));
      if (hasValueWarning) return "warning";

      // 检查是否有高估警告
      const hasOvervaluedWarning = warnings.some((w) => w.includes("高估"));
      if (hasOvervaluedWarning) return "info";

      return "success";
    };

    // 获取市场状态文本
    const getMarketStatusText = (warnings) => {
      if (!warnings || warnings.length === 0) return "正常";

      // 检查是否有极度超跌警告
      const hasExtremeWarning = warnings.some((w) => w.includes("极度超跌"));
      if (hasExtremeWarning) return "极度超跌";

      // 检查是否有价值区间警告
      const hasValueWarning = warnings.some((w) => w.includes("价值区间"));
      if (hasValueWarning) return "价值区间";

      // 检查是否有高估警告
      const hasOvervaluedWarning = warnings.some((w) => w.includes("高估"));
      if (hasOvervaluedWarning) return "高估";

      return "正常";
    };

    return {
      formData,
      loading,
      historicalPlan,
      errorMessage,
      disableFutureDates,
      generateHistoricalPlan,
      formatCurrency,
      getValuationTagType,
      getTrendTagType,
      getVolatilityTagType,
      getMarketTagType,
      getMarketStatusText,
    };
  },
};
</script>

<style scoped>
.historical-test-container {
  padding: 20px;
}

.test-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.historical-form {
  max-width: 600px;
  margin-bottom: 20px;
}

.error-message {
  margin: 20px 0;
}

.historical-plan {
  margin-top: 20px;
}

.plan-overview {
  margin-bottom: 20px;
}

.recommendation-list {
  margin-top: 20px;
}

.asset-info {
  display: flex;
  flex-direction: column;
}

.asset-name {
  font-weight: bold;
}

.asset-code {
  color: #666;
  font-size: 12px;
}

.warning-messages {
  margin-top: 20px;
}

.tip-message {
  display: flex;
  justify-content: center;
  margin: 40px 0;
}
</style>
