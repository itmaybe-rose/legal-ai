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
    """布林带策略
    
    布林带策略有两种常见模式：
    1. 突破策略（Breakout）：价格突破布林带边界时开仓
    2. 反转策略（Mean Reversion）：价格触及边界时反向操作
    
    本实现采用突破策略：
    - 当价格从下轨下方突破到上方时买入
    - 当价格从上轨上方突破到下方时卖出
    """
    
    def __init__(self, window=None, std_dev=None):
        self.window = window or Config.BB_WINDOW  # 布林带窗口大小
        self.std_dev = std_dev or Config.BB_STD_DEV  # 标准差倍数
    
    def calculate_signals(self, df):
        """
        计算买卖信号（布林带突破策略）
        
        :param df: 包含 'close' 列的 DataFrame
        :return: 添加了信号的 DataFrame
        
        信号规则：
        - 买入：收盘价从下轨下方突破到上方（lower_break）
        - 卖出：收盘价从上轨上方突破到下方（upper_break）
        """
        df = df.copy()
        
        # 计算布林带
        df['middle_band'] = df['close'].rolling(window=self.window).mean()
        df['std'] = df['close'].rolling(window=self.window).std()
        df['upper_band'] = df['middle_band'] + self.std_dev * df['std']
        df['lower_band'] = df['middle_band'] - self.std_dev * df['std']
        
        # 初始化信号和持仓
        df['signal'] = 0
        df['position'] = 0
        
        # 下轨突破买入：收盘价从下轨下方突破到上方
        # 条件：今日收盘价 > 下轨 AND 昨日收盘价 <= 下轨
        lower_break = (df['close'] > df['lower_band']) & (df['close'].shift(1) <= df['lower_band'].shift(1))
        df.loc[lower_break, 'signal'] = 1
        
        # 上轨突破卖出：收盘价从上轨上方突破到下方
        # 条件：今日收盘价 < 上轨 AND 昨日收盘价 >= 上轨
        upper_break = (df['close'] < df['upper_band']) & (df['close'].shift(1) >= df['upper_band'].shift(1))
        df.loc[upper_break, 'signal'] = -1
        
        # 计算持仓位置（限制在 0 到 1 之间）
        df['position'] = df['signal'].cumsum().clip(0, 1)
        
        return df
    
    def calculate_signals_reversion(self, df):
        """
        计算买卖信号（布林带反转策略）
        
        :param df: 包含 'close' 列的 DataFrame
        :return: 添加了信号的 DataFrame
        
        信号规则（反转策略）：
        - 买入：价格触及下轨（预期价格回归均值）
        - 卖出：价格触及上轨（预期价格回归均值）
        """
        df = df.copy()
        
        # 计算布林带
        df['middle_band'] = df['close'].rolling(window=self.window).mean()
        df['std'] = df['close'].rolling(window=self.window).std()
        df['upper_band'] = df['middle_band'] + self.std_dev * df['std']
        df['lower_band'] = df['middle_band'] - self.std_dev * df['std']
        
        # 初始化信号和持仓
        df['signal'] = 0
        df['position'] = 0
        
        # 反转策略：触及下轨买入，触及上轨卖出
        touch_lower = df['close'] <= df['lower_band']
        touch_upper = df['close'] >= df['upper_band']
        
        # 买入：当价格触及下轨且当前没有持仓
        df.loc[touch_lower & (df['position'] == 0), 'signal'] = 1
        
        # 卖出：当价格触及上轨且当前有持仓
        df.loc[touch_upper & (df['position'] == 1), 'signal'] = -1
        
        # 计算持仓位置（限制在 0 到 1 之间）
        df['position'] = df['signal'].cumsum().clip(0, 1)
        
        return df
