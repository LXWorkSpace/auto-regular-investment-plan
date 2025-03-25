<template>
  <div class="market-container">
    <el-card shadow="hover" class="market-card">
      <template #header>
        <div class="card-header">
          <h2>市场分析摘要</h2>
          <div class="actions">
            <span class="last-updated">
              最后更新: {{ marketStore.formattedLastUpdated }}
            </span>
            <el-button
              type="primary"
              @click="marketStore.refreshMarketData"
              :loading="marketStore.refreshing"
              size="small"
            >
              刷新数据
            </el-button>
          </div>
        </div>
      </template>

      <div v-loading="marketStore.loading || marketStore.loadingDetails">
        <!-- 投资策略说明 -->
        <el-alert
          type="info"
          show-icon
          :closable="false"
          title="投资策略更新"
          description="系统已更新投资策略，在极度超跌区间（评分80-100）采用每日投资策略，更积极地捕捉市场低点。价值区间（评分65-79）维持每周投资，中性区间（评分40-64）每两周投资，高估区间（评分20-39）和极度泡沫区间（评分0-19）分别采用每月和谨慎投资策略。"
          style="margin-bottom: 15px"
        />

        <!-- 评分区间说明 -->
        <div class="score-range-guide">
          <h3>评分区间与投资策略对照表</h3>
          <el-table
            :data="scoreRanges"
            border
            size="small"
            style="margin-bottom: 20px"
          >
            <el-table-column prop="range" label="评分区间" width="120" />
            <el-table-column prop="level" label="市场状态" width="150" />
            <el-table-column prop="frequency" label="投资频率" width="180" />
            <el-table-column prop="strategy" label="投资策略" />
          </el-table>
        </div>

        <!-- 资产卡片概览 -->
        <el-row :gutter="20">
          <el-col :span="8" v-for="asset in assetsWithScores" :key="asset.code">
            <el-card shadow="hover" class="asset-card">
              <template #header>
                <div class="asset-header">
                  <h3>{{ asset.code }}</h3>
                  <el-tag
                    :type="getScoreTagType(asset.totalScore)"
                    effect="dark"
                    size="small"
                  >
                    {{ asset.totalScore }}分 -
                    {{ getScoreLevelText(asset.totalScore) }}
                  </el-tag>
                </div>
              </template>

              <div class="asset-summary">
                <div class="summary-row">
                  <span class="summary-label">投资频率:</span>
                  <span class="summary-value">{{
                    getFrequencyText(asset.strategy.frequency)
                  }}</span>
                </div>
                <div class="summary-row">
                  <span class="summary-label">金额系数:</span>
                  <span class="summary-value">{{
                    asset.strategy.amount_factor.toFixed(2)
                  }}</span>
                </div>
                <div class="summary-description">
                  {{ asset.strategy.description }}
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>
    </el-card>

    <!-- 评分详情分析 -->
    <el-card
      shadow="hover"
      class="market-card"
      v-if="
        investmentDetails &&
        Object.keys(investmentDetails.market_scores || {}).length > 0
      "
    >
      <template #header>
        <div class="card-header">
          <h2>评分详情分析</h2>
          <div class="description">资产得分细分与投资建议详情展示</div>
        </div>
      </template>

      <div v-loading="marketStore.loadingDetails">
        <el-row :gutter="20">
          <el-col
            :span="8"
            v-for="(asset, index) in assetsWithScores"
            :key="index"
          >
            <el-card shadow="hover" class="asset-score-card">
              <template #header>
                <div class="asset-header">
                  <h3>{{ asset.code }}</h3>
                  <el-tag :type="getScoreTagType(asset.totalScore)">
                    {{ asset.totalScore }}分
                  </el-tag>
                </div>
              </template>

              <div class="score-details">
                <div class="score-components">
                  <div class="score-component">
                    <span class="component-label">估值评分:</span>
                    <span class="component-value"
                      >{{ Math.round(asset.valuationScore) }}分</span
                    >
                    <el-tooltip
                      content="估值评分(0-30分)，基于价格位置和均线偏离度，评分越高表示估值越低"
                    >
                      <el-progress
                        :percentage="(asset.valuationScore / 30) * 100"
                        :color="
                          getScoreComponentColor(asset.valuationScore, 30)
                        "
                        :show-text="false"
                      />
                    </el-tooltip>
                  </div>
                  <div class="score-component">
                    <span class="component-label">趋势评分:</span>
                    <span class="component-value"
                      >{{ Math.round(asset.trendScore) }}分</span
                    >
                    <el-tooltip
                      content="趋势评分(0-30分)，基于RSI和均线关系，评分越高表示积累的价值越多"
                    >
                      <el-progress
                        :percentage="(Math.round(asset.trendScore) / 30) * 100"
                        :color="getScoreComponentColor(asset.trendScore, 30)"
                        :show-text="false"
                      />
                    </el-tooltip>
                  </div>
                  <div class="score-component">
                    <span class="component-label">波动评分:</span>
                    <span class="component-value"
                      >{{ Math.round(asset.volatilityScore) }}分</span
                    >
                    <el-tooltip
                      content="波动评分(0-20分)，基于ATR百分位和波动率，高波动时得分高"
                    >
                      <el-progress
                        :percentage="(asset.volatilityScore / 20) * 100"
                        :color="
                          getScoreComponentColor(asset.volatilityScore, 20)
                        "
                        :show-text="false"
                      />
                    </el-tooltip>
                  </div>
                  <div class="score-component">
                    <span class="component-label">特殊事件:</span>
                    <span class="component-value"
                      >{{ Math.round(asset.specialEventScore) }}分</span
                    >
                    <el-tooltip
                      content="特殊事件评分(0-20分)，基于近期回撤和成交量，大幅下跌时得分高"
                    >
                      <el-progress
                        :percentage="(asset.specialEventScore / 20) * 100"
                        :color="
                          getScoreComponentColor(asset.specialEventScore, 20)
                        "
                        :show-text="false"
                      />
                    </el-tooltip>
                  </div>
                  <div class="score-component score-component-total">
                    <span class="component-label">总评分:</span>
                    <span class="component-value-total"
                      >{{ asset.totalScore }}分</span
                    >
                    <el-tooltip
                      content="总分(0-100分)，包含估值(30分)、趋势(30分)、波动(20分)、特殊事件(20分)。所有评分均显示为整数，前端进行四舍五入，各组件评分之和可能会与总评分有1-2分的误差。"
                    >
                      <el-progress
                        :percentage="asset.totalScore"
                        :color="getScoreTagColor(asset.totalScore)"
                        :show-text="false"
                      />
                    </el-tooltip>
                  </div>
                </div>

                <div class="investment-strategy" v-if="asset.strategy">
                  <h4>投资策略</h4>
                  <div class="strategy-details">
                    <p>
                      <strong>区间类型:</strong>
                      {{ asset.strategy.score_level }}
                    </p>
                    <p>
                      <strong>投资频率:</strong>
                      {{ getFrequencyText(asset.strategy.frequency) }}
                    </p>
                    <p>
                      <strong>金额系数:</strong>
                      {{ asset.strategy.amount_factor.toFixed(2) }}
                    </p>
                    <p class="strategy-description">
                      {{ asset.strategy.description }}
                    </p>
                  </div>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>
    </el-card>

    <!-- 投资系数详情卡片 -->
    <el-card shadow="hover" class="market-card" v-if="investmentDetails">
      <template #header>
        <div class="card-header">
          <h2>投资系数计算细节</h2>
          <el-button
            type="primary"
            size="small"
            @click="loadInvestmentDetails"
            :loading="marketStore.loadingDetails"
          >
            刷新计算详情
          </el-button>
        </div>
      </template>

      <div v-loading="marketStore.loadingDetails">
        <el-collapse accordion>
          <el-collapse-item
            v-for="asset in marketStore.marketDataList"
            :key="asset.code"
            :title="asset.code + ' 投资系数计算细节'"
          >
            <div v-if="getAssetDetails(asset.code)">
              <!-- 市场数据状态 -->
              <div class="detail-section">
                <h3>市场数据状态</h3>
                <el-alert
                  :type="
                    getAssetDetails(asset.code).marketDataStatus
                      ?.has_market_data
                      ? 'success'
                      : 'warning'
                  "
                  :title="
                    getAssetDetails(asset.code).marketDataStatus
                      ?.has_market_data
                      ? '市场数据获取成功'
                      : '使用中性默认值（市场数据不可用）'
                  "
                  :closable="false"
                  show-icon
                  style="margin-bottom: 15px"
                />
                <p
                  v-if="
                    getAssetDetails(asset.code).marketDataStatus?.updated_at
                  "
                >
                  数据更新时间:
                  {{
                    formatDateTime(
                      getAssetDetails(asset.code).marketDataStatus.updated_at
                    )
                  }}
                </p>
              </div>

              <!-- 默认值情况的简单显示 -->
              <div
                v-if="getAssetDetails(asset.code).coefficients?.is_default"
                class="detail-section"
              >
                <el-alert
                  type="info"
                  title="由于缺少市场数据，系统使用以下默认值进行计算"
                  :closable="false"
                  show-icon
                  style="margin-bottom: 15px"
                />
                <ul>
                  <li>估值系数: 1.0 (中性值)</li>
                  <li>投资频率: 每两周 (默认频率)</li>
                </ul>
              </div>

              <!-- 系数计算详情 -->
              <div v-else class="detail-section">
                <h3>系数计算详情</h3>
                <div class="score-summary">
                  <p>
                    <strong>市场总评分:</strong>
                    {{
                      getAssetDetails(
                        asset.code
                      ).marketScores?.total_score?.toFixed(2) ?? "0"
                    }}分 (满分100分)
                    <el-tooltip
                      content="评分由估值(30分)、趋势(30分)、波动(20分)、特殊事件(20分)四个组件组成。后端会确保四个评分组件的整数之和等于总评分的整数部分，以保持前端取整显示的一致性。"
                    >
                      <el-icon><QuestionFilled /></el-icon>
                    </el-tooltip>
                  </p>
                  <p>
                    <strong>评分等级:</strong>
                    {{
                      getScoreLevelText(
                        getAssetDetails(asset.code).marketScores?.total_score ??
                          40
                      )
                    }}
                  </p>
                  <p>
                    <strong>投资建议:</strong>
                    {{
                      getFrequencyText(
                        getAssetDetails(asset.code).frequency?.frequency ??
                          "biweekly"
                      )
                    }}
                    / 系数
                    {{
                      formatNumber(
                        getAssetDetails(asset.code).frequency?.factor ?? 1
                      )
                    }}
                  </p>
                  <el-divider></el-divider>
                </div>
                <!-- 市场指标 -->
                <div class="coefficient-detail">
                  <h4>
                    关键市场指标
                    <el-tooltip content="以下指标是评分和系数计算的基础数据">
                      <el-icon><QuestionFilled /></el-icon>
                    </el-tooltip>
                  </h4>
                  <div class="calculation-details">
                    <p>
                      当前价格:
                      {{
                        formatNumber(
                          getAssetDetails(asset.code).coefficients?.price
                        )
                      }}
                    </p>
                    <p>
                      价格位置 (52周区间):
                      {{
                        formatPercentage(
                          getAssetDetails(asset.code).coefficients
                            ?.price_position
                        )
                      }}
                      <el-tooltip
                        content="价格在52周高低点之间的位置，0%表示52周最低点，100%表示52周最高点"
                      >
                        <el-icon><QuestionFilled /></el-icon>
                      </el-tooltip>
                    </p>
                    <p>
                      均线偏离度:
                      {{
                        formatPercentage(
                          getAssetDetails(asset.code).coefficients?.ma_deviation
                        )
                      }}
                      <el-tooltip
                        content="当前价格相对于200日均线的偏离百分比，负数表示低于均线"
                      >
                        <el-icon><QuestionFilled /></el-icon>
                      </el-tooltip>
                    </p>
                    <p>
                      均线交叉信号:
                      {{
                        getMaCrossText(
                          getAssetDetails(asset.code).coefficients?.ma_cross
                        )
                      }}
                      <el-tooltip
                        content="短期均线与长期均线的交叉信号，金叉表示短期均线上穿长期均线"
                      >
                        <el-icon><QuestionFilled /></el-icon>
                      </el-tooltip>
                    </p>
                    <p>
                      相对强弱指标(RSI):
                      {{
                        formatNumber(
                          getAssetDetails(asset.code).coefficients?.rsi_14
                        )
                      }}
                      <el-tooltip
                        content="RSI用于衡量市场超买超卖，低于30通常认为超卖，高于70通常认为超买"
                      >
                        <el-icon><QuestionFilled /></el-icon>
                      </el-tooltip>
                    </p>
                    <p
                      v-if="
                        getAssetDetails(asset.code).frequency?.atr_percentile
                      "
                    >
                      波动率分位数:
                      {{
                        formatPercentage(
                          getAssetDetails(asset.code).frequency?.atr_percentile
                        )
                      }}
                      <el-tooltip
                        content="ATR分位数表示当前波动率在过去一年中的位置，高分位表示波动率高"
                      >
                        <el-icon><QuestionFilled /></el-icon>
                      </el-tooltip>
                    </p>
                    <p
                      v-if="
                        getAssetDetails(asset.code).specialConditions
                          ?.recent_drawdown
                      "
                    >
                      近期最大回撤:
                      {{
                        formatPercentage(
                          getAssetDetails(asset.code).specialConditions
                            ?.recent_drawdown
                        )
                      }}
                      <el-tooltip
                        content="近期最大回撤，负值越大表示下跌幅度越大"
                      >
                        <el-icon><QuestionFilled /></el-icon>
                      </el-tooltip>
                    </p>
                  </div>
                </div>

                <!-- 评分与系数转化 -->
                <div class="coefficient-detail coefficient-conversion">
                  <h4>
                    评分与系数转化
                    <el-tooltip content="系数由评分转化获得，用于计算投资策略">
                      <el-icon><QuestionFilled /></el-icon>
                    </el-tooltip>
                  </h4>
                  <div class="conversion-details">
                    <div class="conversion-item">
                      <span class="item-label">估值评分:</span>
                      <span class="item-value"
                        >{{
                          Object.prototype.hasOwnProperty.call(
                            getAssetDetails(asset.code).marketScores || {},
                            "valuation_score"
                          )
                            ? getAssetDetails(
                                asset.code
                              ).marketScores.valuation_score.toFixed(2)
                            : "0"
                        }}分</span
                      >
                      <span class="item-arrow">→</span>
                      <span class="item-label">估值系数:</span>
                      <span class="item-value">{{
                        Object.prototype.hasOwnProperty.call(
                          getAssetDetails(asset.code).coefficients || {},
                          "valuation_coefficient"
                        )
                          ? getAssetDetails(
                              asset.code
                            ).coefficients.valuation_coefficient.toFixed(2)
                          : "0"
                      }}</span>
                    </div>
                    <div class="conversion-item">
                      <span class="item-label">趋势评分:</span>
                      <span class="item-value"
                        >{{
                          Object.prototype.hasOwnProperty.call(
                            getAssetDetails(asset.code).marketScores || {},
                            "trend_score"
                          )
                            ? getAssetDetails(
                                asset.code
                              ).marketScores.trend_score.toFixed(2)
                            : "0"
                        }}分</span
                      >
                      <span class="item-arrow">→</span>
                      <span class="item-label">趋势系数:</span>
                      <span class="item-value">{{
                        Object.prototype.hasOwnProperty.call(
                          getAssetDetails(asset.code).coefficients || {},
                          "trend_coefficient"
                        )
                          ? getAssetDetails(
                              asset.code
                            ).coefficients.trend_coefficient.toFixed(2)
                          : "0"
                      }}</span>
                    </div>
                    <div class="conversion-item">
                      <span class="item-label">波动评分:</span>
                      <span class="item-value"
                        >{{
                          Object.prototype.hasOwnProperty.call(
                            getAssetDetails(asset.code).marketScores || {},
                            "volatility_score"
                          )
                            ? getAssetDetails(
                                asset.code
                              ).marketScores.volatility_score.toFixed(2)
                            : "0"
                        }}分</span
                      >
                      <span class="item-arrow">→</span>
                      <span class="item-label">波动系数:</span>
                      <span class="item-value">{{
                        Object.prototype.hasOwnProperty.call(
                          getAssetDetails(asset.code).coefficients || {},
                          "volatility_coefficient"
                        )
                          ? getAssetDetails(
                              asset.code
                            ).coefficients.volatility_coefficient.toFixed(2)
                          : "0"
                      }}</span>
                    </div>

                    <!-- 添加特殊事件评分显示 -->
                    <div class="conversion-item">
                      <span class="item-label">特殊事件评分:</span>
                      <span class="item-value"
                        >{{
                          Object.prototype.hasOwnProperty.call(
                            getAssetDetails(asset.code).marketScores || {},
                            "special_event_score"
                          )
                            ? getAssetDetails(
                                asset.code
                              ).marketScores.special_event_score.toFixed(2)
                            : "0"
                        }}分</span
                      >
                      <span class="item-arrow">→</span>
                      <span class="item-label">特殊系数:</span>
                      <span class="item-value">{{
                        getAssetDetails(asset.code).specialConditions
                          ?.has_special_condition
                          ? "已触发"
                          : "未触发"
                      }}</span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 投资频率详情 -->
              <div class="detail-section">
                <h3>投资频率详情</h3>
                <p>
                  <strong>建议频率:</strong>
                  {{
                    getFrequencyText(
                      getAssetDetails(asset.code).frequency?.frequency
                    )
                  }}
                </p>
                <p>
                  <strong>频率系数:</strong>
                  {{
                    formatNumber(getAssetDetails(asset.code).frequency?.factor)
                  }}
                  <el-tooltip
                    content="频率系数影响每次投资金额，大于1表示增加投资，小于1表示减少投资"
                  >
                    <el-icon><QuestionFilled /></el-icon>
                  </el-tooltip>
                </p>
                <p v-if="getAssetDetails(asset.code).frequency?.atr_percentile">
                  <strong>ATR分位数:</strong>
                  {{
                    formatPercentage(
                      getAssetDetails(asset.code).frequency?.atr_percentile
                    )
                  }}
                  <el-tooltip
                    content="ATR分位数表示当前波动率在过去一年中的位置，高分位表示波动率高"
                  >
                    <el-icon><QuestionFilled /></el-icon>
                  </el-tooltip>
                </p>
              </div>

              <!-- 特殊市场条件 -->
              <div class="detail-section">
                <h3>特殊市场条件</h3>
                <div
                  v-if="
                    getAssetDetails(asset.code).specialConditions
                      ?.has_special_condition
                  "
                >
                  <el-alert
                    type="warning"
                    :title="
                      getSpecialConditionText(
                        getAssetDetails(asset.code).specialConditions
                      )
                    "
                    :closable="false"
                    show-icon
                    style="margin-bottom: 15px"
                  />
                </div>
                <div v-else>
                  <el-alert
                    type="info"
                    title="目前没有检测到特殊市场条件"
                    :closable="false"
                    show-icon
                  />
                </div>

                <div
                  v-if="
                    getAssetDetails(asset.code).specialConditions
                      ?.recent_drawdown
                  "
                >
                  <p>
                    近期最大回撤:
                    {{
                      formatPercentage(
                        getAssetDetails(asset.code).specialConditions
                          ?.recent_drawdown
                      )
                    }}
                  </p>
                </div>
              </div>
            </div>
            <div v-else>
              <el-empty description="暂无计算详情" />
            </div>
          </el-collapse-item>
        </el-collapse>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from "vue";
