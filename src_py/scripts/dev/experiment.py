#!/usr/bin/env python3
"""
P2Rank Python 实验管理工具
移植自原始的 experiment.sh

运行实验并自动推送结果到git仓库
"""

import argparse
import subprocess
import sys
import time
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
import json
import os

# 添加p2rank路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from p2rank import P2RankPredictor, P2RankTrainer, ConfigLoader


class ExperimentManager:
    """实验管理器"""
    
    def __init__(self, 
                 results_repo_path: Optional[str] = None,
                 output_dir: str = "./experiment_results"):
        self.results_repo_path = Path(results_repo_path) if results_repo_path else None
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # 设置日志
        self.setup_logging()
        
    def setup_logging(self):
        """设置日志系统"""
        log_file = self.output_dir / "experiment.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def run_experiment(self, 
                      experiment_type: str,
                      config_name: str = "default",
                      dataset: Optional[str] = None,
                      training_dataset: Optional[str] = None,
                      evaluation_dataset: Optional[str] = None,
                      experiment_name: Optional[str] = None,
                      auto_push: bool = True,
                      **kwargs) -> Dict[str, Any]:
        """
        运行实验
        
        Args:
            experiment_type: 实验类型 ('predict', 'train', 'crossval', 'traineval')
            config_name: 配置名称
            dataset: 数据集路径
            training_dataset: 训练数据集路径
            evaluation_dataset: 评估数据集路径
            experiment_name: 实验名称
            auto_push: 是否自动推送结果
            **kwargs: 其他参数
        """
        
        if not experiment_name:
            experiment_name = f"{experiment_type}_{int(time.time())}"
        
        self.logger.info(f"🧪 开始实验: {experiment_name}")
        self.logger.info(f"🎯 实验类型: {experiment_type}")
        self.logger.info(f"⚙️  配置: {config_name}")
        
        # 创建实验结果目录
        experiment_output = self.output_dir / experiment_name
        experiment_output.mkdir(exist_ok=True)
        
        experiment_metadata = {
            'experiment_name': experiment_name,
            'experiment_type': experiment_type,
            'config_name': config_name,
            'start_time': time.time(),
            'parameters': kwargs,
            'status': 'running'
        }
        
        try:
            # 根据实验类型运行相应的实验
            if experiment_type == 'predict':
                result = self._run_prediction_experiment(
                    config_name, dataset, experiment_output, **kwargs
                )
            elif experiment_type == 'train':
                result = self._run_training_experiment(
                    config_name, training_dataset, experiment_output, **kwargs
                )
            elif experiment_type == 'crossval':
                result = self._run_crossvalidation_experiment(
                    config_name, dataset, experiment_output, **kwargs
                )
            elif experiment_type == 'traineval':
                result = self._run_traineval_experiment(
                    config_name, training_dataset, evaluation_dataset, 
                    experiment_output, **kwargs
                )
            else:
                raise ValueError(f"未知的实验类型: {experiment_type}")
            
            experiment_metadata.update({
                'end_time': time.time(),
                'duration': time.time() - experiment_metadata['start_time'],
                'status': 'completed',
                'result': result
            })
            
            self.logger.info(f"✅ 实验完成: {experiment_name}")
            self.logger.info(f"⏱️  耗时: {experiment_metadata['duration']:.2f}秒")
            
            # 保存实验元数据
            metadata_file = experiment_output / "experiment_metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(experiment_metadata, f, indent=2, ensure_ascii=False, default=str)
            
            # 自动推送结果到git (如果启用)
            if auto_push and self.results_repo_path:
                self._push_results_to_git(experiment_name, experiment_metadata)
            
            return experiment_metadata
            
        except Exception as e:
            experiment_metadata.update({
                'end_time': time.time(),
                'duration': time.time() - experiment_metadata['start_time'],
                'status': 'failed',
                'error': str(e)
            })
            
            self.logger.error(f"❌ 实验失败: {experiment_name} - {e}")
            
            # 保存失败的元数据
            metadata_file = experiment_output / "experiment_metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(experiment_metadata, f, indent=2, ensure_ascii=False, default=str)
            
            return experiment_metadata
    
    def _run_prediction_experiment(self, config_name: str, dataset: str, 
                                 output_dir: Path, **kwargs) -> Dict[str, Any]:
        """运行预测实验"""
        
        self.logger.info(f"🎯 运行预测实验: {dataset}")
        
        # 加载配置和预测器
        config = ConfigLoader().load_config(config_name)
        config.update(kwargs)
        
        predictor = P2RankPredictor(config)
        
        # 加载数据集
        from p2rank.utils import DatasetLoader
        dataset_loader = DatasetLoader()
        dataset_obj = dataset_loader.load_dataset(dataset)
        
        # 运行预测
        prediction_results = []
        
        for i, protein_file in enumerate(dataset_obj.protein_files):
            self.logger.info(f"  预测蛋白质 {i+1}/{len(dataset_obj.protein_files)}: {Path(protein_file).name}")
            
            try:
                result = predictor.predict(str(protein_file))
                
                prediction_result = {
                    'protein_file': str(protein_file),
                    'pocket_count': len(result.pockets),
                    'prediction_scores': [pocket.score for pocket in result.pockets],
                    'status': 'success'
                }
                
                # 保存预测结果
                protein_output = output_dir / f"{Path(protein_file).stem}_predictions.csv"
                result.save_predictions(str(protein_output))
                
                prediction_results.append(prediction_result)
                
            except Exception as e:
                self.logger.warning(f"    预测失败: {e}")
                prediction_results.append({
                    'protein_file': str(protein_file),
                    'status': 'failed',
                    'error': str(e)
                })
        
        # 统计结果
        successful = sum(1 for r in prediction_results if r['status'] == 'success')
        total_pockets = sum(r.get('pocket_count', 0) for r in prediction_results if r['status'] == 'success')
        
        experiment_result = {
            'experiment_type': 'prediction',
            'dataset': dataset,
            'total_proteins': len(dataset_obj.protein_files),
            'successful_predictions': successful,
            'failed_predictions': len(prediction_results) - successful,
            'total_pockets_found': total_pockets,
            'avg_pockets_per_protein': total_pockets / successful if successful > 0 else 0,
            'prediction_results': prediction_results
        }
        
        return experiment_result
    
    def _run_training_experiment(self, config_name: str, training_dataset: str,
                               output_dir: Path, **kwargs) -> Dict[str, Any]:
        """运行训练实验"""
        
        self.logger.info(f"🎯 运行训练实验: {training_dataset}")
        
        # 加载配置和训练器
        config = ConfigLoader().load_config(config_name)
        config.update(kwargs)
        
        trainer = P2RankTrainer(config)
        
        # 训练模型
        start_time = time.time()
        model = trainer.train_model(training_dataset)
        training_time = time.time() - start_time
        
        # 保存模型
        model_file = output_dir / "trained_model.pkl"
        trainer.save_model(model, str(model_file))
        
        experiment_result = {
            'experiment_type': 'training',
            'training_dataset': training_dataset,
            'training_time': training_time,
            'model_file': str(model_file),
            'model_info': {
                'feature_count': getattr(model, 'n_features_', 'unknown'),
                'model_type': type(model).__name__
            }
        }
        
        return experiment_result
    
    def _run_crossvalidation_experiment(self, config_name: str, dataset: str,
                                      output_dir: Path, **kwargs) -> Dict[str, Any]:
        """运行交叉验证实验"""
        
        self.logger.info(f"🎯 运行交叉验证实验: {dataset}")
        
        # 加载配置和训练器
        config = ConfigLoader().load_config(config_name)
        config.update(kwargs)
        
        trainer = P2RankTrainer(config)
        
        # 交叉验证参数
        folds = kwargs.get('folds', 5)
        loop = kwargs.get('loop', 1)
        
        # 运行交叉验证
        cv_results = trainer.cross_validate(
            dataset=dataset,
            folds=folds,
            loop=loop
        )
        
        # 保存详细结果
        cv_file = output_dir / "crossvalidation_results.json"
        with open(cv_file, 'w', encoding='utf-8') as f:
            json.dump(cv_results, f, indent=2, ensure_ascii=False, default=str)
        
        experiment_result = {
            'experiment_type': 'crossvalidation',
            'dataset': dataset,
            'folds': folds,
            'loop': loop,
            'cv_results': cv_results,
            'results_file': str(cv_file)
        }
        
        return experiment_result
    
    def _run_traineval_experiment(self, config_name: str, training_dataset: str,
                                evaluation_dataset: str, output_dir: Path, 
                                **kwargs) -> Dict[str, Any]:
        """运行训练评估实验"""
        
        self.logger.info(f"🎯 运行训练评估实验")
        self.logger.info(f"  训练集: {training_dataset}")
        self.logger.info(f"  评估集: {evaluation_dataset}")
        
        # 加载配置和训练器
        config = ConfigLoader().load_config(config_name)
        config.update(kwargs)
        
        trainer = P2RankTrainer(config)
        
        # 训练模型
        start_time = time.time()
        model = trainer.train_model(training_dataset)
        training_time = time.time() - start_time
        
        # 评估模型
        start_time = time.time()
        evaluation_result = trainer.evaluate_model(model, evaluation_dataset)
        evaluation_time = time.time() - start_time
        
        # 保存模型和结果
        model_file = output_dir / "trained_model.pkl"
        trainer.save_model(model, str(model_file))
        
        eval_file = output_dir / "evaluation_results.json"
        with open(eval_file, 'w', encoding='utf-8') as f:
            json.dump(evaluation_result, f, indent=2, ensure_ascii=False, default=str)
        
        experiment_result = {
            'experiment_type': 'traineval',
            'training_dataset': training_dataset,
            'evaluation_dataset': evaluation_dataset,
            'training_time': training_time,
            'evaluation_time': evaluation_time,
            'evaluation_metrics': evaluation_result,
            'model_file': str(model_file),
            'results_file': str(eval_file)
        }
        
        return experiment_result
    
    def _push_results_to_git(self, experiment_name: str, metadata: Dict[str, Any]):
        """推送实验结果到git仓库"""
        
        if not self.results_repo_path or not self.results_repo_path.exists():
            self.logger.warning("结果仓库路径不存在，跳过git推送")
            return
        
        try:
            self.logger.info(f"📤 推送实验结果到git: {experiment_name}")
            
            # 切换到结果仓库目录
            original_cwd = os.getcwd()
            os.chdir(self.results_repo_path)
            
            try:
                # 拉取最新变更
                subprocess.run(['git', 'pull'], check=True, capture_output=True)
                
                # 复制实验结果到结果仓库
                experiment_dir = self.output_dir / experiment_name
                target_dir = self.results_repo_path / experiment_name
                
                if target_dir.exists():
                    import shutil
                    shutil.rmtree(target_dir)
                
                import shutil
                shutil.copytree(experiment_dir, target_dir)
                
                # 添加所有文件
                subprocess.run(['git', 'add', '--all'], check=True)
                
                # 提交变更
                commit_message = f"experiment: {experiment_name} - {metadata['experiment_type']}"
                if metadata['status'] == 'completed':
                    commit_message += f" (SUCCESS in {metadata['duration']:.1f}s)"
                else:
                    commit_message += f" (FAILED: {metadata.get('error', 'unknown error')})"
                
                subprocess.run(['git', 'commit', '-m', commit_message], check=True)
                
                # 推送到远程
                subprocess.run(['git', 'push'], check=True)
                
                self.logger.info(f"✅ 实验结果已推送到git")
                
            finally:
                os.chdir(original_cwd)
                
        except subprocess.CalledProcessError as e:
            self.logger.error(f"❌ Git操作失败: {e}")
        except Exception as e:
            self.logger.error(f"❌ 推送结果失败: {e}")
    
    def list_experiments(self) -> List[Dict[str, Any]]:
        """列出所有实验"""
        
        experiments = []
        
        for experiment_dir in self.output_dir.iterdir():
            if experiment_dir.is_dir():
                metadata_file = experiment_dir / "experiment_metadata.json"
                
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        experiments.append(metadata)
                    except Exception as e:
                        self.logger.warning(f"无法读取实验元数据: {metadata_file} - {e}")
        
        # 按开始时间排序
        experiments.sort(key=lambda x: x.get('start_time', 0), reverse=True)
        
        return experiments
    
    def generate_experiment_report(self, experiment_name: str) -> str:
        """生成实验报告"""
        
        experiment_dir = self.output_dir / experiment_name
        metadata_file = experiment_dir / "experiment_metadata.json"
        
        if not metadata_file.exists():
            raise FileNotFoundError(f"实验元数据不存在: {experiment_name}")
        
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        report_file = experiment_dir / "experiment_report.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"P2Rank Python 实验报告\n")
            f.write(f"=" * 50 + "\n\n")
            
            f.write(f"实验名称: {metadata['experiment_name']}\n")
            f.write(f"实验类型: {metadata['experiment_type']}\n")
            f.write(f"配置: {metadata['config_name']}\n")
            f.write(f"状态: {metadata['status']}\n")
            f.write(f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(metadata['start_time']))}\n")
            
            if 'end_time' in metadata:
                f.write(f"结束时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(metadata['end_time']))}\n")
                f.write(f"耗时: {metadata['duration']:.2f}秒\n")
            
            f.write(f"\n")
            
            if metadata['status'] == 'completed' and 'result' in metadata:
                result = metadata['result']
                f.write(f"实验结果:\n")
                f.write(f"-" * 20 + "\n")
                
                if result['experiment_type'] == 'prediction':
                    f.write(f"数据集: {result['dataset']}\n")
                    f.write(f"总蛋白质数: {result['total_proteins']}\n")
                    f.write(f"成功预测: {result['successful_predictions']}\n")
                    f.write(f"失败预测: {result['failed_predictions']}\n")
                    f.write(f"发现口袋总数: {result['total_pockets_found']}\n")
                    f.write(f"平均每蛋白口袋数: {result['avg_pockets_per_protein']:.2f}\n")
                
                elif result['experiment_type'] == 'traineval':
                    f.write(f"训练数据集: {result['training_dataset']}\n")
                    f.write(f"评估数据集: {result['evaluation_dataset']}\n")
                    f.write(f"训练时间: {result['training_time']:.2f}秒\n")
                    f.write(f"评估时间: {result['evaluation_time']:.2f}秒\n")
                    
                    metrics = result['evaluation_metrics']
                    f.write(f"\n评估指标:\n")
                    for metric_name, value in metrics.items():
                        if isinstance(value, (int, float)):
                            f.write(f"  {metric_name}: {value:.3f}\n")
            
            elif metadata['status'] == 'failed':
                f.write(f"失败原因: {metadata.get('error', '未知错误')}\n")
        
        self.logger.info(f"📄 实验报告已生成: {report_file}")
        return str(report_file)


