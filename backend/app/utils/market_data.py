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
        self.cn_pe_history = {}  # 中国市场PE历史数据缓存
        self.us_pe_history = {}  # 美国市场PE历史数据缓存
    
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
    
    def get_pe_percentile(self, code: str, market: str = "US") -> Tuple[Optional[float], Optional[float]]:
        """获取PE分位数
        
        Args:
            code: 股票代码
            market: 市场，US为美国，CN为中国
            
        Returns:
            Tuple[Optional[float], Optional[float]]: (当前PE, PE分位数)
        """
        try:
            if market == "US":
                # 美股PE数据
                ticker = yf.Ticker(code)
                pe = ticker.info.get('trailingPE')
                print(f"美股PE数据: {pe}")
                # 获取历史PE数据
                if code not in self.us_pe_history:
                    # 此处简化处理，实际应使用更完整的历史PE数据源
                    # 使用过去5年的季度财报数据计算
                    earnings = ticker.quarterly_financials
                    if earnings.empty:
                        return pe, None
                    
                    # 计算过去的PE
                    prices = ticker.history(period="5y", interval="3mo")["Close"]
                    quarterly_pe = []
                    
                    for date, price in prices.items():
                        if date in earnings.columns:
                            eps = earnings.loc['Basic EPS', date]
                            if eps > 0:  # 避免负EPS
                                quarterly_pe.append(price / (eps * 4))  # 年化EPS
                    
                    self.us_pe_history[code] = quarterly_pe
                
                # 计算当前PE的分位数
                if pe and self.us_pe_history[code]:
                    percentile = sum(1 for x in self.us_pe_history[code] if x < pe) / len(self.us_pe_history[code])
                    return pe, percentile
                
                return pe, None
            
            elif market == "CN":
                # 获取A股PE数据
                if code.startswith(('0', '3')) and len(code) == 6:  # 指数
                    try:
                        # 获取指数估值
                        if code.startswith('0'):  # 上证系列
                            df = ak.stock_a_pe(symbol="000300")  # 使用沪深300作为参考
                        else:  # 深证系列
                            df = ak.stock_a_pe(symbol="399001")  # 使用深证成指作为参考
                        
                        current_pe = df["pe"].iloc[-1]
                        
                        # 计算历史分位数
                        historical_pe = df["pe"].dropna().tolist()
                        percentile = sum(1 for x in historical_pe if x < current_pe) / len(historical_pe)
                        
                        return current_pe, percentile
                    except:
                        # 如果获取不到，尝试基金估值
                        df = ak.fund_etf_fund_info_em(fund=code)
                        if not df.empty:
                            pe_info = df[df["信息"].str.contains("市盈率")]
                            if not pe_info.empty:
                                pe_value = pe_info["数值"].iloc[0]
                                return float(pe_value), None
                
                # 对于ETF和基金，尝试获取基金信息
                df = ak.fund_etf_fund_info_em(fund=code)
                if not df.empty:
                    pe_info = df[df["信息"].str.contains("市盈率")]
                    if not pe_info.empty:
                        pe_value = pe_info["数值"].iloc[0]
                        return float(pe_value), 0.5  # 默认分位数为0.5
                
                return None, None
            
            else:
                logger.error(f"不支持的市场: {market}")
                return None, None
                
        except Exception as e:
            logger.error(f"获取PE分位数出错: {code}, {str(e)}")
            return None, None
    
    def get_pb_percentile(self, code: str, market: str = "US") -> Tuple[Optional[float], Optional[float]]:
        """获取PB分位数
        
        Args:
            code: 股票代码
            market: 市场，US为美国，CN为中国
            
        Returns:
            Tuple[Optional[float], Optional[float]]: (当前PB, PB分位数)
        """
        try:
            if market == "US":
                # 美股PB数据
                ticker = yf.Ticker(code)
                pb = ticker.info.get('priceToBook')
                
                # 对于PB历史数据，可以采用类似PE的方法
                # 简化处理，直接返回当前PB
                return pb, None
            
            elif market == "CN":
                # 获取A股PB数据
                if code.startswith(('0', '3')) and len(code) == 6:  # 指数
                    try:
                        # 获取指数估值
                        if code.startswith('0'):  # 上证系列
                            df = ak.stock_a_pb(symbol="000300")  # 使用沪深300作为参考
                        else:  # 深证系列
                            df = ak.stock_a_pb(symbol="399001")  # 使用深证成指作为参考
                        
                        current_pb = df["pb"].iloc[-1]
                        
                        # 计算历史分位数
                        historical_pb = df["pb"].dropna().tolist()
                        percentile = sum(1 for x in historical_pb if x < current_pb) / len(historical_pb)
                        
                        return current_pb, percentile
                    except:
                        # 如果获取不到，尝试基金估值
                        df = ak.fund_etf_fund_info_em(fund=code)
                        if not df.empty:
                            pb_info = df[df["信息"].str.contains("市净率")]
                            if not pb_info.empty:
                                pb_value = pb_info["数值"].iloc[0]
                                return float(pb_value), None
                
                # 对于ETF和基金，尝试获取基金信息
                df = ak.fund_etf_fund_info_em(fund=code)
                if not df.empty:
                    pb_info = df[df["信息"].str.contains("市净率")]
                    if not pb_info.empty:
                        pb_value = pb_info["数值"].iloc[0]
                        return float(pb_value), 0.5  # 默认分位数为0.5
                
                return None, None
            
            else:
                logger.error(f"不支持的市场: {market}")
                return None, None
                
        except Exception as e:
            logger.error(f"获取PB分位数出错: {code}, {str(e)}")
            return None, None
    
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
            
            # 计算200日均线
            ma_200 = self.calculate_ma(df, 200)
            result["ma_200"] = ma_200
            
            # 计算偏离度
            if ma_200:
                result["deviation_percentage"] = (result["price"] - ma_200) / ma_200
            
            # 计算ATR
            result["atr_20"] = self.calculate_atr(df, 20)
            result["atr_baseline"] = self.calculate_baseline_atr(df)
            
            # 获取PE和PB
            pe, pe_percentile = self.get_pe_percentile(code, market)
            result["pe_ratio"] = pe
            result["pe_percentile"] = pe_percentile
            
            pb, pb_percentile = self.get_pb_percentile(code, market)
            result["pb_ratio"] = pb
            result["pb_percentile"] = pb_percentile
        
        return result 