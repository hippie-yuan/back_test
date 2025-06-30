import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import time
from functools import partial
from matplotlib import animation
import matplotlib.lines as line
from abc import ABC, abstractmethod


class DataGenerator:
    """
    数据生成器类
    负责读取CSV文件，管理数据索引，提供数据迭代功能
    """
    
    def __init__(self, data: pd.DataFrame | None = None, path: str='None', init_index: int = 1000, window_size: int = 50):
        """
        初始化数据生成器
        
        Args:
            data (pd.DataFrame): 直接传入的数据
            path (str): CSV文件路径
            init_index (int): 初始索引位置
            window_size (int): 窗口大小
        """
        if data is not None:
            self.data = data
            if window_size is not None:
                self.window_size = window_size
            else:
                self.window_size = len(data)
        else:
            self.path = path
            self.index = init_index
            self.__index = init_index
            self.window_size = window_size
            if path != 'None':
                self.data = self.get_data_from_csv()
                self.current_data = self.get_current_data()
        

    def get_data_from_csv(self) -> pd.DataFrame:
        return pd.read_csv(self.path)

    def get_initial_data(self, column_names: list, start_index: int = 0, end_index: int | None = None) -> pd.DataFrame:
        """
        获取初始数据
        
        Args:
            column_names (list): 需要的列名列表
            start_index (int): 起始索引，默认为0
            end_index (int): 结束索引，默认为None（取self.index）
            
        Returns:
            pd.DataFrame: 初始数据
        """
        if end_index is None:
            end_index = self.index
        return self.data.iloc[start_index:end_index][column_names].reset_index(drop=True)
    
    def get_current_data(self, column_names: list | None = None) -> pd.DataFrame:
        """
        获取当前数据
        """
        if column_names is not None:
            return self.data.iloc[:self.index][column_names].reset_index(drop=True)
        else:
            return self.data.iloc[:self.index].reset_index(drop=True)
    
    def iter_next_org_datas(self, time_column_name: str = 'Date', value_column_name: str = 'Close'):
        """
        迭代器：逐步获取下一个时间戳和对应的历史数据
        
        Args:
            time_column_name (str): 时间列名，默认为'Date'
            value_column_name (str): 值列名，默认为'Close'
            
        Yields:
            tuple: (时间戳, 历史数据DataFrame)
        """
        # 检查是否还有更多数据
        if self.index >= len(self.data) - 1:
            raise StopIteration("No more data available")

        # 先获取当前索引的数据，然后递增索引
        current_timestamp = self.data.iloc[self.index][time_column_name]
        self.next_org_datas = self.data[[time_column_name, value_column_name]][:self.index].reset_index(drop=True)
        
        # 递增索引
        self.index = self.index + 1
        
        yield current_timestamp, self.next_org_datas

    def append_to_dataframe(self, df: pd.DataFrame, timestamp, prediction_value, 
                           time_column: str = 'Date', value_column: str = 'Close') -> pd.DataFrame:
        """
        往DataFrame最后一行添加时间戳和预测值
        
        Args:
            df (pd.DataFrame): 输入的DataFrame
            timestamp: 时间戳
            prediction_value: 预测值
            time_column (str): 时间列名，默认为'Date'
            value_column (str): 值列名，默认为'Close'
            
        Returns:
            pd.DataFrame: 添加了新行的DataFrame
        """
        new_row = pd.DataFrame({time_column: [timestamp], value_column: [prediction_value]})
        result_df = pd.concat([df, new_row], ignore_index=True)
        return result_df


