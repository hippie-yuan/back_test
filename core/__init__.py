"""
股票预测系统核心模块包
"""
from .data import DataGenerator
from .animation import Animation
from .strategies import BaseStrategy, MeanStrategy, FiscalYearReturnCalculator
from .system import StockPredictionSystem
from .utils import setup_logging, performance_monitor, logger
from .exceptions import (
    StockPredictionError, DataError, StrategyError, 
    AnimationError, ConfigurationError
)

__all__ = [
    'DataGenerator',
    'Animation', 
    'BaseStrategy',
    'MeanStrategy',
    'FiscalYearReturnCalculator',
    'StockPredictionSystem',
    'setup_logging',
    'performance_monitor',
    'logger',
    'StockPredictionError',
    'DataError',
    'StrategyError',
    'AnimationError', 
    'ConfigurationError'
] 