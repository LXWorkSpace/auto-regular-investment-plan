import sys
import os
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 修正导入路径
from app.utils.investment_calculator import InvestmentCalculator
from app.models.base_models import Asset, UserConfig, MarketData, AssetType

def test_investment_calculator():
    """测试投资计算器的资金分配逻辑"""
    
    # 创建投资计算器实例
    calculator = InvestmentCalculator()
    
    # 创建测试用的用户配置
    assets = [
        Asset(
            id="test1",
            name="标普500ETF",
            code="SPY",
            type=AssetType.US_INDEX,
            market="US",
            weight=0.5,
            description="跟踪标普500指数的ETF"
        ),
        Asset(
            id="test2",
            name="纳斯达克ETF",
            code="QQQ",
            type=AssetType.US_INDEX,
            market="US",
            weight=0.5,
            description="跟踪纳斯达克100指数的ETF"
        )
    ]
    
    # 创建用户配置，monthly_investment=3000，buffer_amount=1000
    user_config = UserConfig(
        user_id="test_user",
        monthly_investment=3000.0,
        assets=assets,
        buffer_amount=1000.0
    )
    
    # 创建模拟的市场数据
    market_data = {
        "SPY": MarketData(
            code="SPY",
            name="标普500ETF",
            price=450.0,
            updated_at=datetime.now().strftime("%Y-%m-%d"),
            w52_high=500.0,
            w52_low=400.0,
            ma_20=455.0,
            ma_50=460.0,
            ma_200=440.0,
            ma_cross=0,
            deviation_percentage=0.02,
            atr_20=5.0,
            atr_baseline=4.5,
            atr_percentile=0.6,
            rsi_14=55.0,  # 对应中性市场
            recent_drawdown=-0.03,
            volume_surge=1.2
        ),
        "QQQ": MarketData(
            code="QQQ",
            name="纳斯达克ETF",
            price=370.0,
            updated_at=datetime.now().strftime("%Y-%m-%d"),
            w52_high=420.0,
            w52_low=330.0,
            ma_20=380.0,
            ma_50=370.0,
            ma_200=350.0,
            ma_cross=0,
            deviation_percentage=0.05,
            atr_20=6.0,
            atr_baseline=5.0,
            atr_percentile=0.7,
            rsi_14=70.0,  # 对应价值区间
            recent_drawdown=-0.02,
            volume_surge=1.1
        )
    }
    
    # 生成投资计划
    plan = calculator.generate_investment_plan(user_config, market_data)
    
    # 打印投资计划详情
    print("\n===== 投资计划详情 =====")
    print(f"总月度投资金额: {plan.total_monthly_amount:.2f} 元")
    print(f"有效月度投资金额: {plan.effective_monthly_amount:.2f} 元")
    print(f"资金池金额: {plan.buffer_amount:.2f} 元")
    print(f"实际总投资金额: {plan.actual_investment_amount:.2f} 元")
    print(f"资金池使用金额: {plan.buffer_pool_usage:.2f} 元")
    
    # 计算推荐总额
    recommendation_total = sum(rec.monthly_amount for rec in plan.recommendations)
    print(f"推荐总额: {recommendation_total:.2f} 元")
    
    # 检查总投资金额是否等于月度投资金额
    is_valid = abs(recommendation_total - plan.total_monthly_amount) < 0.01
    print(f"总投资金额是否等于月度预算: {'是' if is_valid else '否'}")
    
    # 打印各资产详情
    print("\n===== 各资产投资详情 =====")
    for rec in plan.recommendations:
        asset_code = rec.asset.code
        market_score = calculator.market_score_calculator.calculate_market_score(market_data[asset_code])
        
        print(f"\n{asset_code} 投资详情:")
        print(f"  评分: {market_score['total_score']:.2f}")
        print(f"  评分组成: 估值={market_score['valuation_score']:.2f}, "
              f"趋势={market_score['trend_score']:.2f}, "
              f"波动={market_score['volatility_score']:.2f}, "
              f"特殊事件={market_score['special_event_score']:.2f}")
        print(f"  投资状态: {rec.special_condition}")
        print(f"  投资频率: {rec.recommended_frequency}")
        print(f"  频率系数: {rec.frequency_factor:.2f}")
        print(f"  月度投资金额: {rec.monthly_amount:.2f} 元 ({rec.monthly_amount/plan.total_monthly_amount*100:.1f}%)")
        print(f"  单次投资金额: {rec.single_amount:.2f} 元")
        print(f"  投资日期: {', '.join(rec.investment_dates)}")

if __name__ == "__main__":
    test_investment_calculator() 