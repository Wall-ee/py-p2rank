#!/usr/bin/env python3
"""
P2Rank Python 基准测试脚本
移植自原始的 benchmark.sh

用于测试不同线程数下的P2Rank性能
"""

import argparse
import time
import subprocess
import statistics
import psutil
import logging
from pathlib import Path
from typing import List, Dict, Callable, Any
import json
import sys
import os

# 添加p2rank路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from p2rank import P2RankPredictor, P2RankTrainer, ConfigLoader


class P2RankBenchmark:
    """P2Rank Python性能基准测试器"""
    
    def __init__(self, output_dir: str = "./benchmark_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # 设置日志
        self.setup_logging()
        
        # 性能统计
        self.results = {}
        
    def setup_logging(self):
        """设置日志系统"""
        log_file = self.output_dir / "benchmark.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def benchmark_prediction(self, 
                           dataset_file: str,
                           config_name: str = "default",
                           repetitions: int = 5,
                           thread_counts: List[int] = None,
                           label: str = "benchmark") -> Dict[str, Any]:
        """
        基准测试预测性能
        
        Args:
            dataset_file: 数据集文件路径
            config_name: 配置名称
            repetitions: 重复次数
            thread_counts: 线程数列表
            label: 基准测试标签
        """
        
        if thread_counts is None:
            thread_counts = [1, 2, 4, 8]
        
        self.logger.info(f"🚀 开始基准测试: {label}")
        self.logger.info(f"📁 数据集: {dataset_file}")
        self.logger.info(f"⚙️  配置: {config_name}")
        self.logger.info(f"🔄 重复次数: {repetitions}")
        self.logger.info(f"🧵 线程数: {thread_counts}")
        
        results = {
            'label': label,
            'dataset': dataset_file,
            'config': config_name,
            'repetitions': repetitions,
            'system_info': self._get_system_info(),
            'thread_results': {}
        }
        
        for thread_count in thread_counts:
            self.logger.info(f"\n🧵 测试线程数: {thread_count}")
            
            # 配置线程数
            config = ConfigLoader().load_config(config_name)
            config.update({
                'threads': thread_count,
                'n_jobs': thread_count
            })
            
            # 预热运行 (如果重复次数>1)
            if repetitions > 1:
                self.logger.info("🔥 预热运行...")
                self._single_prediction_run(dataset_file, config, warmup=True)
            
            # 基准测试运行
            run_times = []
            
            for i in range(repetitions):
                self.logger.info(f"  运行 {i+1}/{repetitions}")
                
                start_time = time.time()
                try:
                    self._single_prediction_run(dataset_file, config)
                    end_time = time.time()
                    
                    run_time = end_time - start_time
                    run_times.append(run_time)
                    
                    self.logger.info(f"    耗时: {run_time:.2f}秒")
                    
                except Exception as e:
                    self.logger.error(f"    运行失败: {e}")
                    run_times.append(float('inf'))
            
            # 统计结果
            valid_times = [t for t in run_times if t != float('inf')]
            
            if valid_times:
                thread_result = {
                    'thread_count': thread_count,
                    'run_times': valid_times,
                    'avg_time': statistics.mean(valid_times),
                    'std_time': statistics.stdev(valid_times) if len(valid_times) > 1 else 0,
                    'min_time': min(valid_times),
                    'max_time': max(valid_times),
                    'success_rate': len(valid_times) / repetitions
                }
                
                results['thread_results'][thread_count] = thread_result
                
                self.logger.info(f"  📊 平均耗时: {thread_result['avg_time']:.2f}秒")
                self.logger.info(f"  📈 标准差: {thread_result['std_time']:.2f}秒")
                self.logger.info(f"  ✅ 成功率: {thread_result['success_rate']:.1%}")
            else:
                self.logger.error(f"  ❌ 线程数 {thread_count} 所有运行都失败")
        
        # 保存结果
        self._save_results(results, label)
        self._generate_report(results)
        
        return results
    
    def benchmark_training(self,
                          training_dataset: str,
                          evaluation_dataset: str = None,
                          config_name: str = "train_default",
                          repetitions: int = 3,
                          thread_counts: List[int] = None,
                          label: str = "training_benchmark") -> Dict[str, Any]:
        """基准测试训练性能"""
        
        if thread_counts is None:
            thread_counts = [1, 2, 4, 8]
        
        self.logger.info(f"🎯 开始训练基准测试: {label}")
        
        results = {
            'label': label,
            'training_dataset': training_dataset,
            'evaluation_dataset': evaluation_dataset,
            'config': config_name,
            'repetitions': repetitions,
            'system_info': self._get_system_info(),
            'thread_results': {}
        }
        
        for thread_count in thread_counts:
            self.logger.info(f"\n🧵 测试线程数: {thread_count}")
            
            config = ConfigLoader().load_config(config_name)
            config.update({
                'threads': thread_count,
                'n_jobs': thread_count,
                'rf_threads': min(thread_count, 8)  # 限制RF线程数
            })
            
            run_times = []
            train_scores = []
            eval_scores = []
            
            for i in range(repetitions):
                self.logger.info(f"  训练运行 {i+1}/{repetitions}")
                
                start_time = time.time()
                try:
                    trainer = P2RankTrainer(config)
                    
                    # 训练模型
                    model = trainer.train_model(training_dataset)
                    train_time = time.time() - start_time
                    
                    # 评估模型 (如果提供了评估数据集)
                    if evaluation_dataset:
                        eval_result = trainer.evaluate_model(model, evaluation_dataset)
                        eval_scores.append(eval_result.get('DCA_4_0', 0))
                        train_scores.append(1.0)  # 训练集上假设完美
                    
                    run_times.append(train_time)
                    self.logger.info(f"    训练耗时: {train_time:.2f}秒")
                    
                except Exception as e:
                    self.logger.error(f"    训练失败: {e}")
                    run_times.append(float('inf'))
            
            # 统计结果
            valid_times = [t for t in run_times if t != float('inf')]
            
            if valid_times:
                thread_result = {
                    'thread_count': thread_count,
                    'train_times': valid_times,
                    'avg_train_time': statistics.mean(valid_times),
                    'std_train_time': statistics.stdev(valid_times) if len(valid_times) > 1 else 0,
                    'success_rate': len(valid_times) / repetitions
                }
                
                if eval_scores:
                    thread_result.update({
                        'eval_scores': eval_scores,
                        'avg_eval_score': statistics.mean(eval_scores),
                        'std_eval_score': statistics.stdev(eval_scores) if len(eval_scores) > 1 else 0
                    })
                
                results['thread_results'][thread_count] = thread_result
                
                self.logger.info(f"  📊 平均训练时间: {thread_result['avg_train_time']:.2f}秒")
                if 'avg_eval_score' in thread_result:
                    self.logger.info(f"  🎯 平均评估分数: {thread_result['avg_eval_score']:.3f}")
        
        self._save_results(results, label)
        self._generate_training_report(results)
        
        return results
    
    def _single_prediction_run(self, dataset_file: str, config: dict, warmup: bool = False):
        """单次预测运行"""
        predictor = P2RankPredictor(config)
        
        # 加载数据集
        from p2rank.utils import DatasetLoader
        dataset = DatasetLoader().load_dataset(dataset_file)
        
        # 进行预测
        for protein_file in dataset.protein_files[:1 if warmup else None]:  # 预热时只处理一个
            try:
                results = predictor.predict(protein_file)
                # 强制计算结果以确保完整运行
                _ = len(results.pockets)
            except Exception as e:
                self.logger.warning(f"预测失败 {protein_file}: {e}")
                raise
    
    def _get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        return {
            'cpu_count': psutil.cpu_count(),
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_total': psutil.virtual_memory().total,
            'memory_available': psutil.virtual_memory().available,
            'platform': sys.platform,
            'python_version': sys.version,
        }
    
    def _save_results(self, results: Dict[str, Any], label: str):
        """保存基准测试结果"""
        output_file = self.output_dir / f"{label}_results.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        self.logger.info(f"💾 结果已保存至: {output_file}")
    
    def _generate_report(self, results: Dict[str, Any]):
        """生成性能报告"""
        report_file = self.output_dir / f"{results['label']}_report.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"P2Rank Python 基准测试报告\n")
            f.write(f"=" * 50 + "\n\n")
            
            f.write(f"测试标签: {results['label']}\n")
            f.write(f"数据集: {results['dataset']}\n")
            f.write(f"配置: {results['config']}\n")
            f.write(f"重复次数: {results['repetitions']}\n\n")
            
            f.write("系统信息:\n")
            for key, value in results['system_info'].items():
                f.write(f"  {key}: {value}\n")
            f.write("\n")
            
            f.write("性能结果:\n")
            f.write(f"{'线程数':<8} {'平均时间(s)':<12} {'标准差(s)':<12} {'最小时间(s)':<12} {'最大时间(s)':<12} {'成功率':<8}\n")
            f.write("-" * 80 + "\n")
            
            for thread_count, result in results['thread_results'].items():
                f.write(f"{thread_count:<8} {result['avg_time']:<12.2f} {result['std_time']:<12.2f} "
                       f"{result['min_time']:<12.2f} {result['max_time']:<12.2f} {result['success_rate']:<8.1%}\n")
        
        self.logger.info(f"📄 报告已生成: {report_file}")
    
    def _generate_training_report(self, results: Dict[str, Any]):
        """生成训练性能报告"""
        report_file = self.output_dir / f"{results['label']}_report.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"P2Rank Python 训练基准测试报告\n")
            f.write(f"=" * 50 + "\n\n")
            
            f.write(f"测试标签: {results['label']}\n")
            f.write(f"训练数据集: {results['training_dataset']}\n")
            f.write(f"评估数据集: {results.get('evaluation_dataset', 'N/A')}\n")
            f.write(f"配置: {results['config']}\n\n")
            
            f.write("训练性能结果:\n")
            f.write(f"{'线程数':<8} {'平均训练时间(s)':<16} {'标准差(s)':<12} {'平均评估分数':<14} {'成功率':<8}\n")
            f.write("-" * 80 + "\n")
            
            for thread_count, result in results['thread_results'].items():
                eval_score = result.get('avg_eval_score', 0)
                f.write(f"{thread_count:<8} {result['avg_train_time']:<16.2f} {result['std_train_time']:<12.2f} "
                       f"{eval_score:<14.3f} {result['success_rate']:<8.1%}\n")


