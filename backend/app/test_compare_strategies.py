import sys
import os
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
from tabulate import tabulate

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.app.utils.market_data import MarketDataFetcher
from backend.app.utils.market_score import MarketScoreCalculator
from backend.app.models.base_models import MarketData

class UserStrategy:
    """用户提出的市场波动捕捉法策略"""
    
    def __init__(self):
        """初始化用户策略"""
        # 增加历史价格记录，用于计算累计下跌
        self.historical_prices = {}
        # 基准评分，设置为中性起点
        self.base_score = 45  # 调整为模拟数据的中性评分起点
    
    def calculate_market_score(self, market_data):
        """计算市场评分 (0-100分)
        
        Args:
            market_data: 市场数据对象
            
        Returns:
            Dict: 包含评分详情的字典
        """
        # 更新历史价格
        if market_data.code not in self.historical_prices:
            self.historical_prices[market_data.code] = []
        
        # 最多保留20个历史价格点
        if len(self.historical_prices[market_data.code]) >= 20:
            self.historical_prices[market_data.code].pop(0)
        
        if market_data.price is not None:
            self.historical_prices[market_data.code].append(market_data.price)
        
        # 计算累计下跌百分比（从历史最高点）
        cumulative_drawdown = self._calculate_cumulative_drawdown(market_data.code)
        
        # 1. 估值指标（30%权重）
        valuation_score = self._calculate_valuation_score(market_data, cumulative_drawdown)
        
        # 2. 趋势指标（30%权重）
        trend_score = self._calculate_trend_score(market_data, cumulative_drawdown)
        
        # 3. 波动率指标（20%权重）
        volatility_score = self._calculate_volatility_score(market_data)
        
        # 4. 特殊事件指标（20%权重）
        special_event_score = self._calculate_special_event_score(market_data, cumulative_drawdown)
        
        # 计算总评分 (0-100)
        total_score = valuation_score + trend_score + volatility_score + special_event_score
        total_score = max(0, min(total_score, 100))
        
        return {
            "total_score": total_score,
            "valuation_score": valuation_score,
            "trend_score": trend_score,
            "volatility_score": volatility_score,
            "special_event_score": special_event_score,
            "score_components": {
                "price_position": self._get_price_position(market_data),
                "ma_deviation": market_data.deviation_percentage,
                "rsi_14": market_data.rsi_14,
                "recent_drawdown": market_data.recent_drawdown,
                "cumulative_drawdown": cumulative_drawdown
            }
        }
    
    def _calculate_cumulative_drawdown(self, code: str):
        """计算从观察期内最高点的累计下跌幅度"""
        if code not in self.historical_prices or len(self.historical_prices[code]) < 2:
            return None
        
        prices = self.historical_prices[code]
        max_price = max(prices[:-1])  # 除当前价格外的最高价
        current_price = prices[-1]
        
        return (current_price / max_price) - 1.0
    
    def _get_price_position(self, market_data):
        """计算价格在52周范围内的位置"""
        if (market_data.price is None or 
            market_data.w52_high is None or 
            market_data.w52_low is None or 
            market_data.w52_high <= market_data.w52_low):
            return None
        
        return (market_data.price - market_data.w52_low) / (market_data.w52_high - market_data.w52_low)
    
    def _calculate_valuation_score(self, market_data, cumulative_drawdown=None):
        """计算估值得分 (0-30分)"""
        # 基准分数 - 调整为中性起点
        score = 15  # 从15分开始，代表中性估值
        
        # 价格位置估值 - 降低权重
        price_position = self._get_price_position(market_data)
        if price_position is not None:
            # 非线性计算，低估值区域加分更多
            if price_position < 0.2:  # 极低位置
                score += 10
            elif price_position < 0.3:  # 较低位置
                score += 8
            elif price_position < 0.4:  # 低位置
                score += 5
            elif price_position > 0.8:  # 极高位置
                score -= 5
            elif price_position > 0.7:  # 较高位置
                score -= 4
            elif price_position > 0.6:  # 高位置
                score -= 3
        
        # 新增：基于累计下跌幅度加分，使策略对下跌更敏感
        if cumulative_drawdown is not None:
            if cumulative_drawdown < -0.07:  # 7%以上的累计下跌
                score += 15  # 给满分
            elif cumulative_drawdown < -0.05:  # 5%以上的累计下跌
                score += 12
            elif cumulative_drawdown < -0.03:  # 3%以上的累计下跌
                score += 8  # 大幅提高对小幅下跌的敏感度
            elif cumulative_drawdown < -0.02:  # 2%以上的累计下跌
                score += 5
        
        # 相对历史位置 - 均线偏离度
        if market_data.deviation_percentage is not None:
            if market_data.deviation_percentage < -0.08:  # 显著低于均线
                score += 10
            elif market_data.deviation_percentage < -0.05:  # 较低于均线
                score += 7
            elif market_data.deviation_percentage < -0.03:  # 略低于均线
                score += 4
            elif market_data.deviation_percentage > 0.08:  # 显著高于均线
                score += 0  # 不加分
            elif market_data.deviation_percentage > 0.05:  # 较高于均线
                score += 2
            elif market_data.deviation_percentage > 0.03:  # 略高于均线
                score += 4
            else:
                score += 6  # 接近均线，适度加分
        
        return min(30, max(0, score))
    
    def _calculate_trend_score(self, market_data, cumulative_drawdown=None):
        """计算趋势得分 (0-30分)"""
        # 基准分数 - 调整为中性起点
        score = 15  # 从15分开始，代表中性趋势
        
        # 多周期均线系统
        if (market_data.ma_20 is not None and 
            market_data.ma_50 is not None and 
            market_data.ma_200 is not None):
            
            # 均线排列 - 降低权重
            if market_data.price > market_data.ma_20 > market_data.ma_50 > market_data.ma_200:
                # 强势多头排列
                score += 2
            elif market_data.price < market_data.ma_20 < market_data.ma_50 < market_data.ma_200:
                # 强势空头排列（逆向思维加分）
                score += 5
            elif market_data.price > market_data.ma_20 and market_data.ma_20 > market_data.ma_50:
                # 中度多头
                score += 3
            elif market_data.price < market_data.ma_20 and market_data.ma_20 < market_data.ma_50:
                # 中度空头（逆向思维加分）
                score += 4
        
        # RSI超买超卖 - 增强敏感度
        if market_data.rsi_14 is not None:
            if market_data.rsi_14 <= 30:  # 极度超卖
                score += 15  # 满分
            elif market_data.rsi_14 <= 35:  # 接近超卖
                score += 12  # 大幅提高对接近超卖的敏感度
            elif market_data.rsi_14 <= 40:  # 偏低RSI
                score += 8   # 大幅提高对偏低RSI的敏感度
            else:
                # 非线性计算，使中等RSI也有合理得分
                rsi_score = max(0, (60 - market_data.rsi_14) / 20 * 7)  # 优化计算公式
                score += rsi_score
        
        # 新增：基于累计下跌的趋势评分
        if cumulative_drawdown is not None:
            if cumulative_drawdown < -0.06:  # 6%以上的累计下跌
                score += 10  # 大幅加分
            elif cumulative_drawdown < -0.04:  # 4%以上的累计下跌
                score += 6
            elif cumulative_drawdown < -0.02:  # 2%以上的累计下跌
                score += 3
        
        return min(30, max(0, score))
    
    def _calculate_volatility_score(self, market_data):
        """计算波动率得分 (0-20分)"""
        # 基准分数
        score = 10  # 从10分开始，代表中性波动
        
        # 波动率锥 - 提高敏感度
        if market_data.atr_percentile is not None:
            if market_data.atr_percentile > 0.9:  # 极高波动
                score += 10  # 满分
            elif market_data.atr_percentile > 0.8:
                score += 8
            elif market_data.atr_percentile > 0.7:
                score += 6
            elif market_data.atr_percentile > 0.6:
                score += 4
            elif market_data.atr_percentile > 0.5:
                score += 2
            elif market_data.atr_percentile < 0.3:  # 低波动
                score -= 2
        
        # 布林带宽度（简化，使用ATR与价格比值） - 提高敏感度
        if market_data.atr_20 is not None and market_data.price is not None and market_data.price > 0:
            atr_price_ratio = market_data.atr_20 / market_data.price
            if atr_price_ratio > 0.025:  # 降低阈值，使中等波动也能得高分
                score += 10
            elif atr_price_ratio > 0.015:
                score += 7
            elif atr_price_ratio > 0.01:
                score += 4
            else:
                score += 2
        
        return min(20, max(0, score))
    
    def _calculate_special_event_score(self, market_data, cumulative_drawdown=None):
        """计算特殊事件得分 (0-20分)"""
        # 基准分数
        score = 0  # 特殊事件从0开始计算
        
        # 短期急跌识别 - 大幅降低阈值
        if market_data.recent_drawdown is not None:
            if market_data.recent_drawdown < -0.08:  # 8%以上的大跌（原来是-0.2）
                score += 15  # 接近满分
            elif market_data.recent_drawdown < -0.06:  # 6%以上的回撤（原来是-0.15）
                score += 12
            elif market_data.recent_drawdown < -0.04:  # 4%以上的回撤（原来是-0.1）
                score += 8
            elif market_data.recent_drawdown < -0.02:  # 2%以上的回撤（原来是-0.05）
                score += 4
        
        # 新增：基于累积下跌的额外加分
        if cumulative_drawdown is not None:
            if cumulative_drawdown < -0.07:  # 7%以上的累计下跌
                score += 5  # 额外加分
            elif cumulative_drawdown < -0.05:  # 5%以上的累计下跌
                score += 3
            elif cumulative_drawdown < -0.03:  # 3%以上的累计下跌
                score += 2
        
        # 成交量异常 - 提高敏感度
        if market_data.volume_surge is not None:
            if market_data.volume_surge > 2.0:  # 成交量是平均值的2倍以上（原来是3倍）
                if market_data.recent_drawdown is not None and market_data.recent_drawdown < 0:
                    score += min(5, int(market_data.volume_surge * 2))  # 下跌+放量，可能是抛售底部
            elif market_data.volume_surge > 1.5:  # 成交量是平均值的1.5倍以上
                if market_data.recent_drawdown is not None and market_data.recent_drawdown < 0:
                    score += min(3, int(market_data.volume_surge))
        
        return min(20, max(0, score))

    def determine_investment_strategy(self, market_score):
        """根据市场评分确定投资策略"""
        # 初始化策略结果
        strategy = {
            "score": market_score,
            "score_level": "",
            "frequency": "",
            "amount_factor": 1.0,
            "description": ""
        }
        
        # 根据评分确定投资策略 - 调整阈值以匹配模拟数据
        if market_score >= 75:
            # 极度超跌区间 (75-100) - 降低阈值，原来是80
            strategy["score_level"] = "极度超跌"
            strategy["frequency"] = "daily"  # 改为与系统一致的英文标识
            strategy["amount_factor"] = 1.5  # 150%
            strategy["description"] = "市场极度超跌，每周投资2次，单次为标准额度的150%"
            
        elif market_score >= 65:
            # 价值区间 (65-74)
            strategy["score_level"] = "价值区间"
            strategy["frequency"] = "weekly"  # 改为与系统一致的英文标识
            strategy["amount_factor"] = 1.2  # 120%
            strategy["description"] = "市场处于价值区间，每周投资1次，单次为标准额度的120%"
            
        elif market_score >= 55:
            # 接近价值区间 (55-64) - 新增区间，匹配模拟数据
            strategy["score_level"] = "中性偏强"
            strategy["frequency"] = "biweekly"  # 改为与系统一致的英文标识
            strategy["amount_factor"] = 1.1  # 110%
            strategy["description"] = "市场接近价值区间，每两周投资1次，单次为标准额度的110%"
            
        elif market_score >= 40:
            # 中性区间 (40-54)
            strategy["score_level"] = "中性市场"
            strategy["frequency"] = "biweekly"  # 改为与系统一致的英文标识
            strategy["amount_factor"] = 1.0
            strategy["description"] = "市场处于中性区间，每两周投资1次，维持标准投资金额"
            
        elif market_score >= 20:
            # 高估区间 (20-39)
            strategy["score_level"] = "高估区间"
            strategy["frequency"] = "monthly"  # 改为与系统一致的英文标识
            strategy["amount_factor"] = 0.8
            strategy["description"] = "市场处于高估区间，每月投资1次，单次为标准投资金额的80%"
            
        else:
            # 极度泡沫区间 (0-19)
            strategy["score_level"] = "极度泡沫"
            strategy["frequency"] = "monthly"  # 改为与系统一致的英文标识
            strategy["amount_factor"] = 0.5
            strategy["description"] = "市场处于极度泡沫区间，每月投资1次或暂停，投入金额为标准投资金额的50%"
            
        return strategy

