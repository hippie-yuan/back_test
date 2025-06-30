"""
系统协调器模块
"""
import pandas as pd
from typing import Optional, Dict, Any
from .utils import logger, performance_monitor
from .exceptions import StockPredictionError, DataError, StrategyError, AnimationError
from .data import DataGenerator
from .strategies import MeanStrategy
from .animation import Animation


class StockPredictionSystem:
    """
    股票预测系统类
    负责管理整个股票价格预测动画系统的生命周期
    """
    
    def __init__(self, csv_path: str = 'nvda_hist.csv', window_size: int = 50, interval: int = 10):
        """
        初始化股票预测系统
        
        Args:
            csv_path (str): CSV文件路径
            window_size (int): 数据窗口大小
            interval (int): 动画更新间隔
        """
        self.csv_path = csv_path
        self.window_size = window_size
        self.interval = interval
        
        # 系统组件
        self.data_generator: Optional[DataGenerator] = None
        self.strategy: Optional[MeanStrategy] = None
        self.animation: Optional[Animation] = None
        self.data_stream_gen = None
        
        # 线条属性配置
        self.line_properties = [
            {'label': 'Real Time Price', 'color': 'blue', 'x_name': 'Date', 'y_name': 'Close'},
            {'label': 'Prediction 5 Price', 'color': 'orange', 'x_name': 'Date', 'y_name': 'Close'},
            {'label': 'Prediction 20 Price', 'color': 'green', 'x_name': 'Date', 'y_name': 'Close'}
        ]
    
    @performance_monitor
    def initialize_data_generator(self):
        """初始化数据生成器"""
        try:
            self.data_generator = DataGenerator(path=self.csv_path, window_size=self.window_size)
            nvda_hist = self.data_generator.get_initial_data(['Date', 'Close'])
            logger.info(f"Data loaded, shape: {nvda_hist.shape}")
        except Exception as e:
            raise DataError(f"Failed to initialize data generator: {str(e)}")
    
    @performance_monitor
    def create_strategy(self):
        """创建策略实例"""
        try:
            self.strategy = MeanStrategy()
            logger.info("Strategy created successfully")
        except Exception as e:
            raise StrategyError(f"Failed to create strategy: {str(e)}")
    
    @performance_monitor
    def create_animation_object(self):
        """创建动画对象"""
        try:
            self.animation = Animation(self.line_properties)
            logger.info("Animation object created successfully")
        except Exception as e:
            raise AnimationError(f"Failed to create animation object: {str(e)}")
    
    @performance_monitor
    def create_data_stream_generator(self):
        """创建数据流生成器"""
        if self.data_generator is None or self.strategy is None:
            raise StockPredictionError("Data generator and strategy must be initialized first")
        
        try:
            self.data_stream_gen = self._data_stream_generator(
                self.data_generator, ['Date', 'Close'], self.strategy
            )
            logger.info("Data stream created successfully")
        except Exception as e:
            raise StockPredictionError(f"Failed to create data stream: {str(e)}")
    
    def _data_stream_generator(self, org_data_class: DataGenerator, column_names: list[str], strategy: MeanStrategy):
        """
        数据流生成器 - 内部方法
        
        Args:
            org_data_class (DataGenerator): 数据生成器实例
            column_names (list[str]): 列名列表
            strategy (MeanStrategy): 策略实例
            
        Yields:
            tuple: (数据流列表, 策略信息字典)
        """
        # 创建预测数据DataFrame
        mean_5_prdt_data = pd.DataFrame(columns=column_names)
        mean_20_prdt_data = pd.DataFrame(columns=column_names)
        prdt_data_class = DataGenerator(data=org_data_class.data, window_size=org_data_class.window_size)
        
        while True:
            try:
                # 获取下一个时间戳和历史数据
                timestamp, iter_org_data = next(org_data_class.iter_next_org_datas('Date'))
                
                # 确保iter_org_data是DataFrame类型
                if not isinstance(iter_org_data, pd.DataFrame):
                    continue
                
                # 执行策略
                strategy.execute_strategy(iter_org_data, 5, 20, timestamp, 'Date', 'Close')
                
                # 每10次交易打印一次结果
                if strategy.trade_count % 10 == 0 and strategy.trade_count > 0:
                    balance, shares, trades, total = strategy.get_strategy_result()
                    logger.info(f"Strategy Update - Balance: ${balance:.2f}, Shares: {shares}, Trades: {trades}")

                # 生成预测值
                pred_5_value = strategy.predict_price(iter_org_data, 5, 'Date', 'Close')
                pred_20_value = strategy.predict_price(iter_org_data, 20, 'Date', 'Close')
                
                # 更新预测数据
                mean_5_prdt_data = prdt_data_class.append_to_dataframe(mean_5_prdt_data, timestamp, pred_5_value)
                mean_20_prdt_data = prdt_data_class.append_to_dataframe(mean_20_prdt_data, timestamp, pred_20_value)
                
                # 只保留窗口内的数据
                mean_5_prdt_data = mean_5_prdt_data.tail(prdt_data_class.window_size).reset_index(drop=True)
                mean_20_prdt_data = mean_20_prdt_data.tail(prdt_data_class.window_size).reset_index(drop=True)
                
                # 创建数据流
                data_stream = [
                    {'label': 'Real Time Price', 'datas': iter_org_data},
                    {'label': 'Prediction 5 Price', 'datas': mean_5_prdt_data},
                    {'label': 'Prediction 20 Price', 'datas': mean_20_prdt_data}
                ]
                
                # 准备策略信息
                current_price = iter_org_data.iloc[-1]['Close'] if len(iter_org_data) > 0 else 0
                strategy_info = strategy.get_profit_info(current_price)
                
                yield (data_stream, strategy_info)
                
            except StopIteration:
                logger.info("Data stream ended")
                # 打印最终策略结果
                balance, shares, trades, total = strategy.get_strategy_result()
                logger.info(f"Final Strategy Result - Balance: ${balance:.2f}, Shares: {shares}, Total Trades: {trades}")
                break
            except Exception as e:
                logger.error(f"Error in data_stream_generator: {str(e)}")
                import traceback
                traceback.print_exc()
                break
    
    @performance_monitor
    def start_animation(self):
        """启动动画"""
        if self.animation is None:
            raise AnimationError("Animation object must be created first")
        
        try:
            self.animation = self.animation.create_animation(
                frames=self.data_stream_gen,
                interval=self.interval,
                cache_frame_data=False
            )
            logger.info("Animation created, starting...")
            
            import matplotlib.pyplot as plt
            plt.show()
            logger.info("Animation finished")
        except Exception as e:
            raise AnimationError(f"Failed to start animation: {str(e)}")
    
    @performance_monitor
    def run(self):
        """
        运行整个股票预测系统
        """
        logger.info("Initializing stock prediction animation system...")
        
        try:
            # 初始化各个组件
            self.initialize_data_generator()
            self.create_strategy()
            self.create_animation_object()
            self.create_data_stream_generator()
            
            # 启动动画
            self.start_animation()
            
        except Exception as e:
            logger.error(f"Error in StockPredictionSystem: {e}")
            import traceback
            traceback.print_exc()
            raise StockPredictionError(f"System failed to run: {str(e)}") 