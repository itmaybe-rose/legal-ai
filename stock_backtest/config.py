# 股票策略回测配置文件

class Config:
    # 数据配置
    DATA_DIR = "data/"
    CACHE_FILE = "data/stock_data.pkl"
    
    # 回测配置
    INITIAL_CAPITAL = 100000.0  # 初始资金
    TRANSACTION_FEE = 0.0003     # 手续费率
    SLIPPAGE = 0.0001            # 滑点
    
    # 双均线策略参数
    MA_SHORT_WINDOW = 5          # 短期均线窗口
    MA_LONG_WINDOW = 20          # 长期均线窗口
    
    # 布林带策略参数
    BB_WINDOW = 20               # 布林带窗口
    BB_STD_DEV = 2.0             # 标准差倍数
    
    # Web配置
    DEBUG = True
    PORT = 8050
    
    # 默认股票代码
    DEFAULT_SYMBOL = "sh600519"  # 贵州茅台
    DEFAULT_START_DATE = "20230101"
    DEFAULT_END_DATE = "20241231"
    
    # 日志配置
    LOG_DIR = "logs/"
    LOG_LEVEL = "INFO"           # DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_FORMAT = '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    LOG_CONSOLE_OUTPUT = True
    LOG_FILE_OUTPUT = True
