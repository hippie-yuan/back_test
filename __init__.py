"""
股票预测系统包
提供模块化的股票价格预测和动画系统
"""

# 从核心包导入所有模块
from .core import (
    # 核心类
    StockPredictionSystem,
    DataGenerator, 
    Animation,
    BaseStrategy,
    MeanStrategy,
    FiscalYearReturnCalculator,
    
    # 工具函数
    setup_logging,
    performance_monitor,
    logger,
    
    # 异常类
    StockPredictionError,
    DataError,
    StrategyError, 
    AnimationError,
    ConfigurationError
)

# 配置导入
try:
    from .config import Config
except ImportError:
    Config = None

__version__ = "1.1.0"
__author__ = "Stock Prediction System Team"

__all__ = [
    # 核心类
    'StockPredictionSystem',
    'DataGenerator', 
    'Animation',
    'BaseStrategy',
    'MeanStrategy',
    'FiscalYearReturnCalculator',
    
    # 工具函数
    'setup_logging',
    'performance_monitor',
    'logger',
    
    # 异常类
    'StockPredictionError',
    'DataError',
    'StrategyError', 
    'AnimationError',
    'ConfigurationError',
    
    # 配置
    'Config',
] 