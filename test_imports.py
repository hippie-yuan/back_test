"""
测试所有模块的导入
"""
def test_imports():
    """测试所有模块的导入"""
    try:
        # 测试核心模块导入
        from core.data import DataGenerator
        print("✓ DataGenerator 导入成功")
        
        from core.animation import Animation
        print("✓ Animation 导入成功")
        
        from core.strategies import BaseStrategy, MeanStrategy, FiscalYearReturnCalculator
        print("✓ 策略模块导入成功")
        
        from core.system import StockPredictionSystem
        print("✓ StockPredictionSystem 导入成功")
        
        from core.utils import setup_logging, performance_monitor, logger
        print("✓ 工具模块导入成功")
        
        from core.exceptions import (
            StockPredictionError, DataError, StrategyError, 
            AnimationError, ConfigurationError
        )
        print("✓ 异常模块导入成功")
        
        # 测试配置模块
        from config import Config
        print("✓ Config 导入成功")
        
        # 测试包级别导入
        from __init__ import StockPredictionSystem as SPS
        print("✓ 包级别导入成功")
        
        print("\n🎉 所有模块导入成功！")
        return True
        
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False

if __name__ == "__main__":
    test_imports() 