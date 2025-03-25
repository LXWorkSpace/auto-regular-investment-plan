import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.app.utils.market_data import MarketDataFetcher
from backend.app.utils.investment_calculator import InvestmentCalculator
from backend.app.models.base_models import (
    Asset, UserConfig, AssetType, RiskPreference, InvestmentFrequency, MarketData
)

def test_improved_strategy():
    """测试改进后的定投策略"""
    
    print("开始测试改进后的定投策略...")
    
    # 创建市场数据获取器
    market_fetcher = MarketDataFetcher()
    
    # 创建投资计算器
    calculator = InvestmentCalculator()
    
    # 测试资产列表
    assets = [
        Asset(
            name="标普500指数ETF",
            code="SPY",
            type=AssetType.US_INDEX,
            market="US",
            weight=0.4
        ),
        Asset(
            name="纳斯达克100指数ETF",
            code="QQQ",
            type=AssetType.US_INDEX,
            market="US",
            weight=0.3
        ),
        Asset(
            name="沪深300指数ETF",
            code="000300",
            type=AssetType.CN_INDEX,
            market="CN",
            weight=0.3
        )
    ]
    
    # 创建用户配置
    user_config = UserConfig(
        user_id="test_user",
        monthly_investment=5000.0,
        risk_preference=RiskPreference.MEDIUM,
        buffer_amount=500.0,
        assets=assets
    )
    
    # 获取市场数据
    market_data = {}
    
    print("正在获取市场数据...")
    for asset in assets:
        print(f"获取 {asset.name} ({asset.code}) 的市场数据...")
        data_dict = market_fetcher.get_complete_market_data(asset.code, asset.market)
        # 将字典转换为 MarketData 对象
        data = MarketData(**data_dict)
        market_data[asset.code] = data
    
    # 生成投资计划
    print("\n生成投资计划...")
    investment_plan = calculator.generate_investment_plan(user_config, market_data)
    
    # 打印投资计划
    print("\n===== 投资计划 =====")
    print(f"总月度投资金额: {investment_plan.total_monthly_amount}")
    print(f"实际可投资金额: {investment_plan.effective_monthly_amount}")
    print(f"资金池金额: {investment_plan.buffer_amount}")
    print(f"熔断级别: {investment_plan.circuit_breaker_level}")
    
    if investment_plan.warning_messages:
        print("\n警告消息:")
        for msg in investment_plan.warning_messages:
            print(f"- {msg}")
    
    print("\n===== 投资建议 =====")
    for rec in investment_plan.recommendations:
        asset = rec.asset
        print(f"\n资产: {asset.name} ({asset.code})")
        print(f"资产权重: {asset.weight:.1%}")
        print(f"估值系数: {rec.valuation_coefficient:.2f}")
        print(f"趋势系数: {rec.trend_coefficient:.2f}")
        print(f"波动系数: {rec.volatility_coefficient:.2f}")
        print(f"建议频率: {rec.recommended_frequency.value}")
        print(f"月度金额: {rec.monthly_amount:.2f}")
        print(f"单次金额: {rec.single_amount:.2f}")
        
        if rec.special_condition:
            print(f"特殊条件: {rec.special_condition}")
        
        print("建议投资日期:")
        for date in rec.investment_dates:
            print(f"- {date}")
    
    print("\n测试完成!")

if __name__ == "__main__":
    test_improved_strategy() 