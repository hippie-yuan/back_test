"""
股票预测系统异常类
"""


class StockPredictionError(Exception):
    """股票预测系统基础异常类"""
    pass


class DataError(StockPredictionError):
    """数据相关错误"""
    pass


class StrategyError(StockPredictionError):
    """策略相关错误"""
    pass


class AnimationError(StockPredictionError):
    """动画相关错误"""
    pass


class ConfigurationError(StockPredictionError):
    """配置相关错误"""
    pass 