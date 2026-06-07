# 源代码包初始化文件
# 提供统一的模块导入接口

from .backtester import Backtester, VectorizedBacktester, BacktesterFactory
from .data_fetcher import DataFetcher
from .strategies import DualMAStrategy, BollingerBandStrategy
from .optimizer import ParameterOptimizer
from .cross_validator import CrossValidator

__all__ = [
    # 回测引擎
    'Backtester',
    'VectorizedBacktester',
    'BacktesterFactory',
    # 数据获取
    'DataFetcher',
    # 策略
    'DualMAStrategy',
    'BollingerBandStrategy',
    # 参数优化
    'ParameterOptimizer',
    # 交叉验证
    'CrossValidator',
]