def test_compare_strategies():
    """比较两种策略在特定时间段的表现"""
    
    print("开始比较两种策略的表现...")
    
    # 创建策略对象
    system_strategy = MarketScoreCalculator()
    user_strategy = UserStrategy()
    
    # 创建市场数据获取器
    market_fetcher = MarketDataFetcher()
    
    # 测试资产列表
    assets = ["SPY", "QQQ"]
    
    # 测试日期范围
    start_date = datetime(2025, 2, 20)
    end_date = datetime(2025, 3, 15)
    
    # 创建日期列表
    date_list = []
    current_date = start_date
    while current_date <= end_date:
        if current_date.weekday() < 5:  # 只考虑工作日
            date_list.append(current_date.strftime('%Y-%m-%d'))
        current_date += timedelta(days=1)
    
    # 准备结果数据
    results = []
    
    print(f"分析时间段: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
    
    # 获取整个时间段的历史数据
    historical_data = {}
    for asset in assets:
        print(f"获取 {asset} 的历史数据...")
        # 获取更长时间的数据以计算技术指标
        ticker = yf.Ticker(asset)
        hist_start = start_date - timedelta(days=252)  # 获取前一年的数据用于计算指标
        df = ticker.history(start=hist_start.strftime('%Y-%m-%d'), end=(end_date + timedelta(days=1)).strftime('%Y-%m-%d'))
        historical_data[asset] = df
    
    # 逐日计算评分
    for date in date_list:
        print(f"分析日期: {date}")
        
        for asset in assets:
            # 获取该日期之前的数据
            current_date = datetime.strptime(date, '%Y-%m-%d')
            df = historical_data[asset].loc[:date]
            
            if df.empty:
                print(f"  {asset}: 无数据")
                continue
            
            # 创建市场数据对象
            price = df['Close'].iloc[-1]
            w52_high = df['High'].iloc[-252:].max() if len(df) >= 252 else df['High'].max()
            w52_low = df['Low'].iloc[-252:].min() if len(df) >= 252 else df['Low'].min()
            
            # 计算均线
            ma_20 = df['Close'].rolling(window=20).mean().iloc[-1] if len(df) >= 20 else None
            ma_50 = df['Close'].rolling(window=50).mean().iloc[-1] if len(df) >= 50 else None
            ma_200 = df['Close'].rolling(window=200).mean().iloc[-1] if len(df) >= 200 else None
            
            # 计算均线偏离度
            deviation_percentage = ((price / ma_200) - 1) if ma_200 is not None else None
            
            # 计算ATR
            df_atr = df.copy()
            df_atr['H-L'] = df_atr['High'] - df_atr['Low']
            df_atr['H-PC'] = abs(df_atr['High'] - df_atr['Close'].shift(1))
            df_atr['L-PC'] = abs(df_atr['Low'] - df_atr['Close'].shift(1))
            df_atr['TR'] = df_atr[['H-L', 'H-PC', 'L-PC']].max(axis=1)
            atr_20 = df_atr['TR'].rolling(window=20).mean().iloc[-1] if len(df_atr) >= 20 else None
            
            # ATR百分位
            if len(df_atr) >= 252 and atr_20 is not None:
                atr_history = df_atr['TR'].rolling(window=20).mean().iloc[-252:]
                atr_percentile = (atr_history < atr_20).mean()
            else:
                atr_percentile = None
            
            # 计算RSI
            delta = df['Close'].diff()
            gain = delta.copy()
            loss = delta.copy()
            gain[gain < 0] = 0
            loss[loss > 0] = 0
            loss = abs(loss)
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            rs = avg_gain / avg_loss
            rsi_14 = 100 - (100 / (1 + rs.iloc[-1])) if len(df) >= 14 else None
            
            # 计算近期回撤
            if len(df) >= 20:
                recent_high = df['Close'].iloc[-20:].max()
                recent_drawdown = (price / recent_high) - 1
            else:
                recent_drawdown = None
            
            # 计算成交量异常
            if len(df) >= 20:
                avg_volume = df['Volume'].iloc[-20:].mean()
                current_volume = df['Volume'].iloc[-1]
                volume_surge = current_volume / avg_volume if avg_volume > 0 else None
            else:
                volume_surge = None
            
            # 创建MarketData对象
            market_data = MarketData(
                code=asset,
                name=asset,
                price=price,
                updated_at=date,
                w52_high=w52_high,
                w52_low=w52_low,
                ma_20=ma_20,
                ma_50=ma_50,
                ma_200=ma_200,
                ma_cross=0,  # 简化处理，不计算均线交叉
                deviation_percentage=deviation_percentage,
                atr_20=atr_20,
                atr_baseline=atr_20 * 0.8 if atr_20 is not None else None,  # 简化处理
                atr_percentile=atr_percentile,
                rsi_14=rsi_14,
                recent_drawdown=recent_drawdown,
                volume_surge=volume_surge
            )
            
            # 计算系统策略评分
            system_score_result = system_strategy.calculate_market_score(market_data)
            system_strategy_result = system_strategy.determine_investment_strategy(system_score_result['total_score'])
            
            # 计算用户策略评分
            user_score_result = user_strategy.calculate_market_score(market_data)
            user_strategy_result = user_strategy.determine_investment_strategy(user_score_result['total_score'])
            
            # 对3月3日的数据进行特殊处理，打印详细信息
            if date == '2025-03-03':
                print(f"\n===== 3月3日 {asset} 详细评分数据 =====")
                print(f"价格: {price}")
                print(f"系统评分: {system_score_result['total_score']}")
                print(f"用户评分: {user_score_result['total_score']}")
                print(f"系统评分组成: 估值={system_score_result['valuation_score']}, 趋势={system_score_result['trend_score']}, 波动={system_score_result['volatility_score']}, 特殊事件={system_score_result['special_event_score']}")
                print(f"用户评分组成: 估值={user_score_result['valuation_score']}, 趋势={user_score_result['trend_score']}, 波动={user_score_result['volatility_score']}, 特殊事件={user_score_result['special_event_score']}")
                print(f"RSI: {rsi_14}")
                print(f"近期回撤: {recent_drawdown}")
                print(f"均线偏离度: {deviation_percentage}")
                print(f"系统投资策略: {system_strategy_result['score_level']}, 频率={system_strategy_result['frequency']}, 系数={system_strategy_result['amount_factor']}")
                print(f"用户投资策略: {user_strategy_result['score_level']}, 频率={user_strategy_result['frequency']}, 系数={user_strategy_result['amount_factor']}")
                
                # 计算投资金额（假设月度金额为10000元，平均分配给两个资产）
                monthly_asset_amount = 5000
                system_single_amount = 0
                user_single_amount = 0
                
                if system_strategy_result['frequency'] == 'daily':
                    system_single_amount = (monthly_asset_amount / 20) * system_strategy_result['amount_factor']
                elif system_strategy_result['frequency'] == 'weekly':
                    system_single_amount = (monthly_asset_amount / 4) * system_strategy_result['amount_factor']
                elif system_strategy_result['frequency'] == 'biweekly':
                    system_single_amount = (monthly_asset_amount / 2) * system_strategy_result['amount_factor']
                else:  # monthly
                    system_single_amount = monthly_asset_amount * system_strategy_result['amount_factor']
                    
                if user_strategy_result['frequency'] == 'daily':
                    user_single_amount = (monthly_asset_amount / 20) * user_strategy_result['amount_factor']
                elif user_strategy_result['frequency'] == 'weekly':
                    user_single_amount = (monthly_asset_amount / 4) * user_strategy_result['amount_factor']
                elif user_strategy_result['frequency'] == 'biweekly':
                    user_single_amount = (monthly_asset_amount / 2) * user_strategy_result['amount_factor']
                else:  # monthly
                    user_single_amount = monthly_asset_amount * user_strategy_result['amount_factor']
                
                print(f"系统单次投资金额: {system_single_amount:.2f}元")
                print(f"用户单次投资金额: {user_single_amount:.2f}元")
            
            # 保存结果
            results.append({
                'date': date,
                'asset': asset,
                'price': price,
                'system_score': system_score_result['total_score'],
                'user_score': user_score_result['total_score'],
                'system_valuation': system_score_result['valuation_score'],
                'user_valuation': user_score_result['valuation_score'],
                'system_trend': system_score_result['trend_score'],
                'user_trend': user_score_result['trend_score'],
                'system_volatility': system_score_result['volatility_score'],
                'user_volatility': user_score_result['volatility_score'],
                'system_special': system_score_result['special_event_score'],
                'user_special': user_score_result['special_event_score'],
                'system_strategy': system_strategy_result['score_level'],
                'user_strategy': user_strategy_result['score_level'],
                'system_frequency': system_strategy_result['frequency'],
                'user_frequency': user_strategy_result['frequency'],
                'system_amount': system_strategy_result['amount_factor'],
                'user_amount': user_strategy_result['amount_factor'],
                'rsi': rsi_14,
                'drawdown': recent_drawdown,
                'atr_percentile': atr_percentile
            })
    
    # 转换为DataFrame进行分析
    df_results = pd.DataFrame(results)
    
    # 定义根据投资频率计算总投资金额的函数
    def calculate_total_investment(monthly_amount, frequencies, amount_factors, work_days):
        """根据投资频率正确计算总投资金额
        
        Args:
            monthly_amount: 月度投资金额
            frequencies: 投资频率列表
            amount_factors: 金额系数列表
            work_days: 总工作日天数
            
        Returns:
            float: 总投资金额
        """
        total = 0
        for freq, factor in zip(frequencies, amount_factors):
            if freq == "daily":
                # 每日投资，假设每个交易日都投资
                single_amount = (monthly_amount / 20) * factor  # 假设一个月20个交易日
                total += single_amount * work_days
            elif freq == "weekly":
                # 每周投资，计算有多少周
                single_amount = (monthly_amount / 4) * factor  # 假设一个月4周
                weeks = work_days / 5  # 假设一周5个交易日
                total += single_amount * weeks
            elif freq == "biweekly":
                # 每两周投资，计算有多少个两周期
                single_amount = (monthly_amount / 2) * factor  # 假设一个月2个两周期
                two_week_periods = work_days / 10  # 假设两周期有10个交易日
                total += single_amount * two_week_periods
            else:  # monthly
                # 每月投资，计算有多少个月
                single_amount = monthly_amount * factor
                months = work_days / 20  # 假设一个月有20个交易日
                total += single_amount * months
        
        return total
    
    # 定义投资频率格式化函数，将英文转为易读的中文
    def format_frequency(frequency):
        """将投资频率转换为易读的中文格式
        
        Args:
            frequency: 投资频率字符串
            
        Returns:
            str: 格式化后的中文投资频率
        """
        frequency_map = {
            "daily": "每日投资",
            "weekly": "每周1次",
            "biweekly": "每两周1次",
            "monthly": "每月1次"
        }
        return frequency_map.get(frequency, frequency)
    
    # 按资产分组显示结果
    for asset in assets:
        asset_data = df_results[df_results['asset'] == asset].copy()
        
        print(f"\n====== {asset} 策略比较结果 ======")
        
        # 格式化投资频率为中文
        asset_data['system_frequency_display'] = asset_data['system_frequency'].apply(format_frequency)
        asset_data['user_frequency_display'] = asset_data['user_frequency'].apply(format_frequency)
        
        # 打印每个日期的评分和策略
        table_data = asset_data[['date', 'price', 'system_score', 'user_score', 
                                 'system_strategy', 'user_strategy',
                                 'system_frequency_display', 'user_frequency_display', 
                                 'system_amount', 'user_amount']].values
        
        headers = ['日期', '价格', '系统评分', '用户评分', 
                   '系统状态', '用户状态',
                   '系统频率', '用户频率', 
                   '系统金额系数', '用户金额系数']
        
        print(tabulate(table_data, headers=headers, tablefmt='pretty', numalign='right'))
        
        # 评分项对比
        print(f"\n{asset} 评分组成对比 (均值):")
        components = {
            '估值评分': ['system_valuation', 'user_valuation', 30],
            '趋势评分': ['system_trend', 'user_trend', 30],
            '波动率评分': ['system_volatility', 'user_volatility', 20],
            '特殊事件评分': ['system_special', 'user_special', 20],
            '总评分': ['system_score', 'user_score', 100]
        }
        
        component_data = []
        for component, cols in components.items():
            system_mean = asset_data[cols[0]].mean()
            user_mean = asset_data[cols[1]].mean()
            max_score = cols[2]
            component_data.append([
                component, 
                f"{system_mean:.2f} ({system_mean / max_score * 100:.1f}%)", 
                f"{user_mean:.2f} ({user_mean / max_score * 100:.1f}%)",
                f"{user_mean - system_mean:.2f}"
            ])
        
        print(tabulate(component_data, 
                       headers=['评分组成', '系统平均分', '用户平均分', '差异'],
                       tablefmt='pretty', numalign='right'))
        
        # 策略分布对比
        print(f"\n{asset} 策略状态分布:")
        system_strategy_counts = asset_data['system_strategy'].value_counts()
        user_strategy_counts = asset_data['user_strategy'].value_counts()
        
        # 合并两种策略的状态计数
        strategy_counts = pd.DataFrame({
            '系统策略': system_strategy_counts,
            '用户策略': user_strategy_counts
        }).fillna(0).astype(int)
        
        print(tabulate(strategy_counts.reset_index().values, 
                       headers=['市场状态', '系统策略(天数)', '用户策略(天数)'],
                       tablefmt='pretty', numalign='right'))
        
        # 计算每种策略的总投资金额（假设每月资金为10000）
        monthly_amount = 10000
        work_days = len(asset_data)  # 工作日天数
        
        # 使用新的函数计算总投资金额
        system_total = calculate_total_investment(
            monthly_amount, 
            asset_data['system_frequency'].tolist(),
            asset_data['system_amount'].tolist(),
            work_days
        )
        
        user_total = calculate_total_investment(
            monthly_amount, 
            asset_data['user_frequency'].tolist(),
            asset_data['user_amount'].tolist(),
            work_days
        )
        
        print(f"\n投资金额对比 (假设月投入 {monthly_amount}元):")
        print(f"系统策略总投入: {system_total:.2f} 元")
        print(f"用户策略总投入: {user_total:.2f} 元")
        print(f"差异: {user_total - system_total:.2f} 元 ({(user_total - system_total) / system_total * 100:.2f}%)")
    
    print("\n比较完成!")

if __name__ == "__main__":
    test_compare_strategies() 