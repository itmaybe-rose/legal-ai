# 回测框架模块 - 基类+派生类重构版本
import pandas as pd
import numpy as np
import sys
import os

# 添加上级目录到路径以便导入config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from .logger import backtest_logger
from .utils import get_limit_ratio, calculate_metrics, ERROR_MARGIN


class BaseBacktester:
    """回测框架基类 - 包含公共逻辑
    
    特点：
    - 封装初始化、涨跌停判断、指标计算等公共逻辑
    - 提供统一的接口规范
    - 派生类只需实现具体的交易执行逻辑
    
    统一返回格式：
    {
        'data': DataFrame,           # 包含信号、持仓、资产价值的完整数据
        'trades': DataFrame,         # 交易记录
        'stats': dict,               # 回测指标字典
        'version': str               # 回测引擎版本标识
    }
    """
    
    def __init__(self, initial_capital=None, transaction_fee=None, slippage=None):
        """
        初始化回测引擎
        
        :param initial_capital: 初始资金（默认从配置读取）
        :param transaction_fee: 交易手续费比例（默认万分之三）
        :param slippage: 滑点比例（默认万分之一）
        """
        self.initial_capital = initial_capital or Config.INITIAL_CAPITAL
        self.transaction_fee = transaction_fee or Config.TRANSACTION_FEE
        self.slippage = slippage or Config.SLIPPAGE
        self.version = 'base'  # 版本标识
    
    def _get_limit_ratio(self, is_st_stock, stock_symbol):
        """
        获取涨跌幅限制比例（调用公共工具函数）
        
        :param is_st_stock: 是否为ST股票
        :param stock_symbol: 股票代码
        :return: 涨跌幅限制比例
        """
        return get_limit_ratio(is_st_stock, stock_symbol)
    
    def calculate_metrics(self, df):
        """
        计算回测指标（调用公共工具函数）
        
        :param df: 包含portfolio列的回测结果数据
        :return: 指标字典
        """
        metrics = calculate_metrics(df, self.initial_capital)
        backtest_logger.info(f"[{self.__class__.__name__}] 回测完成 | 累计收益率={metrics['累计收益率']:.2%} | 最大回撤={metrics['最大回撤']:.2%}")
        return metrics
    
    def run_backtest(self, df, signal_column='signal', stop_loss_pct=0.0, take_profit_pct=0.0, 
                     is_st_stock=False, stock_symbol=None):
        """
        执行回测（派生类必须实现）
        
        :param df: 包含信号的数据（需包含 open, high, low, close）
        :param signal_column: 信号列名
        :param stop_loss_pct: 止损比例
        :param take_profit_pct: 止盈比例
        :param is_st_stock: 是否为ST股票
        :param stock_symbol: 股票代码
        :return: 统一格式的回测结果字典
        """
        raise NotImplementedError("派生类必须实现 run_backtest 方法")


