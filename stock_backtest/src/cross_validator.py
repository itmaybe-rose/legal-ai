# 交叉验证模块 - 防止过拟合
import pandas as pd
import numpy as np
from .data_fetcher import DataFetcher
from .strategies import DualMAStrategy, BollingerBandStrategy
from .backtester import Backtester
from .logger import backtest_logger

class CrossValidator:
    """交叉验证器 - 用于评估策略的泛化能力"""
    
    def __init__(self):
        self.fetcher = DataFetcher()
    
    def walk_forward_validation(self, symbol, start_date, end_date, 
                                strategy_type='dual_ma',
                                train_period=126,  # 约半年交易日
                                test_period=63,    # 约一季度交易日
                                **strategy_params):
        """
        滚动向前验证 (Walk-Forward Validation)
        
        :param symbol: 股票代码
        :param start_date: 开始日期
        :param end_date: 结束日期
        :param strategy_type: 策略类型
        :param train_period: 训练周期（交易日数量）
        :param test_period: 测试周期（交易日数量）
        :param strategy_params: 策略参数
        :return: 验证结果列表
        """
        # 获取数据
        df = self.fetcher.fetch_stock_data(symbol, start_date, end_date)
        if df is None or df.empty:
            return None
        
        results = []
        total_periods = 0
        
        # 滚动窗口验证
        for i in range(train_period, len(df) - test_period + 1, test_period):
            total_periods += 1
            
            # 划分训练集和测试集
            train_df = df.iloc[:i]
            test_df = df.iloc[i:i+test_period]
            
            train_start = train_df.index[0].strftime('%Y-%m-%d')
            train_end = train_df.index[-1].strftime('%Y-%m-%d')
            test_start = test_df.index[0].strftime('%Y-%m-%d')
            test_end = test_df.index[-1].strftime('%Y-%m-%d')
            
            backtest_logger.info(f"周期 {total_periods}: 训练 [{train_start} ~ {train_end}], 测试 [{test_start} ~ {test_end}]")
            
            try:
                # 创建策略
                if strategy_type == 'dual_ma':
                    strategy = DualMAStrategy(
                        short_window=strategy_params.get('short_window', 5),
                        long_window=strategy_params.get('long_window', 20)
                    )
                else:
                    strategy = BollingerBandStrategy(
                        window=strategy_params.get('window', 20),
                        std_dev=strategy_params.get('std_dev', 2.0)
                    )
                
                backtester = Backtester()
                
                # 在测试集上计算信号
                test_with_signals = strategy.calculate_signals(test_df)
                
                # 执行回测（带止损止盈）
                result = backtester.run_backtest(test_with_signals, stop_loss_pct=0.05, take_profit_pct=0.15, stock_symbol=symbol)
                
                # 提取结果（使用统一格式）
                df_result = result['data']
                trades = result['trades']
                metrics = result['stats']
                
                results.append({
                    'period': total_periods,
                    'train_start': train_start,
                    'train_end': train_end,
                    'test_start': test_start,
                    'test_end': test_end,
                    '累计收益率': metrics['累计收益率'],
                    '年化收益率': metrics['年化收益率'],
                    '最大回撤': metrics['最大回撤'],
                    'Sharpe比率': metrics['Sharpe比率'],
                    '交易次数': len(trades),
                    '测试天数': len(test_df)
                })
                
            except Exception as e:
                backtest_logger.error(f"周期 {total_periods} 验证失败: {str(e)}")
        
        # 转换为DataFrame
        results_df = pd.DataFrame(results)
        
        return results_df
    
    def parameter_sensitivity_test(self, symbol, start_date, end_date,
                                   strategy_type='dual_ma', perturbation=0.2,
                                   **base_params):
        """
        参数敏感性分析（鲁棒性检验）
        
        :param symbol: 股票代码
        :param start_date: 开始日期
        :param end_date: 结束日期
        :param strategy_type: 策略类型
        :param perturbation: 参数扰动幅度（默认20%）
        :param base_params: 基准参数
        :return: 敏感性测试结果DataFrame
        """
        results = []
        
        if strategy_type == 'dual_ma':
            params_list = [
                {'short_window': int(base_params['short_window'] * (1 - perturbation)),
                 'long_window': base_params['long_window']},
                {'short_window': int(base_params['short_window'] * (1 + perturbation)),
                 'long_window': base_params['long_window']},
                {'short_window': base_params['short_window'],
                 'long_window': int(base_params['long_window'] * (1 - perturbation))},
                {'short_window': base_params['short_window'],
                 'long_window': int(base_params['long_window'] * (1 + perturbation))},
                {'short_window': int(base_params['short_window'] * (1 - perturbation)),
                 'long_window': int(base_params['long_window'] * (1 - perturbation))},
                {'short_window': int(base_params['short_window'] * (1 + perturbation)),
                 'long_window': int(base_params['long_window'] * (1 + perturbation))}
            ]
            param_names = ['short_window', 'long_window']
        else:
            params_list = [
                {'window': int(base_params['window'] * (1 - perturbation)),
                 'std_dev': base_params['std_dev']},
                {'window': int(base_params['window'] * (1 + perturbation)),
                 'std_dev': base_params['std_dev']},
                {'window': base_params['window'],
                 'std_dev': round(base_params['std_dev'] * (1 - perturbation), 2)},
                {'window': base_params['window'],
                 'std_dev': round(base_params['std_dev'] * (1 + perturbation), 2)},
                {'window': int(base_params['window'] * (1 - perturbation)),
                 'std_dev': round(base_params['std_dev'] * (1 - perturbation), 2)},
                {'window': int(base_params['window'] * (1 + perturbation)),
                 'std_dev': round(base_params['std_dev'] * (1 + perturbation), 2)}
            ]
            param_names = ['window', 'std_dev']
        
        df = self.fetcher.fetch_stock_data(symbol, start_date, end_date)
        if df is None or df.empty:
            return None
        
        backtest_logger.info(f"\n--- 参数敏感性测试（扰动幅度: {perturbation*100}%）---")
        
        for i, params in enumerate(params_list):
            backtest_logger.info(f"测试参数组合 {i+1}/6: {params}")
            
            try:
                if strategy_type == 'dual_ma':
                    strategy = DualMAStrategy(**params)
                else:
                    strategy = BollingerBandStrategy(**params)
                
                backtester = Backtester()
                df_signals = strategy.calculate_signals(df)
                result = backtester.run_backtest(df_signals, stock_symbol=symbol)
                
                # 提取结果（使用统一格式）
                df_result = result['data']
                trades = result['trades']
                metrics = result['stats']
                
                results.append({
                    'params': str(params),
                    '累计收益率': metrics['累计收益率'],
                    '年化收益率': metrics['年化收益率'],
                    '最大回撤': metrics['最大回撤'],
                    'Sharpe比率': metrics['Sharpe比率'],
                    '交易次数': len(trades)
                })
            except Exception as e:
                backtest_logger.error(f"参数组合 {params} 测试失败: {str(e)}")
        
        return pd.DataFrame(results)
    
    def evaluate_overfitting(self, symbol, start_date, end_date, 
                            strategy_type='dual_ma', **strategy_params):
        """
        综合评估策略是否过拟合（基于量化金融最佳实践）
        
        :param symbol: 股票代码
        :param start_date: 开始日期
        :param end_date: 结束日期
        :param strategy_type: 策略类型
        :param strategy_params: 策略参数
        :return: 评估报告字典
        """
        # 获取完整数据回测结果
        df = self.fetcher.fetch_stock_data(symbol, start_date, end_date)
        if df is None or df.empty:
            return None
        
        # 创建策略
        if strategy_type == 'dual_ma':
            strategy = DualMAStrategy(
                short_window=strategy_params.get('short_window', 5),
                long_window=strategy_params.get('long_window', 20)
            )
        else:
            strategy = BollingerBandStrategy(
                window=strategy_params.get('window', 20),
                std_dev=strategy_params.get('std_dev', 2.0)
            )
        
        backtester = Backtester()
        
        # 完整数据集回测（样本内）
        df_signals = strategy.calculate_signals(df)
        result = backtester.run_backtest(df_signals, stock_symbol=symbol)
        
        # 提取结果（使用统一格式）
        df_result = result['data']
        full_trades = result['trades']
        full_metrics = result['stats']
        
        # 滚动向前验证（样本外）
        cv_results = self.walk_forward_validation(
            symbol, start_date, end_date,
            strategy_type,
            **strategy_params
        )
        
        if cv_results is None or cv_results.empty:
            return None
        
        # 参数敏感性测试
        sensitivity_results = self.parameter_sensitivity_test(
            symbol, start_date, end_date,
            strategy_type,
            **strategy_params
        )
        
        # 计算各维度评分
        scores = self._calculate_comprehensive_scores(
            full_metrics, cv_results, sensitivity_results, 
            len(full_trades), len(strategy_params)
        )
        
        # 生成评估报告
        report = {
            '策略类型': '双均线策略' if strategy_type == 'dual_ma' else '布林带策略',
            '股票代码': symbol,
            '回测周期': f"{start_date} ~ {end_date}",
            '参数': strategy_params,
            
            # 完整数据集表现（样本内）
            '样本内年化收益率': full_metrics['年化收益率'],
            '样本内最大回撤': full_metrics['最大回撤'],
            '样本内Sharpe比率': full_metrics['Sharpe比率'],
            '样本内交易次数': len(full_trades),
            
            # 交叉验证表现（样本外）
            '样本外周期数': len(cv_results),
            '样本外年化收益率均值': cv_results['年化收益率'].mean(),
            '样本外最大回撤均值': cv_results['最大回撤'].mean(),
            '样本外Sharpe比率均值': cv_results['Sharpe比率'].mean(),
            '样本外正收益周期比例': (cv_results['累计收益率'] > 0).mean(),
            '样本外收益率标准差': cv_results['累计收益率'].std(),
            
            # 各维度评分
            '衰减容忍度得分': scores['decay_tolerance_score'],
            '参数鲁棒性得分': scores['robustness_score'],
            '统计学检验得分': scores['statistical_score'],
            '泛化能力得分': scores['generalization_score'],
            
            # 综合评估
            '过拟合分数': scores['overall_score'],
            '评估等级': scores['level'],
            '评估建议': scores['suggestion'],
            
            # 详细评估维度
            '评估详情': scores['details']
        }
        
        return report
    
    def _calculate_comprehensive_scores(self, full_metrics, cv_results, 
                                       sensitivity_results, num_trades, num_params):
        """
        计算综合过拟合评分（基于6个核心维度）
        
        :param full_metrics: 完整数据集指标
        :param cv_results: 交叉验证结果
        :param sensitivity_results: 参数敏感性测试结果
        :param num_trades: 交易次数
        :param num_params: 参数数量
        :return: 评分字典
        """
        scores = {}
        details = []
        
        # 1. 衰减容忍度检验（样本内vs样本外）
        # 合理阈值：样本外收益不应低于样本内的60%
        in_sample_return = full_metrics['年化收益率']
        out_sample_return = cv_results['年化收益率'].mean()
        
        if in_sample_return > 0:
            decay_ratio = out_sample_return / in_sample_return
            if decay_ratio >= 0.6:
                decay_score = 100
                details.append("✓ 样本外衰减在可容忍范围内（>60%）")
            elif decay_ratio >= 0.4:
                decay_score = 60
                details.append("⚠ 样本外衰减较明显（40%-60%）")
            else:
                decay_score = 20
                details.append("✗ 样本外衰减严重（<40%），过拟合风险高")
        else:
            decay_score = 50
            details.append("? 样本内收益为负，衰减检验参考价值有限")
        
        scores['decay_tolerance_score'] = decay_score
        
        # 2. 参数鲁棒性检验
        if sensitivity_results is not None and not sensitivity_results.empty:
            base_sharpe = full_metrics['Sharpe比率']
            sensitivity_sharpe = sensitivity_results['Sharpe比率']
            
            # 计算Sharpe比率保持率
            if base_sharpe > 0:
                retention_rate = (sensitivity_sharpe / base_sharpe).mean()
                if retention_rate >= 0.7:
                    robustness_score = 100
                    details.append("✓ 参数敏感性低，策略稳健")
                elif retention_rate >= 0.5:
                    robustness_score = 60
                    details.append("⚠ 参数敏感性中等，建议进一步优化")
                else:
                    robustness_score = 20
                    details.append("✗ 参数敏感性高，策略脆弱")
            else:
                robustness_score = 50
                details.append("? 基准Sharpe比率为负，鲁棒性检验参考价值有限")
        else:
            robustness_score = 50
            details.append("? 未进行参数敏感性测试")
        
        scores['robustness_score'] = robustness_score
        
        # 3. 统计学检验（自由度vs样本量）
        # 经验法则：每个自由参数至少需要10-20个观察值
        min_observations = num_params * 15  # 取中间值15
        if num_trades >= min_observations:
            statistical_score = 100
            details.append(f"✓ 交易次数充足（{num_trades}次 > {min_observations}次）")
        elif num_trades >= min_observations * 0.5:
            statistical_score = 60
            details.append(f"⚠ 交易次数偏少（{num_trades}次），统计显著性有限")
        else:
            statistical_score = 20
            details.append(f"✗ 交易次数不足（{num_trades}次 < {min_observations}次），统计显著性低")
        
        scores['statistical_score'] = statistical_score
        
        # 4. 泛化能力检验（滚动回测一致性）
        positive_ratio = (cv_results['累计收益率'] > 0).mean()
        return_std = cv_results['累计收益率'].std()
        
        # 正收益周期比例
        if positive_ratio >= 0.6:
            gen_score1 = 100
        elif positive_ratio >= 0.4:
            gen_score1 = 60
        else:
            gen_score1 = 20
        
        # 收益率稳定性（波动率越低越稳定）
        if return_std < 0.05:
            gen_score2 = 100
        elif return_std < 0.10:
            gen_score2 = 70
        else:
            gen_score2 = 30
        
        generalization_score = (gen_score1 + gen_score2) // 2
        
        if generalization_score >= 80:
            details.append("✓ 滚动回测表现一致，泛化能力强")
        elif generalization_score >= 50:
            details.append("⚠ 滚动回测表现有波动，泛化能力一般")
        else:
            details.append("✗ 滚动回测表现不稳定，泛化能力差")
        
        scores['generalization_score'] = generalization_score
        
        # 5. 综合评分（加权平均）
        weights = [0.3, 0.25, 0.2, 0.25]  # 衰减容忍度, 鲁棒性, 统计学, 泛化能力
        overall_score = int(round(
            decay_score * weights[0] +
            robustness_score * weights[1] +
            statistical_score * weights[2] +
            generalization_score * weights[3]
        ))
        
        scores['overall_score'] = overall_score
        
        # 6. 评估等级和建议
        if overall_score >= 80:
            level = '优秀'
            suggestion = '策略泛化能力强，过拟合风险低。建议进行实盘测试前的最后验证，包括：(1) 跨品种测试；(2) 极端市场情景压力测试；(3) 交易成本敏感性分析。'
        elif overall_score >= 60:
            level = '良好'
            suggestion = '策略表现基本稳定，但存在一定过拟合风险。建议：(1) 增加参数敏感性分析；(2) 扩大回测周期；(3) 考虑增加趋势过滤等风险控制机制。'
        elif overall_score >= 40:
            level = '一般'
            suggestion = '策略存在明显过拟合迹象。建议：(1) 简化策略逻辑，减少可调参数；(2) 增加样本外测试；(3) 引入止损止盈机制；(4) 考虑重新设计策略核心逻辑。'
        else:
            level = '较差'
            suggestion = '策略过拟合风险极高，不建议实盘使用。需要：(1) 大幅简化或重新设计策略；(2) 增加更多约束条件；(3) 在多个市场环境中验证；(4) 寻求策略逻辑的理论支撑。'
        
        scores['level'] = level
        scores['suggestion'] = suggestion
        scores['details'] = details
        
        return scores
    
    def print_report(self, report):
        """
        打印评估报告
        
        :param report: 评估报告字典
        """
        print("\n" + "="*70)
        print("策略过拟合综合评估报告")
        print("="*70)
        
        print(f"\n【基本信息】")
        print(f"策略类型: {report['策略类型']}")
        print(f"股票代码: {report['股票代码']}")
        print(f"回测周期: {report['回测周期']}")
        print(f"参数设置: {report['参数']}")
        
        print(f"\n【样本内表现（完整数据集）】")
        print(f"年化收益率: {report['样本内年化收益率']:.2%}")
        print(f"最大回撤: {report['样本内最大回撤']:.2%}")
        print(f"Sharpe比率: {report['样本内Sharpe比率']:.2f}")
        print(f"交易次数: {report['样本内交易次数']}")
        
        print(f"\n【样本外表现（滚动验证）】")
        print(f"验证周期数: {report['样本外周期数']}")
        print(f"年化收益率均值: {report['样本外年化收益率均值']:.2%}")
        print(f"最大回撤均值: {report['样本外最大回撤均值']:.2%}")
        print(f"Sharpe比率均值: {report['样本外Sharpe比率均值']:.2f}")
        print(f"正收益周期比例: {report['样本外正收益周期比例']:.2%}")
        print(f"收益率标准差: {report['样本外收益率标准差']:.4f}")
        
        print(f"\n【各维度评分】")
        print(f"┌────────────────┬───────┐")
        print(f"│ 评估维度       │ 得分  │")
        print(f"├────────────────┼───────┤")
        print(f"│ 衰减容忍度     │ {report['衰减容忍度得分']:>5} │")
        print(f"│ 参数鲁棒性     │ {report['参数鲁棒性得分']:>5} │")
        print(f"│ 统计学检验     │ {report['统计学检验得分']:>5} │")
        print(f"│ 泛化能力       │ {report['泛化能力得分']:>5} │")
        print(f"├────────────────┼───────┤")
        print(f"│ 综合得分       │ {report['过拟合分数']:>5} │")
        print(f"└────────────────┴───────┘")
        
        print(f"\n【评估详情】")
        for detail in report['评估详情']:
            print(f"  {detail}")
        
        print(f"\n【综合评估】")
        print(f"评估等级: {report['评估等级']}")
        print(f"过拟合分数: {report['过拟合分数']}/100")
        print(f"\n【建议】")
        print(report['评估建议'])
        
        print("\n" + "="*70)