import { useMarketStore } from "../store/market";
import { ElMessage } from "element-plus";
import { QuestionFilled } from "@element-plus/icons-vue";

const marketStore = useMarketStore();
const investmentDetails = ref(null);

// 评分区间说明数据
const scoreRanges = [
  {
    range: "80-100分",
    level: "极度超跌区间",
    frequency: "每日投资",
    strategy: "积极投资，单次金额为正常的150%，更有效捕捉市场低点",
  },
  {
    range: "65-79分",
    level: "价值区间",
    frequency: "每周投资",
    strategy: "适度投资，单次金额为正常的120%",
  },
  {
    range: "40-64分",
    level: "中性区间",
    frequency: "每两周投资",
    strategy: "常规投资，保持标准投资金额",
  },
  {
    range: "20-39分",
    level: "高估区间",
    frequency: "每月投资",
    strategy: "减少投资，单次金额为正常的80%",
  },
  {
    range: "0-19分",
    level: "极度泡沫区间",
    frequency: "每月投资",
    strategy: "谨慎投资，单次金额为正常的50%",
  },
];

// 加载投资系数计算详情
const loadInvestmentDetails = async () => {
  try {
    const details = await marketStore.loadInvestmentDetails();
    if (details) {
      investmentDetails.value = details;
      ElMessage.success("投资系数计算详情已更新");
    }
  } catch (error) {
    ElMessage.error("获取投资系数计算详情失败");
  }
};

