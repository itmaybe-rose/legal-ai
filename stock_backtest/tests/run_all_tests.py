# 统一测试运行器
# 运行所有测试用例

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests import test_backtester, test_strategies, test_data_fetcher


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 70)
    print(" " * 15 + "股票策略回测系统 - 完整测试套件")
    print("=" * 70 + "\n")
    
    tests = [
        ("回测引擎测试", test_backtester),
        ("策略模块测试", test_strategies),
        ("数据获取测试", test_data_fetcher),
    ]
    
    results = []
    
    for test_name, test_module in tests:
        try:
            print(f"\n{'=' * 70}")
            print(f"  开始执行: {test_name}")
            print(f"{'=' * 70}")
            
            # 运行测试模块中的所有测试函数
            test_funcs = [name for name in dir(test_module) if name.startswith('test_')]
            
            for func_name in test_funcs:
                func = getattr(test_module, func_name)
                if callable(func):
                    func()
            
            results.append((test_name, True, ""))
            print(f"\n[SUCCESS] {test_name} 通过")
            
        except Exception as e:
            results.append((test_name, False, str(e)))
            print(f"\n[ERROR] {test_name} 失败: {e}")
    
    # 汇总报告
    print("\n" + "=" * 70)
    print(" " * 20 + "测试结果汇总")
    print("=" * 70 + "\n")
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for test_name, success, error in results:
        status = "[PASS]" if success else "[FAIL]"
        print(f"  {status} {test_name}")
        if error:
            print(f"        错误: {error}")
    
    print(f"\n  总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n" + "=" * 70)
        print(" " * 20 + "[SUCCESS] 所有测试通过！")
        print("=" * 70 + "\n")
        return True
    else:
        print("\n" + "=" * 70)
        print(" " * 20 + "[WARNING] 部分测试失败")
        print("=" * 70 + "\n")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
