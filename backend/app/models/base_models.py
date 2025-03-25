from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Union, Any
from enum import Enum
from datetime import datetime

class InvestmentFrequency(str, Enum):
    """投资频率枚举"""
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"

class AssetType(str, Enum):
    """资产类型枚举"""
    CN_INDEX = "中国指数"
    US_INDEX = "美国指数"
    GOLD = "黄金"
    BOND = "债券"
    CASH = "现金"
    OTHER = "其他"

class Asset(BaseModel):
    """资产模型"""
    id: Optional[str] = None
    name: str
    code: str
    type: AssetType
    market: str = "US"  # 默认美国市场
    weight: float = 0.0  # 资产权重
    description: Optional[str] = None

class UserConfig(BaseModel):
    """用户配置模型"""
    user_id: str
    monthly_investment: float
    buffer_amount: float = 500.0  # 资金池金额，默认500元
    assets: List[Asset]
    previous_circuit_breaker_level: Optional[int] = 0  # 上次熔断级别
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class MarketData(BaseModel):
    """市场数据模型"""
    code: str
    name: Optional[str]
    price: Optional[float]
    updated_at: Optional[str]
    
    # 价格位置指标
    w52_high: Optional[float]  # 52周高点
    w52_low: Optional[float]   # 52周低点
    
    # 均线指标
    ma_20: Optional[float]    # 20日均线
    ma_50: Optional[float]    # 50日均线
    ma_200: Optional[float]   # 200日均线
    ma_cross: Optional[int]   # 均线交叉信号 (1=金叉, -1=死叉, 0=无交叉)
    deviation_percentage: Optional[float]  # 相对于200日均线的偏离百分比
    
    # 波动率指标
    atr_20: Optional[float]   # 20日ATR
    atr_baseline: Optional[float]  # 基准ATR（过去一年ATR中位数）
    atr_percentile: Optional[float]  # ATR在历史分布中的位置
    
    # 动量指标
    rsi_14: Optional[float]   # 14日RSI
    
    # 风险指标
    recent_drawdown: Optional[float]  # 近期回撤
    volume_surge: Optional[float]     # 成交量异常

class InvestmentRecommendation(BaseModel):
    """投资建议模型"""
    asset: Asset
    valuation_coefficient: float
    trend_coefficient: float
    volatility_coefficient: float
    recommended_frequency: InvestmentFrequency
    frequency_factor: float
    monthly_amount: float
    single_amount: float
    investment_dates: List[str]
    special_condition: Optional[str] = None  # 特殊市场条件类型

class InvestmentPlan(BaseModel):
    """投资计划模型"""
    generated_at: datetime = Field(default_factory=datetime.now)
    total_monthly_amount: float  # 总月度投资金额
    effective_monthly_amount: float  # 实际可投资金额（应用熔断因子后）
    buffer_amount: float  # 资金池金额
    recommendations: List[InvestmentRecommendation]  # 投资建议列表
    circuit_breaker_level: int = 0  # 熔断级别 (0=正常, 1=轻度, 2=中度, 3=严重)
    warning_messages: List[str] = []  # 警告消息
    actual_investment_amount: float = 0  # 实际总投资金额（计入资金池使用后）
    buffer_pool_usage: float = 0  # 资金池使用金额
    market_trend_analysis: Dict[str, Any] = Field(default_factory=dict)  # 市场趋势分析结果 