def standard_benchmarks():
    """运行标准基准测试套件"""
    
    benchmark = P2RankBenchmark()
    
    print("🧪 P2Rank Python 标准基准测试套件")
    print("=" * 50)
    
    # 基准测试配置
    benchmarks_config = [
        {
            'name': 'quick_prediction',
            'dataset': 'test_small.ds',
            'config': 'default',
            'repetitions': 5,
            'threads': [1, 2, 4, 8],
            'type': 'prediction'
        },
        {
            'name': 'standard_prediction',
            'dataset': 'chen11_test.ds',
            'config': 'default',
            'repetitions': 3,
            'threads': [1, 2, 4, 8, 12, 16],
            'type': 'prediction'
        },
        {
            'name': 'training_benchmark',
            'training_dataset': 'chen11_train_small.ds',
            'evaluation_dataset': 'chen11_test_small.ds',
            'config': 'train_default',
            'repetitions': 2,
            'threads': [1, 2, 4, 8],
            'type': 'training'
        }
    ]
    
    results = {}
    
    for config in benchmarks_config:
        print(f"\n🎯 运行基准测试: {config['name']}")
        
        try:
            if config['type'] == 'prediction':
                result = benchmark.benchmark_prediction(
                    dataset_file=config['dataset'],
                    config_name=config['config'],
                    repetitions=config['repetitions'],
                    thread_counts=config['threads'],
                    label=config['name']
                )
            elif config['type'] == 'training':
                result = benchmark.benchmark_training(
                    training_dataset=config['training_dataset'],
                    evaluation_dataset=config.get('evaluation_dataset'),
                    config_name=config['config'],
                    repetitions=config['repetitions'],
                    thread_counts=config['threads'],
                    label=config['name']
                )
            
            results[config['name']] = result
            print(f"✅ {config['name']} 完成")
            
        except Exception as e:
            print(f"❌ {config['name']} 失败: {e}")
            results[config['name']] = {'error': str(e)}
    
    # 生成综合报告
    generate_comprehensive_report(results, benchmark.output_dir)
    
    return results


