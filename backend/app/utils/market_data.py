import yfinance as yf
import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import time
from typing import Dict, List, Optional, Union, Tuple

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
# 6IRLIE9JEKLVA58F

class MarketDataFetcher:
    """市场数据获取工具类"""
    
    def __init__(self):
        """初始化市场数据获取器"""
        self.atr_history = {}    # ATR历史数据缓存
    
    def get_stock_data(self, code: str, market: str = "US", days: int = 400) -> Optional[pd.DataFrame]:
        """获取股票历史数据
        
        Args:
            code: 股票代码
            market: 市场，US为美国，CN为中国
            days: 获取天数
            
        Returns:
            Optional[pd.DataFrame]: 股票历史数据，包括开盘价、收盘价、最高价、最低价、成交量等
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            if market == "US":
                # 使用yfinance获取美股数据
                ticker = yf.Ticker(code)
                df = ticker.history(start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'))
                if df.empty:
                    logger.warning(f"获取美股数据失败: {code}")
                    return None
                return df
            
            elif market == "CN":
                # 使用akshare获取A股数据
                # 处理上证指数、深证指数等
                if code.startswith('0') and len(code) == 6:  # 上证
                    df = ak.stock_zh_index_daily(symbol=f"sh{code}")
                elif code.startswith('3') and len(code) == 6:  # 深证
                    df = ak.stock_zh_index_daily(symbol=f"sz{code}")
                else:
                    # 对于ETF等产品
                    df = ak.fund_etf_hist_sina(symbol=code)
                
                if df.empty:
                    logger.warning(f"获取A股数据失败: {code}")
                    return None
                
                # 重命名列以匹配yfinance输出
                df = df.rename(columns={
                    "date": "Date",
                    "open": "Open",
                    "high": "High",
                    "low": "Low",
                    "close": "Close",
                    "volume": "Volume"
                })
                
                # 设置日期索引
                if "Date" in df.columns:
                    df["Date"] = pd.to_datetime(df["Date"])
                    df.set_index("Date", inplace=True)
                
                # 过滤日期范围
                df = df[df.index >= start_date.strftime('%Y-%m-%d')]
                
                return df
            
            else:
                logger.error(f"不支持的市场: {market}")
                return None
                
        except Exception as e:
            logger.error(f"获取股票数据出错: {code}, {str(e)}")
            return None
    
    def calculate_ma(self, df: pd.DataFrame, window: int = 200) -> Optional[float]:
        """计算移动平均线
        
        Args:
            df: 股票历史数据
            window: 移动平均窗口
            
        Returns:
            Optional[float]: 移动平均值
        """
        if df is None or len(df) < window:
            return None
        
        try:
            ma = df['Close'].rolling(window=window).mean().iloc[-1]
            return ma
        except Exception as e:
            logger.error(f"计算移动平均线出错: {str(e)}")
            return None
    
    def calculate_atr(self, df: pd.DataFrame, window: int = 20) -> Optional[float]:
        """计算平均真实波幅(ATR)
        
        Args:
            df: 股票历史数据
            window: ATR窗口
            
        Returns:
            Optional[float]: ATR值
        """
        if df is None or len(df) < window:
            return None
        
        try:
            # 计算真实范围(TR)
            df = df.copy()
            df['H-L'] = df['High'] - df['Low']
            df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
            df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))
            df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
            
            # 计算ATR
            atr = df['TR'].rolling(window=window).mean().iloc[-1]
            return atr
        except Exception as e:
            logger.error(f"计算ATR出错: {str(e)}")
            return None
    
    def calculate_atr_percentile(self, df: pd.DataFrame, current_atr: float, lookback_days: int = 252) -> Optional[float]:
        """计算ATR在过去一年中的分位数
        
        Args:
            df: 股票历史数据
            current_atr: 当前ATR值
            lookback_days: 回溯天数
            
        Returns:
            Optional[float]: ATR分位数
        """
        if df is None or len(df) < lookback_days or current_atr is None:
            return None
        
        try:
            # 计算过去一年的所有20日ATR值
            df = df.copy()
            df['H-L'] = df['High'] - df['Low']
            df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
            df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))
            df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
            df['ATR20'] = df['TR'].rolling(window=20).mean()
            
            # 取最近一年的ATR数据
            recent_atrs = df['ATR20'].dropna().iloc[-lookback_days:].tolist()
            
            # 计算分位数
            if recent_atrs:
                percentile = sum(1 for x in recent_atrs if x < current_atr) / len(recent_atrs)
                return percentile
            
            return None
        except Exception as e:
            logger.error(f"计算ATR分位数出错: {str(e)}")
            return None
    
    def calculate_rsi(self, df: pd.DataFrame, window: int = 14) -> Optional[float]:
        """计算相对强弱指数(RSI)
        
        Args:
            df: 股票历史数据
            window: RSI窗口
            
        Returns:
            Optional[float]: RSI值
        """
        if df is None or len(df) < window + 1:
            return None
        
        try:
            # 计算价格变化
            delta = df['Close'].diff()
            
            # 分离上涨和下跌
            gain = delta.copy()
            loss = delta.copy()
            gain[gain < 0] = 0
            loss[loss > 0] = 0
            loss = abs(loss)
            
            # 计算平均增益和平均损失
            avg_gain = gain.rolling(window=window).mean()
            avg_loss = loss.rolling(window=window).mean()
            
            # 计算相对强度(RS)和RSI
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            # 返回最新的RSI值
            return rsi.iloc[-1]
        except Exception as e:
            logger.error(f"计算RSI出错: {str(e)}")
            return None
    
    def calculate_ma_cross(self, df: pd.DataFrame, fast_window: int = 20, slow_window: int = 50) -> Optional[int]:
        """计算均线交叉信号
        
        Args:
            df: 股票历史数据
            fast_window: 短期均线窗口
            slow_window: 长期均线窗口
            
        Returns:
            Optional[int]: 交叉信号 (1=金叉, -1=死叉, 0=无交叉)
        """
        if df is None or len(df) < slow_window + 5:  # 需要额外的数据点来检测交叉
            return None
        
        try:
            # 计算均线
            df = df.copy()
            df[f'MA{fast_window}'] = df['Close'].rolling(window=fast_window).mean()
            df[f'MA{slow_window}'] = df['Close'].rolling(window=slow_window).mean()
            
            # 检查最近5天内是否有交叉
            recent_data = df.iloc[-5:].copy()
            
            # 计算短期均线相对于长期均线的位置
            recent_data['Position'] = recent_data[f'MA{fast_window}'] - recent_data[f'MA{slow_window}']
            
            # 检查是否有符号变化（交叉）
            position_shifts = recent_data['Position'].shift(1)
            crosses = ((recent_data['Position'] > 0) & (position_shifts < 0)) | \
                      ((recent_data['Position'] < 0) & (position_shifts > 0))
            
            if crosses.any():
                # 判断是金叉还是死叉
                index = crosses[crosses].index[0]
                if recent_data.loc[index, 'Position'] > 0:
                    return 1  # 金叉
                else:
                    return -1  # 死叉
            
            return 0  # 无交叉
        except Exception as e:
            logger.error(f"计算均线交叉出错: {str(e)}")
            return None
    
    def calculate_recent_drawdown(self, df: pd.DataFrame, window: int = 20) -> Optional[float]:
        """计算最近一段时间的回撤
        
        Args:
            df: 股票历史数据
            window: 回撤计算窗口
            
        Returns:
            Optional[float]: 回撤百分比
        """
        if df is None or len(df) < window:
            return None
        
        try:
            # 获取最近window天的收盘价
            recent_close = df['Close'].iloc[-window:].values
            # 计算期间最高价
            period_high = np.max(recent_close)
            # 计算当前价格
            current_price = recent_close[-1]
            # 计算回撤
            drawdown = (current_price - period_high) / period_high
            return drawdown
        except Exception as e:
            logger.error(f"计算回撤出错: {str(e)}")
            return None
    
    def calculate_volume_surge(self, df: pd.DataFrame, window: int = 20) -> Optional[float]:
        """计算成交量异常值
        
        Args:
            df: 股票历史数据
            window: 成交量均值计算窗口
            
        Returns:
            Optional[float]: 成交量相对于均值的倍数
        """
        if df is None or len(df) < window or 'Volume' not in df.columns:
            return None
        
        try:
            # 计算过去window天的平均成交量
            avg_volume = df['Volume'].iloc[-window-1:-1].mean()
            # 获取最新成交量
            current_volume = df['Volume'].iloc[-1]
            # 计算成交量倍数
            if avg_volume > 0:
                volume_ratio = current_volume / avg_volume
                return volume_ratio
            return None
        except Exception as e:
            logger.error(f"计算成交量异常值出错: {str(e)}")
            return None
    
    def calculate_baseline_atr(self, df: pd.DataFrame) -> Optional[float]:
        """计算基准ATR(过去一年ATR的中位数)
        
        Args:
            df: 股票历史数据
            
        Returns:
            Optional[float]: 基准ATR值
        """
        if df is None or len(df) < 250:  # 至少需要一年的数据
            return None
        
        try:
            # 按20天窗口计算ATR序列
            df = df.copy()
            df['H-L'] = df['High'] - df['Low']
            df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
            df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))
            df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
            
            # 使用过去一年(约250个交易日)的ATR计算中位数
            atr_series = df['TR'].rolling(window=20).mean()
            baseline_atr = atr_series.iloc[-250:].median()
            return baseline_atr
        except Exception as e:
            logger.error(f"计算基准ATR出错: {str(e)}")
            return None
    
    def get_complete_market_data(self, code: str, market: str = "US") -> Dict:
        """获取完整的市场数据
        
        Args:
            code: 股票代码
            market: 市场，US为美国，CN为中国
            
        Returns:
            Dict: 市场数据字典
        """
        result = {
            "code": code,
            "name": code,  # 暂用代码作为名称
            "updated_at": datetime.now().isoformat()
        }
        # 获取股票历史数据
        df = self.get_stock_data(code, market)
        
        if df is not None and not df.empty:
            # 当前价格
            result["price"] = df['Close'].iloc[-1]
            
            # 52周高低点
            one_year_ago = datetime.now() - timedelta(days=365)
            year_data = df[df.index >= one_year_ago.strftime('%Y-%m-%d')]
            if not year_data.empty:
                result["w52_high"] = year_data['Close'].max()
                result["w52_low"] = year_data['Close'].min()
            
            # 计算多个时间周期的均线
            result["ma_20"] = self.calculate_ma(df, 20)
            result["ma_50"] = self.calculate_ma(df, 50)
            result["ma_200"] = self.calculate_ma(df, 200)
            
            # 均线交叉信号
            result["ma_cross"] = self.calculate_ma_cross(df, 20, 50)
            
            # 计算偏离度
            if result["ma_200"]:
                result["deviation_percentage"] = (result["price"] - result["ma_200"]) / result["ma_200"]
            
            # 计算ATR
            atr_20 = self.calculate_atr(df, 20)
            result["atr_20"] = atr_20
            result["atr_baseline"] = self.calculate_baseline_atr(df)
            
            # 计算ATR分位数
            if atr_20 is not None:
                result["atr_percentile"] = self.calculate_atr_percentile(df, atr_20)
            
            # 计算RSI
            result["rsi_14"] = self.calculate_rsi(df, 14)
            
            # 计算近期回撤
            result["recent_drawdown"] = self.calculate_recent_drawdown(df, 20)
            
            # 计算成交量异常
            result["volume_surge"] = self.calculate_volume_surge(df, 20)
        
        return result
    
    def get_historical_market_data(self, code: str, market: str = "US", date_str: str = None) -> Dict:
        """获取指定历史日期的市场数据
        
        Args:
            code: 股票代码
            market: 市场，US为美国，CN为中国
            date_str: 历史日期字符串，格式为YYYY-MM-DD
            
        Returns:
            Dict: 历史市场数据字典
        """
        result = {
            "code": code,
            "name": code,
            "updated_at": datetime.now().isoformat()
        }
        
        try:
            # 解析目标日期
            target_date = datetime.strptime(date_str, '%Y-%m-%d')
            
            # 获取足够长的历史数据
            # 获取从目标日期前400天到目标日期后10天的数据，以确保有足够数据进行技术指标计算
            end_date = target_date + timedelta(days=10)  # 多取几天确保目标日期有数据
            start_date = target_date - timedelta(days=400)  # 回溯足够多的天数以计算均线等指标
            
            if market == "US":
                # 使用yfinance获取美股数据
                ticker = yf.Ticker(code)
                df = ticker.history(start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'))
            elif market == "CN":
                # 使用akshare获取A股数据
                if code.startswith('0') and len(code) == 6:  # 上证
                    df = ak.stock_zh_index_daily(symbol=f"sh{code}")
                elif code.startswith('3') and len(code) == 6:  # 深证
                    df = ak.stock_zh_index_daily(symbol=f"sz{code}")
                else:
                    # 对于ETF等产品
                    df = ak.fund_etf_hist_sina(symbol=code)
                
                # 重命名列以匹配yfinance输出
                df = df.rename(columns={
                    "date": "Date",
                    "open": "Open",
                    "high": "High",
                    "low": "Low",
                    "close": "Close",
                    "volume": "Volume"
                })
                
                # 设置日期索引
                if "Date" in df.columns:
                    df["Date"] = pd.to_datetime(df["Date"])
                    df.set_index("Date", inplace=True)
                
                # 过滤日期范围
                df = df[(df.index >= start_date.strftime('%Y-%m-%d')) & 
                        (df.index <= end_date.strftime('%Y-%m-%d'))]
            else:
                logger.error(f"不支持的市场: {market}")
                return None
            
            if df is None or df.empty:
                logger.warning(f"获取历史数据失败: {code}, 日期: {date_str}")
                return None
            
            # 处理时区问题 - 将索引转换为无时区的日期
            if df.index.tz is not None:
                df.index = df.index.tz_localize(None)
            
            # 找到最接近目标日期的交易日数据
            dates = df.index.tolist()
            # 确保比较时所有日期对象都没有时区信息
            closest_date = min(dates, key=lambda x: abs((x - target_date).total_seconds()))
            
            # 找到该日期在数据中的位置
            target_idx = dates.index(closest_date)
            
            # 从该位置截取数据用于计算当日的指标
            # 确保有足够数据来计算技术指标
            if target_idx < 250:
                logger.warning(f"历史数据不足以计算所有指标: {code}, 日期: {date_str}")
                return None
            
            # 截取到目标日期的数据
            historical_df = df.iloc[:(target_idx + 1)]
            
            # 当日价格
            result["price"] = historical_df['Close'].iloc[-1]
            
            # 52周高低点
            one_year_idx = max(0, target_idx - 252)  # 大约一年的交易日
            year_data = historical_df.iloc[one_year_idx:]
            result["w52_high"] = year_data['Close'].max()
            result["w52_low"] = year_data['Close'].min()
            
            # 计算多个时间周期的均线
            result["ma_20"] = self.calculate_ma(historical_df, 20)
            result["ma_50"] = self.calculate_ma(historical_df, 50)
            result["ma_200"] = self.calculate_ma(historical_df, 200)
            
            # 均线交叉信号
            result["ma_cross"] = self.calculate_ma_cross(historical_df, 20, 50)
            
            # 计算偏离度
            if result["ma_200"]:
                result["deviation_percentage"] = (result["price"] - result["ma_200"]) / result["ma_200"]
            
            # 计算ATR
            atr_20 = self.calculate_atr(historical_df, 20)
            result["atr_20"] = atr_20
            result["atr_baseline"] = self.calculate_baseline_atr(historical_df)
            
            # 计算ATR分位数
            if atr_20 is not None:
                result["atr_percentile"] = self.calculate_atr_percentile(historical_df, atr_20)
            
            # 计算RSI
            result["rsi_14"] = self.calculate_rsi(historical_df, 14)
            
            # 计算近期回撤
            result["recent_drawdown"] = self.calculate_recent_drawdown(historical_df, 20)
            
            # 计算成交量异常
            result["volume_surge"] = self.calculate_volume_surge(historical_df, 20)
            
            # 添加历史日期标记
            result["is_historical"] = True
            result["historical_date"] = closest_date.strftime('%Y-%m-%d')
            
            return result
            
        except Exception as e:
            logger.error(f"获取历史市场数据出错: {code}, 日期: {date_str}, 错误: {str(e)}")
            return None 