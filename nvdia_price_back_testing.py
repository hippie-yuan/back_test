from base import DataGenerator, Animation, MeanStrategy, BaseStrategy
import pandas as pd
import matplotlib.pyplot as plt


def create_predictor():
    """
    创建预测器实例
    Returns:
        MeanStrategy: 移动平均策略实例
    """
    return MeanStrategy()


def create_prediction_dataframes(column_names: list):
    """
    创建预测数据DataFrame
    Args:
        column_names (list): 列名列表
    Returns:
        tuple: (5日均线预测数据, 20日均线预测数据)
    """
    mean_5_prdt_data = pd.DataFrame(columns=column_names)
    mean_20_prdt_data = pd.DataFrame(columns=column_names)
    return mean_5_prdt_data, mean_20_prdt_data


def execute_strategy(strategy: BaseStrategy, iter_org_data: pd.DataFrame, timestamp: pd.Timestamp):
    """
    执行策略
    Args:
        strategy (BaseStrategy): 策略实例
        iter_org_data (pd.DataFrame): 历史数据
        timestamp (pd.Timestamp): 时间戳
    """
    strategy.execute_strategy(iter_org_data, 5, 20, timestamp, 'Date', 'Close')


def generate_predictions(strategy: BaseStrategy, iter_org_data: pd.DataFrame, timestamp: pd.Timestamp):
    """
    生成预测值
    Args:
        strategy (BaseStrategy): 策略实例
        iter_org_data (pd.DataFrame): 历史数据
        timestamp (pd.Timestamp): 时间戳
    Returns:
        tuple: (5日预测值, 20日预测值)
    """
    pred_5_value = strategy.predict_price(iter_org_data, 5, 'Date', 'Close')
    pred_20_value = strategy.predict_price(iter_org_data, 20, 'Date', 'Close')
    return pred_5_value, pred_20_value


def update_prediction_data(prdt_data_class: DataGenerator, mean_5_prdt_data: pd.DataFrame, 
                          mean_20_prdt_data: pd.DataFrame, timestamp: pd.Timestamp, 
                          pred_5_value: float, pred_20_value: float):
    """
    更新预测数据
    Args:
        prdt_data_class (DataGenerator): 数据生成器实例
        mean_5_prdt_data (pd.DataFrame): 5日均线预测数据
        mean_20_prdt_data (pd.DataFrame): 20日均线预测数据
        timestamp (pd.Timestamp): 时间戳
        pred_5_value (float): 5日预测值
        pred_20_value (float): 20日预测值
    Returns:
        tuple: (更新后的5日均线预测数据, 更新后的20日均线预测数据)
    """
    mean_5_prdt_data = prdt_data_class.append_to_dataframe(mean_5_prdt_data, timestamp, pred_5_value)
    mean_20_prdt_data = prdt_data_class.append_to_dataframe(mean_20_prdt_data, timestamp, pred_20_value)
    
    # 只保留窗口内的数据
    mean_5_prdt_data = mean_5_prdt_data.tail(prdt_data_class.window_size).reset_index(drop=True)
    mean_20_prdt_data = mean_20_prdt_data.tail(prdt_data_class.window_size).reset_index(drop=True)
    
    return mean_5_prdt_data, mean_20_prdt_data


def create_data_stream(iter_org_data: pd.DataFrame, mean_5_prdt_data: pd.DataFrame, mean_20_prdt_data: pd.DataFrame):
    """
    创建数据流
    Args:
        iter_org_data (pd.DataFrame): 历史数据
        mean_5_prdt_data (pd.DataFrame): 5日均线预测数据
        mean_20_prdt_data (pd.DataFrame): 20日均线预测数据
    Returns:
        list: 数据流列表
    """
    return [
        {'label': 'Real Time Price', 'datas': iter_org_data},
        {'label': 'Prediction 5 Price', 'datas': mean_5_prdt_data},
        {'label': 'Prediction 20 Price', 'datas': mean_20_prdt_data}
    ]


def create_strategy_info(strategy: BaseStrategy, iter_org_data: pd.DataFrame):
    """
    创建策略信息
    Args:
        strategy (BaseStrategy): 策略实例
        iter_org_data (pd.DataFrame): 历史数据
    Returns:
        dict: 策略信息字典
    """
    current_price = iter_org_data.iloc[-1]['Close'] if len(iter_org_data) > 0 else 0
    return strategy.get_profit_info(current_price)


