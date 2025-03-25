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
                    v-if="plan?.circuit_breaker_triggered"
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
                    <span class="value">{{
                      plan ? plansStore.formattedGeneratedAt(plan) : "-"
                    }}</span>
                  </div>
                  <div class="info-item">
                    <span class="label">月度总投资:</span>
                    <span class="value"
                      >¥{{
                        (plan?.total_monthly_amount || 0).toLocaleString()
                      }}</span
                    >
                  </div>
                  <div class="info-item">
                    <span class="label">资金池金额:</span>
                    <span class="value"
                      >¥{{ (plan?.buffer_amount || 0).toLocaleString() }}</span
                    >
                    <el-tooltip
                      content="资金池可用于在极度超跌市场（评分≥80）时额外加仓"
                      placement="top"
                    >
                      <el-icon class="info-icon"
                        ><el-icon-info-filled
                      /></el-icon>
                    </el-tooltip>
                  </div>
                  <div class="info-item">
                    <span class="label">持仓再平衡:</span>
                    <span class="value">
                      <el-tag
                        :type="plan?.rebalance_required ? 'warning' : 'success'"
                        size="small"
                      >
                        {{
                          plan?.rebalance_required ? "建议再平衡" : "无需再平衡"
                        }}
                      </el-tag>
                    </span>
                  </div>
                  <div class="info-item" v-if="hasSpecialMarketCondition">
                    <span class="label">市场评分状态:</span>
                    <span class="value">
                      <el-tag :type="getScoreLevelType()" size="small">
                        {{ getScoreLevel() }}
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
                <el-statistic
                  title="资产数量"
                  :value="plan?.recommendations?.length || 0"
                >
                  <template #suffix>个</template>
                </el-statistic>
                <el-divider />
                <el-statistic
                  title="本月应投资"
                  :value="calculateTotalInvestment()"
                  :precision="0"
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
                      {{ formatDate(date) }}
                    </el-tag>
                    <el-empty
                      v-if="getNextInvestmentDates().length === 0"
                      description="暂无最近投资日期"
                      :image-size="60"
                    />
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

          <div
            v-if="!plan?.recommendations || plan.recommendations.length === 0"
            class="no-data"
          >
            <el-empty description="暂无投资建议数据" :image-size="100" />
          </div>

          <el-table
            v-else
            :data="plan.recommendations"
            style="width: 100%"
            :border="true"
          >
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
                  <el-tooltip
                    content="估值系数(0.00-3.00)基于价格位置和均线偏离度，系数越高表示资产估值越低，越值得买入"
                    placement="top"
                  >
                    <el-tag
                      :type="
                        getCoefficientType(scope.row.valuation_coefficient)
                      "
                      effect="plain"
                    >
                      估值:
                      {{ formatCoefficient(scope.row.valuation_coefficient) }}
                    </el-tag>
                  </el-tooltip>
                  <el-tooltip
                    content="趋势系数(0.00-3.00)基于RSI和均线关系，系数越高表示资产积累的价值越多"
                    placement="top"
                  >
                    <el-tag
                      :type="getCoefficientType(scope.row.trend_coefficient)"
                      effect="plain"
                    >
                      趋势: {{ formatCoefficient(scope.row.trend_coefficient) }}
                    </el-tag>
                  </el-tooltip>
                  <el-tooltip
                    content="波动系数(0.00-2.00)基于ATR百分位和波动率，系数越高表示市场波动越大，创造更好的买入机会"
                    placement="top"
                  >
                    <el-tag
                      :type="
                        getCoefficientType(scope.row.volatility_coefficient)
                      "
                      effect="plain"
                    >
                      波动:
                      {{ formatCoefficient(scope.row.volatility_coefficient) }}
                    </el-tag>
                  </el-tooltip>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="投资频率" width="120">
              <template #default="scope">
                {{ formatFrequency(scope.row.recommended_frequency) }}
              </template>
            </el-table-column>
            <el-table-column label="投资金额" width="180">
              <template #default="scope">
                <div class="amount-cell">
                  <div>
                    月度: ¥{{ formatNumber(scope.row.monthly_amount || 0, 0) }}
                  </div>
                  <div>
                    单次: ¥{{ formatNumber(scope.row.single_amount || 0, 0) }}
                  </div>
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
              v-if="plan?.circuit_breaker_triggered"
              type="error"
              :closable="false"
              show-icon
              title="市场评分警告"
              description="系统检测到当前市场评分较低，可能处于高估状态，建议谨慎投资，按照推荐的频率和金额进行定投。"
              class="tip-alert"
            />

            <el-alert
              v-if="hasExtremeOversoldAsset"
              type="success"
              :closable="false"
              show-icon
              title="极度超跌投资机会"
              description="系统检测到极度超跌资产，已自动调整为每日投资策略，可以更有效地捕捉市场低点，建议按照推荐的日期和金额积极投资。"
              class="tip-alert"
            />

            <el-alert
              v-if="plan?.rebalance_required"
              type="warning"
              :closable="false"
              show-icon
              title="建议再平衡"
              description="当前投资组合与目标权重偏差较大，建议适当调整持仓结构。"
              class="tip-alert"
            />

            <el-alert
              v-if="hasSpecialMarketCondition"
              type="warning"
              :closable="false"
              show-icon
              :title="'特殊市场条件: ' + getScoreLevel()"
              description="系统检测到特殊市场条件，已自动调整投资策略，请按照推荐的频率和金额进行操作。"
              class="tip-alert"
            />

            <el-alert
              type="info"
              :closable="false"
              show-icon
              title="投资建议"
              description="系统根据市场评分动态调整投资频率和金额，评分较高时增加投资力度，评分较低时减少投资力度，请按照上述推荐的日期和金额进行定投。"
              class="tip-alert"
            />

            <el-alert
              type="success"
              :closable="false"
              show-icon
              title="策略说明"
              description="本系统采用市场波动捕捉法策略，基于价格位置、趋势、波动性和特殊事件进行评分(0-100分)，根据评分调整投资策略，帮助您在市场超跌时增加投入，在市场高估时减少投入。"
              class="tip-alert"
            />
          </div>
        </el-card>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, onUnmounted, nextTick } from "vue";
