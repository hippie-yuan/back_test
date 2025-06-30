"""
工具函数模块
"""
import logging
import time
from typing import Optional
from functools import wraps


def setup_logging(level: str = 'INFO', log_file: Optional[str] = None) -> logging.Logger:
    """
    设置日志系统
    
    Args:
        level (str): 日志级别
        log_file (str, optional): 日志文件路径
        
    Returns:
        logging.Logger: 配置好的日志器
    """
    logger = logging.getLogger('StockPrediction')
    logger.setLevel(getattr(logging, level.upper()))
    
    # 清除现有的处理器
    logger.handlers.clear()
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器（如果指定了文件）
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def performance_monitor(func):
    """
    性能监控装饰器
    用于跟踪方法执行时间
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger = logging.getLogger('StockPrediction')
            logger.debug(f"{func.__name__} executed in {execution_time:.4f} seconds")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger = logging.getLogger('StockPrediction')
            logger.error(f"{func.__name__} failed after {execution_time:.4f} seconds: {str(e)}")
            raise
    return wrapper


# 全局日志器
logger = setup_logging() 