// 获取特定资产的投资详情
const getAssetDetails = (assetCode) => {
  return marketStore.getAssetInvestmentDetails(assetCode);
};

// 格式化日期时间
const formatDateTime = (dateTimeStr) => {
  if (!dateTimeStr) return "-";
  return new Date(dateTimeStr).toLocaleString("zh-CN");
};

// 均线交叉信号文本
const getMaCrossText = (maCross) => {
  if (maCross === 1) return "金叉（上涨信号）";
  if (maCross === -1) return "死叉（下跌信号）";
  return "无明显信号";
};

// 频率文本
const getFrequencyText = (frequency) => {
  if (!frequency) return "每两周（默认）";
  switch (frequency) {
    case "daily":
      return "每日（极度超跌时积极投资）";
    case "weekly":
      return "每周";
    case "biweekly":
      return "每两周";
    case "monthly":
      return "每月";
    default:
      return frequency;
  }
};

// 特殊条件文本
const getSpecialConditionText = (specialConditions) => {
  if (!specialConditions) return "无特殊条件";

  if (specialConditions.condition_type === "极度超跌") {
    return "极度超跌区间 - 建议每日积极投资";
  } else if (specialConditions.condition_type === "价值区间") {
    return "价值区间 - 建议每周适度投资";
  } else if (specialConditions.condition_type === "中性区间") {
    return "中性区间 - 建议每两周常规投资";
  } else if (specialConditions.condition_type === "高估区间") {
    return "高估区间 - 建议每月减少投资";
  } else if (specialConditions.condition_type === "极度泡沫") {
    return "极度泡沫区间 - 建议谨慎最小投资";
  }

  return specialConditions.description || "其他特殊市场条件";
};

