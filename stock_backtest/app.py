# Web可视化模块 - 东方财富风格
import dash
from dash import dcc, html, Input, Output, State, ALL
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

from config import Config
from src.data_fetcher import DataFetcher
from src.strategies import DualMAStrategy, BollingerBandStrategy
from src.backtester import BacktesterFactory

# ============================================================================
# 通用样式常量
# ============================================================================

# Dropdown 下拉框样式
DROPDOWN_STYLE = {
    'backgroundColor': '#1a1a2e',
    'color': '#e0e0e0',
    'borderColor': '#2d2d44',
    'borderRadius': '5px',
    'height': '42px'
}

# Plotly 图表通用布局
CHART_LAYOUT = {
    'template': 'plotly_dark',
    'paper_bgcolor': '#16213e',
    'plot_bgcolor': '#16213e',
    'font': {'color': '#e0e0e0'},
    'showlegend': True,
    'legend': {'orientation': 'h', 'yanchor': 'bottom', 'y': 1.02, 'xanchor': 'right', 'x': 1},
    'xaxis': {'gridcolor': '#2d2d44'},
    'yaxis': {'gridcolor': '#2d2d44'},
}


# ============================================================================
# 通用组件函数
# ============================================================================

def create_dropdown(label, dropdown_id, options, value, placeholder=""):
    """
    创建统一下拉框组件
    
    :param label: 标签文本
    :param dropdown_id: 组件ID
    :param options: 选项列表
    :param value: 默认值
    :param placeholder: 占位符
    :return: Div 组件
    """
    return html.Div([
        html.Label(label, className="label"),
        dcc.Dropdown(
            id=dropdown_id,
            options=options,
            value=value,
            clearable=False,
            className="stock-dropdown",
            style=DROPDOWN_STYLE
        ),
    ], className="search-item")


def create_date_input(label, input_id, value, placeholder):
    """
    创建统一定期输入框组件
    
    :param label: 标签文本
    :param input_id: 组件ID
    :param value: 默认值
    :param placeholder: 占位符
    :return: Div 组件
    """
    return html.Div([
        html.Label(label, className="label"),
        dcc.Input(
            id=input_id,
            type='text',
            value=value,
            placeholder=placeholder,
            className="date-input"
        ),
    ], className="search-item")


def create_metric_card(label, value, value_class=None, card_class=""):
    """
    创建统一指标卡片组件
    
    :param label: 指标标签
    :param value: 指标值
    :param value_class: 值样式类（可选）
    :param card_class: 卡片样式类（可选）
    :return: Div 组件
    """
    return html.Div([
        html.Div(label, className="metric-label"),
        html.Div(value, className=f"metric-value {value_class or ''}"),
    ], className=f"metric-card {card_class}")


def create_chart_container(title, graph):
    """
    创建统一图表容器组件
    
    :param title: 图表标题
    :param graph: Graph 组件
    :return: Div 组件
    """
    return html.Div([
        html.Div(title, className="chart-title"),
        graph,
    ], className="chart-container")


def create_error_message(message):
    """
    创建统一错误消息组件
    
    :param message: 错误消息文本
    :return: Div 组件
    """
    return html.Div([
        html.Div(message, style={
            'color': '#ff4757',
            'textAlign': 'center',
            'padding': '50px',
            'fontSize': '18px'
        })
    ])


# ============================================================================
# 日期格式化函数
# ============================================================================

def normalize_date(date_str):
    """
    标准化日期格式，支持多种输入格式
    
    支持格式：
    - YYYYMMDD (20230101)
    - YYYY-MM-DD (2023-01-01)
    - YYYY/MM/DD (2023/01/01)
    - YYYY.MM.DD (2023.01.01)
    
    :param date_str: 日期字符串
    :return: YYYYMMDD 格式的字符串
    """
    if not date_str:
        return None
    
    # 移除所有分隔符
    date_str = str(date_str).strip()
    
    # 移除常见的分隔符
    for sep in ['-', '/', '.']:
        date_str = date_str.replace(sep, '')
    
    # 验证是否为8位数字
    if len(date_str) == 8 and date_str.isdigit():
        return date_str
    
    return None


# ============================================================================
# Dash 应用初始化
# ============================================================================

app = dash.Dash(__name__, title="股票策略回测系统")
server = app.server


# ============================================================================
# 布局定义
# ============================================================================