def generate_comprehensive_report(results: Dict[str, Any], output_dir: Path):
    """生成综合性能报告"""
    
    report_file = output_dir / "comprehensive_benchmark_report.txt"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("P2Rank Python 综合基准测试报告\n")
        f.write("=" * 60 + "\n\n")
        
        f.write(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"测试项目数: {len(results)}\n\n")
        
        # 成功率统计
        successful_tests = [k for k, v in results.items() if 'error' not in v]
        failed_tests = [k for k, v in results.items() if 'error' in v]
        
        f.write(f"成功测试: {len(successful_tests)}/{len(results)}\n")
        f.write(f"失败测试: {len(failed_tests)}/{len(results)}\n\n")
        
        if failed_tests:
            f.write("失败测试列表:\n")
            for test in failed_tests:
                f.write(f"  - {test}: {results[test]['error']}\n")
            f.write("\n")
        
        # 性能摘要
        f.write("性能摘要:\n")
        f.write("-" * 40 + "\n")
        
        for test_name, result in results.items():
            if 'error' in result:
                continue
                
            f.write(f"\n{test_name.upper()}:\n")
            
            if 'thread_results' in result:
                best_thread = min(result['thread_results'].items(), 
                                key=lambda x: x[1].get('avg_time', float('inf')))
                worst_thread = max(result['thread_results'].items(),
                                 key=lambda x: x[1].get('avg_time', 0))
                
                f.write(f"  最佳性能: {best_thread[1]['avg_time']:.2f}s (线程数: {best_thread[0]})\n")
                f.write(f"  最差性能: {worst_thread[1]['avg_time']:.2f}s (线程数: {worst_thread[0]})\n")
                
                # 线程扩展性分析
                single_thread_time = result['thread_results'].get(1, {}).get('avg_time')
                if single_thread_time:
                    for threads, thread_result in result['thread_results'].items():
                        if threads > 1:
                            speedup = single_thread_time / thread_result['avg_time']
                            efficiency = speedup / threads
                            f.write(f"  {threads}线程加速比: {speedup:.2f}x (效率: {efficiency:.1%})\n")
    
    print(f"📄 综合报告已生成: {report_file}")