// 数字格式化
const formatNumber = (value) => {
  if (value === null || value === undefined) return "-";
  return Number(value).toFixed(2);
};

// 百分比格式化
const formatPercentage = (value) => {
  if (value === null || value === undefined) return "-";
  return `${(value * 100).toFixed(2)}%`;
};

// 根据评分获取标签类型
const getScoreTagType = (score) => {
  if (score >= 80) return "danger"; // 极度超跌 - 红色（突出显示）
  if (score >= 65) return "warning"; // 价值区间 - 橙色
  if (score >= 40) return "info"; // 中性区间 - 蓝色
  if (score >= 20) return "warning"; // 高估区间 - 橙色
  return "danger"; // 极度泡沫 - 红色
};

// 根据评分获取颜色
const getScoreTagColor = (score) => {
  if (score >= 80) return "#F56C6C"; // 极度超跌 - 红色
  if (score >= 65) return "#E6A23C"; // 价值区间 - 橙色
  if (score >= 40) return "#409EFF"; // 中性区间 - 蓝色
  if (score >= 20) return "#E6A23C"; // 高估区间 - 橙色
  return "#F56C6C"; // 极度泡沫 - 红色
};

// 根据评分获取区间文本
const getScoreLevelText = (score) => {
  if (score >= 80) return "极度超跌区间（每日投资）";
  if (score >= 65) return "价值区间（每周投资）";
  if (score >= 40) return "中性区间（每两周投资）";
  if (score >= 20) return "高估区间（每月投资）";
  return "极度泡沫区间（谨慎投资）";
};