import { useRoute, useRouter } from "vue-router";
import { usePlansStore } from "../store/plans";
import { InfoFilled as ElIconInfoFilled } from "@element-plus/icons-vue";
import * as echarts from "echarts/core";
import { PieChart } from "echarts/charts";
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
} from "echarts/components";
import { LabelLayout } from "echarts/features";
import { CanvasRenderer } from "echarts/renderers";

// 注册必需的组件
echarts.use([
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  PieChart,
  CanvasRenderer,
  LabelLayout,
]);

const route = useRoute();
const router = useRouter();
const plansStore = usePlansStore();
const pieChartRef = ref(null);
let pieChart = null;
let resizeHandler = null; // 添加一个变量来存储resize事件处理函数

// 计算属性
const plan = computed(() => plansStore.currentPlan);

// 计算属性 - 检查是否有特殊市场条件
const hasSpecialMarketCondition = computed(() => {
  if (!plan.value || !plan.value.recommendations) return false;
  return plan.value.recommendations.some((rec) => rec.special_condition);
});

// 计算是否有极度超跌的资产
const hasExtremeOversoldAsset = computed(() => {
  if (!plan.value || !plan.value.recommendations) return false;
  return plan.value.recommendations.some(
    (rec) =>
      rec.recommended_frequency === "daily" ||
      (rec.special_condition && rec.special_condition.includes("极度超跌"))
  );
});