def main():
    """主函数 - 命令行接口"""
    
    parser = argparse.ArgumentParser(description="P2Rank Python 基准测试工具")
    parser.add_argument('--mode', choices=['prediction', 'training', 'standard'], 
                       default='standard', help='基准测试模式')
    parser.add_argument('--dataset', help='数据集文件路径')
    parser.add_argument('--config', default='default', help='配置名称')
    parser.add_argument('--repetitions', type=int, default=5, help='重复次数')
    parser.add_argument('--threads', nargs='+', type=int, default=[1, 2, 4, 8], 
                       help='测试的线程数列表')
    parser.add_argument('--label', default='custom_benchmark', help='基准测试标签')
    parser.add_argument('--output-dir', default='./benchmark_results', help='输出目录')
    
    args = parser.parse_args()
    
    # 创建基准测试器
    benchmark = P2RankBenchmark(output_dir=args.output_dir)
    
    if args.mode == 'standard':
        print("🚀 运行标准基准测试套件...")
        results = standard_benchmarks()
        
    elif args.mode == 'prediction':
        if not args.dataset:
            print("❌ 预测模式需要指定数据集文件 (--dataset)")
            return
        
        print(f"🎯 运行预测基准测试: {args.dataset}")
        results = benchmark.benchmark_prediction(
            dataset_file=args.dataset,
            config_name=args.config,
            repetitions=args.repetitions,
            thread_counts=args.threads,
            label=args.label
        )
        
    elif args.mode == 'training':
        if not args.dataset:
            print("❌ 训练模式需要指定训练数据集文件 (--dataset)")
            return
        
        print(f"🎯 运行训练基准测试: {args.dataset}")
        results = benchmark.benchmark_training(
            training_dataset=args.dataset,
            config_name=args.config,
            repetitions=args.repetitions,
            thread_counts=args.threads,
            label=args.label
        )
    
    print(f"\n🎉 基准测试完成! 结果保存在: {args.output_dir}")


if __name__ == "__main__":
    main()