app.layout = html.Div([
    # 隐藏输出组件
    dcc.Store(id='backtest-results'),
    dcc.Store(id='backtest-state', data={'status': 'idle', 'params': None, 'last_clicks': 0}),
    dcc.Store(id='search-state', data={'status': 'idle', 'keyword': ''}),
    
    # 主容器
    html.Div([
        # 标题栏
        html.Div([
            html.Div([
                html.H1("股票策略回测系统", className="main-title"),
                html.Span("专业量化分析平台", className="subtitle"),
            ], className="header-left"),
            html.Div([
                html.Span("实时行情数据", className="tag"),
                html.Span("智能策略回测", className="tag"),
            ], className="header-right"),
        ], className="header"),
        
        # 搜索栏
        html.Div([
            # 股票搜索
            html.Div([
                html.Label("股票搜索", className="label"),
                dcc.Input(
                    id='stock-search-input',
                    type='text',
                    placeholder='输入股票代码或名称，如：贵州茅台',
                    className="stock-search-input",
                    debounce=True  # 防抖
                ),
                # 搜索结果列表
                html.Div(id='stock-search-results', className="stock-search-results"),
            ], className="search-item stock-search-container"),
            
            # 当前选中的股票显示
            html.Div([
                html.Label("当前股票", className="label"),
                html.Div(id='selected-stock-display', className="selected-stock-display", children=[
                    html.Span("贵州茅台 600519", className="stock-name"),
                    html.Span("(双击可重新选择)", className="hint")
                ]),
            ], className="search-item"),
            
            # 隐藏的股票代码存储
            dcc.Store(id='selected-stock-code', data="sh600519"),
            
            # 开始日期
            create_date_input(
                "开始日期",
                "start-date",
                Config.DEFAULT_START_DATE,
                "20230101"
            ),
            
            # 结束日期
            create_date_input(
                "结束日期",
                "end-date",
                Config.DEFAULT_END_DATE,
                "20241231"
            ),
            
            # 策略选择
            create_dropdown(
                "交易策略",
                "strategy-select",
                [
                    {'label': '双均线策略', 'value': 'dual_ma'},
                    {'label': '布林带策略', 'value': 'bollinger'}
                ],
                'dual_ma'
            ),
            
            html.Button('▶ 开始回测', id='run-backtest', n_clicks=0, className="search-btn"),
        ], className="search-bar"),
        
        # 加载提示
        html.Div(id='loading', children=[
            html.Div([
                html.Span(className="loading-spinner"),
                html.Span("正在加载数据...", className="loading-text"),
            ], className="loading-box")
        ], className="loading-container", style={'display': 'none'}),
        
        # 结果区域
        html.Div(id='results', children=[], style={'display': 'none'}),
        
    ], className="main-container"),
    
], style={'backgroundColor': '#1a1a2e', 'minHeight': '100vh'})


# ============================================================================
# 回调函数
# ============================================================================

# 回调函数0：处理搜索输入，更新搜索状态
@app.callback(
    Output('search-state', 'data'),
    [Input('stock-search-input', 'value')],
    [State('search-state', 'data')],
    prevent_initial_call=False
)
def handle_search_input(keyword, state):
    """
    处理搜索输入，更新搜索状态
    
    :param keyword: 搜索关键词
    :param state: 当前搜索状态
    :return: 更新后的搜索状态
    """
    if not keyword or len(keyword) < 1:
        return {'status': 'idle', 'keyword': ''}
    
    return {'status': 'loading', 'keyword': keyword}


