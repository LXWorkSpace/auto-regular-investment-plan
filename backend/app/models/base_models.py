from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Union
from enum import Enum
from datetime import datetime

class RiskPreference(str, Enum):
    """风险偏好枚举"""
    LOW = "低风险"
    MEDIUM = "中等风险"
    HIGH = "高风险"

class InvestmentFrequency(str, Enum):
    """投资频率枚举"""
    DAILY = "日投"
    WEEKLY = "周投"
    BIWEEKLY = "双周投"
    MONTHLY = "月投"

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
    weight: float = Field(..., ge=0, le=1)
    description: Optional[str] = None

class UserConfig(BaseModel):
    """用户配置模型"""
    monthly_investment: float
    risk_preference: RiskPreference
    assets: List[Asset]
    buffer_percentage: float = 0.1  # 默认缓冲池比例为10%
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class MarketData(BaseModel):
    """市场数据模型"""
    code: str
    name: str
    price: float
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    pe_percentile: Optional[float] = None
    pb_percentile: Optional[float] = None
    ma_200: Optional[float] = None
    deviation_percentage: Optional[float] = None
    atr_20: Optional[float] = None
    atr_baseline: Optional[float] = None
    updated_at: datetime = Field(default_factory=datetime.now)

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
    
class InvestmentPlan(BaseModel):
    """投资计划模型"""
    generated_at: datetime = Field(default_factory=datetime.now)
    total_monthly_amount: float
    buffer_amount: float
    recommendations: List[InvestmentRecommendation]
    circuit_breaker_triggered: bool = False
    rebalance_required: bool = False 