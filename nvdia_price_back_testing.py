"""
股票预测系统主脚本
"""
import pandas as pd
from typing import Dict, Any
from core.system import StockPredictionSystem
from core.utils import setup_logging, logger
import os
from config import Config
import matplotlib
matplotlib.use('Qt5Agg')


def load_config() -> Dict[str, Any]:
    """
    加载配置参数
    支持从环境变量或默认值加载配置
    """
    return {
        'csv_path': os.getenv('STOCK_CSV_PATH', 'nvda_hist.csv'),
        'window_size': int(os.getenv('WINDOW_SIZE', '50')),
        'interval': int(os.getenv('ANIMATION_INTERVAL', '10')),
        'short_window': int(os.getenv('SHORT_WINDOW', '5')),
        'long_window': int(os.getenv('LONG_WINDOW', '20')),
        'initial_balance': float(os.getenv('INITIAL_BALANCE', '1000000')),
        'shares_per_trade': int(os.getenv('SHARES_PER_TRADE', '100')),
        'trade_update_frequency': int(os.getenv('TRADE_UPDATE_FREQ', '10'))
    }


def main():
    """
    主函数
    程序入口点，负责创建并运行股票预测系统
    """
    try:
        print("Starting stock prediction system...")
        
        # 加载配置
        config = load_config()
        print(f"Configuration loaded: {config}")
        
        # 创建股票预测系统实例
        print("Creating StockPredictionSystem instance...")
        system = StockPredictionSystem(
            csv_path=config['csv_path'],
            window_size=config['window_size'],
            interval=config['interval']
        )
        
        # 运行系统
        print("Running system...")
        system.run()
        
        print('Program finished successfully')
        
    except Exception as e:
        print(f"Error in main function: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
