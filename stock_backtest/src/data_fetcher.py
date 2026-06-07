# 数据获取模块
import akshare as ak
import pandas as pd
import pickle
import os
import time
from config import Config

class DataFetcher:
    def __init__(self):
        self.data_dir = Config.DATA_DIR
        os.makedirs(self.data_dir, exist_ok=True)
        self.stock_list_cache = None  # 内存缓存股票列表
        self.cache_time = 0  # 缓存时间戳
        self._stock_info_cache = {}  # 股票信息缓存（代码->是否为ST）
    
    def is_st_stock(self, symbol, df=None, stock_name=None):
        """
        判断股票是否为ST或*ST股票
        
        :param symbol: 股票代码（如 '600519' 或 'sh600519'）
        :param df: 可选参数，已获取的日线数据（可从中提取股票名称）
        :param stock_name: 可选参数，股票名称（用于ST识别）
        :return: True=是ST股票, False=非ST股票
        """
        # 标准化股票代码格式
        original_symbol = symbol
        if len(symbol) == 6 and symbol.isdigit():
            if symbol.startswith('6'):
                symbol = 'sh' + symbol
            elif symbol.startswith('0') or symbol.startswith('3'):
                symbol = 'sz' + symbol
        
        # 方法1：先检查传入的股票名称（优先级最高）
        if stock_name is not None and isinstance(stock_name, str):
            if 'ST' in stock_name or 'st' in stock_name:
                self._stock_info_cache[symbol] = True
                return True
        
        # 方法2：检查原始输入是否包含ST（用户可能直接输入ST股票名）
        if isinstance(original_symbol, str):
            if 'ST' in original_symbol or 'st' in original_symbol:
                self._stock_info_cache[symbol] = True
                return True
        
        # 检查缓存（放在原始输入检查之后）
        if symbol in self._stock_info_cache:
            return self._stock_info_cache[symbol]
        
        # 方法3：从传入的DataFrame中获取（最快，无需额外API调用）
        if df is not None and hasattr(df, 'name'):
            name_from_df = str(df.name)
            if 'ST' in name_from_df or 'st' in name_from_df:
                self._stock_info_cache[symbol] = True
                return True
        
        # 方法4：从股票列表缓存中查找（如果已加载）
        if self.stock_list_cache is not None:
            mask = self.stock_list_cache['代码'] == symbol[-6:]
            if mask.any():
                name_from_list = str(self.stock_list_cache.loc[mask, '名称'].iloc[0])
                if 'ST' in name_from_list or 'st' in name_from_list:
                    self._stock_info_cache[symbol] = True
                    return True
        
        # 方法5：从股票列表中查找（需要网络请求，但数据量大）
        try:
            stock_list = ak.stock_zh_a_spot()
            if stock_list is not None and not stock_list.empty:
                mask = stock_list['代码'] == symbol[-6:]
                if mask.any():
                    stock_name = str(stock_list.loc[mask, '名称'].iloc[0])
                    if 'ST' in stock_name or 'st' in stock_name:
                        self._stock_info_cache[symbol] = True
                        return True
        except Exception as e:
            pass
        
        # 方法4：从日线数据获取股票名称
        try:
            df_temp = ak.stock_zh_a_daily(symbol=symbol, adjust="qfq")
            if df_temp is not None and not df_temp.empty and hasattr(df_temp, 'name'):
                stock_name = str(df_temp.name)
                if 'ST' in stock_name or 'st' in stock_name:
                    self._stock_info_cache[symbol] = True
                    return True
        except Exception as e:
            pass
        
        # 方法5：获取股票基本信息（最慢，作为最后尝试）
        try:
            df_info = ak.stock_individual_info_em(symbol=symbol)
            if df_info is not None and not df_info.empty:
                for col in ['value', '名称', '股票简称']:
                    if col in df_info.columns:
                        mask = df_info['item'] == '股票简称'
                        if mask.any():
                            stock_name = str(df_info.loc[mask, col].iloc[0])
                            if 'ST' in stock_name or 'st' in stock_name:
                                self._stock_info_cache[symbol] = True
                                return True
                for idx, row in df_info.iterrows():
                    val = str(row.get('value', ''))
                    if 'ST' in val or 'st' in val:
                        self._stock_info_cache[symbol] = True
                        return True
        except Exception as e:
            print(f"获取股票信息失败: {str(e)}")
        
        # 默认为非ST股票
        self._stock_info_cache[symbol] = False
        return False
    
    def fetch_stock_data(self, symbol, start_date, end_date, use_cache=True):
        """
        获取股票日线数据（带智能缓存）
        :param symbol: 股票代码，如 'sh600519' 或 '600519'
        :param start_date: 开始日期，格式 'YYYYMMDD'
        :param end_date: 结束日期，格式 'YYYYMMDD'
        :param use_cache: 是否使用缓存（默认开启）
        :return: DataFrame
        """
        try:
            # 如果股票代码没有前缀，自动添加
            if len(symbol) == 6 and symbol.isdigit():
                if symbol.startswith('6'):
                    symbol = 'sh' + symbol  # 上海交易所
                elif symbol.startswith('0') or symbol.startswith('3'):
                    symbol = 'sz' + symbol  # 深圳交易所
            
            # 生成缓存文件名
            cache_filename = f"{symbol}_{start_date}_{end_date}.pkl"
            cache_path = os.path.join(self.data_dir, cache_filename)
            
            # 检查缓存
            if use_cache and os.path.exists(cache_path):
                cache_age = time.time() - os.path.getmtime(cache_path)
                # 缓存有效期：最近30天的数据缓存1天，历史数据缓存7天
                days_in_range = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days
                max_cache_age = 24 * 3600 if days_in_range < 30 else 7 * 24 * 3600
                
                if cache_age < max_cache_age:
                    print(f"[缓存] 正在加载缓存数据: {symbol}")
                    with open(cache_path, 'rb') as f:
                        df = pickle.load(f)
                    print(f"[缓存] 缓存加载成功，共 {len(df)} 条数据")
                    return df
            
            # 从网络获取数据
            print(f"[网络] 正在获取股票数据: {symbol}")
            df = ak.stock_zh_a_daily(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"  # 前复权
            )
            
            if df.empty:
                print("[警告] 未获取到数据")
                return None
            
            # 将 date 列设置为索引并转换为 datetime
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            df = df[['open', 'close', 'high', 'low', 'volume']]  # 仅保留必要列
            
            # 保存到缓存
            if use_cache:
                with open(cache_path, 'wb') as f:
                    pickle.dump(df, f)
                print(f"[缓存] 数据已缓存到本地")
            
            print(f"[成功] 成功获取 {len(df)} 条数据")
            return df
        
        except Exception as e:
            print(f"[错误] 获取数据失败: {str(e)}")
            return None
    
    def save_data(self, df, filename):
        """保存数据到文件"""
        filepath = os.path.join(self.data_dir, filename)
        with open(filepath, 'wb') as f:
            pickle.dump(df, f)
        print(f"数据已保存到: {filepath}")
    
    def load_data(self, filename):
        """从文件加载数据"""
        filepath = os.path.join(self.data_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                return pickle.load(f)
        return None
    
    def get_stock_list(self):
        """
        获取股票列表（带缓存）
        
        :return: 股票列表 DataFrame
        """
        cache_file = os.path.join(self.data_dir, 'stock_list_cache.pkl')
        cache_valid_hours = 24  # 缓存有效期24小时
        
        # 首先检查内存缓存
        current_time = time.time()
        if self.stock_list_cache is not None and (current_time - self.cache_time) < cache_valid_hours * 3600:
            return self.stock_list_cache
        
        # 其次检查文件缓存
        if os.path.exists(cache_file):
            file_mtime = os.path.getmtime(cache_file)
            if (current_time - file_mtime) < cache_valid_hours * 3600:
                with open(cache_file, 'rb') as f:
                    self.stock_list_cache = pickle.load(f)
                    self.cache_time = current_time
                    return self.stock_list_cache
        
        # 从网络获取
        try:
            df = ak.stock_info_a_code_name()
            # 缓存到文件和内存
            with open(cache_file, 'wb') as f:
                pickle.dump(df, f)
            self.stock_list_cache = df
            self.cache_time = current_time
            return df
        except Exception as e:
            print(f"获取股票列表失败: {str(e)}")
            # 如果缓存文件存在，即使过期也尝试使用
            if os.path.exists(cache_file):
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
            return pd.DataFrame()
    
    def search_stocks(self, keyword, limit=20):
        """
        搜索股票（使用缓存优化速度）
        
        :param keyword: 搜索关键词（股票代码或名称）
        :param limit: 返回结果数量限制
        :return: 股票列表 [{'label': '名称 代码', 'value': '代码'}, ...]
        """
        try:
            # 获取股票列表（带缓存）
            df = self.get_stock_list()
            
            if df.empty:
                return []
            
            # 过滤：搜索代码或名称
            keyword = keyword.upper()  # 统一大写
            mask = (
                df['code'].str.upper().str.contains(keyword, na=False) |
                df['name'].str.contains(keyword, na=False)
            )
            
            # 筛选前N条
            results = df[mask].head(limit)
            
            # 转换为下拉框格式
            stock_list = [
                {
                    'label': f"{row['name']}  {row['code']}",
                    'value': row['code']
                }
                for _, row in results.iterrows()
            ]
            
            return stock_list
            
        except Exception as e:
            print(f"搜索失败: {str(e)}")
            return []
