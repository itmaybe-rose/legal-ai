"""日志系统配置"""
import sys
from loguru import logger


def setup_logger():
    """配置日志系统"""
    # 移除默认的日志处理器
    logger.remove()

    # 控制台输出（带颜色）
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <7}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="DEBUG",
        colorize=True
    )

    # 文件输出 - 错误日志
    logger.add(
        "logs/error.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <7} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="10 MB",
        retention="30 days",
        encoding="utf-8"
    )

    # 文件输出 - 全部日志
    logger.add(
        "logs/app.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <7} | {name}:{function}:{line} - {message}",
        level="INFO",
        rotation="10 MB",
        retention="7 days",
        encoding="utf-8"
    )

    return logger


# 初始化日志
logger = setup_logger()