# 回调函数1：执行股票搜索
@app.callback(
    [Output('stock-search-results', 'children'),
     Output('selected-stock-code', 'data'),
     Output('selected-stock-display', 'children'),
     Output('search-state', 'data', allow_duplicate=True)],
    [Input('search-state', 'data')],
    [State('selected-stock-code', 'data'),
     State('selected-stock-display', 'children')],
    prevent_initial_call=True
)
def search_stocks(state, current_code, current_display):
    """
    搜索股票并在搜索框下方显示结果列表
    
    :param state: 搜索状态
    :param current_code: 当前选中的股票代码
    :param current_display: 当前显示的内容
    :return: 搜索结果、股票代码、显示内容、更新后的状态
    """
    if state.get('status') != 'loading':
        return [html.Div(), current_code, current_display, state]
    
    keyword = state.get('keyword', '')
    
    try:
        # 调用搜索函数
        fetcher = DataFetcher()
        results = fetcher.search_stocks(keyword, limit=10)
        
        # 去重
        seen_codes = set()
        unique_results = []
        for stock in results:
            code = stock['value']
            if code not in seen_codes:
                seen_codes.add(code)
                unique_results.append(stock)
        
        if not unique_results:
            return [html.Div("未找到匹配的股票", className="search-no-results"), 
                    current_code, current_display, {'status': 'completed', 'keyword': keyword}]
        
        # 如果只有一个结果，自动选中
        if len(unique_results) == 1:
            stock = unique_results[0]
            display_children = [
                html.Span(stock['label'], className="stock-name"),
                html.Span("(双击可重新选择)", className="hint")
            ]
            # 将股票名称和代码一起保存，用于ST识别
            stock_data = {
                'code': stock['value'],
                'name': stock['label']
            }
            return ["", stock_data, display_children, {'status': 'completed', 'keyword': keyword}]
        
        # 显示结果列表（用户需要输入更精确的关键词来得到唯一结果）
        result_items = []
        for stock in unique_results[:5]:
            result_items.append(
                html.Div(
                    stock['label'],
                    className="search-result-item",
                    style={'padding': '8px 12px', 'borderBottom': '1px solid #2d2d44'}
                )
            )
        
        hint_text = f"找到 {len(unique_results)} 只股票，请输入更精确的关键词"
        result_items.append(html.Div(hint_text, className="search-hint", style={'padding': '8px 12px', 'color': '#666'}))
        
        return [html.Div(result_items, className="search-result-list"), 
                current_code, current_display, {'status': 'completed', 'keyword': keyword}]
    except Exception as e:
        print(f"搜索失败: {str(e)}")
        return [html.Div("搜索失败，请重试", className="search-error"), 
                current_code, current_display, {'status': 'error', 'keyword': keyword}]


# 回调函数2：显示搜索加载状态
@app.callback(
    Output('stock-search-results', 'children', allow_duplicate=True),
    [Input('search-state', 'data')],
    prevent_initial_call=True
)
def show_search_loading(state):
    """
    根据搜索状态显示加载提示
    
    :param state: 搜索状态
    :return: 加载提示或空
    """
    if state.get('status') == 'loading':
        return html.Div([
            html.Span(className="loading-spinner-small"),
            html.Span("正在搜索股票...", className="loading-text-small")
        ], className="search-loading")
    return dash.no_update


# 回调函数3：处理点击，显示加载状态
@app.callback(
    [Output('loading', 'style'),
     Output('backtest-state', 'data')],
    [Input('run-backtest', 'n_clicks')],
    [State('selected-stock-code', 'data'),
     State('start-date', 'value'),
     State('end-date', 'value'),
     State('strategy-select', 'value'),
     State('backtest-state', 'data')]
)
def handle_click(n_clicks, symbol, start_date, end_date, strategy_type, state):
    if n_clicks == 0 or n_clicks == state.get('last_clicks', 0):
        return {'display': 'none'}, state
    
    return {'display': 'block', 'textAlign': 'center', 'padding': '50px'}, {
        'status': 'loading',
        'last_clicks': n_clicks,
        'params': {
            'symbol': symbol,
            'start_date': start_date,
            'end_date': end_date,
            'strategy_type': strategy_type
        }
    }