class Backtester(BaseBacktester):
    """回测框架 - 循环版本（精确回测）
    
    特点：
    - 逐笔交易模拟，精确控制每笔交易
    - 适合复杂资金管理策略
    - 支持分批建仓、止损止盈等复杂逻辑
    - 性能相对较低，适合小规模数据
    """
    
    def __init__(self, initial_capital=None, transaction_fee=None, slippage=None):
        super().__init__(initial_capital, transaction_fee, slippage)
        self.version = 'loop'  # 标识版本
    
    def run_backtest(self, df, signal_column='signal', stop_loss_pct=0.0, take_profit_pct=0.0, 
                     is_st_stock=False, stock_symbol=None):
        """
        执行回测（循环版本）
        
        :param df: 包含信号的数据（需包含 open, high, low, close）
        :param signal_column: 信号列名
        :param stop_loss_pct: 止损比例（默认0表示不启用）
        :param take_profit_pct: 止盈比例（默认0表示不启用）
        :param is_st_stock: 是否为ST股票（ST涨跌幅限制为5%）
        :param stock_symbol: 股票代码（用于判断创业板/科创板，如 '300750'）
        :return: 统一格式的回测结果字典
        """
        backtest_logger.info(f"[Backtester] 开始回测 | 股票={stock_symbol} | 数据量={len(df)}条")
        df = df.copy()
        cash = self.initial_capital
        position = 0  # 持仓数量
        entry_price = 0  # 持仓成本价
        portfolio_value = []
        trade_log = []
        
        # 获取涨跌停限制比例
        limit_ratio = self._get_limit_ratio(is_st_stock, stock_symbol)
        
        # 计算涨跌停价格
        df['prev_close'] = df['close'].shift(1)
        df['limit_up'] = df['prev_close'] * (1 + limit_ratio)
        df['limit_down'] = df['prev_close'] * (1 - limit_ratio)
        
        # 初始化结果列
        df['cash'] = float(self.initial_capital)
        df['position'] = 0.0
        df['trade_executed'] = 0  # 标记实际执行的交易：1=买入，-1=卖出
        
        # 逐行遍历数据
        for i in range(len(df)):    
            date = df.index[i]
            close_price = df['close'].iloc[i]
            open_price = df['open'].iloc[i] if 'open' in df.columns else close_price
            high_price = df['high'].iloc[i] if 'high' in df.columns else close_price
            low_price = df['low'].iloc[i] if 'low' in df.columns else close_price
            signal = df[signal_column].iloc[i]
            
            # 检查停牌：当日无价格变动或价格为0
            is_suspended = False
            if 'volume' in df.columns and df['volume'].iloc[i] == 0:
                is_suspended = True
            elif high_price == low_price == open_price == close_price == 0:
                is_suspended = True
            
            if not is_suspended:
                # 止损逻辑
                if position > 0 and entry_price > 0 and stop_loss_pct > 0:
                    current_return = (close_price - entry_price) / entry_price
                    if current_return < -stop_loss_pct:
                        # 卖出止损
                        sell_price = max(close_price * (1 - self.slippage), df['limit_down'].iloc[i])
                        revenue = position * sell_price * (1 - self.transaction_fee)
                        cash += revenue
                        trade_log.append({
                            'date': date,
                            'type': 'sell_stop',
                            'price': sell_price,
                            'shares': position,
                            'cash': cash,
                            'reason': f'止损 {current_return:.2%}'
                        })
                        position = 0
                        entry_price = 0
                
                # 止盈逻辑
                if position > 0 and entry_price > 0 and take_profit_pct > 0:
                    current_return = (close_price - entry_price) / entry_price
                    if current_return > take_profit_pct:
                        # 卖出止盈
                        sell_price = min(close_price * (1 - self.slippage), df['limit_up'].iloc[i])
                        revenue = position * sell_price * (1 - self.transaction_fee)
                        cash += revenue
                        trade_log.append({
                            'date': date,
                            'type': 'sell_take',
                            'price': sell_price,
                            'shares': position,
                            'cash': cash,
                            'reason': f'止盈 {current_return:.2%}'
                        })
                        position = 0
                        entry_price = 0
                
                # 信号执行
                if signal == 1 and position == 0:
                    # 买入信号
                    buy_price = min(close_price * (1 + self.slippage), df['limit_up'].iloc[i])
                    max_shares = int(cash // (buy_price * (1 + self.transaction_fee)))
                    if max_shares > 0:
                        cost = max_shares * buy_price * (1 + self.transaction_fee)
                        cash -= cost
                        position = max_shares
                        entry_price = buy_price
                        trade_log.append({
                            'date': date,
                            'type': 'buy',
                            'price': buy_price,
                            'shares': max_shares,
                            'cash': cash,
                            'reason': '策略信号'
                        })
                
                elif signal == -1 and position > 0:
                    # 卖出信号
                    sell_price = max(close_price * (1 - self.slippage), df['limit_down'].iloc[i])
                    if sell_price <= df['limit_down'].iloc[i] + ERROR_MARGIN:
                        trade_log.append({
                            'date': date,
                            'type': 'sell_failed',
                            'price': close_price,
                            'shares': 0,
                            'cash': cash,
                            'reason': f'跌停无法卖出'
                        })
                    else:
                        # 卖出时价格不能低于跌停价
                        price = max(close_price * (1 - self.slippage), df['limit_down'].iloc[i])
                        revenue = position * price * (1 - self.transaction_fee)
                        cash += revenue
                        trade_log.append({
                            'date': date,
                            'type': 'sell_signal',
                            'price': price,
                            'shares': position,
                            'cash': cash,
                            'reason': '策略信号'
                        })
                        position = 0
                        entry_price = 0
            
            # 计算资产总值
            total_value = cash + position * close_price
            portfolio_value.append(total_value)
            
            # 更新当前行的cash和position
            df.loc[date, 'cash'] = cash
            df.loc[date, 'position'] = position
            
            # 标记交易执行
            if len(trade_log) > 0 and trade_log[-1]['date'] == date:
                df.loc[date, 'trade_executed'] = 1 if trade_log[-1]['type'] == 'buy' else -1
        
        # 整理结果
        df['portfolio'] = portfolio_value
        
        # 计算指标
        stats = self.calculate_metrics(df)
        
        # 返回统一格式
        return {
            'data': df,
            'trades': pd.DataFrame(trade_log),
            'stats': stats,
            'version': self.version
        }


class BacktesterFactory:
    """回测引擎工厂类 - 策略模式
    
    根据需求选择不同的回测引擎：
    - vectorized: 真正向量化版本，适合简单策略和大规模数据快速初筛
    - loop: 循环版本，适合复杂策略和精确控制
    """
    
    @staticmethod
    def create_backtester(strategy_type=None, vectorized=True):
        """
        创建回测引擎实例
        
        :param strategy_type: 策略类型（可选）
        :param vectorized: 是否使用向量化版本
        :return: 回测引擎实例
        """
        if vectorized:
            # 使用真正的向量化版本
            from .true_vectorized import TrueVectorizedBacktester
            return TrueVectorizedBacktester()
        else:
            return Backtester()
    
    @staticmethod
    def create_by_strategy(strategy_type):
        """
        根据策略类型创建回测引擎
        
        :param strategy_type: 策略类型（如 'dual_ma', 'bollinger' 等）
        :return: 回测引擎实例
        """
        # 简单策略使用向量化版本，复杂策略使用循环版本
        simple_strategies = ['dual_ma', 'bollinger', 'simple_momentum']
        
        if strategy_type in simple_strategies:
            from .true_vectorized import TrueVectorizedBacktester
            return TrueVectorizedBacktester()
        else:
            return Backtester()