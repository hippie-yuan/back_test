"""
股票预测系统配置文件
"""
import os
from typing import Dict, Any, Optional


class Config:
    """配置管理类"""
    
    # 默认配置
    DEFAULT_CONFIG = {
        'data': {
            'csv_path': 'nvda_hist.csv',
            'window_size': 50,
            'columns': ['Date', 'Close']
        },
        'animation': {
            'interval': 20,
            'figure_size': (14, 10),
            'dpi': 100
        },
        'strategy': {
            'short_window': 5,
            'long_window': 20,
            'initial_balance': 1000000,
            'shares_per_trade': 100,
            'trade_update_frequency': 10
        },
        'logging': {
            'level': 'INFO',
            'log_file': None,
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
        'performance': {
            'enable_monitoring': True,
            'log_slow_operations': True,
            'slow_threshold': 1.0  # 秒
        }
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置
        
        Args:
            config_file (str): 配置文件路径
        """
        self.config = self.DEFAULT_CONFIG.copy()
        if config_file and os.path.exists(config_file):
            self.load_from_file(config_file)
        self.load_from_env()
    
    def load_from_file(self, config_file: str):
        """从文件加载配置"""
        try:
            import json
            with open(config_file, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
                self._merge_config(file_config)
        except Exception as e:
            print(f"Warning: Failed to load config file {config_file}: {e}")
    
    def load_from_env(self):
        """从环境变量加载配置"""
        env_mappings = {
            'STOCK_CSV_PATH': ('data', 'csv_path'),
            'WINDOW_SIZE': ('data', 'window_size'),
            'ANIMATION_INTERVAL': ('animation', 'interval'),
            'SHORT_WINDOW': ('strategy', 'short_window'),
            'LONG_WINDOW': ('strategy', 'long_window'),
            'INITIAL_BALANCE': ('strategy', 'initial_balance'),
            'SHARES_PER_TRADE': ('strategy', 'shares_per_trade'),
            'TRADE_UPDATE_FREQ': ('strategy', 'trade_update_frequency'),
            'LOG_LEVEL': ('logging', 'level'),
            'LOG_FILE': ('logging', 'log_file'),
            'ENABLE_PERFORMANCE_MONITORING': ('performance', 'enable_monitoring')
        }
        
        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                self._set_nested_value(config_path, value)
    
    def _merge_config(self, new_config: Dict[str, Any]):
        """合并配置"""
        for section, values in new_config.items():
            if section in self.config:
                if isinstance(values, dict):
                    self.config[section].update(values)
                else:
                    self.config[section] = values
            else:
                self.config[section] = values
    
    def _set_nested_value(self, path: tuple, value: str):
        """设置嵌套配置值"""
        current = self.config
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # 类型转换
        key = path[-1]
        if key in ['window_size', 'interval', 'short_window', 'long_window', 
                   'shares_per_trade', 'trade_update_frequency']:
            current[key] = int(value)
        elif key in ['initial_balance']:
            current[key] = float(value)
        elif key in ['enable_monitoring', 'log_slow_operations']:
            current[key] = value.lower() in ['true', '1', 'yes']
        else:
            current[key] = value
    
    def get(self, section: str, key: Optional[str] = None, default=None):
        """
        获取配置值
        
        Args:
            section (str): 配置节
            key (str): 配置键
            default: 默认值
            
        Returns:
            配置值
        """
        if section not in self.config:
            return default
        
        if key is None:
            return self.config[section]
        
        return self.config[section].get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """返回完整配置字典"""
        return self.config.copy()


# 全局配置实例
config = Config() 