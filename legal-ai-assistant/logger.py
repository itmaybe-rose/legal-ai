# logger.py - 日志记录模块

import logging
import os
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler

def setup_logger(name='legal-ai-assistant'):
    """
    设置日志系统
    
    Args:
        name: 日志器名称
        
    Returns:
        logger: 配置好的日志器对象
    """
    # 创建日志目录
    log_dir = './logs'
    os.makedirs(log_dir, exist_ok=True)
    
    # 创建日志器
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
    
    # 日志格式
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s'
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)
    
    # 错误日志文件处理器（每天轮转，保留7天）
    error_handler = TimedRotatingFileHandler(
        os.path.join(log_dir, 'error.log'),
        when='midnight',
        interval=1,
        backupCount=7,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(log_format)
    logger.addHandler(error_handler)
    
    # 访问日志文件处理器（每天轮转，保留7天）
    access_handler = TimedRotatingFileHandler(
        os.path.join(log_dir, 'access.log'),
        when='midnight',
        interval=1,
        backupCount=7,
        encoding='utf-8'
    )
    access_handler.setLevel(logging.INFO)
    access_handler.setFormatter(log_format)
    logger.addHandler(access_handler)
    
    # 调试日志文件处理器（每天轮转，保留3天）
    debug_handler = TimedRotatingFileHandler(
        os.path.join(log_dir, 'debug.log'),
        when='midnight',
        interval=1,
        backupCount=3,
        encoding='utf-8'
    )
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(log_format)
    logger.addHandler(debug_handler)
    
    return logger

class LogManager:
    """日志管理类"""
    
    def __init__(self):
        self.logger = setup_logger()
    
    def log_info(self, message, module='unknown', user_id=None):
        """记录信息日志"""
        context = self._build_context(user_id, module)
        self.logger.info(f"{context} - {message}")
    
    def log_error(self, message, module='unknown', user_id=None, exception=None):
        """记录错误日志"""
        context = self._build_context(user_id, module)
        if exception:
            self.logger.error(f"{context} - {message}", exc_info=exception)
        else:
            self.logger.error(f"{context} - {message}")
    
    def log_debug(self, message, module='unknown', user_id=None):
        """记录调试日志"""
        context = self._build_context(user_id, module)
        self.logger.debug(f"{context} - {message}")
    
    def log_warning(self, message, module='unknown', user_id=None):
        """记录警告日志"""
        context = self._build_context(user_id, module)
        self.logger.warning(f"{context} - {message}")
    
    def log_access(self, endpoint, user_id=None, status='success', duration_ms=None):
        """记录访问日志"""
        context = f"[ACCESS] endpoint={endpoint}, user_id={user_id}, status={status}"
        if duration_ms:
            context += f", duration={duration_ms}ms"
        self.logger.info(context)
    
    def log_file_upload(self, file_name, user_id=None, success=True, error_msg=None):
        """记录文件上传日志"""
        status = "SUCCESS" if success else "FAILED"
        message = f"[FILE_UPLOAD] file={file_name}, status={status}"
        if error_msg:
            message += f", error={error_msg}"
        if success:
            self.logger.info(f"user_id={user_id} - {message}")
        else:
            self.logger.error(f"user_id={user_id} - {message}")
    
    def log_chat_request(self, user_id, question_length, success=True, error_msg=None):
        """记录聊天请求日志"""
        status = "SUCCESS" if success else "FAILED"
        message = f"[CHAT_REQUEST] question_length={question_length}, status={status}"
        if error_msg:
            message += f", error={error_msg}"
        if success:
            self.logger.info(f"user_id={user_id} - {message}")
        else:
            self.logger.error(f"user_id={user_id} - {message}")
    
    def _build_context(self, user_id, module):
        """构建日志上下文"""
        parts = [f"module={module}"]
        if user_id:
            parts.append(f"user_id={user_id}")
        return " ".join(parts)

# 创建全局日志管理器实例
log_manager = LogManager()

# 便捷函数
def get_logger():
    return log_manager

def log_info(message, module='unknown', user_id=None):
    log_manager.log_info(message, module, user_id)

def log_error(message, module='unknown', user_id=None, exception=None):
    log_manager.log_error(message, module, user_id, exception)

def log_debug(message, module='unknown', user_id=None):
    log_manager.log_debug(message, module, user_id)

def log_warning(message, module='unknown', user_id=None):
    log_manager.log_warning(message, module, user_id)

def log_access(endpoint, user_id=None, status='success', duration_ms=None):
    log_manager.log_access(endpoint, user_id, status, duration_ms)

def log_file_upload(file_name, user_id=None, success=True, error_msg=None):
    log_manager.log_file_upload(file_name, user_id, success, error_msg)

def log_chat_request(user_id, question_length, success=True, error_msg=None):
    log_manager.log_chat_request(user_id, question_length, success, error_msg)