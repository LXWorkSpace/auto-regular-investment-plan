from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from ..models.base_models import UserConfig, Asset, AssetType, InvestmentPlan
from ..utils.data_storage import DataStorage
from ..utils.market_data import MarketDataFetcher
from ..utils.investment_calculator import InvestmentCalculator

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 创建路由
router = APIRouter()

# 依赖项
def get_data_storage():
    return DataStorage()

def get_market_data_fetcher():
    return MarketDataFetcher()

def get_investment_calculator():
    return InvestmentCalculator()

# 用户配置相关路由
@router.get("/config", response_model=Dict[str, Any], tags=["配置"])
async def get_user_config(data_storage: DataStorage = Depends(get_data_storage)):
    """获取用户配置"""
    return data_storage.get_user_config()

@router.post("/config", response_model=Dict[str, Any], tags=["配置"])
async def update_user_config(config: Dict[str, Any], data_storage: DataStorage = Depends(get_data_storage)):
    """更新用户配置"""
    try:
        logger.info("正在更新用户配置")
        
        # 处理资产数组中的类型字段
        if "assets" in config and isinstance(config["assets"], list):
            for asset in config["assets"]:
                if "type" in asset and isinstance(asset["type"], str):
                    asset_type = asset["type"]
                    if asset_type not in [e.value for e in AssetType]:
                        # 根据字符串设置对应的枚举值
                        if asset_type == "中国指数":
                            asset["type"] = AssetType.CN_INDEX
                        elif asset_type == "美国指数":
                            asset["type"] = AssetType.US_INDEX
                        elif asset_type == "黄金":
                            asset["type"] = AssetType.GOLD
                        elif asset_type == "债券":
                            asset["type"] = AssetType.BOND
                        elif asset_type == "现金":
                            asset["type"] = AssetType.CASH
                        else:
                            asset["type"] = AssetType.OTHER
        
        # 直接使用接收到的配置，不进行模型验证
        updated_config = data_storage.update_user_config(config)
        logger.info("用户配置更新成功")
        return updated_config
    except Exception as e:
        logger.error(f"更新用户配置时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新用户配置失败: {str(e)}")

# 市场数据相关路由
@router.get("/market-data", response_model=Dict[str, Any], tags=["市场数据"])
async def get_all_market_data(data_storage: DataStorage = Depends(get_data_storage)):
    """获取所有市场数据"""
    try:
        logger.info("正在获取所有市场数据")
        market_data = data_storage.get_market_data()
        
        # 验证市场数据格式
        if not isinstance(market_data, dict):
            logger.error(f"市场数据格式错误: {type(market_data)}")
            raise HTTPException(status_code=500, detail="市场数据格式错误")
            
        # 记录获取到的资产数量
        logger.info(f"成功获取市场数据，包含 {len(market_data)} 个资产")
        
        # 如果市场数据为空，提供友好提示
        if not market_data:
            logger.warning("市场数据为空，可能需要刷新数据")
            return {"message": "市场数据为空，请先刷新数据"}
            
        return market_data
    except Exception as e:
        logger.error(f"获取市场数据时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取市场数据失败: {str(e)}")

@router.get("/market-data/{code}", response_model=Dict[str, Any], tags=["市场数据"])
async def get_asset_market_data(code: str, data_storage: DataStorage = Depends(get_data_storage)):
    """获取特定资产的市场数据"""
    data = data_storage.get_market_data(code)
    if not data:
        raise HTTPException(status_code=404, detail="资产未找到")
    return data

@router.post("/market-data/refresh", response_model=Dict[str, Any], tags=["市场数据"])
async def refresh_market_data(
    background_tasks: BackgroundTasks,
    data_storage: DataStorage = Depends(get_data_storage),
    market_data_fetcher: MarketDataFetcher = Depends(get_market_data_fetcher)
):
    """刷新所有市场数据（异步任务）"""
    # 获取用户配置中的资产列表
    user_config = data_storage.get_user_config()
    assets = user_config.get("assets", [])
    
    # 启动后台任务更新市场数据
    background_tasks.add_task(update_market_data_task, assets, data_storage, market_data_fetcher)
    
    return {"message": "市场数据更新任务已启动"}

