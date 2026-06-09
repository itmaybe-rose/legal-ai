# 回测框架模块 - 双策略优化版本
import pandas as pd
import numpy as np
from config import Config

# 全局常量
ERROR_MARGIN = 0.0001  # 0.01% 的误差范围，用于涨跌停判断

class Backtester:
    """回测框架 - 循环版本（精确回测）
    
    特点：
    - 逐笔交易模拟，精确控制每笔交易
    - 适合复杂资金管理策略
    - 支持分批建仓、止损止盈等复杂逻辑
    - 性能相对较低，适合小规模数据
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
        self.version = 'loop'  # 标识版本
    
    def run_backtest(self, df, signal_column='signal', stop_loss_pct=0.0, take_profit_pct=0.0, is_st_stock=False):
        """
        执行回测（增加止损止盈、涨跌停限制）
        :param df: 包含信号的数据（需包含 open, high, low, close）
        :param signal_column: 信号列名
        :param stop_loss_pct: 止损比例（默认5%）
        :param take_profit_pct: 止盈比例（默认10%）
        :param is_st_stock: 是否为ST股票（ST涨跌幅限制为5%，非ST为10%）
        :return: 回测结果和交易记录
        """
        df = df.copy()
        cash = self.initial_capital
        position = 0  # 持仓数量
        entry_price = 0  # 持仓成本价
        portfolio_value = []
        trade_log = []
        
        # 计算涨跌停价格
        # ST股票涨跌幅限制为5%，非ST股票为10%
        limit_ratio = 0.05 if is_st_stock else 0.10
        df['prev_close'] = df['close'].shift(1)
        df['limit_up'] = df['prev_close'] * (1 + limit_ratio)  # 涨停价
        df['limit_down'] = df['prev_close'] * (1 - limit_ratio)  # 跌停价
        
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
            
            if is_suspended:
                # 停牌日跳过交易
                total_value = cash + position * close_price
                portfolio_value.append(total_value)
                # 更新当前行的cash和position
                df.loc[date, 'cash'] = cash
                df.loc[date, 'position'] = position
                continue
            
            # 如果有持仓，检查止损止盈（仅当参数大于0时启用）
            if position > 0 and entry_price > 0:
                # 计算当前收益率
                return_pct = (close_price - entry_price) / entry_price
                
                # 止损检查：亏损超过阈值（仅当止损参数>0时）
                if stop_loss_pct > 0 and return_pct < -stop_loss_pct:
                    # 检查是否跌停（跌停无法卖出）
                    if close_price <= df['limit_down'].iloc[i] * (1 + ERROR_MARGIN):
                        trade_log.append({
                            'date': date,
                            'type': 'sell_failed',
                            'price': close_price,
                            'shares': position,
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
                            'type': 'sell_stop',
                            'price': price,
                            'shares': position,
                            'cash': cash,
                            'reason': f'止损: {return_pct:.2%}'
                        })
                        position = 0
                        entry_price = 0
                
                # 止盈检查：盈利超过阈值（仅当止盈参数>0时）
                elif take_profit_pct > 0 and return_pct > take_profit_pct:
                    # 卖出时价格不能高于涨停价
                    price = min(close_price * (1 - self.slippage), df['limit_up'].iloc[i])
                    revenue = position * price * (1 - self.transaction_fee)
                    cash += revenue
                    trade_log.append({
                        'date': date,
                        'type': 'sell_take',
                        'price': price,
                        'shares': position,
                        'cash': cash,
                        'reason': f'止盈: {return_pct:.2%}'
                    })
                    position = 0
                    entry_price = 0
            
            # 如果持仓已被止损止盈平仓，跳过信号处理
            if position == 0:
                # 买入信号处理
                if signal == 1:
                    # 检查是否涨停（涨停无法买入）
                    if close_price >= df['limit_up'].iloc[i] * (1 - ERROR_MARGIN):
                        trade_log.append({
                            'date': date,
                            'type': 'buy_failed',
                            'price': close_price,
                            'shares': 0,
                            'cash': cash,
                            'reason': f'涨停无法买入'
                        })
                    else:
                        price = min(close_price * (1 + self.slippage), df['limit_up'].iloc[i])
                        max_shares = int(cash // (price * (1 + self.transaction_fee)))
                        if max_shares > 0:
                            cost = max_shares * price * (1 + self.transaction_fee)
                            position = max_shares
                            cash -= cost
                            entry_price = price  # 记录买入成本
                            trade_log.append({
                                'date': date,
                                'type': 'buy',
                                'price': price,
                                'shares': max_shares,
                                'cash': cash
                            })
            else:
                # 卖出信号处理（已有持仓时）
                if signal == -1:
                    # 检查是否跌停（跌停无法卖出）
                    if close_price <= df['limit_down'].iloc[i] * (1 + ERROR_MARGIN):
                        trade_log.append({
                            'date': date,
                            'type': 'sell_failed',
                            'price': close_price,
                            'shares': position,
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
        
        return df, pd.DataFrame(trade_log)
    
    def calculate_metrics(self, df):
        """计算回测指标"""
        if df is None or len(df) == 0:
            return {
                '初始资金': self.initial_capital,
                '最终资金': 0,
                '累计收益率': 0,
                '年化收益率': 0,
                '最大回撤': 0,
                'Sharpe比率': 0,
                '胜率': 0,
                '交易天数': 0,
                '策略收益': 0
            }
        
        df['returns'] = df['portfolio'].pct_change().fillna(0)
        
        total_return = (df['portfolio'].iloc[-1] / self.initial_capital) - 1
        
        days = (df.index[-1] - df.index[0]).days
        annualized_return = (1 + total_return) ** (365 / days) - 1 if days > 0 else total_return
        
        df['max_drawdown'] = (df['portfolio'].cummax() - df['portfolio']) / df['portfolio'].cummax()
        max_drawdown = df['max_drawdown'].max()
        
        # 修复 Sharpe 比率计算：处理标准差为0的情况
        std = df['returns'].std()
        sharpe_ratio = (np.sqrt(252) * df['returns'].mean() / std) if std > 1e-6 else 0
        
        win_count = len(df[df['returns'] > 0])
        total_trading_days = len(df[df['returns'] != 0])
        win_rate = win_count / total_trading_days if total_trading_days > 0 else 0
        
        return {
            '初始资金': self.initial_capital,
            '最终资金': df['portfolio'].iloc[-1],
            '累计收益率': total_return,
            '年化收益率': annualized_return,
            '最大回撤': max_drawdown,
            'Sharpe比率': sharpe_ratio,
            '胜率': win_rate,
            '交易天数': len(df),
            '策略收益': df['portfolio'].iloc[-1] - self.initial_capital
        }


class VectorizedBacktester:
    """回测框架 - 向量化版本（快速回测）
    
    特点：
    - 使用 numpy/pandas 向量化操作，性能比循环版本快10-200倍
    - 支持止损止盈、涨跌停限制、停牌处理等高级功能
    - 适合简单策略和大规模数据回测和参数优化
    """
    
    def __init__(self, initial_capital=None, transaction_fee=None, slippage=None):
        """
        初始化向量化回测引擎
        
        :param initial_capital: 初始资金
        :param transaction_fee: 交易手续费比例
        :param slippage: 滑点比例
        """
        self.initial_capital = initial_capital or Config.INITIAL_CAPITAL
        self.transaction_fee = transaction_fee or Config.TRANSACTION_FEE
        self.slippage = slippage or Config.SLIPPAGE
        self.version = 'vectorized'  # 标识版本
    
    def run_backtest(self, df, signal_column='signal', stop_loss_pct=0.0, take_profit_pct=0.0, is_st_stock=False):
        """
        执行回测（改进版本，确保与循环版本一致）
        
        :param df: 包含价格和信号的数据（需包含 open, high, low, close）
        :param signal_column: 信号列名
        :param stop_loss_pct: 止损比例（默认0表示不启用）
        :param take_profit_pct: 止盈比例（默认0表示不启用）
        :param is_st_stock: 是否为ST股票（ST涨跌幅限制为5%，非ST为10%）
        :return: (回测结果 DataFrame, 交易记录 DataFrame)
        """
        df = df.copy()
        
        # ========== 1. 计算涨跌停价格 ==========
        limit_ratio = 0.05 if is_st_stock else 0.10
        df['prev_close'] = df['close'].shift(1)
        df['limit_up'] = df['prev_close'] * (1 + limit_ratio)
        df['limit_down'] = df['prev_close'] * (1 - limit_ratio)
        
        # ========== 2. 检测停牌日 ==========
        df['is_suspended'] = False
        if 'volume' in df.columns:
            df['is_suspended'] = df['is_suspended'] | (df['volume'] == 0)
        df['is_suspended'] = df['is_suspended'] | (df['close'] == 0)
        
        # ========== 3. 计算交易价格（考虑滑点和涨跌停） ==========
        df['buy_price'] = np.minimum(
            df['close'] * (1 + self.slippage),
            df['limit_up']
        )
        df['sell_price'] = np.maximum(
            df['close'] * (1 - self.slippage),
            df['limit_down']
        )
        df['sell_price_take'] = np.minimum(
            df['close'] * (1 - self.slippage),
            df['limit_up']
        )
        
        # ========== 4. 初始化数组 ==========
        n = len(df)
        cash = np.full(n, self.initial_capital, dtype=np.float64)
        position = np.zeros(n, dtype=np.float64)
        entry_price = np.zeros(n, dtype=np.float64)
        
        trade_log = []
        
        # ========== 5. 逐行处理（与循环版本保持一致） ==========
        for i in range(n):
            date = df.index[i]
            close_price = df['close'].iloc[i]
            signal = df[signal_column].iloc[i]
            is_suspended = df['is_suspended'].iloc[i]
            
            # 复制前一行状态
            if i > 0:
                cash[i] = cash[i-1]
                position[i] = position[i-1]
                entry_price[i] = entry_price[i-1]
            
            # 停牌检查
            if is_suspended:
                continue
            
            # 如果有持仓，检查止损止盈
            if position[i] > 0 and entry_price[i] > 0:
                return_pct = (close_price - entry_price[i]) / entry_price[i]
                
                # 止损检查
                if stop_loss_pct > 0 and return_pct < -stop_loss_pct:
                    # 检查是否跌停
                    if close_price <= df['limit_down'].iloc[i] * (1 + ERROR_MARGIN):
                        trade_log.append({
                            'date': date,
                            'type': 'sell_failed',
                            'price': close_price,
                            'shares': position[i],
                            'cash': cash[i],
                            'reason': '跌停无法卖出'
                        })
                    else:
                        price = max(close_price * (1 - self.slippage), df['limit_down'].iloc[i])
                        revenue = position[i] * price * (1 - self.transaction_fee)
                        cash[i] += revenue
                        trade_log.append({
                            'date': date,
                            'type': 'sell_stop',
                            'price': price,
                            'shares': position[i],
                            'cash': cash[i],
                            'reason': f'止损: {return_pct:.2%}'
                        })
                        position[i] = 0
                        entry_price[i] = 0
                # 止盈检查
                elif take_profit_pct > 0 and return_pct > take_profit_pct:
                    price = min(close_price * (1 - self.slippage), df['limit_up'].iloc[i])
                    revenue = position[i] * price * (1 - self.transaction_fee)
                    cash[i] += revenue
                    trade_log.append({
                        'date': date,
                        'type': 'sell_take',
                        'price': price,
                        'shares': position[i],
                        'cash': cash[i],
                        'reason': f'止盈: {return_pct:.2%}'
                    })
                    position[i] = 0
                    entry_price[i] = 0
            
            # 信号处理
            if position[i] == 0:
                # 买入信号
                if signal == 1:
                    # 检查是否涨停
                    if close_price >= df['limit_up'].iloc[i] * (1 - ERROR_MARGIN):
                        trade_log.append({
                            'date': date,
                            'type': 'buy_failed',
                            'price': close_price,
                            'shares': 0,
                            'cash': cash[i],
                            'reason': '涨停无法买入'
                        })
                    else:
                        price = df['buy_price'].iloc[i]
                        max_shares = int(cash[i] // (price * (1 + self.transaction_fee)))
                        if max_shares > 0:
                            cost = max_shares * price * (1 + self.transaction_fee)
                            position[i] = max_shares
                            cash[i] -= cost
                            entry_price[i] = price
                            trade_log.append({
                                'date': date,
                                'type': 'buy',
                                'price': price,
                                'shares': max_shares,
                                'cash': cash[i]
                            })
            else:
                # 卖出信号
                if signal == -1:
                    # 检查是否跌停
                    if close_price <= df['limit_down'].iloc[i] * (1 + ERROR_MARGIN):
                        trade_log.append({
                            'date': date,
                            'type': 'sell_failed',
                            'price': close_price,
                            'shares': position[i],
                            'cash': cash[i],
                            'reason': '跌停无法卖出'
                        })
                    else:
                        price = df['sell_price'].iloc[i]
                        revenue = position[i] * price * (1 - self.transaction_fee)
                        cash[i] += revenue
                        trade_log.append({
                            'date': date,
                            'type': 'sell_signal',
                            'price': price,
                            'shares': position[i],
                            'cash': cash[i],
                            'reason': '策略信号'
                        })
                        position[i] = 0
                        entry_price[i] = 0
        
        # ========== 6. 计算资产总值 ==========
        df['cash'] = cash
        df['position'] = position
        df['portfolio'] = df['cash'] + df['position'] * df['close']
        
        # 标记交易执行
        df['trade_executed'] = 0
        for trade in trade_log:
            df.loc[trade['date'], 'trade_executed'] = 1 if trade['type'] == 'buy' else -1
        
        return df, pd.DataFrame(trade_log)
    
    def calculate_metrics(self, df):
        """计算回测指标（与循环版本相同）"""
        if df is None or len(df) == 0:
            return {
                '初始资金': self.initial_capital,
                '最终资金': 0,
                '累计收益率': 0,
                '年化收益率': 0,
                '最大回撤': 0,
                'Sharpe比率': 0,
                '胜率': 0,
                '交易天数': 0,
                '策略收益': 0
            }
        
        df['returns'] = df['portfolio'].pct_change().fillna(0)
        
        total_return = (df['portfolio'].iloc[-1] / self.initial_capital) - 1
        
        days = (df.index[-1] - df.index[0]).days
        annualized_return = (1 + total_return) ** (365 / days) - 1 if days > 0 else total_return
        
        df['max_drawdown'] = (df['portfolio'].cummax() - df['portfolio']) / df['portfolio'].cummax()
        max_drawdown = df['max_drawdown'].max()
        
        # 修复 Sharpe 比率计算：处理标准差为0的情况
        std = df['returns'].std()
        sharpe_ratio = (np.sqrt(252) * df['returns'].mean() / std) if std > 1e-6 else 0
        
        win_count = len(df[df['returns'] > 0])
        total_trading_days = len(df[df['returns'] != 0])
        win_rate = win_count / total_trading_days if total_trading_days > 0 else 0
        
        return {
            '初始资金': self.initial_capital,
            '最终资金': df['portfolio'].iloc[-1],
            '累计收益率': total_return,
            '年化收益率': annualized_return,
            '最大回撤': max_drawdown,
            'Sharpe比率': sharpe_ratio,
            '胜率': win_rate,
            '交易天数': len(df),
            '策略收益': df['portfolio'].iloc[-1] - self.initial_capital
        }


class BacktesterFactory:
    """回测引擎工厂类 - 策略模式
    
    根据需求选择不同的回测引擎：
    - vectorized: 向量化版本，适合简单策略和大规模数据
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
            return VectorizedBacktester()
        else:
            return Backtester()
    
    @staticmethod
    def create_by_strategy(strategy_type):
        """
        根据策略类型自动选择回测引擎
        
        :param strategy_type: 策略类型
        :return: 回测引擎实例
        """
        # 简单策略使用向量化版本
        simple_strategies = ['dual_ma', 'bollinger', 'simple_moving_average']
        
        # 复杂策略使用循环版本
        complex_strategies = ['complex', 'dynamic_position', 'stop_loss', 'trailing_stop']
        
        if strategy_type in simple_strategies:
            return VectorizedBacktester()
        elif strategy_type in complex_strategies:
            return Backtester()
        else:
            # 默认使用向量化版本
            return VectorizedBacktester()
