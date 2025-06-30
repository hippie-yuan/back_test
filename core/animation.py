"""
动画相关模块
"""
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.lines as line
from matplotlib import animation
from datetime import datetime
from typing import List, Dict, Any, Optional
from .utils import logger, performance_monitor
from .exceptions import AnimationError
import pandas as pd
from matplotlib.gridspec import GridSpec


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
        # 创建图形和子图布局
        self.fig = plt.figure(figsize=(16, 10))
        self.gs = GridSpec(1, 2, width_ratios=[4, 1])
        
        # 主图表区域
        self.ax = self.fig.add_subplot(self.gs[0])
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
        # 创建策略信息显示区域
        self.strategy_ax = self.fig.add_subplot(self.gs[1])
        self.strategy_ax.axis('off')  # 隐藏坐标轴
        
        # 在策略信息区域添加文本
        self.strategy_text = self.strategy_ax.text(
            0.1, 0.5, '', 
            fontsize=10,
            verticalalignment='center',
            horizontalalignment='left',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.9),
            fontfamily='monospace',
            transform=self.strategy_ax.transAxes
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
                line_property (dict): 线条属性字典，包含label, color, x_name, y_name
            """
            super().__init__([], [], 
                            label=line_property.get('label', ''),
                            color=line_property.get('color', 'blue'),
                            linewidth=2)
            
            # 存储列名
            self.x_name = line_property.get('x_name', 'Date')
            self.y_name = line_property.get('y_name', 'Close')
    
    def init_fig(self):
        """初始化图形"""
        # 清空所有线条数据
        for line in self.lines:
            line.set_data([], [])
        
        # 重置策略显示文本
        if self.strategy_text:
            self.strategy_text.set_text('')
        
        return self.lines + [self.strategy_text] if self.strategy_text else self.lines
    
    @performance_monitor
    def get_ax_max_min(self, lines_datas: list[dict], x_name: str, y_name: str, window_size: int = 50):
        """
        计算坐标轴的最大最小值
        
        Args:
            lines_datas (list[dict]): 线条数据列表
            x_name (str): x轴列名
            y_name (str): y轴列名
            window_size (int): 窗口大小
            
        Returns:
            tuple: (x_min, x_max, y_min, y_max)
        """
        x_values = []
        y_values = []
        for line_data in lines_datas:
            if 'datas' in line_data and len(line_data['datas']) > 0:
                data = line_data['datas'].tail(window_size)
                if x_name in data.columns and y_name in data.columns:
                    # 转换x为matplotlib日期
                    x_list = [
                        mdates.date2num(pd.to_datetime(x)) if not isinstance(x, (float, int)) else x
                        for x in data[x_name].tolist()
                    ]
                    x_values.extend(x_list)
                    y_values.extend(data[y_name].tolist())
        if not x_values or not y_values:
            return self._get_default_xlim() + (0, 1)
        # 过滤掉无效值
        valid_x = [x for x in x_values if pd.notna(x)]
        valid_y = [y for y in y_values if pd.notna(y)]
        if not valid_x or not valid_y:
            return self._get_default_xlim() + (0, 1)
        x_max = max(valid_x)
        x_min = x_max - (self.window_size - 1)
        y_min, y_max = min(valid_y), max(valid_y)
        # 添加边距
        x_margin = (x_max - x_min) * 0.05
        y_margin = (y_max - y_min) * 0.1
        return (x_min - x_margin, x_max + x_margin, y_min - y_margin, y_max + y_margin)
    
    def update_line_data(self, line, item, window_size: int):
        """
        更新单条线条的数据
        
        Args:
            line: 线条对象
            item (dict): 线条数据
            window_size (int): 窗口大小
        """
        if 'datas' in item and len(item['datas']) > 0:
            data = item['datas'].tail(window_size)
            if line.x_name in data.columns and line.y_name in data.columns:
                x_data = data[line.x_name].tolist()
                y_data = data[line.y_name].tolist()
                # 转换x轴为matplotlib日期
                x_data = [
                    mdates.date2num(pd.to_datetime(x)) if not isinstance(x, (float, int)) else x
                    for x in x_data
                ]
                # 过滤无效数据
                valid_data = [(x, y) for x, y in zip(x_data, y_data) 
                             if pd.notna(x) and pd.notna(y)]
                if valid_data:
                    x_values, y_values = zip(*valid_data)
                    line.set_data(x_values, y_values)
    
    def update_all_lines(self, line_datas: list[dict], window_size: int):
        """
        更新所有线条的数据
        
        Args:
            line_datas (list[dict]): 线条数据列表
            window_size (int): 窗口大小
        """
        for i, line in enumerate(self.lines):
            if i < len(line_datas):
                self.update_line_data(line, line_datas[i], window_size)
    
    def calculate_axis_limits(self, line_datas: list[dict], window_size: int):
        """
        计算坐标轴范围
        
        Args:
            line_datas (list[dict]): 线条数据列表
            window_size (int): 窗口大小
            
        Returns:
            tuple: (x_min, x_max, y_min, y_max)
        """
        return self.get_ax_max_min(line_datas, 'Date', 'Close', window_size)
    
    def set_axis_limits(self, x_min, x_max, y_min, y_max):
        """
        设置坐标轴范围
        
        Args:
            x_min, x_max: x轴范围
            y_min, y_max: y轴范围
        """
        self.ax.set_xlim(x_min, x_max)
        self.ax.set_ylim(y_min, y_max)
        
        # 重新格式化x轴 - 增加刻度数量
        self.ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        self.fig.autofmt_xdate()
        
        # 强制刷新坐标轴
        self.ax.figure.canvas.draw_idle()
    
    def update_strategy_display(self, strategy_info: dict | None):
        """
        更新策略信息显示
        
        Args:
            strategy_info (dict): 策略信息字典
        """
        if self.strategy_text and strategy_info:
            try:
                # 格式化策略信息
                info_text = f"Balance: ${strategy_info.get('balance', 0):,.2f}\n"
                info_text += f"Shares: {strategy_info.get('shares', 0)}\n"
                info_text += f"Trades: {strategy_info.get('trades', 0)}\n"
                info_text += f"Current Price: ${strategy_info.get('current_price', 0):.2f}\n"
                info_text += f"Total Profit: ${strategy_info.get('total_profit', 0):,.2f}\n"
                info_text += f"Annual Return: {strategy_info.get('annualized_return', 0):.4%}\n"
                
                # 添加每年的回报率
                fiscal_year_returns = strategy_info.get('fiscal_year_returns', {})
                if fiscal_year_returns:
                    info_text += f"\nYearly Returns:\n"
                    for year, return_rate in fiscal_year_returns.items():
                        info_text += f"{year}: {return_rate:.4%}\n"
                
                self.strategy_text.set_text(info_text)
            except Exception as e:
                logger.warning(f"Failed to update strategy display: {e}")
    
    @performance_monitor
    def update_fig(self, line_datas: list[dict], window_size: int = 50, strategy_info: dict | None = None):
        """
        更新整个图形
        
        Args:
            line_datas (list[dict]): 线条数据列表
            window_size (int): 窗口大小
            strategy_info (dict): 策略信息
        """
        try:
            # 更新所有线条数据
            self.update_all_lines(line_datas, window_size)
            
            # 计算并设置坐标轴范围
            x_min, x_max, y_min, y_max = self.calculate_axis_limits(line_datas, window_size)
            self.set_axis_limits(x_min, x_max, y_min, y_max)
            
            # 更新策略信息显示
            self.update_strategy_display(strategy_info)
            
            return self.lines + [self.strategy_text] if self.strategy_text else self.lines
            
        except Exception as e:
            logger.error(f"Error updating figure: {e}")
            raise AnimationError(f"Failed to update animation figure: {str(e)}")
    
    def create_animation(self, frames, interval: int = 500, cache_frame_data: bool = False):
        """
        创建动画
        
        Args:
            frames: 数据帧生成器
            interval (int): 更新间隔（毫秒）
            cache_frame_data (bool): 是否缓存帧数据
            
        Returns:
            matplotlib.animation.FuncAnimation: 动画对象
        """
        def update_func(data_tuple):
            """动画更新函数"""
            try:
                line_datas, strategy_info = data_tuple
                return self.update_fig(line_datas, self.window_size, strategy_info)
            except Exception as e:
                logger.error(f"Animation update error: {e}")
                return self.lines
        
        try:
            return animation.FuncAnimation(
                self.fig, update_func, frames=frames,
                init_func=self.init_fig, interval=interval,
                blit=False, cache_frame_data=cache_frame_data
            )
        except Exception as e:
            logger.error(f"Failed to create animation: {e}")
            raise AnimationError(f"Failed to create animation: {str(e)}") 