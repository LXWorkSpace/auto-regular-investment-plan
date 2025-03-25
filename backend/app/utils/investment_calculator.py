from typing import Dict, List, Optional, Union, Tuple
from datetime import datetime, timedelta
import math
import logging
import calendar
import numpy as np

from ..models.base_models import Asset, UserConfig, MarketData, InvestmentRecommendation, InvestmentPlan, InvestmentFrequency
from .market_score import MarketScoreCalculator

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class InvestmentCalculator:
    """投资计算工具类，实现定投策略计算"""
    
    def __init__(self):
        """初始化投资计算器"""
        self.market_score_calculator = MarketScoreCalculator()
        # 历史市场评分记录，用于追踪市场评分变化趋势
        self.historical_scores = {}
        # 资金池设置
        self.default_buffer_pool = 1000.0  # 默认资金池大小
        self.max_buffer_usage_percentage = 0.5  # 最多使用50%的资金池
    
    def analyze_market_trend(self, asset_code: str, days: int = 30) -> Dict:
        """分析特定资产的市场趋势和回调情况
        
        Args:
            asset_code: 资产代码
            days: 分析天数
            
        Returns:
            Dict: 市场趋势分析结果
        """
        result = {
            "asset_code": asset_code,
            "trend": "stable",  # rising, falling, stable
            "pullback_detected": False,
            "pullback_from_high": 0.0,
            "score_trend": "stable",  # rising, falling, stable
            "recent_scores": [],
            "investment_suggestion": ""
        }
        
        # 检查历史评分数据
        if asset_code not in self.historical_scores or len(self.historical_scores[asset_code]) < 2:
            result["investment_suggestion"] = "数据不足，无法提供趋势分析"
            return result
        
        # 获取最近的评分记录
        recent_scores = self.historical_scores[asset_code][-min(days, len(self.historical_scores[asset_code])):]
        result["recent_scores"] = recent_scores
        
        # 分析评分趋势
        if len(recent_scores) >= 3:
            last_scores = [s["score"] for s in recent_scores[-3:]]
            if last_scores[2] > last_scores[1] > last_scores[0]:
                result["score_trend"] = "rising"
                result["trend"] = "improving"
                result["investment_suggestion"] = "市场评分持续上升，表明市场状况正在改善"
            elif last_scores[2] < last_scores[1] < last_scores[0]:
                result["score_trend"] = "falling"
                result["trend"] = "deteriorating"
                result["investment_suggestion"] = "市场评分持续下降，可能表明市场状况正在恶化"
        
        # 检测评分拐点（可能是回调开始或结束）
        if len(recent_scores) >= 5:
            # 寻找最近一次明显的评分拐点
            scores = [s["score"] for s in recent_scores]
            for i in range(len(scores) - 3, 0, -1):
                # 检测下降拐点（先升后降）
                if scores[i] > scores[i-1] and scores[i] > scores[i+1]:
                    result["pullback_detected"] = True
                    result["pullback_days"] = len(scores) - i - 1
                    result["pullback_score_change"] = scores[-1] - scores[i]
                    if result["pullback_score_change"] > 10:
                        result["investment_suggestion"] = "检测到市场从高点回调，评分显著提高，可能是加仓机会"
                    break
                
                # 检测上升拐点（先降后升）
                if i > 1 and scores[i] < scores[i-1] and scores[i] < scores[i+1]:
                    result["trend"] = "recovering"
                    result["recovery_days"] = len(scores) - i - 1
                    result["recovery_score_change"] = scores[-1] - scores[i]
                    if result["recovery_score_change"] > 5:
                        result["investment_suggestion"] = "市场可能开始企稳回升，评分逐步提高"
                    break
        
        # 基于最新评分提供投资建议
        latest_score = recent_scores[-1]["score"] if recent_scores else 0
        if latest_score >= 80:
            result["market_status"] = "极度超跌"
            if not result["investment_suggestion"]:
                result["investment_suggestion"] = "市场处于极度超跌状态，建议积极加仓"
        elif latest_score >= 65:
            result["market_status"] = "价值区间"
            if not result["investment_suggestion"]:
                result["investment_suggestion"] = "市场处于价值区间，建议适度加仓"
        elif latest_score >= 40:
            result["market_status"] = "中性市场"
            if not result["investment_suggestion"]:
                result["investment_suggestion"] = "市场处于中性区间，建议常规定投"
        elif latest_score >= 20:
            result["market_status"] = "高估区间"
            if not result["investment_suggestion"]:
                result["investment_suggestion"] = "市场处于高估区间，建议减少投入"
        else:
            result["market_status"] = "极度泡沫"
            if not result["investment_suggestion"]:
                result["investment_suggestion"] = "市场处于极度泡沫状态，建议谨慎投资或暂停"
        
        return result
    
    def generate_investment_plan(self, user_config: UserConfig, 
                              market_data: Dict[str, MarketData]) -> InvestmentPlan:
        """生成投资计划
        
        Args:
            user_config: 用户配置
            market_data: 市场数据字典
            
        Returns:
            InvestmentPlan: 投资计划
        """
        # 兼容旧版本数据
        if hasattr(user_config, 'buffer_percentage') and not hasattr(user_config, 'buffer_amount'):
            # 如果是旧数据格式，将百分比转为金额
            buffer_percentage = getattr(user_config, 'buffer_percentage', 0.1)
            user_config.buffer_amount = user_config.monthly_investment * buffer_percentage
            
        total_monthly_amount = user_config.monthly_investment
        buffer_amount = user_config.buffer_amount  # 资金池作为额外资金，不从月度投资中扣除
        
        # 将全部月度投资金额作为可用资金
        available_amount = total_monthly_amount
        
        recommendations = []
        warning_messages = []
        
        # 市场评分结果
        market_scores = {}
        highest_score = 0
        market_trend_analysis = {}  # 存储市场趋势分析结果
        
        for asset in user_config.assets:
            asset_data = market_data.get(asset.code)
            # 计算市场评分
            score_result = self.market_score_calculator.calculate_market_score(asset_data)
            market_scores[asset.code] = score_result
            
            # 更新历史评分记录，用于追踪评分变化
            if asset.code not in self.historical_scores:
                self.historical_scores[asset.code] = []
            self.historical_scores[asset.code].append({
                "timestamp": datetime.now().isoformat(),
                "score": score_result.get("total_score", 40)
            })
            
            # 分析市场趋势（包括回调检测）
            trend_analysis = self.analyze_market_trend(asset.code)
            market_trend_analysis[asset.code] = trend_analysis
            
            # 如果检测到回调且评分上升，添加特别提示
            if trend_analysis.get("pullback_detected") and trend_analysis.get("score_trend") == "rising":
                warning_messages.append(f"{asset.code}: {trend_analysis.get('investment_suggestion')}")
            
            # 记录最高评分，用于资金池使用决策
            current_score = score_result.get("total_score", 0)
            if current_score > highest_score:
                highest_score = current_score
            
            # 添加警告消息
            if current_score >= 80:
                warning_messages.append(f"{asset.code}: 市场极度超跌，建议积极加仓")
            elif current_score >= 65:
                warning_messages.append(f"{asset.code}: 市场处于价值区间，建议适度加仓")
            elif current_score <= 25:
                warning_messages.append(f"{asset.code}: 市场重度高估，建议减少投入")
        
        # 资产权重调整
        adjusted_weights = self._adjust_asset_weights(user_config.assets, market_scores)
        
        # 确定是否使用资金池额外资金（在极度超跌区间或需要试探性投资时）
        additional_funding = 0
        probing_funding = 0
        
        # 确定是否使用试探性投资（在评分接近价值区间时）
        is_probing = False
        probing_asset_codes = set()  # 跟踪哪些资产需要试探性投资
        probing_percentage = 0.15  # 使用15%资金作为试探
        
        for asset in user_config.assets:
            score = market_scores.get(asset.code, {}).get("total_score", 40)
            if 60 <= score < 65:  # 接近价值区间
                is_probing = True
                probing_asset_codes.add(asset.code)
                warning_messages.append(f"{asset.code}: 评分接近价值区间，启动小额试探机制")
        
        # 计算需要的资金池金额
        if highest_score >= 80:
            # 在极度超跌区间，可以使用资金池
            additional_funding = buffer_amount * self.max_buffer_usage_percentage
            warning_messages.append(f"市场处于极度超跌状态，启用资金池额外投入 {additional_funding:.2f} 元")
        
        # 计算试探性投资资金
        probing_funding = 0
        if is_probing:
            # 试探性投资资金从资金池中取
            probing_funding = total_monthly_amount * probing_percentage
            # 确保不会使用超过50%的资金池
            probing_funding = min(probing_funding, buffer_amount * self.max_buffer_usage_percentage)
            warning_messages.append(f"启用试探性投资，从资金池中取用 {probing_funding:.2f} 元")
        
        # 计算实际可用的资金池总额
        total_buffer_usage = min(additional_funding + probing_funding, buffer_amount * self.max_buffer_usage_percentage)
        
        # 剩余可用于正常分配的资金
        remaining_amount = total_monthly_amount
        
        # 生成投资建议
        total_investment_amount = 0  # 跟踪总投资金额
        raw_recommendations = []
        
        # 第一轮：计算每个资产的基础月度投资金额
        for asset in user_config.assets:
            asset_code = asset.code
            if asset_code not in adjusted_weights:
                logger.warning(f"资产 {asset_code} 没有调整后的权重，跳过")
                continue
            
            adjusted_weight = adjusted_weights[asset_code]
            score_result = market_scores.get(asset_code, {"total_score": 40})
            score = score_result.get("total_score", 40)
            
            # 确定投资策略
            strategy = self.market_score_calculator.determine_investment_strategy(score)
            
            # 计算基础月度投资金额
            monthly_amount = remaining_amount * adjusted_weight
            
            # 处理特殊频率
            raw_frequency = strategy.get("frequency", "biweekly")
            frequency = self._convert_to_investment_frequency(raw_frequency)
            
            # 添加特殊频率标记，用于生成正确的投资日期
            if raw_frequency == "daily":
                strategy["special_frequency"] = "daily"
            
            frequency_factor = strategy.get("amount_factor", 1.0)
            
            # 如果是试探性投资资产，加上试探资金
            if asset_code in probing_asset_codes:
                # 加上试探资金，不影响基础金额分配
                monthly_amount += probing_funding
                strategy["score_level"] = "接近价值区间(试探)"
                strategy["description"] = "市场接近价值区间，启动试探性小额投资"
            
            # 生成投资日期
            investment_dates = self._get_investment_dates(frequency, 
                                                      special_frequency=strategy.get("special_frequency"))
            
            # 计算单次投资金额 - 根据频率和频率因子调整
            single_amount = self._calculate_single_amount(monthly_amount, frequency, frequency_factor)
            
            # 如果是极度超跌区间且有额外资金，增加投资金额
            if score >= 80 and additional_funding > 0:
                # 按权重分配额外资金
                extra_amount = additional_funding * adjusted_weight
                single_amount += extra_amount / 4  # 假设极度超跌区间分4批投入
            
            # 记录原始建议
            raw_rec = {
                "asset": asset,
                "score": score,
                "monthly_amount": monthly_amount,  # 原始月度分配金额
                "single_amount": single_amount,    # 单次投资金额
                "frequency": frequency,            # 投资频率
                "frequency_factor": frequency_factor,  # 频率系数
                "special_frequency": strategy.get("special_frequency"),
                "investment_dates": investment_dates,  # 投资日期
                "special_condition": strategy.get("score_level")  # 特殊市场条件
            }
            raw_recommendations.append(raw_rec)
        
        # 计算实际每月总投资额
        raw_monthly_total = sum(rec["monthly_amount"] for rec in raw_recommendations)
        
        # 计算预期总投资额（包含频率因子影响）
        expected_total_with_frequency = sum(
            rec["single_amount"] * len(rec["investment_dates"])
            for rec in raw_recommendations
        )
        
        # 确保实际总投资额等于月度预算
        adjustment_factor = 1.0  # 默认为1.0，不进行调整
        
        # 记录原始总投资额，但不进行调整
        if abs(expected_total_with_frequency - (total_monthly_amount + probing_funding)) > 0.01:
            # 仅记录日志，不进行调整
            logger.info(f"总投资额({expected_total_with_frequency:.2f})与预算({total_monthly_amount + probing_funding:.2f})不等，但不进行调整")
        
        # 第二轮：创建最终推荐（不应用预算调整因子）
        for raw_rec in raw_recommendations:
            asset = raw_rec["asset"]
            score = raw_rec["score"]
            score_result = market_scores.get(asset.code, {})
            
            # 使用原始单次投资金额，不应用调整因子
            single_amount = raw_rec["single_amount"]
            
            # 计算月度投资金额，确保与频率和单次金额一致
            frequency = raw_rec["frequency"]
            num_investments = len(raw_rec["investment_dates"])  # 一个月内的投资次数
            monthly_amount = single_amount * num_investments
            
            # 创建投资建议
            recommendation = InvestmentRecommendation(
                asset=asset,
                valuation_coefficient=score_result.get("valuation_score", 10) / 10,  # 转换为系数格式
                trend_coefficient=score_result.get("trend_score", 10) / 10,
                volatility_coefficient=score_result.get("volatility_score", 10) / 10,
                recommended_frequency=frequency,
                frequency_factor=raw_rec["frequency_factor"],
                monthly_amount=monthly_amount,  # 使用原始计算的月度金额
                single_amount=single_amount,    # 使用原始计算的单次金额
                investment_dates=raw_rec["investment_dates"],
                special_condition=raw_rec["special_condition"]
            )
            
            # 更新总投资金额
            total_investment_amount += single_amount * num_investments
            recommendations.append(recommendation)
        
        # 创建投资计划
        investment_plan = InvestmentPlan(
            total_monthly_amount=total_monthly_amount,
            effective_monthly_amount=available_amount,  # 等于total_monthly_amount
            buffer_amount=buffer_amount,  # 保留资金池金额字段，但它是额外资金
            recommendations=recommendations,
            circuit_breaker_level=0,  # 新策略不使用熔断机制
            warning_messages=warning_messages,
            actual_investment_amount=total_investment_amount,  # 添加实际总投资金额
            buffer_pool_usage=total_buffer_usage,  # 记录资金池使用情况（包括试探性投资和额外投资）
            market_trend_analysis=market_trend_analysis
        )
        
        return investment_plan
    
    def _adjust_asset_weights(self, assets: List[Asset], market_scores: Dict[str, Dict]) -> Dict[str, float]:
        """根据市场评分调整资产权重
        
        Args:
            assets: 资产列表
            market_scores: 市场评分结果
            
        Returns:
            Dict[str, float]: 调整后的资产权重，键为资产代码
        """
        # 初始化调整后的权重
        adjusted_weights = {}
        
        # 如果资产列表为空，返回空字典
        if not assets:
            logger.warning("资产列表为空，无法调整权重")
            return {}
        
        # 确保所有资产权重初始有效
        valid_assets = []
        for asset in assets:
            try:
                # 确保权重是有效数字且大于0
                if asset.weight is None or not isinstance(asset.weight, (int, float)) or asset.weight <= 0:
                    logger.warning(f"资产 {asset.code} 的权重无效: {asset.weight}, 设置为默认权重")
                    asset.weight = 1.0
                valid_assets.append(asset)
            except Exception as e:
                logger.error(f"处理资产 {asset.code if hasattr(asset, 'code') else 'unknown'} 权重时出错: {str(e)}")
                continue
        
        # 如果没有有效资产，返回空字典
        if not valid_assets:
            logger.warning("没有有效资产，无法调整权重")
            return {}
        
        # 定义权重调整上限
        max_adjustment = 0.1  # 最大上下浮动10%
        
        # 计算权重调整
        for asset in valid_assets:
            try:
                score_data = market_scores.get(asset.code, {})
                score = score_data.get("total_score", 40)
                
                # 确保score是有效数字
                if not isinstance(score, (int, float)):
                    logger.warning(f"资产 {asset.code} 的评分无效: {score}, 使用默认评分")
                    score = 40
                
                base_weight = asset.weight
                
                # 根据分数调整权重
                if score >= 80:  # 极度超跌
                    adjustment = max_adjustment
                elif score >= 65:  # 重度价值区间
                    adjustment = max_adjustment * 0.7
                elif score >= 55:  # 轻度价值区间
                    adjustment = max_adjustment * 0.3
                elif score <= 25:  # 重度高估
                    adjustment = -max_adjustment
                elif score <= 35:  # 轻度高估
                    adjustment = -max_adjustment * 0.5
                else:  # 中性区间
                    adjustment = 0
                
                adjusted_weights[asset.code] = base_weight * (1 + adjustment)
                logger.debug(f"资产 {asset.code} 权重调整: {base_weight} -> {adjusted_weights[asset.code]}, 评分: {score}")
            except Exception as e:
                logger.error(f"调整资产 {asset.code} 权重时出错: {str(e)}")
                # 如果出错，使用原始权重
                adjusted_weights[asset.code] = asset.weight
        
        # 归一化权重确保总和为1
        total_weight = sum(adjusted_weights.values())
        if total_weight > 0:
            for code in adjusted_weights:
                adjusted_weights[code] /= total_weight
        else:
            # 如果总权重为0，平均分配权重
            equal_weight = 1.0 / len(adjusted_weights) if adjusted_weights else 0
            for code in adjusted_weights:
                adjusted_weights[code] = equal_weight
            logger.warning("总权重为0，已平均分配权重")
        
        return adjusted_weights
    
    def _convert_to_investment_frequency(self, frequency_str: str) -> InvestmentFrequency:
        """将字符串转换为InvestmentFrequency枚举
        
        Args:
            frequency_str: 频率字符串
            
        Returns:
            InvestmentFrequency: 投资频率枚举
        """
        if frequency_str == "daily":
            return InvestmentFrequency.DAILY
        elif frequency_str == "weekly":
            return InvestmentFrequency.WEEKLY
        elif frequency_str == "biweekly":
            return InvestmentFrequency.BIWEEKLY
        else:
            return InvestmentFrequency.MONTHLY
    
    def _calculate_single_amount(self, monthly_amount: float, frequency: InvestmentFrequency, 
                              frequency_factor: float) -> float:
        """计算单次投资金额，考虑频率因子，但保持总投资金额固定
        
        Args:
            monthly_amount: 月度投资金额
            frequency: 投资频率
            frequency_factor: 频率因子影响单次投资金额，但不减少总投资
            
        Returns:
            float: 单次投资金额
        """
        # 计算频率对应的投资次数
        if frequency == InvestmentFrequency.DAILY:
            # 假设月均20个交易日，每日投资
            num_investments = 20
        elif frequency == InvestmentFrequency.WEEKLY:
            # 假设月均4周，每周投资
            num_investments = 4
        elif frequency == InvestmentFrequency.BIWEEKLY:
            # 每两周一次，每月投资2次
            num_investments = 2
        else:  # MONTHLY
            # 月度投资1次
            num_investments = 1
        
        # 计算基本单次投资金额（未考虑频率因子）
        base_single_amount = monthly_amount / num_investments
        
        # 如果有频率因子不为1.0，调整单次金额，但调整投资次数以保持总额
        if frequency_factor != 1.0:
            # 单次金额变为原来的frequency_factor倍
            adjusted_single_amount = base_single_amount * frequency_factor
            # 实际投资次数调整为保持总投资金额不变
            actual_num_investments = monthly_amount / adjusted_single_amount
            
            # 实际投资次数取整可能导致总额略有不同，下一步会有adjustment_factor处理
            logger.debug(f"频率因子调整: {frequency} 单次金额: {base_single_amount:.2f} -> {adjusted_single_amount:.2f}, 投资次数: {num_investments} -> {actual_num_investments:.2f}")
            
            return adjusted_single_amount
        else:
            return base_single_amount
    
    def _get_investment_dates(self, frequency: InvestmentFrequency, special_frequency: str = None) -> List[str]:
        """获取投资日期建议
        
        Args:
            frequency: 投资频率
            special_frequency: 特殊频率标记（用于处理特殊情况）
            
        Returns:
            List[str]: 投资日期列表
        """
        now = datetime.now()
        current_month = now.month
        next_month = (current_month % 12) + 1
        current_year = now.year
        next_year = current_year + 1 if next_month == 1 else current_year
        
        dates = []
        
        # 根据频率生成投资日期
        if frequency == InvestmentFrequency.DAILY:
            # 生成接下来10个工作日，每个工作日都投资
            current_date = now
            count = 0
            days_added = 0
            
            # 极度超跌情况下，生成10个工作日的日期
            while count < 10:
                days_added += 1
                current_date = now + timedelta(days=days_added)
                
                # 简单处理，跳过周末
                if current_date.weekday() < 5:  # 0-4表示周一至周五
                    dates.append(current_date.strftime('%Y-%m-%d'))
                    count += 1
        
        elif frequency == InvestmentFrequency.WEEKLY:
            # 生成未来4周的相同星期几
            current_weekday = now.weekday()
            for i in range(1, 5):
                days_ahead = i * 7
                future_date = now + timedelta(days=days_ahead)
                dates.append(future_date.strftime('%Y-%m-%d'))
        
        elif frequency == InvestmentFrequency.BIWEEKLY:
            # 生成未来2次两周投资日期
            for i in range(1, 3):
                days_ahead = i * 14
                future_date = now + timedelta(days=days_ahead)
                dates.append(future_date.strftime('%Y-%m-%d'))
                
        else:  # MONTHLY
            # 本月投资日期（如果今天已经超过了本月15日）和下月投资日期
            if now.day < 15:
                # 本月15日
                this_month_date = datetime(current_year, current_month, 15)
                dates.append(this_month_date.strftime('%Y-%m-%d'))
            
            # 下月15日
            next_month_date = datetime(next_year, next_month, 15)
            dates.append(next_month_date.strftime('%Y-%m-%d'))
        
        return dates
    
    def get_investment_details(self, market_data: Dict[str, MarketData]) -> Dict:
        """获取投资详情，包括评分和投资建议
        
        Args:
            market_data: 市场数据字典
            
        Returns:
            Dict: 投资详情
        """
        result = {
            "market_scores": {},
            "investment_strategies": {}
        }
        
        for code, data in market_data.items():
            # 计算市场评分
            score_result = self.market_score_calculator.calculate_market_score(data)
            result["market_scores"][code] = score_result
            
            # 确定投资策略
            strategy = self.market_score_calculator.determine_investment_strategy(score_result.get("total_score", 40))
            result["investment_strategies"][code] = strategy
        
        return result
    
    def _detect_market_pullback(self, market_data: MarketData, 
                             historical_scores: List[Dict], window: int = 20) -> Dict:
        """检测市场回调情况
        
        Args:
            market_data: 市场数据
            historical_scores: 历史评分记录
            window: 检测窗口大小
            
        Returns:
            Dict: 回调分析结果
        """
        result = {
            "is_pullback": False,
            "pullback_depth": 0,
            "recent_high": None,
            "days_from_high": 0,
            "score_trend": "stable"  # stable, rising, falling
        }
        
        # 检查历史数据是否足够
        if len(historical_scores) < 2:
            return result
        
        # 分析评分趋势
        recent_scores = [s["score"] for s in historical_scores[-min(window, len(historical_scores)):]]
        if len(recent_scores) >= 3:
            if recent_scores[-1] > recent_scores[-2] > recent_scores[-3]:
                result["score_trend"] = "rising"
            elif recent_scores[-1] < recent_scores[-2] < recent_scores[-3]:
                result["score_trend"] = "falling"
        
        # 检测近期高点
        if market_data and market_data.w52_high and market_data.price:
            # 计算从52周高点的回撤
            pullback = (market_data.price - market_data.w52_high) / market_data.w52_high
            if pullback < -0.05:  # 至少5%的回撤
                result["is_pullback"] = True
                result["pullback_depth"] = pullback
                result["recent_high"] = market_data.w52_high
        
        return result 