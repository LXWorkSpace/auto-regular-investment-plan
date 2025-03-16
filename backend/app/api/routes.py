from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging

from ..models.base_models import UserConfig, Asset, AssetType, InvestmentPlan, RiskPreference
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
async def update_user_config(config: UserConfig, data_storage: DataStorage = Depends(get_data_storage)):
    """更新用户配置"""
    return data_storage.update_user_config(config.dict())

# 市场数据相关路由
@router.get("/market-data", response_model=Dict[str, Any], tags=["市场数据"])
async def get_all_market_data(data_storage: DataStorage = Depends(get_data_storage)):
    """获取所有市场数据"""
    return data_storage.get_market_data()

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

@router.post("/investment-plans/generate", response_model=Dict[str, Any], tags=["投资计划"])
async def generate_investment_plan(
    data_storage: DataStorage = Depends(get_data_storage),
    market_data_fetcher: MarketDataFetcher = Depends(get_market_data_fetcher),
    investment_calculator: InvestmentCalculator = Depends(get_investment_calculator)
):
    """生成新的投资计划"""
    # 获取用户配置
    user_config_dict = data_storage.get_user_config()
    
    # 转换为UserConfig对象
    assets = []
    for asset_dict in user_config_dict.get("assets", []):
        assets.append(Asset(
            id=asset_dict.get("id"),
            name=asset_dict.get("name"),
            code=asset_dict.get("code"),
            type=AssetType(asset_dict.get("type")),
            weight=asset_dict.get("weight"),
            description=asset_dict.get("description")
        ))
    
    user_config = UserConfig(
        monthly_investment=user_config_dict.get("monthly_investment"),
        risk_preference=RiskPreference(user_config_dict.get("risk_preference")),
        assets=assets,
        buffer_percentage=user_config_dict.get("buffer_percentage", 0.1)
    )
    
    # 获取市场数据
    market_data_dict = data_storage.get_market_data()
    market_data = {}
    
    # 生成投资计划
    investment_plan = investment_calculator.generate_investment_plan(user_config, market_data)
    
    # 保存投资计划
    saved_plan = data_storage.save_investment_plan(investment_plan.dict())
    
    return saved_plan

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