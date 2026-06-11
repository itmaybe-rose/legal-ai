# 回测引擎测试文件
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import pandas as pd
from src.backtester import Backtester, VectorizedBacktester, BacktesterFactory
from src.data_fetcher import DataFetcher
from src.strategies import DualMAStrategy, BollingerBandStrategy
from config import Config


def test_backtester_versions():
    """测试向量化版本和循环版本的一致性"""
    print("=" * 60)
    print("双策略回测引擎对比测试")
    print("=" * 60)
    
    # 1. 获取数据
    fetcher = DataFetcher()
    df = fetcher.fetch_stock_data(
        symbol=Config.DEFAULT_SYMBOL,
        start_date=Config.DEFAULT_START_DATE,
        end_date=Config.DEFAULT_END_DATE
    )
    
    if df is None:
        print("[ERROR] 数据获取失败")
        return
    
    # 2. 应用策略
    strategy = DualMAStrategy()
    df = strategy.calculate_signals(df)
    
    # 3. 测试向量化版本
    print("\n[测试1] 向量化版本回测")
    start_time = time.time()
    vectorized_backtester = BacktesterFactory.create_backtester(vectorized=True)
    result_vec = vectorized_backtester.run_backtest(df)
    df_vec = result_vec['data']
    trades_vec = result_vec['trades']
    metrics_vec = result_vec['stats']
    elapsed_vec = time.time() - start_time
    
    print(f"版本类型: {vectorized_backtester.version}")
    print(f"执行时间: {elapsed_vec:.4f} 秒")
    print("回测指标:")
    for key, value in metrics_vec.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.4f}")
        else:
            print(f"  {key}: {value}")
    
    # 4. 测试循环版本
    print("\n[测试2] 循环版本回测")
    start_time = time.time()
    loop_backtester = BacktesterFactory.create_backtester(vectorized=False)
    result_loop = loop_backtester.run_backtest(df)
    df_loop = result_loop['data']
    trades_loop = result_loop['trades']
    metrics_loop = result_loop['stats']
    elapsed_loop = time.time() - start_time
    
    print(f"版本类型: {loop_backtester.version}")
    print(f"执行时间: {elapsed_loop:.4f} 秒")
    print("回测指标:")
    for key, value in metrics_loop.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.4f}")
        else:
            print(f"  {key}: {value}")
    
    # 5. 对比结果
    print("\n[结果对比]")
    print(f"性能提升: {elapsed_loop / elapsed_vec:.2f} 倍")
    print(f"结果一致性（最终资金差）: {abs(metrics_vec['最终资金'] - metrics_loop['最终资金']):.2f} 元")
    
    # 验证结果一致性
    assert abs(metrics_vec['最终资金'] - metrics_loop['最终资金']) < 0.01, \
        f"结果不一致: {metrics_vec['最终资金']} vs {metrics_loop['最终资金']}"
    print("[OK] 结果一致性验证通过")


def test_factory_pattern():
    """测试工厂模式按策略类型选择"""
    print("\n[测试3] 工厂模式按策略类型选择")
    
    # 简单策略应该使用向量化版本
    bt_simple = BacktesterFactory.create_by_strategy('dual_ma')
    assert bt_simple.version == 'vectorized', "双均线策略应该使用向量化版本"
    print(f"双均线策略 -> {bt_simple.version} 版本 [OK]")
    
    bt_bollinger = BacktesterFactory.create_by_strategy('bollinger')
    assert bt_bollinger.version == 'vectorized', "布林带策略应该使用向量化版本"
    print(f"布林带策略 -> {bt_bollinger.version} 版本 [OK]")
    
    # 复杂策略应该使用循环版本
    bt_complex = BacktesterFactory.create_by_strategy('stop_loss')
    assert bt_complex.version == 'loop', "止损策略应该使用循环版本"
    print(f"止损策略 -> {bt_complex.version} 版本 [OK]")
    
    bt_dynamic = BacktesterFactory.create_by_strategy('dynamic_position')
    assert bt_dynamic.version == 'loop', "动态仓位策略应该使用循环版本"
    print(f"动态仓位策略 -> {bt_dynamic.version} 版本 [OK]")
    
    # 未知策略默认使用向量化版本
    bt_unknown = BacktesterFactory.create_by_strategy('unknown')
    assert bt_unknown.version == 'vectorized', "未知策略应该默认使用向量化版本"
    print(f"未知策略 -> {bt_unknown.version} 版本 [OK]")


def test_strategy_signals():
    """测试不同策略的信号生成"""
    print("\n[测试4] 策略信号生成测试")
    
    fetcher = DataFetcher()
    df = fetcher.fetch_stock_data(
        symbol=Config.DEFAULT_SYMBOL,
        start_date=Config.DEFAULT_START_DATE,
        end_date=Config.DEFAULT_END_DATE
    )
    
    if df is None:
        print("[ERROR] 数据获取失败")
        return
    
    # 测试双均线策略
    strategy_ma = DualMAStrategy()
    df_ma = strategy_ma.calculate_signals(df)
    ma_signals = df_ma['signal'].abs().sum()
    print(f"双均线策略信号数量: {int(ma_signals)}")
    
    # 测试布林带策略
    strategy_bb = BollingerBandStrategy()
    df_bb = strategy_bb.calculate_signals(df)
    bb_signals = df_bb['signal'].abs().sum()
    print(f"布林带策略信号数量: {int(bb_signals)}")
    
    print("[OK] 策略信号生成测试通过")


if __name__ == "__main__":
    try:
        test_backtester_versions()
        test_factory_pattern()
        test_strategy_signals()
        print("\n" + "=" * 60)
        print("[SUCCESS] 所有测试通过！")
        print("=" * 60)
    except Exception as e:
        print(f"\n[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()