// 获取市场评分等级
const getScoreLevel = () => {
  if (!plan.value || !plan.value.recommendations) return "中性区间";

  // 寻找第一个有特殊条件的推荐
  const recWithCondition = plan.value.recommendations.find(
    (rec) => rec.special_condition
  );

  if (!recWithCondition) return "中性区间";

  // 根据特殊条件返回适当的描述
  const condition = recWithCondition.special_condition;

  switch (condition) {
    case "极度超跌":
      return "极度超跌区间 - 每日积极投资";
    case "价值区间":
      return "价值区间 - 每周适度投资";
    case "中性区间":
      return "中性区间 - 每两周常规投资";
    case "高估区间":
      return "高估区间 - 每月减少投资";
    case "极度泡沫":
      return "极度泡沫区间 - 谨慎最小投资";
    default:
      return condition || "中性区间";
  }
};

// 根据评分等级返回标签类型
const getScoreLevelType = () => {
  const level = getScoreLevel();
  if (level.includes("极度超跌")) return "success";
  if (level.includes("价值区间")) return "success";
  if (level.includes("中性区间")) return "info";
  if (level.includes("高估区间")) return "warning";
  if (level.includes("极度泡沫")) return "danger";
  return "info";
};

// 方法
const goBack = () => {
  router.push("/plans");
};

const formatPercentage = (value) => {
  if (value === undefined || value === null) return "0.00%";
  return `${(Number(value) * 100 || 0).toFixed(2)}%`;
};

const formatCoefficient = (value) => {
  if (value === undefined || value === null) return "0.00";
  return (Number(value) || 0).toFixed(2);
};

const getCoefficientType = (value) => {
  if (value === undefined || value === null) return "info";
  value = Number(value) || 0;

  // 不同类型的系数有不同的上限和评估标准
  // 估值和趋势系数是0-3范围，波动系数是0-2范围
  if (value >= 2.5) return "success";
  if (value >= 1.5) return "success";
  if (value <= 0.5) return "danger";
  if (value < 1.0) return "warning";
  return "info";
};

// 格式化投资频率为中文
const formatFrequency = (frequency) => {
  if (!frequency) return "每两周一次";

  const frequencyMap = {
    daily: "每日一次（极度超跌状态）",
    weekly: "每周一次",
    biweekly: "每两周一次",
    monthly: "每月一次",
  };

  return frequencyMap[frequency] || frequency;
};

const calculateTotalInvestment = () => {
  if (!plan.value || !plan.value.recommendations) return 0;
  return plan.value.recommendations.reduce(
    (sum, rec) => sum + (rec.single_amount || 0),
    0
  );
};

const getNextInvestmentDates = () => {
  if (!plan.value || !plan.value.recommendations) return [];

  // 收集所有日期并去重
  const allDates = [];
  plan.value.recommendations.forEach((rec) => {
    if (rec.investment_dates && rec.investment_dates.length > 0) {
      rec.investment_dates.forEach((date) => {
        if (!allDates.includes(date)) {
          allDates.push(date);
        }
      });
    }
  });

  // 排序日期
  allDates.sort();

  // 只返回未来30天内的日期
  const now = new Date();
  const thirtyDaysLater = new Date();
  thirtyDaysLater.setDate(now.getDate() + 30);

  return allDates.filter((dateStr) => {
    const date = new Date(dateStr);
    return date >= now && date <= thirtyDaysLater;
  });
};