// 根据评分组件值获取颜色
const getScoreComponentColor = (score, maxScore) => {
  const percentage = (score / maxScore) * 100;
  if (percentage >= 80) return "#F56C6C"; // 高分 - 红色
  if (percentage >= 60) return "#E6A23C"; // 中高分 - 橙色
  if (percentage >= 40) return "#67C23A"; // 中分 - 绿色
  return "#909399"; // 低分 - 灰色
};

// 计算包含评分的资产列表
const assetsWithScores = computed(() => {
  if (!investmentDetails.value || !investmentDetails.value.market_scores)
    return [];

  return marketStore.marketDataList.map((asset) => {
    const scoreData = investmentDetails.value.market_scores[asset.code] || {};
    const strategyData =
      investmentDetails.value.investment_strategies?.[asset.code] || {};

    // 确保所有分数取整
    const totalScore = Math.round(scoreData.total_score ?? 40);
    const valuationScore = Math.round(scoreData.valuation_score ?? 10);
    const trendScore = Math.round(scoreData.trend_score ?? 10);
    const volatilityScore = Math.round(scoreData.volatility_score ?? 10);
    const specialEventScore = Math.round(scoreData.special_event_score ?? 0);

    return {
      code: asset.code,
      totalScore,
      valuationScore,
      trendScore,
      volatilityScore,
      specialEventScore,
      strategy: {
        score_level: strategyData.score_level || "中性区间",
        frequency: strategyData.frequency || "biweekly",
        amount_factor: strategyData.amount_factor || 1.0,
        description: strategyData.description || "维持常规投资节奏和金额",
      },
    };
  });
});

