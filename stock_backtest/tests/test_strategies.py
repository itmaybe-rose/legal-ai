# 策略模块测试文件
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_fetcher import DataFetcher
from src.strategies import DualMAStrategy, BollingerBandStrategy
from config import Config


def test_dual_ma_strategy():
    """测试双均线策略"""
    print("=" * 60)
    print("测试双均线策略")
    print("=" * 60)
    
    fetcher = DataFetcher()
    df = fetcher.fetch_stock_data(
        symbol=Config.DEFAULT_SYMBOL,
        start_date=Config.DEFAULT_START_DATE,
        end_date=Config.DEFAULT_END_DATE
    )
    
    if df is None:
        print("[ERROR] 数据获取失败")
        return
    
    strategy = DualMAStrategy()
    df_result = strategy.calculate_signals(df)
    
    print(f"策略参数:")
    print(f"  短期均线窗口: {strategy.short_window}")
    print(f"  长期均线窗口: {strategy.long_window}")
    
    # 统计信号
    buy_signals = len(df_result[df_result['signal'] == 1])
    sell_signals = len(df_result[df_result['signal'] == -1])
    
    print(f"\n信号统计:")
    print(f"  买入信号: {buy_signals}")
    print(f"  卖出信号: {sell_signals}")
    
    print("\n最近10条数据:")
    print(df_result[['close', 'short_ma', 'long_ma', 'signal']].tail(10))
    
    print("[OK] 双均线策略测试通过")


def test_bollinger_strategy():
    """测试布林带策略"""
    print("\n" + "=" * 60)
    print("测试布林带策略")
    print("=" * 60)
    
    fetcher = DataFetcher()
    df = fetcher.fetch_stock_data(
        symbol=Config.DEFAULT_SYMBOL,
        start_date=Config.DEFAULT_START_DATE,
        end_date=Config.DEFAULT_END_DATE
    )
    
    if df is None:
        print("[ERROR] 数据获取失败")
        return
    
    strategy = BollingerBandStrategy()
    df_result = strategy.calculate_signals(df)
    
    print(f"策略参数:")
    print(f"  窗口大小: {strategy.window}")
    print(f"  标准差倍数: {strategy.std_dev}")
    
    # 统计信号
    buy_signals = len(df_result[df_result['signal'] == 1])
    sell_signals = len(df_result[df_result['signal'] == -1])
    
    print(f"\n信号统计:")
    print(f"  买入信号: {buy_signals}")
    print(f"  卖出信号: {sell_signals}")
    
    print("\n最近10条数据:")
    print(df_result[['close', 'upper_band', 'middle_band', 'lower_band', 'signal']].tail(10))
    
    print("[OK] 布林带策略测试通过")


def test_strategy_parameters():
    """测试自定义参数"""
    print("\n" + "=" * 60)
    print("测试自定义参数")
    print("=" * 60)
    
    # 测试自定义均线参数
    strategy_ma = DualMAStrategy(short_window=3, long_window=10)
    assert strategy_ma.short_window == 3, "短期均线窗口设置错误"
    assert strategy_ma.long_window == 10, "长期均线窗口设置错误"
    print("[OK] 双均线策略自定义参数测试通过")
    
    # 测试自定义布林带参数
    strategy_bb = BollingerBandStrategy(window=30, std_dev=3.0)
    assert strategy_bb.window == 30, "布林带窗口设置错误"
    assert strategy_bb.std_dev == 3.0, "标准差倍数设置错误"
    print("[OK] 布林带策略自定义参数测试通过")


if __name__ == "__main__":
    try:
        test_dual_ma_strategy()
        test_bollinger_strategy()
        test_strategy_parameters()
        print("\n" + "=" * 60)
        print("[SUCCESS] 所有策略测试通过！")
        print("=" * 60)
    except Exception as e:
        print(f"\n[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()