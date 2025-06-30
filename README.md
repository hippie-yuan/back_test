# 股票价格预测动画系统

一个基于Python的股票价格实时预测和交易策略可视化系统，支持移动平均策略回测和动画展示。

## 🚀 功能特性

- **实时数据流**: 支持CSV数据文件的实时读取和处理
- **策略回测**: 实现移动平均交叉策略的交易回测
- **动画可视化**: 使用matplotlib创建实时价格预测动画
- **配置管理**: 支持环境变量和配置文件的多层次配置
- **日志系统**: 完整的日志记录和性能监控
- **异常处理**: 健壮的错误处理和恢复机制
- **模块化设计**: 清晰的类结构和职责分离

## 📁 项目结构

```
test/
├── base.py                    # 核心模块，包含所有类
│   ├── DataGenerator         # 数据生成器
│   ├── Animation            # 动画类
│   ├── BaseStrategy         # 策略基类
│   ├── MeanStrategy         # 移动平均策略
│   └── StockPredictionSystem # 系统协调器
├── config.py                 # 配置管理
├── nvdia_price_back_testing.py  # 应用示例
├── test_system.py            # 测试文件
├── README.md                 # 项目文档
└── nvda_hist.csv            # 股票数据文件
```

## 🛠️ 安装依赖

```bash
pip install pandas matplotlib yfinance numpy
```

## 🚀 快速开始

### 基本使用

```python
from base import StockPredictionSystem

# 创建系统实例
system = StockPredictionSystem(
    csv_path='nvda_hist.csv',
    window_size=50,
    interval=10
)

# 运行系统
system.run()
```

### 使用配置文件

```python
from config import Config
from base import StockPredictionSystem

# 加载配置
config = Config('config.json')

# 创建系统实例
system = StockPredictionSystem(
    csv_path=config.get('data', 'csv_path'),
    window_size=config.get('data', 'window_size'),
    interval=config.get('animation', 'interval')
)

# 运行系统
system.run()
```

## ⚙️ 配置选项

### 环境变量

| 变量名 | 描述 | 默认值 |
|--------|------|--------|
| `STOCK_CSV_PATH` | CSV文件路径 | `nvda_hist.csv` |
| `WINDOW_SIZE` | 数据窗口大小 | `50` |
| `ANIMATION_INTERVAL` | 动画更新间隔(ms) | `10` |
| `SHORT_WINDOW` | 短期移动平均窗口 | `5` |
| `LONG_WINDOW` | 长期移动平均窗口 | `20` |
| `INITIAL_BALANCE` | 初始资金 | `1000000` |
| `SHARES_PER_TRADE` | 每次交易股数 | `100` |
| `TRADE_UPDATE_FREQ` | 交易更新频率 | `10` |
| `LOG_LEVEL` | 日志级别 | `INFO` |
| `LOG_FILE` | 日志文件路径 | `None` |

### 配置文件示例

```json
{
  "data": {
    "csv_path": "nvda_hist.csv",
    "window_size": 50,
    "columns": ["Date", "Close"]
  },
  "animation": {
    "interval": 10,
    "figure_size": [14, 10],
    "dpi": 100
  },
  "strategy": {
    "short_window": 5,
    "long_window": 20,
    "initial_balance": 1000000,
    "shares_per_trade": 100,
    "trade_update_frequency": 10
  },
  "logging": {
    "level": "INFO",
    "log_file": "stock_prediction.log",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  }
}
```

## 📊 系统组件

### DataGenerator (数据生成器)

负责读取CSV文件，管理数据索引，提供数据迭代功能。

```python
dg = DataGenerator(path='data.csv', window_size=50)
initial_data = dg.get_initial_data(['Date', 'Close'])
```

### Animation (动画类)

负责创建和管理matplotlib动画，包括图形初始化、数据更新和坐标轴管理。

```python
animation = Animation(line_properties)
animation.create_animation(frames=data_stream, interval=10)
```

### BaseStrategy (策略基类)

抽象基类，定义策略接口。

### MeanStrategy (移动平均策略)

实现移动平均交叉策略，包括：
- 价格预测
- 交易信号生成
- 收益计算

### StockPredictionSystem (系统协调器)

管理整个系统的生命周期，协调各个组件的工作。

## 🧪 测试

运行测试套件：

```bash
python test_system.py
```

测试覆盖：
- 数据生成器功能
- 策略计算逻辑
- 动画组件
- 系统集成
- 配置管理

## 📈 策略说明

### 移动平均交叉策略

1. **买入信号**: 短期移动平均线上穿长期移动平均线
2. **卖出信号**: 短期移动平均线下穿长期移动平均线
3. **仓位管理**: 每次交易固定股数
4. **风险控制**: 基于历史数据的回测验证

### 性能指标

- 总收益
- 年化收益率
- 交易次数
- 胜率
- 最大回撤

## 🔧 开发指南

### 添加新策略

1. 继承 `BaseStrategy` 类
2. 实现 `predict_price` 和 `execute_strategy` 方法
3. 在 `StockPredictionSystem` 中注册新策略

```python
class MyStrategy(BaseStrategy):
    def predict_price(self, org_data, window, time_column, target_column):
        # 实现价格预测逻辑
        pass
    
    def execute_strategy(self, org_data, short_window, long_window, 
                        next_timestamp, time_column, account_column):
        # 实现策略执行逻辑
        pass
```

### 自定义动画

修改 `Animation` 类中的线条属性和显示设置：

```python
line_properties = [
    {'label': 'My Line', 'color': 'purple', 'x_name': 'Date', 'y_name': 'Close'}
]
```

## 🐛 故障排除

### 常见问题

1. **数据文件不存在**
   - 检查CSV文件路径是否正确
   - 确保文件包含必要的列（Date, Close）

2. **动画显示问题**
   - 检查matplotlib后端设置
   - 确保有图形界面支持

3. **性能问题**
   - 调整窗口大小
   - 减少动画更新频率
   - 启用性能监控

### 日志调试

设置日志级别为DEBUG获取详细信息：

```python
import os
os.environ['LOG_LEVEL'] = 'DEBUG'
```

## 📝 更新日志

### v1.0.0
- 初始版本发布
- 基本功能实现
- 移动平均策略
- 动画可视化

### v1.1.0
- 添加配置管理
- 改进日志系统
- 添加性能监控
- 完善异常处理

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

MIT License

## 📞 联系方式

如有问题或建议，请提交 Issue 或联系开发者。 