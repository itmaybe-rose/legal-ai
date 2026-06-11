# 源代码包初始化文件
# 提供统一的模块导入接口

from .backtester import BaseBacktester, Backtester, BacktesterFactory
from .strategies import DualMAStrategy, BollingerBandStrategy
from .optimizer import ParameterOptimizer
from .cross_validator import CrossValidator
from .true_vectorized import TrueVectorizedBacktester
from .event_driven import EventDrivenBacktester, EventDrivenStrategy
from .hybrid_framework import HybridBacktestFramework

__all__ = [
    # 回测引擎
    'BaseBacktester',
    'Backtester',
    'BacktesterFactory',
    'TrueVectorizedBacktester',
    'EventDrivenBacktester',
    'HybridBacktestFramework',
    # 策略
    'DualMAStrategy',
    'BollingerBandStrategy',
    'EventDrivenStrategy',
    # 参数优化
    'ParameterOptimizer',
    # 交叉验证
    'CrossValidator',
]
