# 股票搜索功能测试
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_fetcher import DataFetcher


def test_stock_search():
    """测试股票搜索功能"""
    print("=" * 60)
    print("测试股票搜索功能")
    print("=" * 60)
    
    fetcher = DataFetcher()
    
    # 测试1：按名称搜索
    print("\n测试1：搜索 '茅台'")
    results = fetcher.search_stocks("茅台")
    print(f"找到 {len(results)} 个结果:")
    for stock in results[:5]:
        print(f"  {stock['label']}")
    
    # 测试2：按代码搜索
    print("\n测试2：搜索 '600519'")
    results = fetcher.search_stocks("600519")
    print(f"找到 {len(results)} 个结果:")
    for stock in results[:5]:
        print(f"  {stock['label']}")
    
    # 测试3：部分代码搜索
    print("\n测试3：搜索 '002'")
    results = fetcher.search_stocks("002")
    print(f"找到 {len(results)} 个结果:")
    for stock in results[:5]:
        print(f"  {stock['label']}")
    
    # 测试4：英文大写
    print("\n测试4：搜索 'GUOQI'")
    results = fetcher.search_stocks("GUOQI")
    print(f"找到 {len(results)} 个结果:")
    for stock in results[:5]:
        print(f"  {stock['label']}")
    
    print("\n[OK] 股票搜索功能测试通过")


if __name__ == "__main__":
    try:
        test_stock_search()
        print("\n" + "=" * 60)
        print("[SUCCESS] 股票搜索功能测试通过！")
        print("=" * 60)
    except Exception as e:
        print(f"\n[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
