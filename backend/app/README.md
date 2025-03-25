# 改进版定投策略

## 策略概述

本项目实现了一个改进版的自动定投计划系统，主要针对宽基指数 ETF 定投进行了优化。策略基于市场数据分析，动态调整投资频率和金额，旨在优化长期投资回报。

## 核心特点

1. **完全基于价格相对位置的估值系统**

   - 使用价格在 52 周范围内的位置评估当前估值
   - 基于相对长期均线的偏离度判断估值
   - 无需依赖难以获取的 PE/PB 估值数据

2. **多指标趋势分析**

   - 整合多条均线关系评估趋势强度
   - 使用 RSI 指标评估超买超卖状况
   - 考虑均线金叉死叉等技术信号

3. **智能波动率适应**

   - 建立波动率锥，将 ATR 置于历史位置
   - 根据波动率环境动态调整投资频率与金额
   - 低波动环境采用高频小额策略，高波动环境采用低频大额策略

4. **多层次熔断机制**

   - 轻度预警：减少 20%投资
   - 中度预警：减少 50%投资
   - 重度预警：暂停大部分投资，仅保留 10%额度
   - 根据市场改善渐进式恢复投资额度

5. **特殊市场机会识别**
   - 识别超跌反弹机会，适度增加投资
   - 监测系统性风险事件，分散增加投资
   - 应对大幅下跌，调整投资节奏

## 技术实现

### 市场数据获取 (MarketDataFetcher)

使用 yfinance 库获取股票及 ETF 数据，支持以下指标计算：

- 52 周高低点分析
- 多周期移动均线 (20/50/200 日)
- 均线交叉信号检测
- RSI 超买超卖指标
- ATR 及其历史分位数
- 近期回撤计算

### 投资计算 (InvestmentCalculator)

实现了以下关键方法：

- `calculate_valuation_coefficient`: 基于价格位置计算估值系数
- `calculate_trend_coefficient`: 整合多指标计算趋势系数
- `calculate_volatility_coefficient`: 基于 ATR 分位计算波动系数
- `determine_frequency`: 根据波动环境确定投资频率
- `check_special_market_condition`: 检查特殊市场条件
- `evaluate_market_condition`: 多层次评估市场状况和熔断
- `check_recovery_condition`: 检查是否从熔断中恢复

## 使用方法

1. 配置资产列表和权重
2. 设置月度投资金额
3. 运行系统获取市场数据
4. 生成投资计划和建议

## 示例

```python
# 创建市场数据获取器
market_fetcher = MarketDataFetcher()

# 创建投资计算器
calculator = InvestmentCalculator()

# 配置资产列表
assets = [
    Asset(name="标普500指数ETF", code="SPY", weight=0.4),
    Asset(name="纳斯达克100指数ETF", code="QQQ", weight=0.3),
    Asset(name="沪深300指数ETF", code="000300", weight=0.3)
]

# 创建用户配置
user_config = UserConfig(
    user_id="test_user",
    monthly_investment=5000.0,
    buffer_percentage=0.1,
    assets=assets
)

# 获取市场数据
market_data = {}
for asset in assets:
    data_dict = market_fetcher.get_complete_market_data(asset.code, asset.market)
    data = MarketData(**data_dict)
    market_data[asset.code] = data

# 生成投资计划
investment_plan = calculator.generate_investment_plan(user_config, market_data)
```

## 与原策略对比

| 策略方面   | 原策略                 | 改进策略                         |
| ---------- | ---------------------- | -------------------------------- |
| 估值评估   | 依赖 PE/PB 分位数      | 完全使用价格相对位置和均线偏离度 |
| 趋势判断   | 仅使用价格与均线偏离度 | 整合多条均线关系和 RSI 指标      |
| 波动率应用 | 机械对应投资频率       | 创建波动率锥，动态频率与金额     |
| 熔断机制   | 简单的开关模式         | 多级别预警和渐进式调整           |
| 特殊机会   | 基本不考虑             | 识别超跌反弹、系统性风险机会     |
| 数据要求   | 需要估值历史数据       | 仅使用价格和成交量基础数据       |

## 注意事项

- 本策略仅作为投资参考，不构成投资建议
- 实际投资应结合个人风险承受能力和投资目标
- 策略参数可根据个人偏好进行调整