async def update_market_data_task(
    assets: List[Dict[str, Any]], 
    data_storage: DataStorage,
    market_data_fetcher: MarketDataFetcher
):
    """更新市场数据的后台任务"""
    for asset in assets:
        try:
            code = asset.get("code")
            asset_type = asset.get("type")
            
            # 确定市场类型
            market = "US" if asset_type == "美国指数" else "CN"
            
            # 获取市场数据
            market_data = market_data_fetcher.get_complete_market_data(code, market)
            
            # 更新存储
            data_storage.update_market_data(code, market_data)
            
            logger.info(f"已更新资产 {code} 的市场数据")
        except Exception as e:
            logger.error(f"更新资产 {asset.get('code')} 的市场数据失败: {str(e)}")

# 投资计划相关路由
@router.get("/investment-plans", response_model=List[Dict[str, Any]], tags=["投资计划"])
async def get_investment_plans(data_storage: DataStorage = Depends(get_data_storage)):
    """获取历史投资计划"""
    return data_storage.get_investment_plans()

@router.get("/investment-plans/latest", response_model=Dict[str, Any], tags=["投资计划"])
async def get_latest_investment_plan(data_storage: DataStorage = Depends(get_data_storage)):
    """获取最新投资计划"""
    plan = data_storage.get_latest_investment_plan()
    if not plan:
        raise HTTPException(status_code=404, detail="没有找到投资计划")
    return plan

@router.delete("/investment-plans/{plan_id}", response_model=Dict[str, Any], tags=["投资计划"])
async def delete_investment_plan(plan_id: str, data_storage: DataStorage = Depends(get_data_storage)):
    """删除指定的投资计划"""
    try:
        result = data_storage.delete_investment_plan(plan_id)
        if result:
            return {"success": True, "message": f"成功删除ID为 {plan_id} 的投资计划"}
        else:
            raise HTTPException(status_code=404, detail=f"未找到ID为 {plan_id} 的投资计划")
    except Exception as e:
        logger.error(f"删除投资计划时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除投资计划失败: {str(e)}")

@router.post("/investment-plans/generate", response_model=Dict[str, Any], tags=["投资计划"])
async def generate_investment_plan(
    data_storage: DataStorage = Depends(get_data_storage),
    market_data_fetcher: MarketDataFetcher = Depends(get_market_data_fetcher),
    investment_calculator: InvestmentCalculator = Depends(get_investment_calculator)
):
    """生成新的投资计划"""
    try:
        # 获取用户配置
        user_config_dict = data_storage.get_user_config()
        logger.info(f"成功获取用户配置: {user_config_dict.get('monthly_investment')} 元/月")
        
        # 转换为UserConfig对象
        assets = []
        for asset_dict in user_config_dict.get("assets", []):
            try:
                assets.append(Asset(
                    id=asset_dict.get("id"),
                    name=asset_dict.get("name"),
                    code=asset_dict.get("code"),
                    type=AssetType(asset_dict.get("type")),
                    market=asset_dict.get("market", "US"),  # 确保market字段存在
                    weight=float(asset_dict.get("weight", 0)),  # 确保weight是浮点数
                    description=asset_dict.get("description")
                ))
            except Exception as asset_error:
                logger.error(f"处理资产时出错: {asset_dict.get('code')}, 错误: {str(asset_error)}")
                # 跳过有问题的资产，继续处理其他资产
                continue
        
        if not assets:
            return {"error": "没有有效的资产配置", "success": False}
        
        logger.info(f"处理了 {len(assets)} 个资产")
        
        user_config = UserConfig(
            user_id=user_config_dict.get("user_id", "default_user"),
            monthly_investment=float(user_config_dict.get("monthly_investment", 0)),
            assets=assets,
            buffer_amount=float(user_config_dict.get("buffer_amount", 500.0))
        )
        
        # 获取市场数据
        market_data_dict = data_storage.get_market_data()
        logger.info(f"成功获取市场数据，共 {len(market_data_dict)} 条记录")
        
        if not market_data_dict:
            logger.warning("市场数据为空，将使用默认评分")
        
        market_data = {}
        
        # 将字典转换为MarketData对象
        for code, data in market_data_dict.items():
            try:
                from ..models.base_models import MarketData
                market_data[code] = MarketData(**data)
            except Exception as data_error:
                logger.error(f"处理市场数据时出错: {code}, 错误: {str(data_error)}")
                # 跳过有问题的市场数据，继续处理其他数据
                continue
        
        # 生成投资计划
        logger.info("开始生成投资计划...")
        investment_plan = investment_calculator.generate_investment_plan(user_config, market_data)
        
        # 保存投资计划
        plan_dict = investment_plan.dict()
        logger.info(f"投资计划生成成功，总金额: {plan_dict.get('total_monthly_amount')} 元")
        
        try:
            saved_plan = data_storage.save_investment_plan(plan_dict)
            logger.info(f"投资计划保存成功，ID: {saved_plan.get('id')}")
            return saved_plan
        except Exception as save_error:
            logger.error(f"保存投资计划时出错: {str(save_error)}")
            # 即使保存失败，仍然返回生成的计划
            plan_dict["save_error"] = str(save_error)
            plan_dict["success"] = False
            return plan_dict
        
    except Exception as e:
        logger.error(f"生成投资计划时出错: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": f"生成投资计划失败: {str(e)}",
            "error_type": str(type(e).__name__)
        }

