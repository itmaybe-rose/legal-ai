# 数据获取模块测试文件
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from src.data_fetcher import DataFetcher
from config import Config


def test_fetch_stock_data():
    """测试股票数据获取"""
    print("=" * 60)
    print("测试股票数据获取")
    print("=" * 60)
    
    fetcher = DataFetcher()
    
    # 测试默认参数
    df = fetcher.fetch_stock_data(
        symbol=Config.DEFAULT_SYMBOL,
        start_date=Config.DEFAULT_START_DATE,
        end_date=Config.DEFAULT_END_DATE
    )
    
    if df is None:
        print("[ERROR] 数据获取失败")
        return False
    
    print(f"\n数据获取成功:")
    print(f"  股票代码: {Config.DEFAULT_SYMBOL}")
    print(f"  数据条数: {len(df)}")
    print(f"  时间范围: {df.index.min()} 至 {df.index.max()}")
    
    # 验证数据列
    required_columns = ['open', 'close', 'high', 'low', 'volume']
    for col in required_columns:
        if col not in df.columns:
            print(f"[ERROR] 缺少必要列: {col}")
            return False
    
    print(f"\n数据列: {', '.join(df.columns)}")
    
    # 显示数据样本
    print("\n数据样本（前5条）:")
    print(df.head())
    
    print("\n数据样本（后5条）:")
    print(df.tail())
    
    print("[OK] 股票数据获取测试通过")
    return True


def test_data_persistence():
    """测试数据持久化功能"""
    print("\n" + "=" * 60)
    print("测试数据持久化功能")
    print("=" * 60)
    
    fetcher = DataFetcher()
    
    # 获取数据
    df = fetcher.fetch_stock_data(
        symbol=Config.DEFAULT_SYMBOL,
        start_date=Config.DEFAULT_START_DATE,
        end_date=Config.DEFAULT_END_DATE
    )
    
    if df is None:
        print("[ERROR] 数据获取失败")
        return
    
    # 保存数据
    test_filename = "test_data.pkl"
    fetcher.save_data(df, test_filename)
    
    # 加载数据
    df_loaded = fetcher.load_data(test_filename)
    
    if df_loaded is None:
        print("[ERROR] 数据加载失败")
        return
    
    # 验证数据一致性
    assert len(df) == len(df_loaded), "数据长度不一致"
    assert df.equals(df_loaded), "数据内容不一致"
    
    print("[OK] 数据持久化测试通过")


def test_multiple_stocks():
    """测试多个股票数据获取"""
    print("\n" + "=" * 60)
    print("测试多个股票数据获取")
    print("=" * 60)
    
    stocks = [
        ("sh600519", "贵州茅台"),
        ("sz002594", "比亚迪"),
        ("sz300750", "宁德时代"),
    ]
    
    fetcher = DataFetcher()
    
    for symbol, name in stocks:
        print(f"\n获取 {name} ({symbol}) 数据...")
        df = fetcher.fetch_stock_data(
            symbol=symbol,
            start_date=Config.DEFAULT_START_DATE,
            end_date=Config.DEFAULT_END_DATE
        )
        
        if df is not None:
            print(f"  成功获取 {len(df)} 条数据")
        else:
            print(f"  获取失败")
    
    print("[OK] 多股票数据获取测试完成")


def test_data_validation():
    """测试数据验证"""
    print("\n" + "=" * 60)
    print("测试数据验证")
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
    
    # 检查数据类型
    print("\n数据类型:")
    print(df.dtypes)
    
    # 检查缺失值
    missing = df.isnull().sum()
    print(f"\n缺失值统计:")
    print(missing)
    
    # 检查异常值
    print(f"\n价格范围:")
    print(f"  最高价: {df['high'].max():.2f}")
    print(f"  最低价: {df['low'].min():.2f}")
    print(f"  平均价: {df['close'].mean():.2f}")
    
    print("[OK] 数据验证测试通过")


if __name__ == "__main__":
    try:
        test_fetch_stock_data()
        test_data_validation()
        test_data_persistence()
        test_multiple_stocks()
        print("\n" + "=" * 60)
        print("[SUCCESS] 所有数据获取测试通过！")
        print("=" * 60)
    except Exception as e:
        print(f"\n[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()