# 回调函数4：执行实际回测
@app.callback(
    [Output('loading', 'style', allow_duplicate=True),
     Output('results', 'children'),
     Output('results', 'style'),
     Output('backtest-state', 'data', allow_duplicate=True)],
    [Input('backtest-state', 'data')],
    prevent_initial_call=True
)
def run_backtest(state):
    if state.get('status') != 'loading':
        return {'display': 'none'}, [], {'display': 'none'}, state
    
    params = state.get('params', {})
    symbol = params.get('symbol')
    start_date = params.get('start_date')
    end_date = params.get('end_date')
    strategy_type = params.get('strategy_type')
    
    try:
        # 标准化日期格式
        start_date = normalize_date(start_date)
        end_date = normalize_date(end_date)
        
        # 验证日期格式
        if not start_date or not end_date:
            return {'display': 'none'}, \
                   create_error_message("日期格式错误，请使用 YYYYMMDD 格式（如：20230101）"), \
                   {'display': 'block'}, state
        
        # 处理股票代码数据格式（可能是字符串或字典）
        stock_name = None
        if isinstance(symbol, dict):
            stock_code = symbol.get('code', symbol)
            stock_name = symbol.get('name', '')
        else:
            stock_code = symbol
        
        # 获取数据
        fetcher = DataFetcher()
        df = fetcher.fetch_stock_data(stock_code, start_date, end_date)
        
        if df is None or df.empty:
            return {'display': 'none'}, \
                   create_error_message("数据获取失败，请检查股票代码和日期"), \
                   {'display': 'block'}, state
        
        # 检查是否为ST股票（传入已获取的数据和股票名称，避免重复API调用）
        is_st = fetcher.is_st_stock(stock_code, df, stock_name)
        
        # 判断股票类型和涨跌幅限制
        if is_st:
            stock_type = "ST股票 (±5%)"
        elif stock_code.startswith('300'):
            stock_type = "创业板 (±20%)"
        elif stock_code.startswith('688'):
            stock_type = "科创板 (±20%)"
        else:
            stock_type = "普通股票 (±10%)"
        data_type = "前复权"
        
        # 选择策略
        strategy = DualMAStrategy() if strategy_type == 'dual_ma' else BollingerBandStrategy()
        strategy_name = "双均线策略" if strategy_type == 'dual_ma' else "布林带策略"
        
        # 计算信号
        df = strategy.calculate_signals(df)
        
        # 执行回测（传入是否为ST股票和股票代码）
        backtester = BacktesterFactory.create_by_strategy(strategy_type)
        df_result, trades = backtester.run_backtest(df, is_st_stock=is_st, stock_symbol=stock_code)
        
        # 计算指标
        metrics = backtester.calculate_metrics(df_result)
        
        # 创建指标卡片
        is_profit = metrics['累计收益率'] >= 0
        metrics_cards = html.Div([
            create_metric_card("初始资金", f"¥{metrics['初始资金']:,.2f}"),
            create_metric_card("最终资金", f"¥{metrics['最终资金']:,.2f}"),
            create_metric_card(
                "累计收益率",
                f"{metrics['累计收益率']:.2%}",
                'red' if is_profit else 'green',
                'positive' if is_profit else 'negative'
            ),
            create_metric_card(
                "年化收益率",
                f"{metrics['年化收益率']:.2%}",
                'red' if metrics['年化收益率'] >= 0 else 'green'
            ),
            create_metric_card("最大回撤", f"{metrics['最大回撤']:.2%}", "green"),
            create_metric_card("Sharpe比率", f"{metrics['Sharpe比率']:.2f}"),
            create_metric_card("交易天数", f"{metrics['交易天数']}"),
            create_metric_card(
                "策略收益",
                f"¥{metrics['策略收益']:,.2f}",
                'red' if metrics['策略收益'] >= 0 else 'green',
                'positive' if metrics['策略收益'] >= 0 else 'negative'
            ),
            create_metric_card("股票类型", stock_type, "blue"),
            create_metric_card("数据类型", data_type, "blue"),
        ], className="metrics-container")
        
        # 创建价格图表
        fig_price = create_price_chart(df_result, strategy_type)
        
        # 创建资产曲线图
        fig_portfolio = create_portfolio_chart(df_result)
        
        # 创建交易记录表格
        trade_table = create_trade_table(trades)
        
        # 组装结果
        results = html.Div([
            html.Div(strategy_name + " - 回测结果", className="result-title"),
            metrics_cards,
            create_chart_container("价格走势与信号", dcc.Graph(figure=fig_price)),
            create_chart_container("资产净值变化", dcc.Graph(figure=fig_portfolio)),
            create_chart_container("交易记录", trade_table),
        ])
        
        return {'display': 'none'}, results, {'display': 'block'}, {**state, 'status': 'completed'}
    
    except Exception as e:
        return {'display': 'none'}, \
               [html.P(f"回测失败: {str(e)}", style={'color': '#ff4757', 'textAlign': 'center', 'padding': '50px'})], \
               {'display': 'block'}, {**state, 'status': 'error'}


# ============================================================================
# 图表创建函数
# ============================================================================