# 示例资产路由
@router.get("/assets/examples", tags=["参考数据"])
async def get_example_assets():
    """获取示例资产列表"""
    return [
        {
            "name": "沪深300ETF",
            "code": "510300",
            "type": "中国指数",
            "description": "跟踪沪深300指数的ETF"
        },
        {
            "name": "中证500ETF",
            "code": "510500",
            "type": "中国指数",
            "description": "跟踪中证500指数的ETF"
        },
        {
            "name": "创业板ETF",
            "code": "159915",
            "type": "中国指数",
            "description": "跟踪创业板指数的ETF"
        },
        {
            "name": "标普500ETF",
            "code": "SPY",
            "type": "美国指数",
            "description": "跟踪标普500指数的ETF"
        },
        {
            "name": "纳斯达克ETF",
            "code": "QQQ",
            "type": "美国指数",
            "description": "跟踪纳斯达克100指数的ETF"
        },
        {
            "name": "黄金ETF",
            "code": "GLD",
            "type": "黄金",
            "description": "跟踪黄金价格的ETF"
        }
    ]

# 添加一个新的API端点，用于获取投资系数计算细节
@router.get("/investment-details", response_model=Dict[str, Any], tags=["投资计划"])
async def get_investment_details(
    data_storage: DataStorage = Depends(get_data_storage),
    investment_calculator: InvestmentCalculator = Depends(get_investment_calculator)
):
    """获取投资系数计算细节和市场数据获取状态"""
    try:
        # 获取用户配置
        user_config = data_storage.get_user_config()
        # 获取市场数据
        market_data_dict = data_storage.get_market_data()
        
        # 准备计算结果
        result = {
            "market_data_status": {},
            "coefficients": {},
            "frequency": {},
            "special_conditions": {},
            "market_scores": {}  # 新增：市场评分
        }
        
        # 如果市场数据不为空，使用新的投资详情接口
        if market_data_dict:
            # 将字典转换为MarketData对象
            market_data_objects = {}
            for code, data in market_data_dict.items():
                from ..models.base_models import MarketData
                market_data_objects[code] = MarketData(**data)
            
            # 获取投资详情
            investment_details = investment_calculator.get_investment_details(market_data_objects)
            
            # 处理每个资产
            for asset in user_config.get("assets", []):
                asset_code = asset.get("code")
                if not asset_code:
                    continue
                
                # 检查是否有市场数据
                has_market_data = asset_code in market_data_dict and market_data_dict[asset_code].get("price") is not None
                result["market_data_status"][asset_code] = {
                    "has_market_data": has_market_data,
                    "updated_at": market_data_dict.get(asset_code, {}).get("updated_at") if has_market_data else None
                }
                
                # 如果没有市场数据，记录使用中性值的情况
                if not has_market_data:
                    result["coefficients"][asset_code] = {
                        "valuation_coefficient": 1.0,
                        "is_default": True,
                        "reason": "没有市场数据，使用中性值"
                    }
                    result["frequency"][asset_code] = {
                        "frequency": "biweekly",  # 新策略默认两周一次
                        "factor": 1.0,
                        "is_default": True
                    }
                    result["special_conditions"][asset_code] = {
                        "has_special_condition": False,
                        "is_default": True
                    }
                    result["market_scores"][asset_code] = {
                        "total_score": 40,
                        "valuation_score": 10,
                        "trend_score": 10,
                        "volatility_score": 10,
                        "special_event_score": 10,
                        "is_default": True
                    }
                    continue
                
                # 获取市场评分和投资策略
                market_score = investment_details["market_scores"].get(asset_code, {})
                investment_strategy = investment_details["investment_strategies"].get(asset_code, {})
                
                # 转换评分结果为系数格式（向后兼容）
                result["coefficients"][asset_code] = {
                    "price": market_data_dict[asset_code].get("price"),
                    "w52_high": market_data_dict[asset_code].get("w52_high"),
                    "w52_low": market_data_dict[asset_code].get("w52_low"),
                    "price_position": market_score.get("score_components", {}).get("price_position"),
                    "ma_deviation": market_data_dict[asset_code].get("deviation_percentage"),
                    "valuation_coefficient": market_score.get("valuation_score", 10) / 10,
                    "trend_coefficient": market_score.get("trend_score", 10) / 10,
                    "volatility_coefficient": market_score.get("volatility_score", 10) / 10,
                    "rsi_14": market_data_dict[asset_code].get("rsi_14"),
                    "ma_cross": market_data_dict[asset_code].get("ma_cross"),
                    "is_default": False
                }
                
                # 将投资策略转换为频率格式
                result["frequency"][asset_code] = {
                    "frequency": investment_strategy.get("frequency", "biweekly"),
                    "factor": investment_strategy.get("amount_factor", 1.0),
                    "atr_percentile": market_data_dict[asset_code].get("atr_percentile"),
                    "is_default": False
                }
                
                # 特殊市场条件
                result["special_conditions"][asset_code] = {
                    "has_special_condition": investment_strategy.get("score_level") is not None,
                    "condition_type": investment_strategy.get("score_level"),
                    "recent_drawdown": market_data_dict[asset_code].get("recent_drawdown"),
                    "description": investment_strategy.get("description", ""),
                    "is_default": False
                }
                
                # 市场评分
                result["market_scores"][asset_code] = market_score
        
        return result
    except Exception as e:
        logger.error(f"获取投资细节时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取投资细节失败: {str(e)}")

