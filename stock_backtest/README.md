# 股票策略回测系统

一个功能完善的A股量化交易策略回测系统，支持多种回测引擎、策略参数优化和过拟合评估。

## 📋 目录

- [功能特性](#-功能特性)
- [项目架构](#-项目架构)
- [快速开始](#-快速开始)
- [详细使用说明](#-详细使用说明)
- [策略说明](#-策略说明)
- [回测引擎](#-回测引擎)
- [参数优化与验证](#-参数优化与验证)
- [API文档](#-api文档)
- [配置说明](#-配置说明)
- [注意事项](#-注意事项)

---

## ✨ 功能特性

### 核心功能

- **多数据源**：通过 akshare 获取A股日线数据（前复权）
- **多种策略**：支持双均线策略、布林带策略
- **三个回测引擎**：
  - 🔄 **循环回测引擎**：精确逐笔处理，适合精细验证
  - ⚡ **向量化回测引擎**：高性能批量计算，适合快速初筛
  - 🎯 **事件驱动回测引擎**：模拟真实交易，适合实盘验证
- **参数优化**：网格搜索 + 遗传算法寻优
- **交叉验证**：滚动向前验证，评估策略泛化能力
- **过拟合评估**：多维度量化评估策略过拟合风险

### 交易机制模拟

- ✅ **手续费**：真实交易手续费（默认万分之三）
- ✅ **滑点**：买卖价格滑点（默认万分之一）
- ✅ **止损止盈**：支持动态止损止盈
- ✅ **涨跌停限制**：普通±10%、ST±5%、创业板/科创板±20%、北交所±30%
- ✅ **ST股票识别**：自动识别并调整涨跌幅限制
- ✅ **停牌处理**：自动跳过停牌日期
- ✅ **前复权数据**：消除除权除息影响

### 数据优化

- 🗄️ **智能缓存**：历史数据缓存7天，近期数据缓存1天
- 🔍 **股票搜索**：支持代码和名称模糊搜索
- 📊 **批量处理**：支持多股票、多策略批量测试

---

## 🏗️ 项目架构

### 目录结构

```
stock_backtest/
├── main.py                    # 命令行入口
├── app.py                     # Web界面入口
├── config.py                  # 全局配置
├── requirements.txt           # 依赖列表
│
├── src/                       # 源代码目录
│   ├── __init__.py
│   ├── data_fetcher.py        # 数据获取模块
│   ├── strategies.py          # 策略实现
│   ├── backtester.py          # 回测引擎基类
│   ├── true_vectorized.py     # 向量化回测引擎
│   ├── event_driven.py        # 事件驱动回测引擎
│   ├── optimizer.py            # 参数优化器
│   ├── cross_validator.py     # 交叉验证器
│   ├── utils.py               # 工具函数
│   ├── logger.py              # 日志系统
│   └── hybrid_framework.py    # 混合框架
│
├── tests/                     # 测试目录
│   ├── test_backtester.py
│   ├── test_strategies.py
│   ├── test_data_fetcher.py
│   └── test_logger.py
│
├── data/                      # 数据缓存目录
├── logs/                      # 日志文件目录
└── assets/                    # 静态资源目录
```

### 系统架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                        用户交互层                                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────┐              ┌─────────────────┐               │
│  │   命令行界面    │              │    Web界面      │               │
│  │   (main.py)    │              │    (app.py)     │               │
│  └────────┬───────┘              └────────┬────────┘               │
│           │                               │                        │
│           └───────────────┬───────────────┘                        │
│                           ↓                                         │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │                      业务逻辑层                                │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │  Optimizer   │    │  CrossValid  │    │   Utils      │          │
│  │  参数优化    │    │  交叉验证    │    │  工具函数    │          │
│  └──────────────┘    └──────────────┘    └──────────────┘          │
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │  Backtester  │    │TrueVectorized│    │EventDriven   │          │
│  │  循环引擎    │    │  向量化引擎  │    │ 事件驱动引擎 │          │
│  └──────────────┘    └──────────────┘    └──────────────┘          │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │                      数据策略层                                │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐                              │
│  │  Strategy    │    │DataFetcher   │                              │
│  │  双均线/布林带│    │ AKShare数据   │                              │
│  └──────────────┘    └──────────────┘                              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 快速开始

### 1. 环境准备

```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows
.\.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 命令行快速回测

```bash
# 双均线策略回测
python main.py -s 600519 -start 20230101 -end 20241231

# 布林带策略回测
python main.py -s 600519 -strategy bollinger -start 20230101 -end 20241231

# 参数优化
python main.py -s 600519 -strategy dual_ma -optimize

# 交叉验证
python main.py -s 600519 -strategy bollinger -validate
```

### 3. Web界面回测

```bash
# 启动Web服务
python app.py

# 访问地址
http://127.0.0.1:8050/
```

---

## 📖 详细使用说明

### 命令行参数

| 参数 | 说明 | 默认值 | 示例 |
|:---:|---|---|:---:|
| `-s` | 股票代码（6位数字） | 必填 | `600519` |
| `-strategy` | 策略类型 | `dual_ma` | `dual_ma`, `bollinger` |
| `-start` | 开始日期 | `20230101` | `20200101` |
| `-end` | 结束日期 | `20241231` | `20241231` |
| `-optimize` | 是否优化参数 | `False` | 不带值 |
| `-validate` | 是否交叉验证 | `False` | 不带值 |
| `-vectorized` | 是否使用向量化引擎 | `False` | 不带值 |

### 使用示例

#### 示例1：贵州茅台双均线策略回测

```bash
python main.py -s 600519 -strategy dual_ma -start 20230101 -end 20241231
```

输出：
```
【双均线策略回测结果】
==================================================
初始资金: 100,000.00 元
最终资金: 67,693.33 元
累计收益率: -32.31%
年化收益率: -17.77%
最大回撤: 33.57%
Sharpe比率: -1.42
胜率: 36.50%
交易天数: 484 天
==================================================
```

#### 示例2：布林带策略参数优化

```bash
python main.py -s 600519 -strategy bollinger -optimize
```

#### 示例3：交叉验证评估

```bash
python main.py -s 600519 -strategy dual_ma -validate
```

#### 示例4：使用向量化引擎

```bash
python main.py -s 600519 -strategy bollinger -vectorized
```

### Web界面使用

1. **启动服务**：`python app.py`
2. **访问界面**：浏览器打开 `http://127.0.0.1:8050/`
3. **搜索股票**：输入代码（如 `600519`）或名称（如 `茅台`）
4. **选择策略**：双均线或布林带
5. **设置参数**：设置日期范围和策略参数
6. **开始回测**：点击按钮，查看结果图表和交易记录

---

## 📊 策略说明

### 1. 双均线策略（Dual MA Strategy）

**原理**：利用短期和长期移动平均线的交叉判断趋势

**信号逻辑**：
```
买入信号：MA_short 上穿 MA_long（金叉）
卖出信号：MA_short 下穿 MA_long（死叉）
```

**参数**：
- `short_window`：短期均线周期（默认：5）
- `long_window`：长期均线周期（默认：20）

**适用场景**：趋势明显的市场

**优点**：
- 简单直观，易于理解和实现
- 能够捕捉中长期趋势

**缺点**：
- 滞后性强，在震荡市容易亏损
- 频繁交易增加成本

---

### 2. 布林带策略（Bollinger Bands Strategy）

**原理**：基于统计学中的标准差概念，价格围绕均线波动

**组成**：
```
中轨 (Middle Band) = N日移动平均线
上轨 (Upper Band) = 中轨 + K × N日标准差
下轨 (Lower Band) = 中轨 - K × N日标准差
```

**信号模式**：

#### 突破模式（Breakout）
```
买入信号：价格从下方突破下轨
卖出信号：价格从上方突破上轨
```

#### 反转模式（Mean Reversion）
```
买入信号：价格触及或跌破下轨（超卖）
卖出信号：价格触及或突破上轨（超买）
```

**参数**：
- `window`：窗口周期（默认：20）
- `std_dev`：标准差倍数（默认：2.0）

**适用场景**：波动性较大的市场

**优点**：
- 能够捕捉价格异常波动
- 提供明确的支撑阻力位

**缺点**：
- 在强趋势中可能持续亏损
- 参数敏感度高

---

## ⚙️ 回测引擎

### 1. 循环回测引擎（Backtester）

**位置**：`src/backtester.py`

**特点**：
- 逐行遍历数据，逐笔执行交易
- 支持止损、止盈、涨跌停等复杂逻辑
- 计算精确，适合小规模数据验证

**适用场景**：
- 策略开发和调试
- 需要精确控制每笔交易
- 最终验证阶段

**性能**：⚠️ 较慢（适合单次回测）

---

### 2. 向量化回测引擎（TrueVectorizedBacktester）

**位置**：`src/true_vectorized.py`

**特点**：
- 使用 NumPy/Pandas 向量化操作
- 批量计算，忽略未成交订单
- 性能极高，比循环版本快数十倍

**适用场景**：
- 参数优化（大量迭代）
- 多策略批量测试
- 快速初筛

**性能**：⚡ 极快（适合批量测试）

---

### 3. 事件驱动回测引擎（EventDrivenBacktester）

**位置**：`src/event_driven.py`

**特点**：
- 基于事件队列处理交易
- 模拟真实交易所见即所得
- 支持复杂市场事件处理

**适用场景**：
- 实盘前最终验证
- 处理特殊市场情况
- 精细化策略验证

**性能**：⚡⚡ 较快（精确且高效）

---

### 三引擎对比

| 特性 | 循环引擎 | 向量化引擎 | 事件驱动引擎 |
|:---:|:---:|:---:|:---:|
| **精度** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **性能** | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **功能完整性** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **适用场景** | 精细验证 | 快速初筛 | 实盘验证 |
| **止损止盈** | ✅ | ✅ | ✅ |
| **涨跌停** | ✅ | ✅ | ✅ |
| **停牌处理** | ✅ | ✅ | ✅ |

---

### 统一接口

所有回测引擎继承自 `BaseBacktester`，提供统一的 `run_backtest()` 方法：

```python
result = backtester.run_backtest(
    df,
    signal_column='signal',
    stop_loss_pct=0.05,
    take_profit_pct=0.15,
    is_st_stock=False,
    stock_symbol='600519'
)

# 返回格式
{
    'data': DataFrame,      # 完整回测数据
    'trades': DataFrame,    # 交易记录
    'stats': dict,          # 性能指标
    'version': str          # 引擎版本
}
```

---

## 🎯 参数优化与验证

### 1. 参数优化器（ParameterOptimizer）

**功能**：网格搜索寻找最优参数组合

**支持策略**：
- 双均线策略：短期/长期均线周期
- 布林带策略：窗口周期、标准差倍数

**优化流程**：
```python
from src.optimizer import ParameterOptimizer

optimizer = ParameterOptimizer()

# 双均线参数优化
results = optimizer.optimize_dual_ma(
    symbol='sh600519',
    start_date='20230101',
    end_date='20241231',
    short_window_range=(5, 30),
    long_window_range=(20, 100),
    step=5
)

# 获取最优参数
best_params = optimizer.get_best_parameters(results)
```

---

### 2. 交叉验证器（CrossValidator）

**功能**：评估策略的泛化能力，防止过拟合

**核心方法**：

#### 滚动向前验证（Walk-Forward）
```python
cv_results = validator.walk_forward_validation(
    symbol='sh600519',
    start_date='20230101',
    end_date='20241231',
    strategy_type='dual_ma',
    train_period=126,  # 训练期：约半年
    test_period=63,   # 测试期：约一季度
    **best_params
)
```

#### 参数敏感性分析
```python
sensitivity_results = validator.parameter_sensitivity_test(
    symbol='sh600519',
    start_date='20230101',
    end_date='20241231',
    strategy_type='dual_ma',
    perturbation=0.2,  # 参数扰动20%
    **best_params
)
```

---

### 3. 过拟合评估

**评估维度**：

| 维度 | 指标 | 权重 |
|:---:|---|:---:|
| 衰减容忍度 | 样本外收益/样本内收益 | 30% |
| 参数鲁棒性 | 扰动后Sharpe保持率 | 25% |
| 统计学检验 | 交易次数vs参数数量 | 20% |
| 泛化能力 | 滚动回测一致性 | 25% |

**评分标准**：

| 综合得分 | 等级 | 含义 |
|:---:|:---:|---|
| ≥80 | 优秀 | 泛化能力强，过拟合风险低 |
| 60-79 | 良好 | 表现稳定，存在一定风险 |
| 40-59 | 一般 | 明显过拟合迹象 |
| <40 | 较差 | 过拟合风险极高 |

**使用示例**：
```python
report = validator.evaluate_overfitting(
    symbol='sh600519',
    start_date='20230101',
    end_date='20241231',
    strategy_type='dual_ma',
    **best_params
)

validator.print_report(report)
```

---

## 📚 API文档

### 数据获取模块（DataFetcher）

```python
from src.data_fetcher import DataFetcher

fetcher = DataFetcher()

# 获取股票数据
df = fetcher.fetch_stock_data(
    symbol='sh600519',
    start_date='20230101',
    end_date='20241231'
)

# 搜索股票
results = fetcher.search_stock('茅台')

# 获取股票信息
info = fetcher.get_stock_info('sh600519')
```

**返回数据格式**：
```
                open    high    low     close   volume
date
2023-01-03  1850.0  1865.0  1846.0  1856.0  2856423
2023-01-04  1856.0  1870.0  1851.0  1865.0  3214567
...
```

---

### 策略模块（Strategies）

```python
from src.strategies import DualMAStrategy, BollingerBandStrategy

# 双均线策略
strategy = DualMAStrategy(short_window=5, long_window=20)
df = strategy.calculate_signals(df)

# 布林带策略（突破模式）
bollinger = BollingerBandStrategy(window=20, std_dev=2.0)
df = bollinger.calculate_signals(df)

# 布林带策略（反转模式）
df = bollinger.calculate_signals_reversion(df)
```

---

### 回测引擎模块（Backtester）

```python
from src.backtester import Backtester, TrueVectorizedBacktester, EventDrivenBacktester

# 循环回测
backtester = Backtester()
result = backtester.run_backtest(df, stop_loss_pct=0.05, take_profit_pct=0.15)

# 向量化回测
vectorized = TrueVectorizedBacktester()
result = vectorized.run_backtest(df)

# 事件驱动回测
event_driven = EventDrivenBacktester()
result = event_driven.run_backtest(df, strategy=strategy)

# 获取结果
df_result = result['data']
trades = result['trades']
stats = result['stats']
```

---

### 优化器模块（Optimizer）

```python
from src.optimizer import ParameterOptimizer

optimizer = ParameterOptimizer()

# 参数优化
results = optimizer.optimize_dual_ma(
    symbol='sh600519',
    start_date='20230101',
    end_date='20241231',
    short_window_range=(5, 30),
    long_window_range=(20, 100)
)

# 获取最优参数
best_params = optimizer.get_best_parameters(results)
```

---

### 交叉验证模块（CrossValidator）

```python
from src.cross_validator import CrossValidator

validator = CrossValidator()

# 滚动向前验证
cv_results = validator.walk_forward_validation(
    symbol='sh600519',
    start_date='20230101',
    end_date='20241231',
    strategy_type='dual_ma',
    train_period=126,
    test_period=63,
    **best_params
)

# 参数敏感性分析
sensitivity = validator.parameter_sensitivity_test(
    symbol='sh600519',
    start_date='20230101',
    end_date='20241231',
    strategy_type='dual_ma',
    perturbation=0.2,
    **best_params
)

# 综合过拟合评估
report = validator.evaluate_overfitting(
    symbol='sh600519',
    start_date='20230101',
    end_date='20241231',
    strategy_type='dual_ma',
    **best_params
)

# 打印报告
validator.print_report(report)
```

---

## ⚙️ 配置说明

### 配置文件（config.py）

```python
# 回测参数
INITIAL_CAPITAL = 100000      # 初始资金（元）
TRANSACTION_FEE = 0.0003      # 交易手续费（万分之三）
SLIPPAGE = 0.0001             # 滑点（万分之一）

# 数据参数
CACHE_EXPIRY = 7              # 历史数据缓存天数
RECENT_CACHE_EXPIRY = 1        # 近期数据缓存天数

# 涨跌停限制
STOCK_LIMIT = 0.10             # 普通股票涨跌幅限制
ST_LIMIT = 0.05               # ST股票涨跌幅限制
GEM_LIMIT = 0.20              # 创业板/科创板涨跌幅限制
BSE_LIMIT = 0.30              # 北交所涨跌幅限制

# Web服务
DEBUG = False                  # 调试模式
PORT = 8050                    # Web服务端口
```

---

## ⚠️ 注意事项

### 数据相关

1. **数据来源**：使用 akshare 获取A股公开数据
2. **复权方式**：默认使用前复权数据，消除除权除息影响
3. **数据延迟**：实际使用时应注意数据实时性
4. **缓存机制**：
   - 历史数据（>1个月）：缓存7天
   - 近期数据（≤1个月）：缓存1天

### 交易相关

1. **涨跌停限制**：
   - 普通股票：±10%
   - ST股票：±5%
   - 创业板(300)、科创板(688)：±20%
   - 北交所(8开头)：±30%

2. **交易成本**：
   - 手续费：默认万分之三
   - 滑点：默认万分之一
   - 实际费用可能更高

3. **涨停买入限制**：涨停时无法买入
4. **跌停卖出限制**：跌停时无法卖出

### 策略相关

1. **过拟合风险**：回测结果可能过拟合历史数据
2. **样本外验证**：务必进行交叉验证评估泛化能力
3. **交易频率**：高频交易会显著增加成本
4. **市场适应性**：策略可能不适用于所有市场环境

### 风险提示

⚠️ **重要声明**：
- 回测结果**不代表未来收益**
- 本系统仅供**学习和研究**使用
- 实盘交易前请充分评估风险
- 作者不对使用本系统造成的任何损失负责

---

## 🛠️ 故障排除

### 常见问题

**Q1: 数据获取失败？**
```bash
# 检查网络连接
# 重试或更换时间范围
```

**Q2: 回测结果异常？**
```bash
# 检查参数设置
# 确认股票代码正确
# 查看日志文件 logs/stock_backtest.log
```

**Q3: Web界面无法访问？**
```bash
# 确认服务已启动
# 检查端口是否被占用
python app.py  # 重新启动
```

**Q4: 依赖安装失败？**
```bash
# 升级pip
python -m pip install --upgrade pip

# 单独安装失败的包
pip install akshare
```

---

## 📈 扩展指南

### 添加新策略

1. 在 `src/strategies.py` 中创建新策略类
2. 继承 `BaseStrategy` 或直接实现 `calculate_signals()` 方法
3. 在 `main.py` 和 `app.py` 中添加策略选项

**示例**：
```python
class MyStrategy:
    def __init__(self, param1=10, param2=20):
        self.param1 = param1
        self.param2 = param2
    
    def calculate_signals(self, df):
        # 实现策略逻辑
        df['signal'] = 0
        # ... 计算信号
        return df
```

### 添加新回测引擎

1. 在 `src/` 目录创建新引擎文件
2. 继承 `BaseBacktester` 类
3. 实现 `run_backtest()` 方法
4. 返回统一格式的结果

---

## 📄 许可证

本项目仅供学习和研究使用，不构成任何投资建议。

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

## 📞 联系方式

如有问题，请在 GitHub 提交 Issue。

---

## 📌 更新日志

### v1.1.0 (2026-06-11)
- ✅ 统一回测引擎接口
- ✅ 添加向量化回测引擎
- ✅ 添加事件驱动回测引擎
- ✅ 抽取公共工具函数到 utils.py
- ✅ 修正布林带策略信号逻辑
- ✅ 修复涨跌停限制逻辑
- ✅ 完善参数优化和交叉验证
- ✅ 添加过拟合评估系统

### v1.0.0 (2024)
- 🎉 初始版本发布
- ✅ 基本回测功能
- ✅ 双均线和布林带策略
- ✅ 参数优化和交叉验证
- ✅ Web界面

---

**© 2024-2026 Stock Backtest System. All rights reserved.**
