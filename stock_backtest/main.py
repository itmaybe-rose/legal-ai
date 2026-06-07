# 股票策略回测系统主入口
import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import Config
from src.data_fetcher import DataFetcher
from src.strategies import DualMAStrategy, BollingerBandStrategy
from src.backtester import Backtester
from src.optimizer import ParameterOptimizer
from src.cross_validator import CrossValidator
import pandas as pd
import os

def run_backtest_cli(symbol, start_date, end_date, strategy_type='dual_ma'):
    """
    命令行回测接口
    """
    print(f"股票策略回测系统")
    print(f"股票代码: {symbol}")
    print(f"时间范围: {start_date} ~ {end_date}")
    print(f"策略类型: {'双均线策略' if strategy_type == 'dual_ma' else '布林带策略'}")
    print("-" * 50)
    
    # 获取数据
    fetcher = DataFetcher()
    df = fetcher.fetch_stock_data(symbol, start_date, end_date)
    
    if df is None or df.empty:
        print("错误：获取数据失败")
        return
    
    # 检查是否为ST股票（传入已获取的数据，避免重复API调用）
    is_st = fetcher.is_st_stock(symbol, df)
    stock_type = "ST股票" if is_st else "普通股票"
    print(f"股票类型: {stock_type} (涨跌幅限制: {'±5%' if is_st else '±10%'})")
    print(f"数据类型: 前复权")
    print("-" * 50)
    
    # 选择策略
    if strategy_type == 'dual_ma':
        strategy = DualMAStrategy()
        strategy_name = "双均线策略"
    else:
        strategy = BollingerBandStrategy()
        strategy_name = "布林带策略"
    
    # 计算信号
    df = strategy.calculate_signals(df)
    
    # 执行回测（传入是否为ST股票）
    backtester = Backtester()
    df_result, trades = backtester.run_backtest(df, is_st_stock=is_st)
    
    # 计算指标
    metrics = backtester.calculate_metrics(df_result)
    
    # 输出结果
    print(f"\n【{strategy_name}回测结果】")
    print("=" * 50)
    print(f"初始资金: {metrics['初始资金']:,.2f} 元")
    print(f"最终资金: {metrics['最终资金']:,.2f} 元")
    print(f"累计收益率: {metrics['累计收益率']:.2%}")
    print(f"年化收益率: {metrics['年化收益率']:.2%}")
    print(f"最大回撤: {metrics['最大回撤']:.2%}")
    print(f"Sharpe比率: {metrics['Sharpe比率']:.2f}")
    print(f"胜率: {metrics['胜率']:.2%}")
    print(f"交易天数: {metrics['交易天数']} 天")
    print(f"策略收益: {metrics['策略收益']:,.2f} 元")
    print(f"股票类型: {stock_type}")
    print(f"涨跌幅限制: {'±5%' if is_st else '±10%'}")
    print("=" * 50)
    
    # 输出交易记录
    print(f"\n【交易记录】")
    if len(trades) > 0:
        trades['date'] = trades['date'].dt.strftime('%Y-%m-%d')
        print(trades.to_string(index=False))
    else:
        print("没有产生交易")
    
    # 保存结果
    output_file = f"data/{symbol}_{strategy_type}_result.csv"
    df_result.to_csv(output_file)
    print(f"\n回测结果已保存到: {output_file}")

