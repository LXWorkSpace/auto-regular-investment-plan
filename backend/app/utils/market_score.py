from typing import Dict, Optional, List, Tuple
import logging
from datetime import datetime, timedelta
import numpy as np
from ..models.base_models import MarketData

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MarketScoreCalculator:
    """市场评分计算器 - 实现市场波动捕捉法策略"""
    
    def __init__(self):
        """初始化市场评分计算器"""
        # 增加历史价格记录，用于计算累计下跌
        self.historical_prices = {}
        # 基准评分，用于调整起点
        self.base_score = 45  # 将基准分从隐含的35-40提高到45分，与模拟数据一致
        
    def calculate_market_score(self, market_data: MarketData) -> Dict:
        """计算市场评分 (0-100分)
        
        Args:
            market_data: 市场数据对象
            
        Returns:
            Dict: 包含评分详情的字典
        """
        if market_data is None:
            logger.warning("市场数据对象为空，返回默认评分")
            return self._get_default_score_result()
        
        try:
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
            
            # 初始化评分组件
            valuation_score = self._calculate_valuation_score(market_data, cumulative_drawdown)
            trend_score = self._calculate_trend_score(market_data, cumulative_drawdown)
            volatility_score = self._calculate_volatility_score(market_data)
            special_event_score = self._calculate_special_event_score(market_data, cumulative_drawdown)
            
            # 计算总评分 (0-100)
            total_score = valuation_score + trend_score + volatility_score + special_event_score
            
            # 限制评分范围
            total_score = max(0, min(total_score, 100))
            
            # 记录每个资产的得分
            logger.info(f"资产 {market_data.code} 评分: 总分={total_score}, 估值={valuation_score}, 趋势={trend_score}, 波动={volatility_score}, 特殊事件={special_event_score}")
            
            # 调整评分组件，使得四个组件的整数之和等于总评分的整数值
            # 这样在前端取整显示时就不会有不一致问题
            component_sum = int(valuation_score) + int(trend_score) + int(volatility_score) + int(special_event_score)
            total_int = int(total_score)
            
            # 记录调整前的评分情况，用于调试
            logger.info(f"调整前评分整数值: 总分整数={total_int}, 组件整数和={component_sum}, 各组件整数=[{int(valuation_score)}, {int(trend_score)}, {int(volatility_score)}, {int(special_event_score)}]")
            
            # 如果组件之和与总分的整数部分不一致，进行调整
            if component_sum != total_int:
                # 计算差值
                diff = total_int - component_sum
                logger.info(f"评分整数不一致，差值={diff}，开始调整组件分数")
                
                # 精确计算小数部分，用于决定调整哪个组件
                val_frac = valuation_score - int(valuation_score)
                trend_frac = trend_score - int(trend_score)
                vol_frac = volatility_score - int(volatility_score)
                special_frac = special_event_score - int(special_event_score)
                
                # 记录各组件小数部分，用于调试
                logger.info(f"各组件小数部分: 估值={val_frac:.2f}, 趋势={trend_frac:.2f}, 波动={vol_frac:.2f}, 特殊={special_frac:.2f}")
                
                # 根据差值大小选择要调整的组件
                old_val = valuation_score
                old_trend = trend_score
                old_vol = volatility_score
                old_special = special_event_score
                
                if diff > 0:  # 需要增加某个组件的分数
                    # 优先调整小数部分接近0.5的组件（向上取整影响最小）
                    fracs = [
                        (abs(0.5 - special_frac), 0, special_event_score),
                        (abs(0.5 - vol_frac), 1, volatility_score),
                        (abs(0.5 - trend_frac), 2, trend_score),
                        (abs(0.5 - val_frac), 3, valuation_score)
                    ]
                    fracs.sort()  # 按照与0.5的差异从小到大排序
                    
                    for _, component_idx, _ in fracs:
                        if component_idx == 0 and special_frac < 0.5:
                            special_event_score = int(special_event_score) + diff
                            logger.info(f"增加特殊事件分数 {old_special} -> {special_event_score}")
                            break
                        elif component_idx == 1 and vol_frac < 0.5:
                            volatility_score = int(volatility_score) + diff
                            logger.info(f"增加波动分数 {old_vol} -> {volatility_score}")
                            break
                        elif component_idx == 2 and trend_frac < 0.5:
                            trend_score = int(trend_score) + diff
                            logger.info(f"增加趋势分数 {old_trend} -> {trend_score}")
                            break
                        elif component_idx == 3 and val_frac < 0.5:
                            valuation_score = int(valuation_score) + diff
                            logger.info(f"增加估值分数 {old_val} -> {valuation_score}")
                            break
                    else:
                        # 如果没有合适的组件，增加波动分数（波动分数影响相对较小）
                        volatility_score = int(volatility_score) + diff
                        logger.info(f"没有合适的组件，增加波动分数 {old_vol} -> {volatility_score}")
                else:  # 需要减少某个组件的分数
                    diff = abs(diff)
                    # 优先调整小数部分接近0.5的组件（向下取整影响最小）
                    fracs = [
                        (abs(0.5 - special_frac), 0, special_event_score),
                        (abs(0.5 - vol_frac), 1, volatility_score),
                        (abs(0.5 - trend_frac), 2, trend_score),
                        (abs(0.5 - val_frac), 3, valuation_score)
                    ]
                    fracs.sort()  # 按照与0.5的差异从小到大排序
                    
                    for _, component_idx, component_val in fracs:
                        if component_idx == 0 and special_frac >= 0.5 and int(special_event_score) >= diff:
                            special_event_score = int(special_event_score) - diff
                            logger.info(f"减少特殊事件分数 {old_special} -> {special_event_score}")
                            break
                        elif component_idx == 1 and vol_frac >= 0.5 and int(volatility_score) >= diff:
                            volatility_score = int(volatility_score) - diff
                            logger.info(f"减少波动分数 {old_vol} -> {volatility_score}")
                            break
                        elif component_idx == 2 and trend_frac >= 0.5 and int(trend_score) >= diff:
                            trend_score = int(trend_score) - diff
                            logger.info(f"减少趋势分数 {old_trend} -> {trend_score}")
                            break
                        elif component_idx == 3 and val_frac >= 0.5 and int(valuation_score) >= diff:
                            valuation_score = int(valuation_score) - diff
                            logger.info(f"减少估值分数 {old_val} -> {valuation_score}")
                            break
                    else:
                        # 如果没有合适的组件，减少最大的一个组件
                        candidates = [(special_event_score, 0), (volatility_score, 1), 
                                     (trend_score, 2), (valuation_score, 3)]
                        candidates.sort(reverse=True)  # 按分数从大到小排序
                        
                        for _, component_idx in candidates:
                            if component_idx == 0 and int(special_event_score) >= diff:
                                special_event_score = int(special_event_score) - diff
                                logger.info(f"减少最大分数组件-特殊事件 {old_special} -> {special_event_score}")
                                break
                            elif component_idx == 1 and int(volatility_score) >= diff:
                                volatility_score = int(volatility_score) - diff
                                logger.info(f"减少最大分数组件-波动 {old_vol} -> {volatility_score}")
                                break
                            elif component_idx == 2 and int(trend_score) >= diff:
                                trend_score = int(trend_score) - diff
                                logger.info(f"减少最大分数组件-趋势 {old_trend} -> {trend_score}")
                                break
                            elif component_idx == 3 and int(valuation_score) >= diff:
                                valuation_score = int(valuation_score) - diff
                                logger.info(f"减少最大分数组件-估值 {old_val} -> {valuation_score}")
                                break
                
                # 确保调整后的分数不小于0
                special_event_score = max(0, special_event_score)
                volatility_score = max(0, volatility_score)
                trend_score = max(0, trend_score)
                valuation_score = max(0, valuation_score)
                
                # 再次检查调整后的整数和
                adjusted_sum = int(valuation_score) + int(trend_score) + int(volatility_score) + int(special_event_score)
                logger.info(f"调整后评分整数值: 总分整数={total_int}, 组件整数和={adjusted_sum}, 各组件整数=[{int(valuation_score)}, {int(trend_score)}, {int(volatility_score)}, {int(special_event_score)}]")
                
                if adjusted_sum != total_int:
                    logger.warning(f"调整后评分整数和仍不匹配总分整数部分: {adjusted_sum} != {total_int}")
                
                logger.info(f"已调整资产 {market_data.code} 评分组件: 总分={total_score}, 调整后: 估值={valuation_score}, 趋势={trend_score}, 波动={volatility_score}, 特殊事件={special_event_score}")
            
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
                    "cumulative_drawdown": cumulative_drawdown  # 新增累计下跌指标
                }
            }
        except Exception as e:
            logger.error(f"计算市场评分出错: {str(e)}, 资产代码: {market_data.code if hasattr(market_data, 'code') else 'unknown'}")
            # 发生错误时返回默认评分结果
            return self._get_default_score_result()
    
    def _calculate_cumulative_drawdown(self, code: str) -> Optional[float]:
        """计算从观察期内最高点的累计下跌幅度"""
        if code not in self.historical_prices or len(self.historical_prices[code]) < 2:
            return None
        
        prices = self.historical_prices[code]
        max_price = max(prices[:-1])  # 除当前价格外的最高价
        current_price = prices[-1]
        
        return (current_price / max_price) - 1.0
    
    def _get_default_score_result(self) -> Dict:
        """获取默认评分结果"""
        return {
            "total_score": self.base_score,  # 使用基准分45
            "valuation_score": 15,
            "trend_score": 15,
            "volatility_score": 10,
            "special_event_score": 5,
            "is_default": True,
            "score_components": {}
        }
    
    def _get_price_position(self, market_data: MarketData) -> Optional[float]:
        """计算价格在52周范围内的位置"""
        if (market_data.price is None or 
            market_data.w52_high is None or 
            market_data.w52_low is None or 
            market_data.w52_high <= market_data.w52_low):
            return None
        
        return (market_data.price - market_data.w52_low) / (market_data.w52_high - market_data.w52_low)
    
    def _calculate_valuation_score(self, market_data: MarketData, cumulative_drawdown: Optional[float] = None) -> float:
        """计算估值得分 (0-30分)
        
        Args:
            market_data: 市场数据
            cumulative_drawdown: 累计下跌幅度
            
        Returns:
            float: 估值得分
        """
        # 初始分数 - 调整为中性起点
        score = 15  # 从15分开始，代表中性估值
        
        # 基于价格位置计算分数 - 降低权重
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
                score -= 5  # 修改为与测试脚本一致的值
            elif price_position > 0.7:  # 较高位置
                score -= 4  # 修改为与测试脚本一致的值
            elif price_position > 0.6:  # 高位置
                score -= 3  # 修改为与测试脚本一致的值
        
        # 新增：基于累计下跌幅度加分，使系统对下跌更敏感
        if cumulative_drawdown is not None:
            if cumulative_drawdown < -0.07:  # 7%以上的累计下跌（与测试脚本保持一致）
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
                score += 10  # 修改为与测试脚本一致
            elif market_data.deviation_percentage < -0.05:  # 较低于均线
                score += 7  # 修改为与测试脚本一致
            elif market_data.deviation_percentage < -0.03:  # 略低于均线
                score += 4  # 修改为与测试脚本一致
            elif market_data.deviation_percentage > 0.08:  # 显著高于均线
                score += 0  # 不加分，与测试脚本保持一致
            elif market_data.deviation_percentage > 0.05:  # 较高于均线
                score += 2  # 添加测试脚本中的加分逻辑
            elif market_data.deviation_percentage > 0.03:  # 略高于均线
                score += 4  # 添加测试脚本中的加分逻辑
            else:
                score += 6  # 接近均线，适度加分，与测试脚本保持一致
        
        # 限制分数范围
        return max(0, min(score, 30))
    
    def _calculate_trend_score(self, market_data: MarketData, cumulative_drawdown: Optional[float] = None) -> float:
        """计算趋势得分 (0-30分)
        
        Args:
            market_data: 市场数据
            cumulative_drawdown: 累计下跌幅度
            
        Returns:
            float: 趋势得分
        """
        # 初始分数 - 调整为中性起点
        score = 15  # 从15分开始，代表中性趋势
        
        # 多周期均线系统 - 修改为与测试脚本一致的逻辑
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
                score += 12  # 大幅提高接近超卖的加分
            elif market_data.rsi_14 <= 40:  # 偏低RSI
                score += 8   # 大幅提高对偏低RSI的敏感度
            else:
                # 非线性计算，使中等RSI也有合理得分 - 添加测试脚本中的逻辑
                rsi_score = max(0, (60 - market_data.rsi_14) / 20 * 7)  # 优化计算公式
                score += rsi_score
        
        # 新增：基于累计下跌的趋势加分 - 调整为与测试脚本一致的阈值
        if cumulative_drawdown is not None:
            if cumulative_drawdown < -0.06:  # 6%以上的累计下跌
                score += 10  # 大幅加分
            elif cumulative_drawdown < -0.04:  # 4%以上的累计下跌
                score += 6
            elif cumulative_drawdown < -0.02:  # 2%以上的累计下跌
                score += 3
        
        # 限制分数范围
        return max(0, min(score, 30))
    
    def _calculate_volatility_score(self, market_data: MarketData) -> float:
        """计算波动性得分 (0-20分)"""
        # 初始分数 - 调整为中性起点
        score = 10  # 从10分开始，代表中性波动
        
        # 基于ATR百分位数调整分数
        if market_data.atr_percentile is not None:
            if market_data.atr_percentile > 0.9:  # 极高波动
                score += 10  # 逆向思维，高波动通常是机会
            elif market_data.atr_percentile > 0.8:
                score += 8
            elif market_data.atr_percentile > 0.7:
                score += 6
            elif market_data.atr_percentile > 0.6:
                score += 4
            elif market_data.atr_percentile > 0.5:
                score += 2
            elif market_data.atr_percentile < 0.3:  # 低波动
                score -= 3  # 低波动通常缺乏机会
        
        # 基于ATR比值调整（备选方案）
        elif market_data.atr_20 is not None and market_data.atr_baseline is not None:
            volatility_ratio = market_data.atr_20 / market_data.atr_baseline
            if volatility_ratio > 2.0:  # 剧烈波动
                score += 10
            elif volatility_ratio > 1.5:  # 显著波动
                score += 7
            elif volatility_ratio > 1.2:  # 增加波动
                score += 4
            elif volatility_ratio < 0.8:  # 低于基准波动
                score -= 2
        
        # 限制分数范围
        return max(0, min(score, 20))
    
    def _calculate_special_event_score(self, market_data: MarketData, cumulative_drawdown: Optional[float] = None) -> float:
        """计算特殊事件得分 (0-20分)
        
        Args:
            market_data: 市场数据
            cumulative_drawdown: 累计下跌幅度
            
        Returns:
            float: 特殊事件得分
        """
        # 初始分数
        score = 0  # 特殊事件从0开始计算
        
        # 检查近期回撤 - 大幅提高敏感度
        if market_data.recent_drawdown is not None:
            if market_data.recent_drawdown < -0.08:  # 8%以上的回撤（与测试脚本一致）
                score += 15  # 改为15分，与测试脚本一致
            elif market_data.recent_drawdown < -0.06:  # 6%以上的回撤（与测试脚本一致）
                score += 12  # 改为12分，与测试脚本一致
            elif market_data.recent_drawdown < -0.04:  # 4%以上的回撤（与测试脚本一致）
                score += 8   # 改为8分，与测试脚本一致
            elif market_data.recent_drawdown < -0.02:  # 2%以上的回撤（与测试脚本一致）
                score += 4   # 改为4分，与测试脚本一致
        
        # 新增：基于累计下跌额外加分，对连续下跌更敏感 - 与测试脚本保持一致
        if cumulative_drawdown is not None:
            if cumulative_drawdown < -0.07:  # 7%以上的累计下跌
                score += 5  # 额外奖励下跌持久性
            elif cumulative_drawdown < -0.05:  # 5%以上的累计下跌
                score += 3
            elif cumulative_drawdown < -0.03:  # 3%以上的累计下跌
                score += 2  # 添加测试脚本中的逻辑
        
        # 成交量分析 - 调整为与测试脚本一致的阈值
        if market_data.volume_surge is not None:
            if market_data.volume_surge > 2.0:  # 成交量剧增（与测试脚本一致）
                # 成交量剧增，可能是恐慌性抛盘或重要突破
                if market_data.recent_drawdown is not None and market_data.recent_drawdown < 0:
                    # 下跌+放量，可能是抛售底部
                    score += min(5, int(market_data.volume_surge * 2))  # 与测试脚本一致
            elif market_data.volume_surge > 1.5:  # 成交量明显放大
                if market_data.recent_drawdown is not None and market_data.recent_drawdown < 0:
                    score += min(3, int(market_data.volume_surge))  # 与测试脚本一致
        
        # 限制分数范围
        return max(0, min(score, 20))
        
    def determine_investment_strategy(self, market_score: float) -> Dict:
        """根据市场评分确定投资策略
        
        Args:
            market_score: 市场评分 (0-100)
            
        Returns:
            Dict: 投资策略详情
        """
        # 初始化策略结果
        strategy = {
            "score": market_score,
            "score_level": "",
            "frequency": "",
            "amount_factor": 1.0,
            "description": ""
        }
        
        # 根据评分确定投资策略 - 修改为与测试脚本一致的阈值
        if market_score >= 75:  # 将80改为75，与测试脚本一致
            # 极度超跌区间 (75-100)
            strategy["score_level"] = "极度超跌"
            strategy["frequency"] = "daily"  # 改为每日投资
            strategy["amount_factor"] = 1.5  # 保持150%不变
            strategy["description"] = "市场极度超跌，建议每日投资，单次投入金额为标准投资金额的150%"
            
        elif market_score >= 65:
            # 价值区间 (65-74)
            strategy["score_level"] = "价值区间"
            strategy["frequency"] = "weekly"
            strategy["amount_factor"] = 1.2  # 调整为120%，与模拟一致
            strategy["description"] = "市场处于价值区间，建议每周投资1次，单次投入金额为标准投资金额的120%"
            
        elif market_score >= 55:  # 将50改为55，与测试脚本一致
            # 接近价值区间 (55-64)
            strategy["score_level"] = "中性偏强"
            strategy["frequency"] = "biweekly"
            strategy["amount_factor"] = 1.1  # 略高于标准额度
            strategy["description"] = "市场接近价值区间，建议每两周投资1次，单次投入金额为标准投资金额的110%"
            
        elif market_score >= 40:
            # 中性区间 (40-49)
            strategy["score_level"] = "中性市场"
            strategy["frequency"] = "biweekly"
            strategy["amount_factor"] = 1.0
            strategy["description"] = "市场处于中性区间，建议每两周投资1次，维持标准投资金额"
            
        elif market_score >= 20:
            # 高估区间 (20-39)
            strategy["score_level"] = "高估区间"
            strategy["frequency"] = "monthly"
            strategy["amount_factor"] = 0.8
            strategy["description"] = "市场处于高估区间，建议每月投资1次，单次投入金额为标准投资金额的80%"
            
        else:
            # 极度泡沫区间 (0-19)
            strategy["score_level"] = "极度泡沫"
            strategy["frequency"] = "monthly"
            strategy["amount_factor"] = 0.5
            strategy["description"] = "市场处于极度泡沫区间，建议每月投资1次或暂停投资，投入金额为标准投资金额的50%"
            
        return strategy 