const initPieChart = () => {
  // 取消之前的resize监听器
  if (resizeHandler) {
    window.removeEventListener("resize", resizeHandler);
    resizeHandler = null;
  }

  // 提前返回如果组件已经被卸载
  if (!pieChartRef.value) return;

  try {
    // 销毁之前的图表实例
    if (pieChart) {
      pieChart.dispose();
      pieChart = null;
    }

    // 确认DOM元素仍然存在
    if (!pieChartRef.value) return;

    // 初始化图表
    pieChart = echarts.init(pieChartRef.value);

    // 检查plan是否存在
    if (
      !plan.value ||
      !plan.value.recommendations ||
      plan.value.recommendations.length === 0
    ) {
      // 显示无数据提示
      pieChart.setOption({
        title: {
          text: "暂无资产分配数据",
          left: "center",
          top: "center",
          textStyle: {
            color: "#909399",
            fontSize: 16,
          },
        },
      });
      return;
    }

    // 准备数据
    const data = plan.value.recommendations.map((rec) => ({
      name: rec.asset?.name || "未命名资产",
      value: rec.monthly_amount || 0, // 确保值不是undefined
    }));

    // 设置图表选项
    const option = {
      title: {
        text: "资产分配",
        left: "center",
      },
      tooltip: {
        trigger: "item",
        formatter: "{a} <br/>{b}: {c} ({d}%)",
      },
      legend: {
        orient: "vertical",
        left: "left",
        data: data.map((item) => item.name),
      },
      series: [
        {
          name: "月度投资额",
          type: "pie",
          radius: ["40%", "70%"],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 10,
            borderColor: "#fff",
            borderWidth: 2,
          },
          label: {
            show: false,
            position: "center",
          },
          emphasis: {
            label: {
              show: true,
              fontSize: "18",
              fontWeight: "bold",
            },
          },
          labelLine: {
            show: false,
          },
          data: data,
        },
      ],
    };

    // 确保图表实例仍然存在
    if (pieChart) {
      // 设置图表
      pieChart.setOption(option);

      // 添加窗口大小变化时的自适应
      resizeHandler = () => {
        if (pieChart && pieChartRef.value) {
          pieChart.resize();
        }
      };
      window.addEventListener("resize", resizeHandler);
    }
  } catch (error) {
    console.error("初始化饼图时出错:", error);
    // 显示错误信息
    if (pieChartRef.value) {
      try {
        const errorDiv = document.createElement("div");
        errorDiv.style.textAlign = "center";
        errorDiv.style.padding = "20px";
        errorDiv.style.color = "#F56C6C";
        errorDiv.innerText = "图表加载失败";
        pieChartRef.value.innerHTML = "";
        pieChartRef.value.appendChild(errorDiv);
      } catch (e) {
        console.error("无法添加错误信息:", e);
      }
    }
  }
};

// 新增格式化数字的方法，支持指定小数位
const formatNumber = (value, decimal = 2) => {
  if (value === undefined || value === null) return "0";
  if (decimal === 0) {
    return Math.round(Number(value) || 0).toLocaleString();
  }
  return (Number(value) || 0).toFixed(decimal);
};

// 添加格式化日期的方法
const formatDate = (dateString) => {
  if (!dateString) return "";
  const date = new Date(dateString);
  if (isNaN(date)) return dateString;
  return date.toLocaleDateString("zh-CN");
};

// 生命周期钩子
onMounted(async () => {
  const planId = route.params.id;
  if (planId) {
    try {
      await plansStore.loadPlanById(planId);
    } catch (error) {
      console.error("加载计划失败:", error);
    }
  }
});

// 监视plan变化，初始化图表
watch(
  plan,
  () => {
    // 使用nextTick确保DOM已更新
    nextTick(() => {
      // 检查组件是否已卸载
      if (pieChartRef.value) {
        initPieChart();
      }
    });
  },
  { immediate: true }
);

// 清理函数，确保组件卸载时清理所有资源
onUnmounted(() => {
  // 移除resize事件监听
  if (resizeHandler) {
    window.removeEventListener("resize", resizeHandler);
    resizeHandler = null;
  }

  // 销毁图表实例
  if (pieChart) {
    try {
      pieChart.dispose();
    } catch (e) {
      console.error("销毁图表实例失败:", e);
    }
    pieChart = null;
  }
});
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

.plan-card,
.recommendations-card,
.tips-card,
.summary-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2,
.card-header h3 {
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

.no-data {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 300px;
}
</style>