def optimize_parameters_cli(symbol, start_date, end_date, strategy_type='dual_ma'):
    """
    命令行参数优化接口
    """
    print(f"股票策略参数优化")
    print(f"股票代码: {symbol}")
    print(f"时间范围: {start_date} ~ {end_date}")
    print(f"策略类型: {'双均线策略' if strategy_type == 'dual_ma' else '布林带策略'}")
    print("-" * 50)
    
    optimizer = ParameterOptimizer()
    
    if strategy_type == 'dual_ma':
        results = optimizer.optimize_dual_ma(symbol, start_date, end_date)
    else:
        results = optimizer.optimize_bollinger(symbol, start_date, end_date)
    
    if results is None or results.empty:
        print("参数优化失败")
        return
    
    # 输出最优参数
    best_params = optimizer.get_best_parameters(results, strategy_type)
    print("\n【最优参数】")
    print("=" * 50)
    if strategy_type == 'dual_ma':
        print(f"短期均线窗口: {best_params['short_window']}")
        print(f"长期均线窗口: {best_params['long_window']}")
    else:
        print(f"布林带窗口: {best_params['window']}")
        print(f"标准差倍数: {best_params['std_dev']}")
    print(f"年化收益率: {best_params['年化收益率']:.2%}")
    print(f"最大回撤: {best_params['最大回撤']:.2%}")
    print(f"Sharpe比率: {best_params['Sharpe比率']:.2f}")
    print("=" * 50)
    
    # 输出前10个最佳参数组合
    print("\n【前10个最佳参数组合】")
    print(results.head(10).to_string(index=False))
    
    # 保存结果
    output_file = f"data/{symbol}_{strategy_type}_optimization_result.csv"
    results.to_csv(output_file, index=False)
    print(f"\n优化结果已保存到: {output_file}")


def cross_validate_cli(symbol, start_date, end_date, strategy_type='dual_ma', use_optimal=False):
    """
    命令行交叉验证接口
    """
    print(f"股票策略交叉验证")
    print(f"股票代码: {symbol}")
    print(f"时间范围: {start_date} ~ {end_date}")
    print(f"策略类型: {'双均线策略' if strategy_type == 'dual_ma' else '布林带策略'}")
    print("-" * 50)
    
    # 尝试从优化结果文件读取最优参数
    params = None
    if use_optimal:
        opt_file = f"data/{symbol}_{strategy_type}_optimization_result.csv"
        if os.path.exists(opt_file):
            opt_results = pd.read_csv(opt_file)
            if not opt_results.empty:
                best_row = opt_results.iloc[0]
                if strategy_type == 'dual_ma':
                    params = {
                        'short_window': int(best_row['short_window']),
                        'long_window': int(best_row['long_window'])
                    }
                else:
                    params = {
                        'window': int(best_row['window']),
                        'std_dev': best_row['std_dev']
                    }
                print(f"已加载优化参数: {params}")
    
    # 如果没有最优参数，使用默认参数
    if params is None:
        if strategy_type == 'dual_ma':
            params = {
                'short_window': Config.MA_SHORT_WINDOW,
                'long_window': Config.MA_LONG_WINDOW
            }
        else:
            params = {
                'window': Config.BB_WINDOW,
                'std_dev': Config.BB_STD_DEV
            }
        print(f"使用默认参数: {params}")
    
    validator = CrossValidator()
    report = validator.evaluate_overfitting(
        symbol, start_date, end_date,
        strategy_type,
        **params
    )
    
    if report:
        validator.print_report(report)


if __name__ == "__main__":
    # 解析命令行参数
    import argparse
    parser = argparse.ArgumentParser(description="股票策略回测系统")
    parser.add_argument("-s", "--symbol", default=Config.DEFAULT_SYMBOL, help="股票代码")
    parser.add_argument("-start", "--start_date", default=Config.DEFAULT_START_DATE, help="开始日期")
    parser.add_argument("-end", "--end_date", default=Config.DEFAULT_END_DATE, help="结束日期")
    parser.add_argument("-strategy", "--strategy_type", default='dual_ma', choices=['dual_ma', 'bollinger'], help="策略类型")
    parser.add_argument("-optimize", action='store_true', help="执行参数优化")
    parser.add_argument("-validate", action='store_true', help="执行交叉验证")
    parser.add_argument("-use-optimal", action='store_true', help="使用优化后的参数进行交叉验证")
    
    args = parser.parse_args()
    
    if args.validate:
        cross_validate_cli(args.symbol, args.start_date, args.end_date, args.strategy_type, args.use_optimal)
    elif args.optimize:
        optimize_parameters_cli(args.symbol, args.start_date, args.end_date, args.strategy_type)
    else:
        run_backtest_cli(args.symbol, args.start_date, args.end_date, args.strategy_type)
