"""
策略相关模块
"""
import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from .utils import logger, performance_monitor
from .exceptions import StrategyError


class FiscalYearReturnCalculator:
    """
    财年收益率计算器
    用于计算不同财年的收益率
    """
    
    def __init__(self):
        self.fiscal_year_data = {}
    
    def get_fiscal_year(self, date: pd.Timestamp) -> int:
        """
        获取财年
        
        Args:
            date (pd.Timestamp): 日期
            
        Returns:
            int: 财年
        """
        # 假设财年从1月1日开始
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
                'start_date': date,
                'initial_balance': initial_balance,
                'current_balance': initial_balance,
                'trade_count': 0,
                'max_balance': initial_balance,
                'min_balance': initial_balance
            }
    
    def update_fiscal_year_data(self, date: pd.Timestamp, current_balance: float, trade_count: int):
        """
        更新财年数据
        
        Args:
            date (pd.Timestamp): 日期
            current_balance (float): 当前资金
            trade_count (int): 交易次数
        """
        fiscal_year = self.get_fiscal_year(date)
        if fiscal_year in self.fiscal_year_data:
            self.fiscal_year_data[fiscal_year]['current_balance'] = current_balance
            self.fiscal_year_data[fiscal_year]['trade_count'] = trade_count
            self.fiscal_year_data[fiscal_year]['max_balance'] = max(
                self.fiscal_year_data[fiscal_year]['max_balance'], current_balance
            )
            self.fiscal_year_data[fiscal_year]['min_balance'] = min(
                self.fiscal_year_data[fiscal_year]['min_balance'], current_balance
            )
    
    def calculate_fiscal_year_return(self, fiscal_year: int) -> float:
        """
        计算财年收益率
        
        Args:
            fiscal_year (int): 财年
            
        Returns:
            float: 收益率
        """
        if fiscal_year not in self.fiscal_year_data:
            return 0.0
        
        data = self.fiscal_year_data[fiscal_year]
        initial_balance = data['initial_balance']
        current_balance = data['current_balance']
        
        if initial_balance == 0:
            return 0.0
        
        return (current_balance - initial_balance) / initial_balance
    
    def get_all_fiscal_year_returns(self) -> dict:
        """
        获取所有财年收益率
        
        Returns:
            dict: 财年收益率字典
        """
        returns = {}
        for fiscal_year in self.fiscal_year_data:
            returns[fiscal_year] = self.calculate_fiscal_year_return(fiscal_year)
        return returns
    
    def get_current_fiscal_year_return(self, date: pd.Timestamp) -> float:
        """
        获取当前财年收益率
        
        Args:
            date (pd.Timestamp): 日期
            
        Returns:
            float: 当前财年收益率
        """
        fiscal_year = self.get_fiscal_year(date)
        return self.calculate_fiscal_year_return(fiscal_year)


class BaseStrategy(ABC):
    """
    策略基类
    定义策略的基本接口和通用功能
    """
    
    def __init__(self):
        """初始化策略"""
        self.balance = 1000000  # 初始资金
        self.share_num = 0      # 持有股数
        self.trade_count = 0    # 交易次数
        self.start_date = None  # 开始日期
        self.current_date = None # 当前日期
        
        # 财年收益率计算器
        self.fiscal_calculator = FiscalYearReturnCalculator()
        
        # 盈利信息
        self.profit_info = {
            'total_profit': 0.0,
            'annualized_return': 0.0,
            'current_total': 0.0
        }
    
    @abstractmethod
    def predict_price(self, org_data: pd.DataFrame, window: int, 
                     time_column: str = 'Date', target_column: str = 'Close') -> float:
        """
        预测价格（抽象方法）
        
        Args:
            org_data (pd.DataFrame): 历史数据
            window (int): 预测窗口
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
            org_data (pd.DataFrame): 历史数据
            short_window (int): 短期窗口
            long_window (int): 长期窗口
            next_timestamp (pd.Timestamp): 下一个时间戳
            time_column (str): 时间列名
            account_column (str): 账户列名
        """
        pass
    
    def set_start_date(self, start_date):
        """设置开始日期"""
        self.start_date = pd.to_datetime(start_date)
        # 初始化财年数据
        self.fiscal_calculator.initialize_fiscal_year(self.start_date, self.balance)
    
    def execute_buy(self, current_price: float, shares_to_buy: int = 100):
        """
        执行买入操作
        
        Args:
            current_price (float): 当前价格
            shares_to_buy (int): 买入股数
        """
        cost = current_price * shares_to_buy
        if cost <= self.balance:
            self.balance -= cost
            self.share_num += shares_to_buy
            self.trade_count += 1
            logger.info(f"BUY: {shares_to_buy} shares at ${current_price:.2f}, Balance: ${self.balance:.2f}")
        else:
            logger.warning(f"Insufficient balance for buy order: ${cost:.2f} > ${self.balance:.2f}")
    
    def execute_sell(self, current_price: float, shares_to_sell: int = 100):
        """
        执行卖出操作
        
        Args:
            current_price (float): 当前价格
            shares_to_sell (int): 卖出股数
        """
        if shares_to_sell <= self.share_num:
            revenue = current_price * shares_to_sell
            self.balance += revenue
            self.share_num -= shares_to_sell
            self.trade_count += 1
            logger.info(f"SELL: {shares_to_sell} shares at ${current_price:.2f}, Balance: ${self.balance:.2f}")
        else:
            logger.warning(f"Insufficient shares for sell order: {shares_to_sell} > {self.share_num}")
    
    def _update_profit_info(self, current_price: float):
        """
        更新盈利信息
        
        Args:
            current_price (float): 当前价格
        """
        # 计算当前总资产
        current_total = self.balance + (self.share_num * current_price)
        
        # 计算总盈利
        total_profit = current_total - 1000000  # 相对于初始资金
        
        # 计算年化收益率
        if self.start_date and self.current_date:
            days_elapsed = (self.current_date - self.start_date).days
            if days_elapsed > 0:
                annualized_return = (total_profit / 1000000) * (365 / days_elapsed)
            else:
                annualized_return = 0.0
        else:
            annualized_return = 0.0
        
        # 更新盈利信息
        self.profit_info = {
            'total_profit': total_profit,
            'annualized_return': annualized_return,
            'current_total': current_total
        }
        
        # 更新财年数据
        if self.current_date:
            self.fiscal_calculator.update_fiscal_year_data(
                self.current_date, current_total, self.trade_count
            )
        
        # 调试信息
        if days_elapsed > 0:
            logger.debug(f"Debug - Days elapsed: {days_elapsed}, Total profit: ${total_profit:.2f}, Annual return: {annualized_return:.4%}")
    
    def get_strategy_result(self):
        """
        获取策略结果
        
        Returns:
            tuple: (余额, 股数, 交易次数, 总资产)
        """
        return self.balance, self.share_num, self.trade_count, self.profit_info['current_total']
    
    def get_profit_info(self, current_price: float) -> dict:
        """
        获取盈利信息
        
        Args:
            current_price (float): 当前价格
            
        Returns:
            dict: 盈利信息字典
        """
        self._update_profit_info(current_price)
        
        return {
            'balance': self.balance,
            'shares': self.share_num,
            'trades': self.trade_count,
            'current_price': current_price,
            'total_profit': self.profit_info['total_profit'],
            'annualized_return': self.profit_info['annualized_return'],
            'current_total': self.profit_info['current_total'],
            'fiscal_year_returns': self.fiscal_calculator.get_all_fiscal_year_returns(),
            'current_fiscal_year_return': self.fiscal_calculator.get_current_fiscal_year_return(self.current_date) if self.current_date else 0.0
        }