@router.get("/market-trend/{code}", response_model=Dict[str, Any], tags=["市场数据"])
async def get_market_trend(
    code: str,
    data_storage: DataStorage = Depends(get_data_storage),
    investment_calculator: InvestmentCalculator = Depends(get_investment_calculator)
):
    """获取特定资产的市场趋势分析
    
    Args:
        code: 资产代码
        
    Returns:
        Dict: 市场趋势分析结果
    """
    try:
        # 分析市场趋势
        trend_analysis = investment_calculator.analyze_market_trend(code)
        
        # 如果历史数据不足，尝试获取当前市场数据进行基础分析
        if "数据不足" in trend_analysis.get("investment_suggestion", ""):
            market_data = data_storage.get_market_data(code)
            if market_data:
                # 计算市场评分
                score_result = investment_calculator.market_score_calculator.calculate_market_score(market_data)
                
                # 添加到历史记录
                if code not in investment_calculator.historical_scores:
                    investment_calculator.historical_scores[code] = []
                investment_calculator.historical_scores[code].append({
                    "timestamp": datetime.now().isoformat(),
                    "score": score_result.get("total_score", 40)
                })
                
                # 更新趋势分析中的当前市场状态
                score = score_result.get("total_score", 40)
                if score >= 80:
                    trend_analysis["market_status"] = "极度超跌"
                    trend_analysis["investment_suggestion"] = "市场处于极度超跌状态，建议积极加仓"
                elif score >= 65:
                    trend_analysis["market_status"] = "价值区间"
                    trend_analysis["investment_suggestion"] = "市场处于价值区间，建议适度加仓"
                elif score >= 40:
                    trend_analysis["market_status"] = "中性市场"
                    trend_analysis["investment_suggestion"] = "市场处于中性区间，建议常规定投"
                elif score >= 20:
                    trend_analysis["market_status"] = "高估区间"
                    trend_analysis["investment_suggestion"] = "市场处于高估区间，建议减少投入"
                else:
                    trend_analysis["market_status"] = "极度泡沫"
                    trend_analysis["investment_suggestion"] = "市场处于极度泡沫状态，建议谨慎投资或暂停"
                
                trend_analysis["current_score"] = score
                trend_analysis["score_components"] = score_result.get("score_components", {})
        
        return trend_analysis
        
    except Exception as e:
        logger.error(f"获取市场趋势分析时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取市场趋势分析失败: {str(e)}")