onMounted(async () => {
  // 如果市场数据为空，自动尝试获取一次
  if (
    Object.keys(marketStore.marketData).length === 0 &&
    !marketStore.loading
  ) {
    await marketStore.loadMarketData();
  }

  // 加载投资系数计算详情
  await loadInvestmentDetails();
});
</script>

<style scoped>
.market-container {
  max-width: 1200px;
  margin: 0 auto;
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
  font-size: 18px;
}

.last-updated {
  margin-right: 15px;
  font-size: 14px;
  color: #606266;
}

/* 评分区间说明 */
.score-range-guide {
  margin-bottom: 20px;
}

.score-range-guide h3 {
  font-size: 16px;
  margin-bottom: 10px;
  color: #303133;
}

/* 资产摘要卡片 */
.asset-card {
  margin-bottom: 15px;
  height: 100%;
}

.asset-summary {
  padding: 10px 0;
}

.summary-row {
  display: flex;
  margin-bottom: 8px;
  align-items: center;
}

.summary-label {
  font-weight: 500;
  color: #606266;
  width: 80px;
}

.summary-value {
  font-weight: bold;
  color: #303133;
}

.summary-description {
  margin-top: 10px;
  padding: 8px;
  background-color: #f5f7fa;
  border-radius: 4px;
  color: #606266;
  font-size: 14px;
  line-height: 1.4;
}

