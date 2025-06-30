"""
股票预测系统测试模块
"""
import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import tempfile
import os

# 导入被测试的模块
from core.data import DataGenerator
from core.strategies import MeanStrategy
from core.animation import Animation
from core.system import StockPredictionSystem
from core.utils import setup_logging
from config import Config


class TestDataGenerator(unittest.TestCase):
    """数据生成器测试"""
    
    def setUp(self):
        """测试前准备"""
        # 创建测试数据
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        prices = np.random.uniform(100, 200, 100)
        self.test_data = pd.DataFrame({
            'Date': dates,
            'Close': prices
        })
        
        # 保存到临时文件
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        self.test_data.to_csv(self.temp_file.name, index=False)
        self.temp_file.close()
    
    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_data_generator_initialization(self):
        """测试数据生成器初始化"""
        dg = DataGenerator(path=self.temp_file.name, window_size=20)
        self.assertIsNotNone(dg.data)
        self.assertEqual(len(dg.data), 100)
        self.assertEqual(dg.window_size, 20)
    
    def test_get_initial_data(self):
        """测试获取初始数据"""
        dg = DataGenerator(path=self.temp_file.name, window_size=20)
        initial_data = dg.get_initial_data(['Date', 'Close'], end_index=50)
        self.assertEqual(len(initial_data), 50)
        self.assertListEqual(list(initial_data.columns), ['Date', 'Close'])
    
    def test_iter_next_org_datas(self):
        """测试数据迭代器"""
        dg = DataGenerator(path=self.temp_file.name, window_size=20)
        iterator = dg.iter_next_org_datas('Date')
        
        # 获取第一个数据点
        timestamp, data = next(iterator)
        self.assertIsInstance(timestamp, pd.Timestamp)
        self.assertIsInstance(data, pd.DataFrame)
        self.assertEqual(len(data), 1000)  # 初始索引


class TestMeanStrategy(unittest.TestCase):
    """移动平均策略测试"""
    
    def setUp(self):
        """测试前准备"""
        self.strategy = MeanStrategy()
        
        # 创建测试数据
        dates = pd.date_range('2023-01-01', periods=30, freq='D')
        prices = np.random.uniform(100, 200, 30)
        self.test_data = pd.DataFrame({
            'Date': dates,
            'Close': prices
        })
    
    def test_predict_price(self):
        """测试价格预测"""
        prediction = self.strategy.predict_price(self.test_data, 5, 'Date', 'Close')
        self.assertIsInstance(prediction, float)
        self.assertGreater(prediction, 0)
    
    def test_calculate_moving_averages(self):
        """测试移动平均计算"""
        short_ma, long_ma = self.strategy.calculate_moving_averages(
            self.test_data, 5, 20, 'Close'
        )
        self.assertIsInstance(short_ma, float)
        self.assertIsInstance(long_ma, float)
        self.assertGreater(short_ma, 0)
        self.assertGreater(long_ma, 0)
    
    def test_trading_decisions(self):
        """测试交易决策"""
        # 测试买入条件
        self.assertTrue(self.strategy.should_buy(110, 100, 105))
        self.assertFalse(self.strategy.should_buy(90, 100, 95))
        
        # 测试卖出条件
        self.assertTrue(self.strategy.should_sell(90, 100, 95))
        self.assertFalse(self.strategy.should_sell(110, 100, 105))


class TestAnimation(unittest.TestCase):
    """动画类测试"""
    
    def setUp(self):
        """测试前准备"""
        self.line_properties = [
            {'label': 'Test Line 1', 'color': 'blue', 'x_name': 'Date', 'y_name': 'Close'},
            {'label': 'Test Line 2', 'color': 'red', 'x_name': 'Date', 'y_name': 'Close'}
        ]
        self.animation = Animation(self.line_properties)
    
    def test_animation_initialization(self):
        """测试动画初始化"""
        self.assertIsNotNone(self.animation.fig)
        self.assertIsNotNone(self.animation.ax)
        self.assertEqual(len(self.animation.lines), 2)
    
    def test_line_properties(self):
        """测试线条属性"""
        for i, line in enumerate(self.animation.lines):
            self.assertEqual(line.get_label(), self.line_properties[i]['label'])
            self.assertEqual(line.get_color(), self.line_properties[i]['color'])


class TestStockPredictionSystem(unittest.TestCase):
    """股票预测系统测试"""
    
    def setUp(self):
        """测试前准备"""
        # 创建测试数据文件
        dates = pd.date_range('2023-01-01', periods=200, freq='D')
        prices = np.random.uniform(100, 200, 200)
        self.test_data = pd.DataFrame({
            'Date': dates,
            'Close': prices
        })
        
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        self.test_data.to_csv(self.temp_file.name, index=False)
        self.temp_file.close()
        
        # 创建系统实例
        self.system = StockPredictionSystem(
            csv_path=self.temp_file.name,
            window_size=20,
            interval=100  # 快速测试
        )
    
    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_system_initialization(self):
        """测试系统初始化"""
        self.assertEqual(self.system.csv_path, self.temp_file.name)
        self.assertEqual(self.system.window_size, 20)
        self.assertEqual(self.system.interval, 100)
        self.assertIsNone(self.system.data_generator)
        self.assertIsNone(self.system.strategy)
        self.assertIsNone(self.system.animation)
    
    def test_initialize_data_generator(self):
        """测试数据生成器初始化"""
        self.system.initialize_data_generator()
        self.assertIsNotNone(self.system.data_generator)
        self.assertEqual(len(self.system.data_generator.data), 200)
    
    def test_create_strategy(self):
        """测试策略创建"""
        self.system.create_strategy()
        self.assertIsNotNone(self.system.strategy)
        self.assertIsInstance(self.system.strategy, MeanStrategy)
    
    def test_create_animation_object(self):
        """测试动画对象创建"""
        self.system.create_animation_object()
        self.assertIsNotNone(self.system.animation)
        self.assertEqual(len(self.system.animation.lines), 3)


class TestConfig(unittest.TestCase):
    """配置管理测试"""
    
    def setUp(self):
        """测试前准备"""
        self.config = Config()
    
    def test_default_config(self):
        """测试默认配置"""
        self.assertEqual(self.config.get('data', 'csv_path'), 'nvda_hist.csv')
        self.assertEqual(self.config.get('data', 'window_size'), 50)
        self.assertEqual(self.config.get('animation', 'interval'), 10)
    
    def test_config_get_method(self):
        """测试配置获取方法"""
        # 测试获取整个节
        data_config = self.config.get('data')
        self.assertIsInstance(data_config, dict)
        self.assertIn('csv_path', data_config)
        
        # 测试获取特定键
        csv_path = self.config.get('data', 'csv_path')
        self.assertEqual(csv_path, 'nvda_hist.csv')
        
        # 测试默认值
        non_existent = self.config.get('non_existent', 'key', 'default')
        self.assertEqual(non_existent, 'default')


def run_tests():
    """运行所有测试"""
    # 设置日志级别为WARNING以减少输出
    setup_logging('WARNING')
    
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加测试类
    test_classes = [
        TestDataGenerator,
        TestMeanStrategy,
        TestAnimation,
        TestStockPredictionSystem,
        TestConfig
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 输出结果摘要
    print(f"\n测试结果摘要:")
    print(f"运行测试: {result.testsRun}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    if result.failures:
        print("\n失败的测试:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\n错误的测试:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1) 