class Animation(animation.Animation):
    """
    动画类
    负责创建和管理matplotlib动画，包括图形初始化、数据更新和坐标轴管理
    """
    
    def __init__(self, line_properties: list, window_size: int = 50):
        """
        初始化动画
        
        Args:
            line_properties (list): 线条属性列表，每个元素包含name, color, x_name, y_name
        """
        # 创建图形和坐标轴
        self.fig, self.ax = plt.subplots(figsize=(14, 10))
        self.lines = []
        self.window_size = window_size
        
        # 创建线条对象并添加到坐标轴
        for prop in line_properties:
            line_obj = self.Line(prop)
            self.lines.append(line_obj)
            self.ax.add_line(line_obj)

        # 设置初始坐标轴范围和格式
        self._setup_axes()
        
        # 添加策略结果显示区域
        self.strategy_text = None
        self._setup_strategy_display()
    
    def _setup_strategy_display(self):
        """设置策略结果显示区域"""
        # 在图的右上角添加文本显示区域
        self.strategy_text = self.ax.text(
            0.02, 0.98, '', 
            transform=self.ax.transAxes,
            fontsize=10,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
            fontfamily='monospace'
        )
    
    def _setup_axes(self):
        """设置坐标轴的基本属性"""
        # 设置初始x轴范围（使用类方法获取默认值）
        x_min, x_max = self._get_default_xlim()
        self.ax.set_xlim(x_min, x_max)
        
        # 设置y轴初始范围
        self.ax.set_ylim(0, 1)
        
        # 设置x轴格式，显示年月日
        self.ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        self.fig.autofmt_xdate()
        
        # 添加图例
        self.ax.legend(loc='upper left')
        
        # 设置标题和标签
        self.ax.set_title('Stock Price Real-Time Prediction with Trading Strategy', fontsize=14, fontweight='bold')
        self.ax.set_xlabel('Date', fontsize=12)
        self.ax.set_ylabel('Price', fontsize=12)
        
        # 设置网格
        self.ax.grid(True, alpha=0.3)
    
    @classmethod
    def _get_default_xlim(cls):
        """获取默认的x轴范围"""
        return (float(mdates.date2num(datetime(2023, 1, 1))), 
                float(mdates.date2num(datetime(2023, 1, 20))))
    
    class Line(line.Line2D):
        """
        自定义线条类
        继承自matplotlib的Line2D，添加自定义属性
        """
        
        def __init__(self, line_property: dict):
            """
            初始化线条
            
            Args:
                line_property (dict): 包含label, color, x_name, y_name的字典
            """
            self.label = line_property.get('label')
            self.color = line_property.get('color')
            self.x_name = line_property.get('x_name')
            self.y_name = line_property.get('y_name')
            
            # 调用父类构造函数
            super().__init__([], [], color=self.color, label=self.label, linewidth=2)

    def init_fig(self):
        """
        初始化图形（动画开始时调用）
        
        Returns:
            tuple: 需要更新的图形元素
        """
        print("Initializing animation...")
        # 清空所有线条数据
        for line_artist in self.lines:
            line_artist.set_data([], [])
        return tuple(self.lines)
    
    def get_ax_max_min(self, lines_datas: list[dict], x_name: str, y_name: str, window_size: int = 50):
        """
        计算所有线条数据的坐标轴范围
        
        Args:
            lines_datas (list): 线条数据列表
            x_name (str): x轴列名
            y_name (str): y轴列名
            window_size (int): 窗口大小
            
        Returns:
            tuple: (x_min, x_max, y_min, y_max)
        """
        window_size = self.window_size
        all_x = []
        all_y = []
        
        for item in lines_datas:
            df = item['datas']
            # 确保不超过数据长度
            actual_window = min(window_size, len(df))
            # 只考虑窗口内的数据
            if len(df) > 0:
                all_x.extend(df[x_name].tail(actual_window))
                all_y.extend(df[y_name].tail(actual_window))
        
        if not all_x:
            # 如果没有数据，返回默认值
            return datetime.now(), datetime.now() + timedelta(days=1), 0, 1
        
        # 确保返回单个值而不是数组
        x_min = min(all_x)
        x_max = max(all_x)
        y_min = min(all_y)
        y_max = max(all_y)
        
        return x_min, x_max, y_min, y_max

    def update_line_data(self, line, item, window_size: int):
        """
        更新单条线的数据
        Args:
            line: 线条对象
            item: 数据项
            window_size (int): 窗口大小
        """
        df = item['datas']
        if len(df) > 0:
            # 转换日期为matplotlib可识别的数字格式
            xdata = mdates.date2num(df[line.x_name].tail(window_size))
            ydata = df[line.y_name].tail(window_size)
            line.set_data(xdata, ydata)

    def update_all_lines(self, line_datas: list[dict], window_size: int):
        """
        更新所有线条的数据
        Args:
            line_datas (list): 线条数据列表
            window_size (int): 窗口大小
        """
        for line in self.lines:
            for item in line_datas:
                if line.label == item['label']:
                    self.update_line_data(line, item, window_size)

    def calculate_axis_limits(self, line_datas: list[dict], window_size: int):
        """
        计算坐标轴范围
        Args:
            line_datas (list): 线条数据列表
            window_size (int): 窗口大小
        Returns:
            tuple: (x_min, x_max, y_min, y_max)
        """
        return self.get_ax_max_min(line_datas, 'Date', 'Close', window_size)

    def set_axis_limits(self, x_min, x_max, y_min, y_max):
        """
        设置坐标轴范围
        Args:
            x_min: x轴最小值
            x_max: x轴最大值
            y_min: y轴最小值
            y_max: y轴最大值
        """
        # 强制转换为pd.Timestamp，避免date2num报错
        x_min = pd.to_datetime(x_min)
        x_max = pd.to_datetime(x_max)
        self.ax.set_xlim(float(mdates.date2num(x_min)), float(mdates.date2num(x_max)))
        self.ax.set_ylim(y_min * 0.95, y_max * 1.1)

    def update_strategy_display(self, strategy_info: dict | None):
        """
        更新策略显示
        Args:
            strategy_info (dict): 策略信息字典
        """
        if strategy_info and self.strategy_text:
            # 添加调试信息
            print(f"Debug - Strategy info received: {strategy_info}")
            
            # 根据盈利情况设置颜色
            profit_color = 'green' if strategy_info.get('total_profit', 0) >= 0 else 'red'
            
            # 获取年化收益率，确保有默认值
            annual_return = strategy_info.get('annualized_return', 0)
            if annual_return is None:
                annual_return = 0
            
            # 获取财年收益率信息
            fiscal_year_returns = strategy_info.get('fiscal_year_returns', {})
            current_fiscal_year_return = strategy_info.get('current_fiscal_year_return', 0)
            
            # 构建财年收益率显示文本
            fiscal_year_text = "Fiscal Year Returns:\n"
            for year, return_rate in fiscal_year_returns.items():
                fiscal_year_text += f"  {year}: {return_rate:.4f}%\n"
            
            strategy_text = f"""Strategy Status:
Balance: ${strategy_info.get('balance', 0):,.2f}
Shares: {strategy_info.get('shares', 0)}
Trades: {strategy_info.get('trades', 0)}
Current Price: ${strategy_info.get('current_price', 0):.2f}
Total Assets: ${strategy_info.get('current_total', 0):,.2f}
Profit: ${strategy_info.get('total_profit', 0):,.2f}
Overall Annual Return: {annual_return:.4f}%
Current Fiscal Year Return: {current_fiscal_year_return:.4f}%

{fiscal_year_text}"""
            
            self.strategy_text.set_text(strategy_text)
            # 根据盈利情况设置文本颜色
            self.strategy_text.set_color(profit_color)

    def update_fig(self, line_datas: list[dict], window_size: int = 50, strategy_info: dict | None = None):
        """
        更新图形数据（动画的每一帧调用）
        
        Args:
            line_datas (list): 当前帧的线条数据
            window_size (int): 显示窗口大小
            strategy_info (dict): 策略信息字典
            
        Returns:
            tuple: 需要更新的图形元素
        """
        # 更新所有线条的数据
        self.update_all_lines(line_datas, window_size)

        # 计算并设置坐标轴范围
        x_min, x_max, y_min, y_max = self.calculate_axis_limits(line_datas, window_size)
        self.set_axis_limits(x_min, x_max, y_min, y_max)
        
        # 更新策略显示
        self.update_strategy_display(strategy_info)
        
        # 更新图例
        self.ax.legend()
        return tuple(self.lines)

    def create_animation(self, frames, interval: int = 500, cache_frame_data: bool = False):
        """
        创建动画对象
        
        Args:
            frames: 数据帧生成器
            interval (int): 帧间隔（毫秒）
            cache_frame_data (bool): 是否缓存帧数据
            
        Returns:
            FuncAnimation: 动画对象
        """
        # 使用lambda包装update_fig，处理包含策略信息的元组数据
        def update_func(data_tuple):
            if isinstance(data_tuple, tuple) and len(data_tuple) == 2:
                data_stream, strategy_info = data_tuple
                return self.update_fig(data_stream, window_size=self.window_size, strategy_info=strategy_info)
            else:
                # 兼容旧格式
                return self.update_fig(data_tuple, window_size=self.window_size)
        
        return animation.FuncAnimation(
            self.fig,
            update_func,
            frames=frames,
            init_func=self.init_fig,
            interval=interval,
            cache_frame_data=cache_frame_data,
            repeat=False  # 不重复播放
        )