class MeanStrategy(BaseStrategy):
    """
    移动平均策略
    实现基于移动平均线交叉的交易策略
    """
    
    @performance_monitor
    def predict_price(self, org_data: pd.DataFrame, window: int, 
                     time_column: str = 'Date', target_column: str = 'Close') -> float:
        """
        使用移动平均预测价格
        
        Args:
            org_data (pd.DataFrame): 历史数据
            window (int): 移动平均窗口
            time_column (str): 时间列名
            target_column (str): 目标列名
            
        Returns:
            float: 预测价格
        """
        if len(org_data) < window:
            return org_data[target_column].iloc[-1] if len(org_data) > 0 else 0.0
        
        # 计算移动平均
        moving_average = org_data[target_column].rolling(window=window).mean().iloc[-1]
        return moving_average if not pd.isna(moving_average) else org_data[target_column].iloc[-1]
    
    def calculate_moving_averages(self, org_data: pd.DataFrame, short_window: int, long_window: int, account_column: str = 'Close'):
        """
        计算短期和长期移动平均线
        
        Args:
            org_data (pd.DataFrame): 历史数据
            short_window (int): 短期窗口
            long_window (int): 长期窗口
            account_column (str): 价格列名
            
        Returns:
            tuple: (短期移动平均, 长期移动平均)
        """
        if len(org_data) < max(short_window, long_window):
            current_price = org_data[account_column].iloc[-1] if len(org_data) > 0 else 0.0
            return current_price, current_price
        
        short_ma = org_data[account_column].rolling(window=short_window).mean().iloc[-1]
        long_ma = org_data[account_column].rolling(window=long_window).mean().iloc[-1]
        
        # 处理NaN值
        if pd.isna(short_ma):
            short_ma = org_data[account_column].iloc[-1]
        if pd.isna(long_ma):
            long_ma = org_data[account_column].iloc[-1]
        
        return short_ma, long_ma
    
    def should_buy(self, short_ma: float, long_ma: float, current_price: float) -> bool:
        """
        判断是否应该买入
        
        Args:
            short_ma (float): 短期移动平均
            long_ma (float): 长期移动平均
            current_price (float): 当前价格
            
        Returns:
            bool: 是否应该买入
        """
        # 短期移动平均线上穿长期移动平均线
        return short_ma > long_ma and self.balance > 0
    
    def should_sell(self, short_ma: float, long_ma: float, current_price: float) -> bool:
        """
        判断是否应该卖出
        
        Args:
            short_ma (float): 短期移动平均
            long_ma (float): 长期移动平均
            current_price (float): 当前价格
            
        Returns:
            bool: 是否应该卖出
        """
        # 短期移动平均线下穿长期移动平均线
        return short_ma < long_ma and self.share_num > 0
    
    @performance_monitor
    def execute_strategy(self, org_data: pd.DataFrame, short_window: int, long_window: int, next_timestamp: pd.Timestamp, 
                        time_column: str = 'Date', account_column: str = 'Close'):
        """
        执行移动平均策略
        
        Args:
            org_data (pd.DataFrame): 历史数据
            short_window (int): 短期窗口
            long_window (int): 长期窗口
            next_timestamp (pd.Timestamp): 下一个时间戳
            time_column (str): 时间列名
            account_column (str): 价格列名
        """
        if len(org_data) == 0:
            return
        
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