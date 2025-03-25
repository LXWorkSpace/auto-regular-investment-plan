import json
import os
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pathlib import Path
import uuid
import logging

logger = logging.getLogger(__name__)

class DataStorage:
    """数据存储工具类，使用JSON文件存储数据"""
    
    def __init__(self, data_dir: str = "app/data"):
        """初始化数据存储
        
        Args:
            data_dir: 数据存储目录
        """
        self.data_dir = Path(data_dir)
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 定义各类数据的文件路径
        self.user_config_path = self.data_dir / "user_config.json"
        self.market_data_path = self.data_dir / "market_data.json"
        self.investment_plans_path = self.data_dir / "investment_plans.json"
        
        # 初始化存储文件
        self._init_files()
    
    def _init_files(self):
        """初始化文件，如果不存在则创建"""
        default_files = {
            self.user_config_path: {"monthly_investment": 0, "assets": [], "buffer_amount": 500.0},
            self.market_data_path: {},
            self.investment_plans_path: []
        }
        
        for file_path, default_data in default_files.items():
            if not file_path.exists():
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(default_data, f, ensure_ascii=False, indent=2)
    
    def _read_json(self, file_path: Path) -> Union[Dict, List]:
        """读取JSON文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            Union[Dict, List]: JSON数据
        """
        try:
            if not file_path.exists():
                logger.warning(f"文件不存在，将创建默认文件: {file_path}")
                return {} if "market_data" in file_path.name or "user_config" in file_path.name else []
            
            logger.info(f"正在读取文件: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if not content.strip():
                    logger.warning(f"文件为空: {file_path}")
                    return {} if "market_data" in file_path.name or "user_config" in file_path.name else []
                
                try:
                    data = json.loads(content)
                    return data
                except json.JSONDecodeError as e:
                    logger.error(f"JSON解析错误: {str(e)}, 文件: {file_path}")
                    # 保存错误的文件内容以便后续检查
                    error_file = file_path.with_suffix('.error')
                    with open(error_file, 'w', encoding='utf-8') as ef:
                        ef.write(content)
                    logger.info(f"已将错误文件内容保存到: {error_file}")
                    
                    # 返回默认空数据
                    return {} if "market_data" in file_path.name or "user_config" in file_path.name else []
        except Exception as e:
            logger.error(f"读取文件出错: {str(e)}, 文件: {file_path}")
            return {} if "market_data" in file_path.name or "user_config" in file_path.name else []
    
    def _write_json(self, file_path: Path, data: Any) -> None:
        """写入JSON文件
        
        Args:
            file_path: 文件路径
            data: 要写入的数据
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            if isinstance(data, dict) and "updated_at" in data:
                data["updated_at"] = datetime.now().isoformat()
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    
    # 用户配置相关操作
    def get_user_config(self) -> Dict:
        """获取用户配置
        
        Returns:
            Dict: 用户配置数据
        """
        return self._read_json(self.user_config_path)
    
    def update_user_config(self, config: Dict) -> Dict:
        """更新用户配置
        
        Args:
            config: 新的用户配置
            
        Returns:
            Dict: 更新后的用户配置
        """
        try:
            # 读取当前配置
            current_config = self.get_user_config()
            
            # 保存创建时间
            if "created_at" in current_config:
                config["created_at"] = current_config.get("created_at")
            else:
                config["created_at"] = datetime.now().isoformat()
                
            # 确保有user_id字段
            if "user_id" not in config:
                config["user_id"] = "default_user"
                
            # 更新时间戳
            config["updated_at"] = datetime.now().isoformat()
            
            # 写入文件
            self._write_json(self.user_config_path, config)
            logger.info(f"用户配置更新成功: {config.get('user_id', 'default_user')}")
            
            return config
        except Exception as e:
            logger.error(f"更新用户配置出错: {str(e)}")
            return config
    
    # 市场数据相关操作
    def get_market_data(self, code: Optional[str] = None) -> Dict:
        """获取市场数据
        
        Args:
            code: 资产代码，如果为None则返回所有数据
            
        Returns:
            Dict: 市场数据
        """
        try:
            data = self._read_json(self.market_data_path)
            logger.info(f"读取市场数据成功: {self.market_data_path}")
            
            # 确保返回的是字典
            if not isinstance(data, dict):
                logger.warning(f"市场数据格式错误，期望字典，但得到 {type(data)}")
                data = {}
                
            if code:
                result = data.get(code, {})
                logger.info(f"获取资产 {code} 的市场数据")
                return result
            
            logger.info(f"返回所有市场数据, 共 {len(data)} 个资产")
            return data
        except Exception as e:
            logger.error(f"获取市场数据出错: {str(e)}")
            # 出错时返回空字典
            return {} if code is None else {}
    
    def update_market_data(self, code: str, data: Dict) -> Dict:
        """更新市场数据
        
        Args:
            code: 资产代码
            data: 市场数据
            
        Returns:
            Dict: 更新后的所有市场数据
        """
        all_data = self.get_market_data()
        data["updated_at"] = datetime.now().isoformat()
        all_data[code] = data
        self._write_json(self.market_data_path, all_data)
        return all_data
    
    # 投资计划相关操作
    def get_investment_plans(self) -> List[Dict]:
        """获取所有投资计划
        
        Returns:
            List[Dict]: 投资计划列表
        """
        return self._read_json(self.investment_plans_path)
    
    def save_investment_plan(self, plan: Dict) -> Dict:
        """保存投资计划
        
        Args:
            plan: 投资计划数据
            
        Returns:
            Dict: 更新后的投资计划，包含ID
        """
        try:
            plans = self.get_investment_plans()
            
            # 确保plans是列表
            if not isinstance(plans, list):
                logger.warning("投资计划格式错误，重置为空列表")
                plans = []
            
            # 确保plan是字典
            if not isinstance(plan, dict):
                logger.error(f"投资计划数据类型错误: {type(plan)}")
                raise ValueError("投资计划必须是字典格式")
                
            # 添加ID和时间戳
            if "id" not in plan:
                plan["id"] = str(uuid.uuid4())
            
            if "generated_at" not in plan:
                plan["generated_at"] = datetime.now().isoformat()
            
            # 确保推荐列表存在
            if "recommendations" not in plan or not isinstance(plan["recommendations"], list):
                logger.warning("投资计划推荐列表为空或格式错误，设置为空列表")
                plan["recommendations"] = []
            
            # 处理推荐中的日期格式
            for rec in plan.get("recommendations", []):
                if isinstance(rec, dict) and "investment_dates" in rec:
                    if not isinstance(rec["investment_dates"], list):
                        rec["investment_dates"] = []
            
            # 添加到列表头部（最新的计划排在前面）
            plans.insert(0, plan)
            
            # 只保留最近的10个计划
            if len(plans) > 10:
                plans = plans[:10]
                
            self._write_json(self.investment_plans_path, plans)
            logger.info(f"投资计划保存成功, ID: {plan['id']}")
            
            return plan
        except Exception as e:
            logger.error(f"保存投资计划出错: {str(e)}")
            # 即使出错，也返回原计划（不保存）
            plan["save_error"] = str(e)
            return plan
    
    def get_latest_investment_plan(self) -> Optional[Dict]:
        """获取最新的投资计划
        
        Returns:
            Optional[Dict]: 最新的投资计划，如果没有则返回None
        """
        plans = self.get_investment_plans()
        return plans[0] if plans else None
        
    def delete_investment_plan(self, plan_id: str) -> bool:
        """删除指定ID的投资计划
        
        Args:
            plan_id: 投资计划ID
            
        Returns:
            bool: 删除成功返回True，未找到或删除失败返回False
        """
        try:
            # 获取当前所有计划
            plans = self.get_investment_plans()
            
            # 查找并删除指定ID的计划
            original_length = len(plans)
            filtered_plans = [plan for plan in plans if plan.get("id") != plan_id]
            
            # 如果长度相同，表示没有找到匹配的计划
            if len(filtered_plans) == original_length:
                logger.warning(f"未找到ID为 {plan_id} 的投资计划")
                return False
                
            # 写入更新后的计划列表
            self._write_json(self.investment_plans_path, filtered_plans)
            logger.info(f"成功删除ID为 {plan_id} 的投资计划")
            return True
            
        except Exception as e:
            logger.error(f"删除投资计划时出错: {str(e)}")
            return False 