"""
数据相关模块
"""
import pandas as pd
from .utils import logger, performance_monitor
from .exceptions import DataError


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

    @performance_monitor
    def get_data_from_csv(self) -> pd.DataFrame:
        """从CSV文件读取数据"""
        try:
            return pd.read_csv(self.path)
        except Exception as e:
            raise DataError(f"Failed to read CSV file {self.path}: {str(e)}")

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