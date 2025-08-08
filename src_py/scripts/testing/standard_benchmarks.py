#!/usr/bin/env python3
"""
P2Rank Python 标准基准测试套件
移植自原始的 standard-benchmarks.sh

提供一整套标准的性能基准测试
"""

import argparse
import time
import json
import logging
from pathlib import Path
from typing import Dict, List, Any
import sys

# 添加p2rank路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.testing.benchmark import P2RankBenchmark
from p2rank.utils import DatasetLoader


class StandardBenchmarkSuite:
    """标准基准测试套件"""
    
    def __init__(self, output_dir: str = "./standard_benchmark_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.benchmark = P2RankBenchmark(output_dir=str(self.output_dir))
        
        # 设置日志
        self.setup_logging()
        
    def setup_logging(self):
        """设置日志系统"""
        log_file = self.output_dir / "standard_benchmarks.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def run_all_standard_tests(self) -> Dict[str, Any]:
        """运行所有标准基准测试"""
        
        self.logger.info("🚀 开始运行P2Rank Python标准基准测试套件")
        self.logger.info("=" * 60)
        
        # 定义标准测试套件
        test_suite = self._get_standard_test_definitions()
        
        results = {
            'suite_name': 'P2Rank Python Standard Benchmarks',
            'start_time': time.time(),
            'test_results': {},
            'summary': {}
        }
        
        successful_tests = 0
        failed_tests = 0
        
        for test_name, test_config in test_suite.items():
            self.logger.info(f"\n🧪 运行测试: {test_name}")
            self.logger.info(f"📝 描述: {test_config['description']}")
            
            try:
                if test_config['type'] == 'prediction':
                    result = self._run_prediction_test(test_name, test_config)
                elif test_config['type'] == 'training':
                    result = self._run_training_test(test_name, test_config)
                elif test_config['type'] == 'memory':
                    result = self._run_memory_test(test_name, test_config)
                elif test_config['type'] == 'accuracy':
                    result = self._run_accuracy_test(test_name, test_config)
                else:
                    raise ValueError(f"未知测试类型: {test_config['type']}")
                
                results['test_results'][test_name] = result
                successful_tests += 1
                
                self.logger.info(f"✅ {test_name} 测试成功完成")
                
            except Exception as e:
                self.logger.error(f"❌ {test_name} 测试失败: {e}")
                results['test_results'][test_name] = {
                    'status': 'failed',
                    'error': str(e),
                    'test_config': test_config
                }
                failed_tests += 1
        
        # 生成测试总结
        results['end_time'] = time.time()
        results['total_duration'] = results['end_time'] - results['start_time']
        results['summary'] = {
            'total_tests': len(test_suite),
            'successful_tests': successful_tests,
            'failed_tests': failed_tests,
            'success_rate': successful_tests / len(test_suite) if test_suite else 0,
            'total_duration_minutes': results['total_duration'] / 60
        }
        
        # 保存完整结果
        self._save_suite_results(results)
        self._generate_suite_report(results)
        
        self.logger.info(f"\n🎉 标准基准测试套件完成!")
        self.logger.info(f"📊 总体结果: {successful_tests}/{len(test_suite)} 测试成功")
        self.logger.info(f"⏱️  总耗时: {results['total_duration']:.1f}秒")
        
        return results
    
    def _get_standard_test_definitions(self) -> Dict[str, Dict[str, Any]]:
        """获取标准测试定义"""
        
        return {
            'quick_prediction_u48': {
                'type': 'prediction',
                'description': 'U48小型数据集快速预测测试',
                'dataset': 'u48_small.ds',
                'config': 'default',
                'repetitions': 20,
                'threads': [1, 2, 4, 8],
                'expected_max_time': 60,  # 预期最大时间(秒)
                'priority': 'high'
            },
            
            'standard_prediction_u48': {
                'type': 'prediction',
                'description': 'U48标准预测性能测试',
                'dataset': 'u48.ds',
                'config': 'default',
                'repetitions': 10,
                'threads': [1, 2, 4, 8, 12, 16, 20, 24],
                'expected_max_time': 300,
                'priority': 'high'
            },
            
            'large_dataset_prediction': {
                'type': 'prediction',
                'description': '大型数据集预测测试',
                'dataset': 'holo4k.ds',
                'config': 'default',
                'repetitions': 3,
                'threads': [8, 16, 20, 24, 28, 32, 40],
                'expected_max_time': 1800,
                'priority': 'medium'
            },
            
            'training_performance': {
                'type': 'training',
                'description': '训练性能基准测试',
                'training_dataset': 'chen11_train_fpocket.ds',
                'evaluation_dataset': 'chen11_test.ds',
                'config': 'train_default',
                'repetitions': 3,
                'threads': [1, 4, 8, 12],
                'expected_max_time': 3600,
                'priority': 'high'
            },
            
            'memory_efficiency': {
                'type': 'memory',
                'description': '内存使用效率测试',
                'dataset': 'chen11.ds',
                'config': 'memory_efficient',
                'repetitions': 5,
                'threads': [1, 2, 4],
                'monitor_memory': True,
                'priority': 'medium'
            },
            
            'prediction_accuracy': {
                'type': 'accuracy',
                'description': '预测准确性验证测试',
                'dataset': 'chen11_test.ds',
                'config': 'default',
                'repetitions': 1,
                'threads': [4],
                'expected_min_dca': 0.5,  # 预期最小DCA分数
                'priority': 'high'
            },
            
            'single_protein_speed': {
                'type': 'prediction',
                'description': '单蛋白质预测速度测试',
                'dataset': 'dt198_single.ds',
                'config': 'default',
                'repetitions': 1,
                'threads': [1],
                'expected_max_time': 30,
                'priority': 'low'
            }
        }
    
    def _run_prediction_test(self, test_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """运行预测测试"""
        
        result = self.benchmark.benchmark_prediction(
            dataset_file=config['dataset'],
            config_name=config['config'],
            repetitions=config['repetitions'],
            thread_counts=config['threads'],
            label=test_name
        )
        
        # 添加性能评估
        result['performance_analysis'] = self._analyze_prediction_performance(result, config)
        
        return result
    
    def _run_training_test(self, test_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """运行训练测试"""
        
        result = self.benchmark.benchmark_training(
            training_dataset=config['training_dataset'],
            evaluation_dataset=config.get('evaluation_dataset'),
            config_name=config['config'],
            repetitions=config['repetitions'],
            thread_counts=config['threads'],
            label=test_name
        )
        
        # 添加训练效率分析
        result['training_analysis'] = self._analyze_training_performance(result, config)
        
        return result
    
    def _run_memory_test(self, test_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """运行内存测试"""
        import psutil
        import threading
        
        # 内存监控
        memory_usage = []
        monitoring = True
        
        def monitor_memory():
            while monitoring:
                memory_usage.append(psutil.virtual_memory().percent)
                time.sleep(0.5)
        
        # 启动内存监控
        monitor_thread = threading.Thread(target=monitor_memory)
        monitor_thread.start()
        
        try:
            # 运行预测测试
            result = self._run_prediction_test(test_name, config)
            
            # 停止监控
            monitoring = False
            monitor_thread.join()
            
            # 添加内存分析
            result['memory_analysis'] = {
                'peak_memory_percent': max(memory_usage) if memory_usage else 0,
                'avg_memory_percent': sum(memory_usage) / len(memory_usage) if memory_usage else 0,
                'memory_samples': len(memory_usage)
            }
            
            return result
            
        except Exception as e:
            monitoring = False
            monitor_thread.join()
            raise e
    
    def _run_accuracy_test(self, test_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """运行准确性测试"""
        
        from p2rank import P2RankPredictor, ConfigLoader
        from p2rank.evaluation import ModelEvaluator
        
        # 加载配置和模型
        cfg = ConfigLoader().load_config(config['config'])
        predictor = P2RankPredictor(cfg)
        
        # 加载数据集
        dataset = DatasetLoader().load_dataset(config['dataset'])
        
        # 运行预测和评估
        evaluator = ModelEvaluator()
        evaluation_results = evaluator.evaluate_dataset(predictor, dataset)
        
        result = {
            'test_name': test_name,
            'dataset': config['dataset'],
            'config': config['config'],
            'accuracy_metrics': evaluation_results,
            'accuracy_analysis': self._analyze_accuracy_performance(evaluation_results, config)
        }
        
        return result
    
    def _analyze_prediction_performance(self, result: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """分析预测性能"""
        
        analysis = {
            'status': 'pass',
            'issues': [],
            'recommendations': []
        }
        
        # 检查是否超过预期时间
        expected_max_time = config.get('expected_max_time', float('inf'))
        
        for thread_count, thread_result in result['thread_results'].items():
            avg_time = thread_result.get('avg_time', float('inf'))
            
            if avg_time > expected_max_time:
                analysis['status'] = 'warning'
                analysis['issues'].append(
                    f"线程数{thread_count}的平均时间({avg_time:.2f}s)超过预期({expected_max_time}s)"
                )
        
        # 分析线程扩展性
        if 1 in result['thread_results'] and len(result['thread_results']) > 1:
            single_thread_time = result['thread_results'][1]['avg_time']
            
            for threads in [2, 4, 8]:
                if threads in result['thread_results']:
                    multi_thread_time = result['thread_results'][threads]['avg_time']
                    speedup = single_thread_time / multi_thread_time
                    ideal_speedup = threads
                    efficiency = speedup / ideal_speedup
                    
                    if efficiency < 0.5:  # 效率低于50%
                        analysis['recommendations'].append(
                            f"线程数{threads}的并行效率较低({efficiency:.1%})，考虑优化并行策略"
                        )
        
        return analysis
    
    def _analyze_training_performance(self, result: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """分析训练性能"""
        
        analysis = {
            'status': 'pass',
            'issues': [],
            'recommendations': []
        }
        
        expected_max_time = config.get('expected_max_time', float('inf'))
        
        for thread_count, thread_result in result['thread_results'].items():
            avg_time = thread_result.get('avg_train_time', float('inf'))
            
            if avg_time > expected_max_time:
                analysis['status'] = 'warning'
                analysis['issues'].append(
                    f"线程数{thread_count}的训练时间({avg_time:.2f}s)超过预期({expected_max_time}s)"
                )
            
            # 检查评估分数
            if 'avg_eval_score' in thread_result:
                eval_score = thread_result['avg_eval_score']
                if eval_score < 0.3:  # 假设最低可接受分数
                    analysis['status'] = 'fail'
                    analysis['issues'].append(
                        f"线程数{thread_count}的评估分数过低({eval_score:.3f})"
                    )
        
        return analysis
    
    def _analyze_accuracy_performance(self, evaluation_results: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """分析准确性性能"""
        
        analysis = {
            'status': 'pass',
            'issues': [],
            'recommendations': []
        }
        
        expected_min_dca = config.get('expected_min_dca', 0.0)
        actual_dca = evaluation_results.get('DCA_4_0', 0.0)
        
        if actual_dca < expected_min_dca:
            analysis['status'] = 'fail'
            analysis['issues'].append(
                f"DCA分数({actual_dca:.3f})低于预期最小值({expected_min_dca:.3f})"
            )
        
        return analysis
    
    def _save_suite_results(self, results: Dict[str, Any]):
        """保存套件结果"""
        
        output_file = self.output_dir / "standard_benchmark_suite_results.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        self.logger.info(f"💾 完整结果已保存至: {output_file}")
    
    def _generate_suite_report(self, results: Dict[str, Any]):
        """生成套件报告"""
        
        report_file = self.output_dir / "standard_benchmark_suite_report.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("P2Rank Python 标准基准测试套件报告\n")
            f.write("=" * 70 + "\n\n")
            
            # 基本信息
            f.write(f"套件名称: {results['suite_name']}\n")
            f.write(f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(results['start_time']))}\n")
            f.write(f"结束时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(results['end_time']))}\n")
            f.write(f"总耗时: {results['summary']['total_duration_minutes']:.1f} 分钟\n\n")
            
            # 总结统计
            summary = results['summary']
            f.write("测试总结:\n")
            f.write("-" * 30 + "\n")
            f.write(f"总测试数: {summary['total_tests']}\n")
            f.write(f"成功测试: {summary['successful_tests']}\n")
            f.write(f"失败测试: {summary['failed_tests']}\n")
            f.write(f"成功率: {summary['success_rate']:.1%}\n\n")
            
            # 详细测试结果
            f.write("详细测试结果:\n")
            f.write("=" * 50 + "\n")
            
            for test_name, test_result in results['test_results'].items():
                f.write(f"\n{test_name.upper()}:\n")
                f.write("-" * (len(test_name) + 1) + "\n")
                
                if 'status' in test_result and test_result['status'] == 'failed':
                    f.write(f"状态: 失败\n")
                    f.write(f"错误: {test_result['error']}\n")
                    continue
                
                # 性能统计
                if 'thread_results' in test_result:
                    f.write("性能统计:\n")
                    
                    for thread_count, thread_data in test_result['thread_results'].items():
                        if 'avg_time' in thread_data:
                            f.write(f"  {thread_count}线程: {thread_data['avg_time']:.2f}s ± {thread_data.get('std_time', 0):.2f}s\n")
                        elif 'avg_train_time' in thread_data:
                            f.write(f"  {thread_count}线程: 训练{thread_data['avg_train_time']:.2f}s")
                            if 'avg_eval_score' in thread_data:
                                f.write(f", 评估{thread_data['avg_eval_score']:.3f}")
                            f.write("\n")
                
                # 性能分析
                if 'performance_analysis' in test_result:
                    analysis = test_result['performance_analysis']
                    f.write(f"性能评估: {analysis['status'].upper()}\n")
                    
                    if analysis['issues']:
                        f.write("问题:\n")
                        for issue in analysis['issues']:
                            f.write(f"  - {issue}\n")
                    
                    if analysis['recommendations']:
                        f.write("建议:\n")
                        for rec in analysis['recommendations']:
                            f.write(f"  - {rec}\n")
                
                # 准确性结果
                if 'accuracy_metrics' in test_result:
                    metrics = test_result['accuracy_metrics']
                    f.write("准确性指标:\n")
                    for metric_name, value in metrics.items():
                        if isinstance(value, (int, float)):
                            f.write(f"  {metric_name}: {value:.3f}\n")
        
        self.logger.info(f"📄 套件报告已生成: {report_file}")


def run_quick_suite():
    """运行快速测试套件"""
    
    suite = StandardBenchmarkSuite()
    
    # 只运行高优先级的快速测试
    quick_tests = {
        'quick_prediction': {
            'type': 'prediction',
            'description': '快速预测测试',
            'dataset': 'test_small.ds',
            'config': 'default',
            'repetitions': 3,
            'threads': [1, 2, 4],
            'expected_max_time': 30,
            'priority': 'high'
        }
    }
    
    print("🚀 运行快速基准测试套件...")
    
    results = {'test_results': {}}
    
    for test_name, config in quick_tests.items():
        try:
            result = suite._run_prediction_test(test_name, config)
            results['test_results'][test_name] = result
            print(f"✅ {test_name} 完成")
        except Exception as e:
            print(f"❌ {test_name} 失败: {e}")
            results['test_results'][test_name] = {'error': str(e)}
    
    return results


def main():
    """主函数"""
    
    parser = argparse.ArgumentParser(description="P2Rank Python 标准基准测试套件")
    parser.add_argument('--mode', choices=['full', 'quick', 'custom'], 
                       default='quick', help='测试模式')
    parser.add_argument('--output-dir', default='./standard_benchmark_results', 
                       help='输出目录')
    parser.add_argument('--tests', nargs='+', help='自定义测试列表 (仅custom模式)')
    
    args = parser.parse_args()
    
    if args.mode == 'full':
        print("🎯 运行完整标准基准测试套件...")
        suite = StandardBenchmarkSuite(output_dir=args.output_dir)
        results = suite.run_all_standard_tests()
        
    elif args.mode == 'quick':
        print("⚡ 运行快速基准测试...")
        results = run_quick_suite()
        
    elif args.mode == 'custom':
        if not args.tests:
            print("❌ 自定义模式需要指定测试列表 (--tests)")
            return
        
        print(f"🎯 运行自定义测试: {args.tests}")
        # TODO: 实现自定义测试选择
        print("自定义测试模式暂未实现")
        return
    
    print("\n🎉 基准测试套件完成!")


if __name__ == "__main__":
    main()