class FiscalYearReturnCalculator:
    """
    财年收益率计算类
    专门负责计算和跟踪每年的收益率
    """
    def __init__(self):
        self.fiscal_year_data = {}  # 存储每年的数据
        self.current_fiscal_year = None
        
    def get_fiscal_year(self, date: pd.Timestamp) -> int:
        """
        获取财年
        Args:
            date (pd.Timestamp): 日期
        Returns:
            int: 财年
        """
        return date.year
    
    def initialize_fiscal_year(self, date: pd.Timestamp, initial_balance: float):
        """
        初始化财年数据
        Args:
            date (pd.Timestamp): 日期
            initial_balance (float): 初始资金
        """
        fiscal_year = self.get_fiscal_year(date)
        if fiscal_year not in self.fiscal_year_data:
            self.fiscal_year_data[fiscal_year] = {
                'start_balance': initial_balance,
                'start_date': date,
                'end_balance': initial_balance,
                'end_date': date,
                'trades': 0
            }
    
    def update_fiscal_year_data(self, date: pd.Timestamp, current_balance: float, trade_count: int):
        """
        更新财年数据
        Args:
            date (pd.Timestamp): 当前日期
            current_balance (float): 当前资金
            trade_count (int): 交易次数
        """
        fiscal_year = self.get_fiscal_year(date)
        if fiscal_year in self.fiscal_year_data:
            self.fiscal_year_data[fiscal_year]['end_balance'] = current_balance
            self.fiscal_year_data[fiscal_year]['end_date'] = date
            self.fiscal_year_data[fiscal_year]['trades'] = trade_count
    
    def calculate_fiscal_year_return(self, fiscal_year: int) -> float:
        """
        计算指定财年的收益率
        Args:
            fiscal_year (int): 财年
        Returns:
            float: 年化收益率（百分比）
        """
        if fiscal_year not in self.fiscal_year_data:
            return 0.0
        
        data = self.fiscal_year_data[fiscal_year]
        start_balance = data['start_balance']
        end_balance = data['end_balance']
        start_date = data['start_date']
        end_date = data['end_date']
        
        if start_balance == 0:
            return 0.0
        
        days_in_year = (end_date - start_date).days
        if days_in_year <= 0:
            return 0.0
        
        total_return = (end_balance - start_balance) / start_balance
        annualized_return = (total_return / days_in_year) * 365 * 100
        
        return annualized_return
    
    def get_all_fiscal_year_returns(self) -> dict:
        """
        获取所有财年的收益率
        Returns:
            dict: 财年收益率字典
        """
        returns = {}
        for fiscal_year in sorted(self.fiscal_year_data.keys()):
            returns[fiscal_year] = self.calculate_fiscal_year_return(fiscal_year)
        return returns
    
    def get_current_fiscal_year_return(self, date: pd.Timestamp) -> float:
        """
        获取当前财年的收益率
        Args:
            date (pd.Timestamp): 当前日期
        Returns:
            float: 当前财年年化收益率
        """
        fiscal_year = self.get_fiscal_year(date)
        return self.calculate_fiscal_year_return(fiscal_year)