def main():
    """主函数"""
    
    parser = argparse.ArgumentParser(description="P2Rank Python 实验管理工具")
    parser.add_argument('command', choices=['run', 'list', 'report'], help='执行的命令')
    
    # 运行实验相关参数
    parser.add_argument('--type', choices=['predict', 'train', 'crossval', 'traineval'],
                       help='实验类型')
    parser.add_argument('--config', default='default', help='配置名称')
    parser.add_argument('--dataset', help='数据集路径')
    parser.add_argument('--training-dataset', help='训练数据集路径')
    parser.add_argument('--evaluation-dataset', help='评估数据集路径')
    parser.add_argument('--name', help='实验名称')
    parser.add_argument('--output-dir', default='./experiment_results', help='输出目录')
    parser.add_argument('--results-repo', help='结果Git仓库路径')
    parser.add_argument('--no-push', action='store_true', help='不自动推送到git')
    
    # 实验参数
    parser.add_argument('--folds', type=int, default=5, help='交叉验证折数')
    parser.add_argument('--loop', type=int, default=1, help='重复次数')
    parser.add_argument('--threads', type=int, help='线程数')
    
    args = parser.parse_args()
    
    # 创建实验管理器
    manager = ExperimentManager(
        results_repo_path=args.results_repo,
        output_dir=args.output_dir
    )
    
    if args.command == 'run':
        if not args.type:
            print("❌ 运行实验需要指定类型 (--type)")
            return
        
        # 准备实验参数
        experiment_kwargs = {}
        if args.threads:
            experiment_kwargs['threads'] = args.threads
        if args.folds:
            experiment_kwargs['folds'] = args.folds
        if args.loop:
            experiment_kwargs['loop'] = args.loop
        
        print(f"🧪 运行实验: {args.type}")
        
        result = manager.run_experiment(
            experiment_type=args.type,
            config_name=args.config,
            dataset=args.dataset,
            training_dataset=args.training_dataset,
            evaluation_dataset=args.evaluation_dataset,
            experiment_name=args.name,
            auto_push=not args.no_push,
            **experiment_kwargs
        )
        
        if result['status'] == 'completed':
            print(f"✅ 实验完成: {result['experiment_name']}")
            print(f"⏱️  耗时: {result['duration']:.2f}秒")
        else:
            print(f"❌ 实验失败: {result['experiment_name']}")
            print(f"错误: {result.get('error', '未知错误')}")
    
    elif args.command == 'list':
        print("📋 实验列表:")
        experiments = manager.list_experiments()
        
        if not experiments:
            print("  (无实验记录)")
            return
        
        for exp in experiments:
            status_icon = "✅" if exp['status'] == 'completed' else "❌"
            duration = exp.get('duration', 0)
            print(f"  {status_icon} {exp['experiment_name']} ({exp['experiment_type']}) - {duration:.1f}s")
    
    elif args.command == 'report':
        if not args.name:
            print("❌ 生成报告需要指定实验名称 (--name)")
            return
        
        try:
            report_file = manager.generate_experiment_report(args.name)
            print(f"📄 实验报告已生成: {report_file}")
        except FileNotFoundError as e:
            print(f"❌ {e}")
    
    print(f"\n💾 结果保存在: {args.output_dir}")


if __name__ == "__main__":
    main()
