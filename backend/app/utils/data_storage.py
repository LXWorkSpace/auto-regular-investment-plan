import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import uuid

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
            self.user_config_path: {"monthly_investment": 0, "risk_preference": "中等风险", "assets": [], "buffer_percentage": 0.1},
            self.market_data_path: {},
            self.investment_plans_path: []
        }
        
        for file_path, default_data in default_files.items():
            if not file_path.exists():
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(default_data, f, ensure_ascii=False, indent=2)
    
    def _read_json(self, file_path: Path) -> Dict:
        """读取JSON文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            Dict: 读取的JSON数据
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    
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
        config["updated_at"] = datetime.now().isoformat()
        self._write_json(self.user_config_path, config)
        return config
    
    # 市场数据相关操作
    def get_market_data(self, code: Optional[str] = None) -> Dict:
        """获取市场数据
        
        Args:
            code: 资产代码，如果为None则返回所有数据
            
        Returns:
            Dict: 市场数据
        """
        data = self._read_json(self.market_data_path)
        if code:
            return data.get(code, {})
        return data
    
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
        plans = self.get_investment_plans()
        if "id" not in plan:
            plan["id"] = str(uuid.uuid4())
        plan["generated_at"] = datetime.now().isoformat()
        
        # 添加到列表头部（最新的计划排在前面）
        plans.insert(0, plan)
        
        # 只保留最近的10个计划
        if len(plans) > 10:
            plans = plans[:10]
            
        self._write_json(self.investment_plans_path, plans)
        return plan
    
    def get_latest_investment_plan(self) -> Optional[Dict]:
        """获取最新的投资计划
        
        Returns:
            Optional[Dict]: 最新的投资计划，如果没有则返回None
        """
        plans = self.get_investment_plans()
        return plans[0] if plans else None 