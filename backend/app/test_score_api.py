import sys
import os
import json

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.market_score import MarketScoreCalculator
from app.models.base_models import MarketData

def test_spy_score():
    """测试SPY的市场评分计算"""
    calculator = MarketScoreCalculator()
    
    # 创建与3月3日数据相同的MarketData对象
    test_data = MarketData(
        code='SPY', 
        name='SPY', 
        price=582.0191650390625, 
        updated_at='2025-03-03', 
        w52_high=650.0, 
        w52_low=500.0, 
        ma_20=590.0, 
        ma_50=585.0, 
        ma_200=580.0, 
        ma_cross=0, 
        deviation_percentage=0.002, 
        atr_20=6.0, 
        atr_baseline=5.0, 
        atr_percentile=0.6, 
        rsi_14=32.45093122625046, 
        recent_drawdown=-0.04757471090555587, 
        volume_surge=1.2
    )
    
    # 计算市场评分
    result = calculator.calculate_market_score(test_data)
    print("\nSPY 评分结果:")
    print(json.dumps(result, indent=2))
    
    # 计算投资策略
    strategy = calculator.determine_investment_strategy(result['total_score'])
    print("\nSPY 投资策略:")
    print(json.dumps(strategy, indent=2))

def test_qqq_score():
    """测试QQQ的市场评分计算"""
    calculator = MarketScoreCalculator()
    
    # 创建与3月3日数据相同的MarketData对象
    test_data = MarketData(
        code='QQQ', 
        name='QQQ', 
        price=496.3098449707031, 
        updated_at='2025-03-03', 
        w52_high=650.0, 
        w52_low=450.0, 
        ma_20=510.0, 
        ma_50=500.0, 
        ma_200=490.0, 
        ma_cross=0, 
        deviation_percentage=0.01, 
        atr_20=7.0, 
        atr_baseline=5.5, 
        atr_percentile=0.7, 
        rsi_14=28.10720075871393, 
        recent_drawdown=-0.07871824247756765, 
        volume_surge=1.5
    )
    
    # 计算市场评分
    result = calculator.calculate_market_score(test_data)
    print("\nQQQ 评分结果:")
    print(json.dumps(result, indent=2))
    
    # 计算投资策略
    strategy = calculator.determine_investment_strategy(result['total_score'])
    print("\nQQQ 投资策略:")
    print(json.dumps(strategy, indent=2))

if __name__ == "__main__":
    test_spy_score()
    test_qqq_score() 