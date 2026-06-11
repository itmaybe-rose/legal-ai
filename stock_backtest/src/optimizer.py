# 参数优化模块
import pandas as pd
import numpy as np
from itertools import product
from .data_fetcher import DataFetcher
from .strategies import DualMAStrategy, BollingerBandStrategy
from .backtester import Backtester
from .logger import backtest_logger, log_function_call

class ParameterOptimizer:
    """参数优化器"""
    
    def __init__(self):
        self.fetcher = DataFetcher()
    
    def optimize_dual_ma(self, symbol, start_date, end_date, 
                         short_window_range=(5, 30), long_window_range=(20, 100),
                         step=5):
        """
        优化双均线策略参数
        
        :param symbol: 股票代码
        :param start_date: 开始日期
        :param end_date: 结束日期
        :param short_window_range: 短期均线窗口范围 (min, max)
        :param long_window_range: 长期均线窗口范围 (min, max)
        :param step: 步长
        :return: 优化结果 DataFrame
        """
        # 获取数据
        df = self.fetcher.fetch_stock_data(symbol, start_date, end_date)
        if df is None or df.empty:
            return None
        
        results = []
        
        # 生成参数组合
        short_windows = range(short_window_range[0], short_window_range[1] + 1, step)
        long_windows = range(long_window_range[0], long_window_range[1] + 1, step)
        
        total_combinations = len(list(short_windows)) * len(list(long_windows))
        current = 0
        
        for short_window, long_window in product(short_windows, long_windows):
            # 确保短期窗口小于长期窗口
            if short_window >= long_window:
                continue
            
            current += 1
            backtest_logger.info(f"正在测试参数组合 {current}/{total_combinations}: 短期均线={short_window}, 长期均线={long_window}")
            
            try:
                # 创建策略和回测器
                strategy = DualMAStrategy(short_window=short_window, long_window=long_window)
                backtester = Backtester()
                
                # 计算信号
                df_signals = strategy.calculate_signals(df)
                
                # 执行回测（带止损止盈）
                result = backtester.run_backtest(df_signals, stop_loss_pct=0.05, take_profit_pct=0.15, stock_symbol=symbol)
                
                # 提取结果（使用统一格式）
                df_result = result['data']
                trades = result['trades']
                metrics = result['stats']
                
                # 记录结果
                results.append({
                    'short_window': short_window,
                    'long_window': long_window,
                    '累计收益率': metrics['累计收益率'],
                    '年化收益率': metrics['年化收益率'],
                    '最大回撤': metrics['最大回撤'],
                    'Sharpe比率': metrics['Sharpe比率'],
                    '交易次数': len(trades),
                    '最终资金': metrics['最终资金']
                })
            except Exception as e:
                backtest_logger.error(f"参数组合 ({short_window}, {long_window}) 测试失败: {str(e)}")
        
        # 转换为DataFrame
        results_df = pd.DataFrame(results)
        
        if not results_df.empty:
            # 按年化收益率排序
            results_df = results_df.sort_values('年化收益率', ascending=False)
            results_df.reset_index(drop=True, inplace=True)
        
        return results_df
    
    def optimize_bollinger(self, symbol, start_date, end_date,
                          window_range=(10, 50), std_range=(1.5, 3.0),
                          window_step=5, std_step=0.25):
        """
        优化布林带策略参数
        
        :param symbol: 股票代码
        :param start_date: 开始日期
        :param end_date: 结束日期
        :param window_range: 窗口大小范围 (min, max)
        :param std_range: 标准差倍数范围 (min, max)
        :param window_step: 窗口步长
        :param std_step: 标准差步长
        :return: 优化结果 DataFrame
        """
        # 获取数据
        df = self.fetcher.fetch_stock_data(symbol, start_date, end_date)
        if df is None or df.empty:
            return None
        
        results = []
        
        # 生成参数组合
        windows = range(window_range[0], window_range[1] + 1, window_step)
        std_devs = np.arange(std_range[0], std_range[1] + std_step, std_step)
        
        total_combinations = len(list(windows)) * len(std_devs)
        current = 0
        
        for window, std_dev in product(windows, std_devs):
            current += 1
            std_dev_rounded = round(std_dev, 2)
            backtest_logger.info(f"正在测试参数组合 {current}/{total_combinations}: 窗口={window}, 标准差={std_dev_rounded}")
            
            try:
                # 创建策略和回测器
                strategy = BollingerBandStrategy(window=window, std_dev=std_dev)
                backtester = Backtester()
                
                # 计算信号
                df_signals = strategy.calculate_signals(df)
                
                # 执行回测（带止损止盈）
                result = backtester.run_backtest(df_signals, stop_loss_pct=0.05, take_profit_pct=0.15, stock_symbol=symbol)
                
                # 提取结果（使用统一格式）
                df_result = result['data']
                trades = result['trades']
                metrics = result['stats']
                
                # 记录结果
                results.append({
                    'window': window,
                    'std_dev': std_dev_rounded,
                    '累计收益率': metrics['累计收益率'],
                    '年化收益率': metrics['年化收益率'],
                    '最大回撤': metrics['最大回撤'],
                    'Sharpe比率': metrics['Sharpe比率'],
                    '交易次数': len(trades),
                    '最终资金': metrics['最终资金']
                })
            except Exception as e:
                backtest_logger.error(f"参数组合 ({window}, {std_dev_rounded}) 测试失败: {str(e)}")
        
        # 转换为DataFrame
        results_df = pd.DataFrame(results)
        
        if not results_df.empty:
            # 按年化收益率排序
            results_df = results_df.sort_values('年化收益率', ascending=False)
            results_df.reset_index(drop=True, inplace=True)
        
        return results_df
    
    def get_best_parameters(self, results_df, strategy_type='dual_ma'):
        """
        获取最优参数
        
        :param results_df: 优化结果 DataFrame
        :param strategy_type: 策略类型
        :return: 最优参数字典
        """
        if results_df is None or results_df.empty:
            return None
        
        # 获取最优参数（年化收益率最高）
        best_row = results_df.iloc[0]
        
        if strategy_type == 'dual_ma':
            return {
                'short_window': int(best_row['short_window']),
                'long_window': int(best_row['long_window']),
                '年化收益率': best_row['年化收益率'],
                '最大回撤': best_row['最大回撤'],
                'Sharpe比率': best_row['Sharpe比率']
            }
        else:
            return {
                'window': int(best_row['window']),
                'std_dev': best_row['std_dev'],
                '年化收益率': best_row['年化收益率'],
                '最大回撤': best_row['最大回撤'],
                'Sharpe比率': best_row['Sharpe比率']
            }