.detail-section {
  margin-bottom: 15px;
}

.detail-section h3 {
  margin: 0 0 5px 0;
  font-size: 14px;
  color: #606266;
}

.calculation-details {
  margin-left: 20px;
}

.coefficient-detail {
  margin-bottom: 10px;
}

.description {
  color: #909399;
  font-size: 14px;
  margin-top: 5px;
}

.asset-score-card {
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
  font-size: 16px;
}

.score-details {
  padding: 10px 0;
}

.score-components {
  margin-bottom: 20px;
}

.score-component {
  margin-bottom: 12px;
}

.score-component-total {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px dashed #ebeef5;
}

.component-label {
  display: inline-block;
  width: 80px;
  font-weight: 500;
}

.component-value {
  display: inline-block;
  width: 50px;
  text-align: right;
  margin-right: 10px;
}

.component-value-total {
  display: inline-block;
  width: 50px;
  text-align: right;
  margin-right: 10px;
  font-weight: bold;
  color: #409eff;
  font-size: 16px;
}

.investment-strategy {
  background-color: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
}

.investment-strategy h4 {
  margin-top: 0;
  margin-bottom: 12px;
  color: #333;
}

.strategy-details p {
  margin: 6px 0;
}

.strategy-description {
  padding: 8px;
  background-color: #fff;
  border-radius: 4px;
  margin-top: 12px;
  color: #606266;
  font-size: 14px;
}

.score-summary {
  background-color: #f5f7fa;
  padding: 12px;
  margin-bottom: 15px;
  border-radius: 4px;
}

.score-summary p {
  margin: 6px 0;
}

.coefficient-conversion {
  margin-top: 20px;
}

.conversion-details {
  padding: 10px;
  background-color: #f9f9f9;
  border-radius: 4px;
}

.conversion-item {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  padding: 5px 0;
}

.item-label {
  font-weight: 500;
  color: #606266;
  min-width: 70px;
}

.item-value {
  color: #303133;
  font-weight: bold;
  margin: 0 10px;
}

.item-arrow {
  color: #909399;
  margin: 0 8px;
  font-size: 16px;
}
</style>