def create_price_chart(df_result, strategy_type):
    """
    创建价格走势图
    
    :param df_result: 回测结果数据
    :param strategy_type: 策略类型
    :return: Plotly Figure 对象
    """
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        row_heights=[0.7, 0.3],
        subplot_titles=('价格走势 & 策略信号', '持仓状态')
    )
    
    # 收盘价
    fig.add_trace(
        go.Scatter(x=df_result.index, y=df_result['close'], 
                  name='收盘价', line=dict(color='#fff', width=1)),
        row=1, col=1
    )
    
    # 根据策略类型添加指标线
    if strategy_type == 'dual_ma':
        fig.add_trace(
            go.Scatter(x=df_result.index, y=df_result['short_ma'], 
                      name='短期均线', line=dict(color='red', width=1)),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df_result.index, y=df_result['long_ma'], 
                      name='长期均线', line=dict(color='blue', width=1)),
            row=1, col=1
        )
    else:
        fig.add_trace(
            go.Scatter(x=df_result.index, y=df_result['upper_band'], 
                      name='上轨', line=dict(color='red', width=1, dash='dash')),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df_result.index, y=df_result['middle_band'], 
                      name='中轨', line=dict(color='yellow', width=1)),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df_result.index, y=df_result['lower_band'], 
                      name='下轨', line=dict(color='green', width=1, dash='dash')),
            row=1, col=1
        )
    
    # 买入信号（只显示实际执行的交易）
    buy_signals = df_result[df_result['trade_executed'] == 1]
    if len(buy_signals) > 0:
        fig.add_trace(
            go.Scatter(x=buy_signals.index, y=buy_signals['close'],
                      name='买入', mode='markers',
                      marker=dict(color='#2ed573', size=10, symbol='triangle-up')),
            row=1, col=1
        )
    
    # 卖出信号（只显示实际执行的交易）
    sell_signals = df_result[df_result['trade_executed'] == -1]
    if len(sell_signals) > 0:
        fig.add_trace(
            go.Scatter(x=sell_signals.index, y=sell_signals['close'],
                      name='卖出', mode='markers',
                      marker=dict(color='#ff4757', size=10, symbol='triangle-down')),
            row=1, col=1
        )
    
    # 持仓状态
    fig.add_trace(
        go.Scatter(x=df_result.index, y=df_result['position'],
                  name='持仓', fill='tozeroy',
                  line=dict(color='#00d4ff', width=1),
                  fillcolor='rgba(0, 212, 255, 0.2)'),
        row=2, col=1
    )
    
    # 应用通用布局
    fig.update_layout(height=600, **CHART_LAYOUT)
    
    return fig


def create_portfolio_chart(df_result):
    """
    创建资产净值曲线图
    
    :param df_result: 回测结果数据
    :return: Plotly Figure 对象
    """
    fig = go.Figure()
    
    # 资产曲线
    fig.add_trace(
        go.Scatter(x=df_result.index, y=df_result['portfolio'],
                  name='策略资产',
                  line=dict(color='#00d4ff', width=2),
                  fill='tozeroy',
                  fillcolor='rgba(0, 212, 255, 0.1)')
    )
    
    # 初始资金线
    fig.add_trace(
        go.Scatter(x=df_result.index, y=[Config.INITIAL_CAPITAL] * len(df_result),
                  name='初始资金',
                  line=dict(color='#666', width=1, dash='dash'))
    )
    
    # 应用通用布局
    fig.update_layout(height=300, **CHART_LAYOUT)
    
    return fig


def create_trade_table(trades):
    """
    创建交易记录表格
    
    :param trades: 交易记录 DataFrame
    :return: Table 或 Div 组件
    """
    if len(trades) == 0:
        return html.Div("本次回测期间没有产生交易", style={
        'textAlign': 'center', 'color': '#888', 'padding': '30px'
    })
    
    # 格式化数据
    trades['date'] = pd.to_datetime(trades['date']).dt.strftime('%Y-%m-%d')
    trades['type_cn'] = trades['type'].apply(lambda x: '买入' if x == 'buy' else '卖出')
    trades['type_class'] = trades['type'].apply(lambda x: 'buy' if x == 'buy' else 'sell')
    
    # 生成表格行
    trade_rows = [
        html.Tr([
            html.Td(trade['date']),
            html.Td(trade['type_cn'], className=f"trade-type {trade['type_class']}"),
            html.Td(f"¥{trade['price']:.2f}"),
            html.Td(f"{trade['shares']:.0f}股"),
            html.Td(f"¥{trade['cash']:,.2f}"),
        ])
        for _, trade in trades.iterrows()
    ]
    
    return html.Table([
        html.Thead(html.Tr([
            html.Th('日期'), html.Th('类型'), html.Th('价格'), html.Th('数量'), html.Th('剩余资金')
        ])),
        html.Tbody(trade_rows)
    ], className="trade-table")


# ============================================================================
# 应用入口
# ============================================================================

if __name__ == '__main__':
    app.run(debug=Config.DEBUG, port=Config.PORT)