class BaseStrategy(ABC):
    """
    策略基类（接口）
    定义所有策略必须实现的接口方法
    """
    
    def __init__(self):
        self.balance = 1000000  # 初始资金
        self.share_num = 0      # 持有股票数量
        self.last_action = None # 上次交易动作
        self.trade_count = 0    # 交易次数
        self.initial_balance = 1000000  # 初始资金，用于计算盈利
        self.total_profit = 0   # 总盈利
        self.annualized_return = 0  # 年化收益率
        self.start_date = None  # 开始日期
        self.current_date = None  # 当前日期
        self.fiscal_calculator = FiscalYearReturnCalculator()  # 财年收益率计算器

    @abstractmethod
    def predict_price(self, org_data: pd.DataFrame, window: int, 
                     time_column: str = 'Date', target_column: str = 'Close') -> float:
        """
        预测价格（抽象方法）
        Args:
            org_data (pd.DataFrame): 历史数据
            window (int): 预测窗口大小
            time_column (str): 时间列名
            target_column (str): 目标列名
        Returns:
            float: 预测价格
        """
        pass

    @abstractmethod
    def execute_strategy(self, org_data: pd.DataFrame, short_window: int, long_window: int, 
                        next_timestamp: pd.Timestamp, time_column: str = 'Date', 
                        account_column: str = 'Close'):
        """
        执行策略（抽象方法）
        Args:
            org_data (pd.DataFrame): 原始数据
            short_window (int): 短期窗口大小
            long_window (int): 长期窗口大小
            next_timestamp (pd.Timestamp): 下一个时间戳
            time_column (str): 时间列名
            account_column (str): 价格列名
        """
        pass

    def set_start_date(self, start_date):
        """
        设置开始日期
        Args:
            start_date: 开始日期
        """
        self.start_date = pd.to_datetime(start_date)
        # 初始化财年数据
        self.fiscal_calculator.initialize_fiscal_year(self.start_date, self.initial_balance)

    def execute_buy(self, current_price: float, shares_to_buy: int = 100):
        """
        执行买入操作
        Args:
            current_price (float): 当前价格
            shares_to_buy (int): 买入股数
        """
        cost = shares_to_buy * current_price
        if self.balance >= cost:
            self.balance -= cost
            self.share_num += shares_to_buy
            self.trade_count += 1
            self.last_action = 'BUY'
            print(f"BUY: {shares_to_buy} shares at ${current_price:.2f}, Balance: ${self.balance:.2f}")

    def execute_sell(self, current_price: float, shares_to_sell: int = 100):
        """
        执行卖出操作
        Args:
            current_price (float): 当前价格
            shares_to_sell (int): 卖出股数
        """
        revenue = shares_to_sell * current_price
        self.balance += revenue
        self.share_num -= shares_to_sell
        self.trade_count += 1
        self.last_action = 'SELL'
        print(f"SELL: {shares_to_sell} shares at ${current_price:.2f}, Balance: ${self.balance:.2f}")

    def _update_profit_info(self, current_price: float):
        """
        更新盈利信息
        Args:
            current_price (float): 当前股价
        """
        # 计算当前总资产（现金 + 股票市值）
        current_total = self.balance + (self.share_num * current_price)
        self.total_profit = current_total - self.initial_balance
        
        # 更新财年数据
        if self.current_date is not None:
            self.fiscal_calculator.update_fiscal_year_data(
                self.current_date, current_total, self.trade_count
            )
        
        # 计算年化收益率
        if self.start_date is not None and self.current_date is not None:
            days_elapsed = (self.current_date - self.start_date).days
            if days_elapsed > 0:
                # 年化收益率 = (总收益率 / 天数) * 365
                total_return_rate = self.total_profit / self.initial_balance
                self.annualized_return = (total_return_rate / days_elapsed) * 365 * 100
            else:
                # 第一天，设置为0
                self.annualized_return = 0
        else:
            self.annualized_return = 0
        
        # 添加调试信息
        if self.start_date is not None and self.current_date is not None:
            days_elapsed = (self.current_date - self.start_date).days
        else:
            days_elapsed = 'N/A'
        print(f"Debug - Days elapsed: {days_elapsed}, "
              f"Total profit: ${self.total_profit:.2f}, Annual return: {self.annualized_return:.4f}%")

    def get_strategy_result(self):
        """
        获取策略结果
        Returns:
            tuple: (余额, 股票数量, 交易次数, 总资产)
        """
        return self.balance, self.share_num, self.trade_count, self.balance + self.share_num * 0.1

    def get_profit_info(self, current_price: float):
        """
        获取盈利信息
        Args:
            current_price (float): 当前股价
        Returns:
            dict: 包含盈利信息的字典
        """
        self._update_profit_info(current_price)
        current_total = self.balance + (self.share_num * current_price)
        
        # 获取财年收益率信息
        fiscal_year_returns = self.fiscal_calculator.get_all_fiscal_year_returns()
        current_fiscal_year_return = 0.0
        if self.current_date is not None:
            current_fiscal_year_return = self.fiscal_calculator.get_current_fiscal_year_return(self.current_date)
        
        return {
            'balance': self.balance,
            'shares': self.share_num,
            'trades': self.trade_count,
            'current_price': current_price,
            'total_profit': self.total_profit,
            'annualized_return': self.annualized_return,
            'current_total': current_total,
            'fiscal_year_returns': fiscal_year_returns,
            'current_fiscal_year_return': current_fiscal_year_return
        }


