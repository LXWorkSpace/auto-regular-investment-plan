# 自动定投策略提醒系统 - 后端

本项目是一个基于FastAPI的自动定投策略提醒系统后端，实现了智能定投策略框架，包含估值择时、趋势跟踪和波动率适配三大智能模块。

## 功能特点

- 基于PE/PB分位的估值择时
- 基于均线的趋势跟踪
- 基于ATR的波动率适配
- 自动生成投资建议报告
- 支持中国和美国市场的宽基指数ETF
- 数据以JSON格式存储在本地

## 安装指南

### 前提条件

- Python 3.8+
- pip包管理器

### 安装步骤

1. 克隆本仓库

```bash
git clone <repository-url>
cd auto-regular-investment-plan/backend
```

2. 安装依赖

```bash
pip install -r requirements.txt
```

### 获取API密钥

本项目使用的API都是免费的，无需特殊密钥：

- Yahoo Finance API (yfinance): 免费API，无需密钥
- AKShare: 免费中国市场数据接口，无需密钥

## 运行应用

```bash
cd backend
python main.py
```

应用将在 http://localhost:8000 运行。

## API文档

启动应用后，可以访问以下地址查看API文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 主要API路由

### 配置管理

- GET `/api/config` - 获取用户配置
- POST `/api/config` - 更新用户配置

### 市场数据

- GET `/api/market-data` - 获取所有市场数据
- GET `/api/market-data/{code}` - 获取特定资产的市场数据
- POST `/api/market-data/refresh` - 刷新所有市场数据

### 投资计划

- GET `/api/investment-plans` - 获取历史投资计划
- GET `/api/investment-plans/latest` - 获取最新投资计划
- POST `/api/investment-plans/generate` - 生成新的投资计划

### 参考数据

- GET `/api/assets/examples` - 获取示例资产列表

## 数据存储

所有数据以JSON格式存储在 `app/data` 目录下:

- `user_config.json` - 用户配置
- `market_data.json` - 市场数据
- `investment_plans.json` - 投资计划

## 定投策略框架

系统整合了三大模块的智能定投策略:

1. **估值系数**：基于PE/PB分位，在低估时增加投入，高估时减少投入
2. **趋势系数**：基于200日均线，严重超跌时加码，超涨时减码
3. **波动系数**：基于ATR波动率，低波动时频繁小额投入，高波动时降低频率集中投入

详细算法请参考代码中的 `InvestmentCalculator` 类。 