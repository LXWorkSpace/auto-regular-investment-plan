from typing import Dict, List, Optional, Union, Tuple
from datetime import datetime, timedelta
import math
import logging
import calendar

from ..models.base_models import Asset, UserConfig, MarketData, InvestmentRecommendation, InvestmentPlan, InvestmentFrequency

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class InvestmentCalculator:
    """投资计算工具类，实现定投策略计算"""
    
    def __init__(self):
        """初始化投资计算器"""
        pass
    
    def calculate_valuation_coefficient(self, pe_percentile: Optional[float] = None, pb_percentile: Optional[float] = None) -> float:
        """计算估值系数
        
        Args:
            pe_percentile: PE分位数（优先使用）
            pb_percentile: PB分位数（PE不可用时使用）
            
        Returns:
            float: 估值系数
        """
        # 优先使用PE分位数
        percentile = pe_percentile if pe_percentile is not None else pb_percentile
        
        # 如果没有分位数据，返回1.0（中性）
        if percentile is None:
            return 1.0
        
        # 按照策略计算估值系数
        if percentile < 0.3:
            # 越低估加成越大
            return 1 + (0.3 - percentile) / 0.3
        elif percentile > 0.7:
            # 越高估减仓越多
            return 1 - (percentile - 0.7) / 0.3
        else:
            # 中性区域
            return 1.0
    
    def calculate_trend_coefficient(self, deviation_percentage: Optional[float]) -> float:
        """计算趋势系数
        
        Args:
            deviation_percentage: 价格与200日均线的偏离百分比
            
        Returns:
            float: 趋势系数
        """
        # 如果没有偏离度数据，返回1.0（中性）
        if deviation_percentage is None:
            return 1.0
        
        # 按照策略计算趋势系数
        if deviation_percentage < -0.15:
            # 严重超跌区域
            return 1.5
        elif -0.15 <= deviation_percentage < -0.05:
            # 弱势区域
            return 1.2
        elif -0.05 <= deviation_percentage <= 0.05:
            # 平衡区域
            return 1.0
        else:
            # 超涨区域
            return 0.8
    
    def calculate_volatility_coefficient(self, atr_20: Optional[float], atr_baseline: Optional[float]) -> float:
        """计算波动系数
        
        Args:
            atr_20: 20日ATR
            atr_baseline: 基准ATR（过去一年ATR中位数）
            
        Returns:
            float: 波动系数
        """
        # 如果没有ATR数据，返回1.0（中性）
        if atr_20 is None or atr_baseline is None or atr_20 == 0:
            return 1.0
        
        # 计算波动系数 = 基准波动率 / 当前ATR
        volatility_coefficient = atr_baseline / atr_20
        
        # 限制系数范围，避免极端值
        return max(0.5, min(volatility_coefficient, 1.5))
    
    def determine_frequency(self, volatility_coefficient: float) -> Tuple[InvestmentFrequency, float]:
        """根据波动系数确定投资频率
        
        Args:
            volatility_coefficient: 波动系数
            
        Returns:
            Tuple[InvestmentFrequency, float]: (投资频率, 频率因子)
        """
        # 按照波动系数分层决策
        if volatility_coefficient > 1.3:
            # 极度平静
            return InvestmentFrequency.DAILY, 0.2
        elif 0.9 <= volatility_coefficient <= 1.3:
            # 正常波动
            return InvestmentFrequency.WEEKLY, 0.4
        elif 0.6 <= volatility_coefficient < 0.9:
            # 波动加剧
            return InvestmentFrequency.BIWEEKLY, 0.7
        else:
            # 极端动荡
            return InvestmentFrequency.MONTHLY, 1.0
    
    def calculate_monthly_amount(self, total_amount: float, weight: float, 
                               valuation_coefficient: float, trend_coefficient: float) -> float:
        """计算月度投资金额
        
        Args:
            total_amount: 总投资金额
            weight: 资产权重
            valuation_coefficient: 估值系数
            trend_coefficient: 趋势系数
            
        Returns:
            float: 月度投资金额
        """
        # 理论月投资额 = 总金额 × 权重 × 估值系数 × 趋势系数
        monthly_amount = total_amount * weight * valuation_coefficient * trend_coefficient
        return monthly_amount
    
    def calculate_single_amount(self, monthly_amount: float, volatility_coefficient: float, 
                              frequency_factor: float, frequency: InvestmentFrequency) -> float:
        """计算单次投资金额
        
        Args:
            monthly_amount: 月度投资金额
            volatility_coefficient: 波动系数
            frequency_factor: 频率因子
            frequency: 投资频率
            
        Returns:
            float: 单次投资金额
        """
        # 对于月投资，需要应用补偿乘数
        if frequency == InvestmentFrequency.MONTHLY and volatility_coefficient < 1.0:
            # 低频补偿算法
            baseline_atr_ratio = max(0, 1 + (1.0 - volatility_coefficient))
            compensation_multiplier = min(1.2, baseline_atr_ratio)
            
            # 单次投资额 = 理论月投资额 × 波动系数 × 频率因子 × 补偿乘数
            single_amount = monthly_amount * volatility_coefficient * frequency_factor * compensation_multiplier
        else:
            # 单次投资额 = 理论月投资额 × 波动系数 × 频率因子
            single_amount = monthly_amount * volatility_coefficient * frequency_factor
        
        return single_amount
    
    def get_investment_dates(self, frequency: InvestmentFrequency) -> List[str]:
        """获取投资日期建议
        
        Args:
            frequency: 投资频率
            
        Returns:
            List[str]: 投资日期列表
        """
        now = datetime.now()
        current_month = now.month
        next_month = (current_month % 12) + 1
        current_year = now.year
        next_year = current_year + 1 if next_month == 1 else current_year
        
        dates = []
        
        if frequency == InvestmentFrequency.DAILY:
            # 日投：建议最近5个交易日
            for i in range(5):
                date = now + timedelta(days=i+1)
                # 跳过周末
                while date.weekday() >= 5:  # 5和6是周六和周日
                    date += timedelta(days=1)
                dates.append(date.strftime("%Y-%m-%d"))
        
        elif frequency == InvestmentFrequency.WEEKLY:
            # 周投：建议每周四
            for i in range(4):  # 四周
                # 找到下一个周四
                days_ahead = 3 - now.weekday()  # 周四是3
                if days_ahead <= 0:  # 如果今天是周四或之后，则计算下周四
                    days_ahead += 7
                date = now + timedelta(days=days_ahead + i*7)
                dates.append(date.strftime("%Y-%m-%d"))
        
        elif frequency == InvestmentFrequency.BIWEEKLY:
            # 双周投：每月第2、4个星期四
            # 获取下个月的日历
            cal = calendar.monthcalendar(next_year, next_month)
            
            # 找到第2和第4个周四（周四索引为3）
            thursdays = [week[3] for week in cal if week[3] != 0]
            if len(thursdays) >= 2:
                dates.append(f"{next_year}-{next_month:02d}-{thursdays[1]:02d}")
            if len(thursdays) >= 4:
                dates.append(f"{next_year}-{next_month:02d}-{thursdays[3]:02d}")
        
        elif frequency == InvestmentFrequency.MONTHLY:
            # 月投：下月首个非农数据公布后第3个交易日
            # 非农通常在每月第一个星期五公布
            cal = calendar.monthcalendar(next_year, next_month)
            first_friday = next(week[4] for week in cal if week[4] != 0)
            
            # 非农数据后第3个交易日（跳过周末）
            nonfarm_date = datetime(next_year, next_month, first_friday)
            trading_day_count = 0
            days_after = 0
            
            while trading_day_count < 3:
                days_after += 1
                date = nonfarm_date + timedelta(days=days_after)
                if date.weekday() < 5:  # 工作日
                    trading_day_count += 1
            
            dates.append(date.strftime("%Y-%m-%d"))
        
        return dates
    
    def check_circuit_breaker(self, market_data: Dict[str, MarketData]) -> bool:
        """检查熔断机制是否触发
        
        Args:
            market_data: 市场数据字典
            
        Returns:
            bool: 是否触发熔断
        """
        for code, data in market_data.items():
            # 检查是否满足熔断条件：PE分位>90%且偏离度>20%
            if (data.pe_percentile is not None and data.pe_percentile > 0.9 and
                data.deviation_percentage is not None and data.deviation_percentage > 0.2):
                return True
        
        return False
    
    def check_rebalance_required(self, assets: List[Asset], market_data: Dict[str, MarketData]) -> bool:
        """检查是否需要再平衡
        
        Args:
            assets: 资产列表
            market_data: 市场数据字典
            
        Returns:
            bool: 是否需要再平衡
        """
        # 简化实现：假设已经基于市场数据计算出当前持仓比例
        # 实际应用中，需要获取用户实际持仓数据
        
        # 这里仅返回False，表示不需要再平衡
        # 实际应用中，需要检查|实际权重 - 目标权重| > 15%
        return False
    
    def generate_investment_plan(self, user_config: UserConfig, 
                               market_data: Dict[str, MarketData]) -> InvestmentPlan:
        """生成投资计划
        
        Args:
            user_config: 用户配置
            market_data: 市场数据字典
            
        Returns:
            InvestmentPlan: 投资计划
        """
        total_monthly_amount = user_config.monthly_investment
        buffer_amount = total_monthly_amount * user_config.buffer_percentage
        available_amount = total_monthly_amount - buffer_amount
        
        recommendations = []
        
        # 检查熔断和再平衡
        circuit_breaker_triggered = self.check_circuit_breaker(market_data)
        rebalance_required = self.check_rebalance_required(user_config.assets, market_data)
        
        for asset in user_config.assets:
            # 获取市场数据
            asset_market_data = market_data.get(asset.code)
            
            if asset_market_data is None:
                # 如果没有市场数据，使用默认值
                valuation_coefficient = 1.0
                trend_coefficient = 1.0
                volatility_coefficient = 1.0
                frequency = InvestmentFrequency.MONTHLY
                frequency_factor = 1.0
            else:
                # 计算三大系数
                valuation_coefficient = self.calculate_valuation_coefficient(
                    asset_market_data.pe_percentile, 
                    asset_market_data.pb_percentile
                )
                
                trend_coefficient = self.calculate_trend_coefficient(
                    asset_market_data.deviation_percentage
                )
                
                volatility_coefficient = self.calculate_volatility_coefficient(
                    asset_market_data.atr_20,
                    asset_market_data.atr_baseline
                )
                
                # 确定投资频率
                frequency, frequency_factor = self.determine_frequency(volatility_coefficient)
            
            # 计算月度和单次投资金额
            monthly_amount = self.calculate_monthly_amount(
                available_amount, 
                asset.weight, 
                valuation_coefficient, 
                trend_coefficient
            )
            
            single_amount = self.calculate_single_amount(
                monthly_amount,
                volatility_coefficient,
                frequency_factor,
                frequency
            )
            
            # 获取投资日期建议
            investment_dates = self.get_investment_dates(frequency)
            
            # 创建投资建议
            recommendation = InvestmentRecommendation(
                asset=asset,
                valuation_coefficient=valuation_coefficient,
                trend_coefficient=trend_coefficient,
                volatility_coefficient=volatility_coefficient,
                recommended_frequency=frequency,
                frequency_factor=frequency_factor,
                monthly_amount=monthly_amount,
                single_amount=single_amount,
                investment_dates=investment_dates
            )
            
            recommendations.append(recommendation)
        
        # 创建投资计划
        investment_plan = InvestmentPlan(
            total_monthly_amount=total_monthly_amount,
            buffer_amount=buffer_amount,
            recommendations=recommendations,
            circuit_breaker_triggered=circuit_breaker_triggered,
            rebalance_required=rebalance_required
        )
        
        return investment_plan 