def data_stream_generator(org_data_class: DataGenerator, column_names: list, strategy: BaseStrategy):
    """
    数据流生成器 - 使用DataGenerator作为工具类
    
    Args:
        org_data_class (DataGenerator): 数据生成器实例
        column_names (list): 列名列表
        strategy (BaseStrategy): 策略实例
        
    Yields:
        tuple: (数据流列表, 策略信息字典)
    """
    # 创建预测数据DataFrame
    mean_5_prdt_data, mean_20_prdt_data = create_prediction_dataframes(column_names)
    prdt_data_class = DataGenerator(data=org_data_class.data, window_size=org_data_class.window_size)
    
    while True:
        try:
            # 获取下一个时间戳和历史数据
            timestamp, iter_org_data = next(org_data_class.iter_next_org_datas('Date'))
            
            # 执行策略
            execute_strategy(strategy, iter_org_data, timestamp)
            
            # 每10次交易打印一次结果
            if strategy.trade_count % 10 == 0 and strategy.trade_count > 0:
                balance, shares, trades, total = strategy.get_strategy_result()
                print(f"Strategy Update - Balance: ${balance:.2f}, Shares: {shares}, Trades: {trades}")

            # 生成预测值
            pred_5_value, pred_20_value = generate_predictions(strategy, iter_org_data, timestamp)
            
            # 更新预测数据
            mean_5_prdt_data, mean_20_prdt_data = update_prediction_data(
                prdt_data_class, mean_5_prdt_data, mean_20_prdt_data, 
                timestamp, pred_5_value, pred_20_value
            )
            
            # 创建数据流
            data_stream = create_data_stream(iter_org_data, mean_5_prdt_data, mean_20_prdt_data)
            
            # 准备策略信息
            strategy_info = create_strategy_info(strategy, iter_org_data)
            
            yield (data_stream, strategy_info)
            
        except StopIteration:
            print("Data stream ended")
            # 打印最终策略结果
            balance, shares, trades, total = strategy.get_strategy_result()
            print(f"Final Strategy Result - Balance: ${balance:.2f}, Shares: {shares}, Total Trades: {trades}")
            break
        except Exception as e:
            print(f"Error in data_stream_generator: {str(e)}")
            import traceback
            traceback.print_exc()
            break


def initialize_data_generator(path: str = 'nvda_hist.csv', window_size: int = 50):
    """
    初始化数据生成器
    Args:
        path (str): CSV文件路径
        window_size (int): 窗口大小
    Returns:
        DataGenerator: 数据生成器实例
    """
    nvda_hist_class = DataGenerator(path=path, window_size=window_size)
    nvda_hist = nvda_hist_class.get_initial_data(['Date', 'Close'])
    print(f"Data loaded, shape: {nvda_hist.shape}")
    return nvda_hist_class


def create_strategy():
    """
    创建策略实例
    Returns:
        MeanStrategy: 移动平均策略实例
    """
    return MeanStrategy()


def create_line_properties():
    """
    创建线条属性
    Returns:
        list: 线条属性列表
    """
    return [
        {'label': 'Real Time Price', 'color': 'blue', 'x_name': 'Date', 'y_name': 'Close'},
        {'label': 'Prediction 5 Price', 'color': 'orange', 'x_name': 'Date', 'y_name': 'Close'},
        {'label': 'Prediction 20 Price', 'color': 'green', 'x_name': 'Date', 'y_name': 'Close'}
    ]


def create_animation_object(line_properties: list):
    """
    创建动画对象
    Args:
        line_properties (list): 线条属性列表
    Returns:
        Animation: 动画对象
    """
    global ani
    ani = Animation(line_properties)
    print("Animation object created")
    return ani


def create_data_stream_generator(nvda_hist_class: DataGenerator, strategy: BaseStrategy):
    """
    创建数据流生成器
    Args:
        nvda_hist_class (DataGenerator): 数据生成器实例
        strategy (BaseStrategy): 策略实例
    Returns:
        generator: 数据流生成器
    """
    data_stream_gen = data_stream_generator(nvda_hist_class, ['Date', 'Close'], strategy)
    print("Data stream created")
    return data_stream_gen


def start_animation(ani: Animation, data_stream_gen, interval: int = 10):
    """
    启动动画
    Args:
        ani (Animation): 动画对象
        data_stream_gen: 数据流生成器
        interval (int): 更新间隔
    """
    ani = ani.create_animation(
        frames=data_stream_gen,
        interval=interval,
        cache_frame_data=False
    )
    print("Animation created, starting...")
    
    plt.show()
    print("Animation finished")


def main():
    """
    主函数
    程序入口点，负责初始化各个组件并启动动画
    """
    print("Initializing stock prediction animation system...")
    
    try:
        # 初始化数据生成器
        nvda_hist_class = initialize_data_generator()
        
        # 创建策略
        strategy = create_strategy()
        
        # 定义线条属性
        line_properties = create_line_properties()
        
        # 创建动画对象
        ani = create_animation_object(line_properties)
        
        # 创建数据流
        data_stream_gen = create_data_stream_generator(nvda_hist_class, strategy)
        
        # 启动动画
        start_animation(ani, data_stream_gen)
        
    except Exception as e:
        print(f"Error in main: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
    print('Program finished')
