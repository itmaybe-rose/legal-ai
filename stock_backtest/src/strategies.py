# 策略模块
from config import Config

class DualMAStrategy:
    """双均线策略"""
    
    def __init__(self, short_window=None, long_window=None):
        self.short_window = short_window or Config.MA_SHORT_WINDOW # 短期均线窗口
        self.long_window = long_window or Config.MA_LONG_WINDOW # 长期均线窗口
    
    def calculate_signals(self, df):
        """
        计算买卖信号
        :param df: 包含 'close' 列的 DataFrame
        :return: 添加了信号的 DataFrame
        """
        df = df.copy() # 避免修改原始数据
        
        # 计算均线
        df['short_ma'] = df['close'].rolling(window=self.short_window).mean() # 短期均线
        df['long_ma'] = df['close'].rolling(window=self.long_window).mean() # 长期均线
        
        # 生成信号：1=买入，-1=卖出，0=持有
        df['signal'] = 0
        df['position'] = 0
        
        # 金叉：短期均线上穿长期均线 -> 买入
        golden_cross = (df['short_ma'] > df['long_ma']) & (df['short_ma'].shift(1) <= df['long_ma'].shift(1))
        df.loc[golden_cross, 'signal'] = 1
        
        # 死叉：短期均线下穿长期均线 -> 卖出
        death_cross = (df['short_ma'] < df['long_ma']) & (df['short_ma'].shift(1) >= df['long_ma'].shift(1))
        df.loc[death_cross, 'signal'] = -1
        
        # 计算持仓位置
        df['position'] = df['signal'].cumsum().clip(0, 1) # 限制持仓位置在 0 到 1 之间
        
        return df

class BollingerBandStrategy:
    """布林带策略"""
    
    def __init__(self, window=None, std_dev=None):
        self.window = window or Config.BB_WINDOW # 布林带窗口大小
        self.std_dev = std_dev or Config.BB_STD_DEV # 标准差倍数
    
    def calculate_signals(self, df):
        """
        计算买卖信号（简化版：纯布林带突破策略）
        :param df: 包含 'close' 列的 DataFrame
        :return: 添加了信号的 DataFrame
        """
        df = df.copy()
        
        # 计算布林带
        df['middle_band'] = df['close'].rolling(window=self.window).mean()
        df['std'] = df['close'].rolling(window=self.window).std()
        df['upper_band'] = df['middle_band'] + self.std_dev * df['std']
        df['lower_band'] = df['middle_band'] - self.std_dev * df['std']
        
        # 生成信号（简化为纯突破策略）
        df['signal'] = 0
        df['position'] = 0
        
        # 下轨突破买入：收盘价从下往上突破下轨
        lower_break = (df['close'] > df['lower_band']) & (df['close'].shift(1) <= df['lower_band'].shift(1))
        df.loc[lower_break, 'signal'] = 1
        
        # 上轨突破卖出：收盘价从上往下突破上轨
        upper_break = (df['close'] < df['upper_band']) & (df['close'].shift(1) >= df['upper_band'].shift(1))
        df.loc[upper_break, 'signal'] = -1
        
        # 计算持仓位置
        df['position'] = df['signal'].cumsum().clip(0, 1)
        
        return df