class MeanStrategy(BaseStrategy):
    """
    移动平均策略类
    继承自BaseStrategy，实现移动平均交易策略
    """
    
    def predict_price(self, org_data: pd.DataFrame, window: int, 
                     time_column: str = 'Date', target_column: str = 'Close') -> float:
        """
        预测价格（移动平均）
        Args:
            org_data (pd.DataFrame): 历史数据
            window (int): 预测窗口大小
            time_column (str): 时间列名
            target_column (str): 目标列名
        Returns:
            float: 预测价格
        """
        window_df = org_data[-window:].reset_index(drop=True)
        predicted_price = float(window_df[target_column].mean())
        return predicted_price

    def calculate_moving_averages(self, org_data: pd.DataFrame, short_window: int, long_window: int, account_column: str = 'Close'):
        """
        计算移动平均线
        Args:
            org_data (pd.DataFrame): 原始数据
            short_window (int): 短期窗口大小
            long_window (int): 长期窗口大小
            account_column (str): 价格列名
        Returns:
            tuple: (短期均线, 长期均线)
        """
        short_ma = org_data[account_column].rolling(window=short_window).mean().iloc[-1]
        long_ma = org_data[account_column].rolling(window=long_window).mean().iloc[-1]
        return short_ma, long_ma

    def should_buy(self, short_ma: float, long_ma: float, current_price: float):
        """
        判断是否应该买入
        Args:
            short_ma (float): 短期均线
            long_ma (float): 长期均线
            current_price (float): 当前价格
        Returns:
            bool: 是否应该买入
        """
        return short_ma > long_ma and self.balance >= current_price * 100

    def should_sell(self, short_ma: float, long_ma: float, current_price: float):
        """
        判断是否应该卖出
        Args:
            short_ma (float): 短期均线
            long_ma (float): 长期均线
            current_price (float): 当前价格
        Returns:
            bool: 是否应该卖出
        """
        return short_ma < long_ma and self.share_num >= 100

    def execute_strategy(self, org_data: pd.DataFrame, short_window: int, long_window: int, next_timestamp: pd.Timestamp, 
                        time_column: str = 'Date', account_column: str = 'Close'):
        """
        执行移动平均策略
        Args:
            org_data (pd.DataFrame): 原始数据
            short_window (int): 短期窗口大小
            long_window (int): 长期窗口大小
            next_timestamp (pd.Timestamp): 下一个时间戳
            time_column (str): 时间列名
            account_column (str): 价格列名
        """
        if len(org_data) < long_window:
            return  # 数据不足，不交易
            
        current_price = org_data[account_column].iloc[-1]
        
        # 设置开始日期（如果还没有设置）
        if self.start_date is None:
            self.set_start_date(org_data[time_column].iloc[0])
        
        # 更新当前日期
        self.current_date = pd.to_datetime(next_timestamp)
        
        # 检查是否需要初始化新的财年
        current_fiscal_year = self.fiscal_calculator.get_fiscal_year(self.current_date)
        if current_fiscal_year not in self.fiscal_calculator.fiscal_year_data:
            # 计算当前总资产作为新财年的起始资金
            current_total = self.balance + (self.share_num * current_price)
            self.fiscal_calculator.initialize_fiscal_year(self.current_date, current_total)
        
        # 计算移动平均线
        short_ma, long_ma = self.calculate_moving_averages(org_data, short_window, long_window, account_column)
        
        # 执行交易决策
        if self.should_buy(short_ma, long_ma, current_price):
            self.execute_buy(current_price)
        elif self.should_sell(short_ma, long_ma, current_price):
            self.execute_sell(current_price)
            
        # 更新盈利信息
        self._update_profit_info(current_price) 