# 添加历史数据测试相关路由
@router.post("/historical-test", response_model=Dict[str, Any], tags=["历史测试"])
async def generate_historical_investment_plan(
    historical_test_data: Dict[str, str],
    data_storage: DataStorage = Depends(get_data_storage),
    market_data_fetcher: MarketDataFetcher = Depends(get_market_data_fetcher),
    investment_calculator: InvestmentCalculator = Depends(get_investment_calculator)
):
    """根据历史日期生成投资计划
    
    Args:
        historical_test_data: 包含历史日期的数据字典
        
    Returns:
        Dict[str, Any]: 基于历史数据生成的投资计划
    """
    try:
        # 获取历史日期
        historical_date = historical_test_data.get("historical_date")
        if not historical_date:
            return {"error": "未提供历史日期", "success": False}
        
        # 获取用户配置
        user_config_dict = data_storage.get_user_config()
        logger.info(f"成功获取用户配置: {user_config_dict.get('monthly_investment')} 元/月，历史日期测试: {historical_date}")
        
        # 转换为UserConfig对象
        assets = []
        for asset_dict in user_config_dict.get("assets", []):
            try:
                assets.append(Asset(
                    id=asset_dict.get("id"),
                    name=asset_dict.get("name"),
                    code=asset_dict.get("code"),
                    type=AssetType(asset_dict.get("type")),
                    market=asset_dict.get("market", "US"),
                    weight=float(asset_dict.get("weight", 0)),
                    description=asset_dict.get("description")
                ))
            except Exception as asset_error:
                logger.error(f"处理资产时出错: {asset_dict.get('code')}, 错误: {str(asset_error)}")
                continue
        
        if not assets:
            return {"error": "没有有效的资产配置", "success": False}
        
        user_config = UserConfig(
            user_id=user_config_dict.get("user_id", "default_user"),
            monthly_investment=float(user_config_dict.get("monthly_investment", 0)),
            assets=assets,
            buffer_amount=float(user_config_dict.get("buffer_amount", 500.0))
        )
        
        # 获取历史市场数据
        historical_market_data = {}
        for asset in assets:
            try:
                # 对每个资产获取历史数据
                historical_data = market_data_fetcher.get_historical_market_data(asset.code, asset.market, historical_date)
                if historical_data:
                    from ..models.base_models import MarketData
                    historical_market_data[asset.code] = MarketData(**historical_data)
            except Exception as e:
                logger.error(f"获取资产 {asset.code} 的历史数据时出错: {str(e)}")
        
        if not historical_market_data:
            return {"error": f"无法获取 {historical_date} 的历史市场数据", "success": False}
        
        # 生成基于历史数据的投资计划
        historical_plan = investment_calculator.generate_investment_plan(user_config, historical_market_data)
        
        # 保存计划但标记为历史测试
        plan_dict = historical_plan.dict()
        plan_dict["is_historical_test"] = True
        plan_dict["historical_date"] = historical_date
        
        # 不保存历史测试计划到数据库中
        return plan_dict
        
    except Exception as e:
        logger.error(f"生成历史投资计划时出错: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": f"生成历史投资计划失败: {str(e)}",
            "error_type": str(type(e).__name__)
        } 