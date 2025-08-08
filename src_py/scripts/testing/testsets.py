#!/usr/bin/env python3
"""
P2Rank Python 测试集管理工具
移植自原始的 testsets.sh

用于管理和验证P2Rank测试数据集
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys
import time

# 添加p2rank路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from p2rank.utils import DatasetLoader
from p2rank import P2RankPredictor, ConfigLoader


class TestsetManager:
    """测试集管理器"""
    
    def __init__(self, datasets_dir: str = "./datasets", output_dir: str = "./testset_results"):
        self.datasets_dir = Path(datasets_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # 设置日志
        self.setup_logging()
        
        # 数据集加载器
        self.dataset_loader = DatasetLoader()
        
    def setup_logging(self):
        """设置日志系统"""
        log_file = self.output_dir / "testsets.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def discover_datasets(self) -> Dict[str, Dict[str, Any]]:
        """发现可用的数据集"""
        
        self.logger.info("🔍 发现数据集...")
        
        datasets = {}
        
        # 搜索数据集文件
        dataset_patterns = ['*.ds', '*.csv', '*.txt']
        
        for pattern in dataset_patterns:
            for dataset_file in self.datasets_dir.glob(f"**/{pattern}"):
                if dataset_file.is_file():
                    try:
                        # 尝试加载数据集以验证格式
                        dataset_info = self._analyze_dataset(dataset_file)
                        datasets[dataset_file.stem] = dataset_info
                        self.logger.info(f"  ✅ 发现数据集: {dataset_file.name}")
                    except Exception as e:
                        self.logger.warning(f"  ⚠️  跳过无效数据集 {dataset_file.name}: {e}")
        
        self.logger.info(f"📊 总共发现 {len(datasets)} 个有效数据集")
        
        # 保存发现结果
        discovery_file = self.output_dir / "discovered_datasets.json"
        with open(discovery_file, 'w', encoding='utf-8') as f:
            json.dump(datasets, f, indent=2, ensure_ascii=False, default=str)
        
        return datasets
    
    def _analyze_dataset(self, dataset_file: Path) -> Dict[str, Any]:
        """分析单个数据集"""
        
        try:
            dataset = self.dataset_loader.load_dataset(str(dataset_file))
            
            info = {
                'file_path': str(dataset_file),
                'file_size_mb': dataset_file.stat().st_size / (1024 * 1024),
                'protein_count': len(dataset.protein_files),
                'format': dataset_file.suffix,
                'created_time': dataset_file.stat().st_ctime,
                'modified_time': dataset_file.stat().st_mtime,
                'status': 'valid'
            }
            
            # 样本分析
            if dataset.protein_files:
                sample_proteins = dataset.protein_files[:3]
                info['sample_proteins'] = [str(p) for p in sample_proteins]
                
                # 检查蛋白质文件是否存在
                existing_proteins = 0
                for protein_file in dataset.protein_files:
                    if Path(protein_file).exists():
                        existing_proteins += 1
                
                info['existing_proteins'] = existing_proteins
                info['missing_proteins'] = len(dataset.protein_files) - existing_proteins
                info['completeness'] = existing_proteins / len(dataset.protein_files)
            
            return info
            
        except Exception as e:
            return {
                'file_path': str(dataset_file),
                'status': 'invalid',
                'error': str(e)
            }
    
    def validate_datasets(self, dataset_names: Optional[List[str]] = None) -> Dict[str, Dict[str, Any]]:
        """验证数据集完整性"""
        
        self.logger.info("🔍 验证数据集...")
        
        # 发现数据集
        discovered = self.discover_datasets()
        
        # 筛选要验证的数据集
        if dataset_names:
            datasets_to_validate = {name: info for name, info in discovered.items() 
                                  if name in dataset_names}
        else:
            datasets_to_validate = discovered
        
        validation_results = {}
        
        for dataset_name, dataset_info in datasets_to_validate.items():
            self.logger.info(f"\n🧪 验证数据集: {dataset_name}")
            
            validation_result = self._validate_single_dataset(dataset_name, dataset_info)
            validation_results[dataset_name] = validation_result
            
            # 显示验证结果
            status = validation_result['overall_status']
            if status == 'pass':
                self.logger.info(f"  ✅ {dataset_name}: 验证通过")
            elif status == 'warning':
                self.logger.warning(f"  ⚠️  {dataset_name}: 有警告")
            else:
                self.logger.error(f"  ❌ {dataset_name}: 验证失败")
        
        # 保存验证结果
        validation_file = self.output_dir / "dataset_validation_results.json"
        with open(validation_file, 'w', encoding='utf-8') as f:
            json.dump(validation_results, f, indent=2, ensure_ascii=False, default=str)
        
        # 生成验证报告
        self._generate_validation_report(validation_results)
        
        return validation_results
    
    def _validate_single_dataset(self, dataset_name: str, dataset_info: Dict[str, Any]) -> Dict[str, Any]:
        """验证单个数据集"""
        
        validation = {
            'dataset_name': dataset_name,
            'validation_time': time.time(),
            'checks': {},
            'issues': [],
            'warnings': [],
            'overall_status': 'pass'
        }
        
        # 检查1: 基本文件存在性
        dataset_file = Path(dataset_info['file_path'])
        validation['checks']['file_exists'] = dataset_file.exists()
        if not validation['checks']['file_exists']:
            validation['issues'].append("数据集文件不存在")
            validation['overall_status'] = 'fail'
            return validation
        
        try:
            # 检查2: 数据集可加载性
            dataset = self.dataset_loader.load_dataset(str(dataset_file))
            validation['checks']['loadable'] = True
            
            # 检查3: 蛋白质文件完整性
            protein_files = dataset.protein_files
            existing_count = 0
            missing_files = []
            
            for protein_file in protein_files:
                if Path(protein_file).exists():
                    existing_count += 1
                else:
                    missing_files.append(str(protein_file))
            
            completeness = existing_count / len(protein_files) if protein_files else 1.0
            validation['checks']['protein_completeness'] = completeness
            validation['checks']['missing_protein_files'] = missing_files[:10]  # 最多显示10个
            
            if completeness < 0.5:
                validation['issues'].append(f"蛋白质文件缺失过多 (完整性: {completeness:.1%})")
                validation['overall_status'] = 'fail'
            elif completeness < 0.9:
                validation['warnings'].append(f"部分蛋白质文件缺失 (完整性: {completeness:.1%})")
                if validation['overall_status'] == 'pass':
                    validation['overall_status'] = 'warning'
            
            # 检查4: 数据集大小合理性
            if len(protein_files) == 0:
                validation['issues'].append("数据集为空")
                validation['overall_status'] = 'fail'
            elif len(protein_files) < 3:
                validation['warnings'].append(f"数据集太小 (仅{len(protein_files)}个蛋白质)")
                if validation['overall_status'] == 'pass':
                    validation['overall_status'] = 'warning'
            
            validation['checks']['protein_count'] = len(protein_files)
            
            # 检查5: 蛋白质文件格式
            if protein_files:
                sample_file = Path(protein_files[0])
                if sample_file.exists():
                    validation['checks']['protein_format'] = sample_file.suffix
                    if sample_file.suffix not in ['.pdb', '.cif', '.ent']:
                        validation['warnings'].append(f"未知蛋白质文件格式: {sample_file.suffix}")
                        if validation['overall_status'] == 'pass':
                            validation['overall_status'] = 'warning'
        
        except Exception as e:
            validation['checks']['loadable'] = False
            validation['issues'].append(f"数据集加载失败: {str(e)}")
            validation['overall_status'] = 'fail'
        
        return validation
    
    def test_prediction_on_datasets(self, dataset_names: List[str], 
                                  config_name: str = "default",
                                  max_proteins: int = 3) -> Dict[str, Any]:
        """在数据集上测试预测功能"""
        
        self.logger.info("🎯 测试数据集预测功能...")
        
        # 加载预测器
        config = ConfigLoader().load_config(config_name)
        predictor = P2RankPredictor(config)
        
        test_results = {
            'test_time': time.time(),
            'config': config_name,
            'max_proteins_per_dataset': max_proteins,
            'dataset_results': {}
        }
        
        for dataset_name in dataset_names:
            self.logger.info(f"\n🧪 测试数据集: {dataset_name}")
            
            try:
                # 查找数据集文件
                dataset_file = self._find_dataset_file(dataset_name)
                if not dataset_file:
                    self.logger.error(f"  ❌ 未找到数据集: {dataset_name}")
                    continue
                
                # 加载数据集
                dataset = self.dataset_loader.load_dataset(str(dataset_file))
                proteins_to_test = dataset.protein_files[:max_proteins]
                
                dataset_result = {
                    'dataset_file': str(dataset_file),
                    'total_proteins': len(dataset.protein_files),
                    'tested_proteins': len(proteins_to_test),
                    'protein_results': {},
                    'summary': {'successful': 0, 'failed': 0}
                }
                
                # 测试每个蛋白质
                for i, protein_file in enumerate(proteins_to_test):
                    self.logger.info(f"  预测蛋白质 {i+1}/{len(proteins_to_test)}: {Path(protein_file).name}")
                    
                    try:
                        if not Path(protein_file).exists():
                            raise FileNotFoundError(f"蛋白质文件不存在: {protein_file}")
                        
                        start_time = time.time()
                        prediction_result = predictor.predict(str(protein_file))
                        prediction_time = time.time() - start_time
                        
                        protein_result = {
                            'status': 'success',
                            'prediction_time': prediction_time,
                            'pocket_count': len(prediction_result.pockets),
                            'file_size_mb': Path(protein_file).stat().st_size / (1024 * 1024)
                        }
                        
                        dataset_result['summary']['successful'] += 1
                        self.logger.info(f"    ✅ 成功 - 发现{len(prediction_result.pockets)}个口袋 ({prediction_time:.2f}s)")
                        
                    except Exception as e:
                        protein_result = {
                            'status': 'failed',
                            'error': str(e)
                        }
                        dataset_result['summary']['failed'] += 1
                        self.logger.error(f"    ❌ 失败: {e}")
                    
                    dataset_result['protein_results'][Path(protein_file).name] = protein_result
                
                # 计算数据集成功率
                total_tested = dataset_result['summary']['successful'] + dataset_result['summary']['failed']
                dataset_result['success_rate'] = dataset_result['summary']['successful'] / total_tested if total_tested > 0 else 0
                
                test_results['dataset_results'][dataset_name] = dataset_result
                
                self.logger.info(f"  📊 数据集结果: {dataset_result['summary']['successful']}/{total_tested} 成功")
                
            except Exception as e:
                self.logger.error(f"  ❌ 数据集测试失败: {e}")
                test_results['dataset_results'][dataset_name] = {
                    'status': 'failed',
                    'error': str(e)
                }
        
        # 保存测试结果
        test_file = self.output_dir / "prediction_test_results.json"
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_results, f, indent=2, ensure_ascii=False, default=str)
        
        # 生成测试报告
        self._generate_prediction_test_report(test_results)
        
        return test_results
    
    def _find_dataset_file(self, dataset_name: str) -> Optional[Path]:
        """查找数据集文件"""
        
        # 尝试不同的扩展名
        extensions = ['.ds', '.csv', '.txt']
        
        for ext in extensions:
            dataset_file = self.datasets_dir / f"{dataset_name}{ext}"
            if dataset_file.exists():
                return dataset_file
        
        # 递归搜索
        for ext in extensions:
            for dataset_file in self.datasets_dir.glob(f"**/{dataset_name}{ext}"):
                if dataset_file.is_file():
                    return dataset_file
        
        return None
    
    def _generate_validation_report(self, validation_results: Dict[str, Any]):
        """生成验证报告"""
        
        report_file = self.output_dir / "dataset_validation_report.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("P2Rank Python 数据集验证报告\n")
            f.write("=" * 50 + "\n\n")
            
            # 总结统计
            total_datasets = len(validation_results)
            passed = sum(1 for r in validation_results.values() if r['overall_status'] == 'pass')
            warned = sum(1 for r in validation_results.values() if r['overall_status'] == 'warning')
            failed = sum(1 for r in validation_results.values() if r['overall_status'] == 'fail')
            
            f.write(f"验证总结:\n")
            f.write(f"  总数据集: {total_datasets}\n")
            f.write(f"  通过: {passed}\n")
            f.write(f"  警告: {warned}\n")
            f.write(f"  失败: {failed}\n")
            f.write(f"  成功率: {(passed + warned) / total_datasets:.1%}\n\n")
            
            # 详细结果
            f.write("详细验证结果:\n")
            f.write("-" * 30 + "\n")
            
            for dataset_name, result in validation_results.items():
                f.write(f"\n{dataset_name.upper()}:\n")
                f.write(f"  状态: {result['overall_status'].upper()}\n")
                
                if result['issues']:
                    f.write("  问题:\n")
                    for issue in result['issues']:
                        f.write(f"    - {issue}\n")
                
                if result['warnings']:
                    f.write("  警告:\n")
                    for warning in result['warnings']:
                        f.write(f"    - {warning}\n")
                
                # 检查详情
                checks = result['checks']
                if 'protein_count' in checks:
                    f.write(f"  蛋白质数量: {checks['protein_count']}\n")
                if 'protein_completeness' in checks:
                    f.write(f"  完整性: {checks['protein_completeness']:.1%}\n")
        
        self.logger.info(f"📄 验证报告已生成: {report_file}")
    
    def _generate_prediction_test_report(self, test_results: Dict[str, Any]):
        """生成预测测试报告"""
        
        report_file = self.output_dir / "prediction_test_report.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("P2Rank Python 数据集预测测试报告\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"测试配置: {test_results['config']}\n")
            f.write(f"每数据集最大测试蛋白质数: {test_results['max_proteins_per_dataset']}\n\n")
            
            # 总结统计
            total_datasets = len(test_results['dataset_results'])
            successful_datasets = 0
            total_proteins_tested = 0
            total_successful_predictions = 0
            
            for dataset_result in test_results['dataset_results'].values():
                if isinstance(dataset_result, dict) and 'summary' in dataset_result:
                    if dataset_result['summary']['successful'] > 0:
                        successful_datasets += 1
                    total_proteins_tested += dataset_result.get('tested_proteins', 0)
                    total_successful_predictions += dataset_result['summary']['successful']
            
            f.write("测试总结:\n")
            f.write(f"  测试数据集: {total_datasets}\n")
            f.write(f"  成功数据集: {successful_datasets}\n")
            f.write(f"  总测试蛋白质: {total_proteins_tested}\n")
            f.write(f"  成功预测: {total_successful_predictions}\n")
            if total_proteins_tested > 0:
                f.write(f"  预测成功率: {total_successful_predictions / total_proteins_tested:.1%}\n")
            f.write("\n")
            
            # 详细结果
            f.write("详细测试结果:\n")
            f.write("-" * 30 + "\n")
            
            for dataset_name, result in test_results['dataset_results'].items():
                f.write(f"\n{dataset_name.upper()}:\n")
                
                if 'error' in result:
                    f.write(f"  状态: 失败\n")
                    f.write(f"  错误: {result['error']}\n")
                    continue
                
                f.write(f"  总蛋白质: {result['total_proteins']}\n")
                f.write(f"  测试蛋白质: {result['tested_proteins']}\n")
                f.write(f"  成功预测: {result['summary']['successful']}\n")
                f.write(f"  失败预测: {result['summary']['failed']}\n")
                f.write(f"  成功率: {result['success_rate']:.1%}\n")
        
        self.logger.info(f"📄 预测测试报告已生成: {report_file}")


def main():
    """主函数"""
    
    parser = argparse.ArgumentParser(description="P2Rank Python 测试集管理工具")
    parser.add_argument('command', choices=['discover', 'validate', 'test-prediction'], 
                       help='执行的命令')
    parser.add_argument('--datasets-dir', default='./datasets', help='数据集目录')
    parser.add_argument('--output-dir', default='./testset_results', help='输出目录')
    parser.add_argument('--datasets', nargs='+', help='指定数据集名称')
    parser.add_argument('--config', default='default', help='预测配置')
    parser.add_argument('--max-proteins', type=int, default=3, help='每数据集最大测试蛋白质数')
    
    args = parser.parse_args()
    
    # 创建管理器
    manager = TestsetManager(datasets_dir=args.datasets_dir, output_dir=args.output_dir)
    
    if args.command == 'discover':
        print("🔍 发现数据集...")
        datasets = manager.discover_datasets()
        print(f"📊 发现 {len(datasets)} 个数据集")
        
        for name, info in datasets.items():
            status = "✅" if info['status'] == 'valid' else "❌"
            print(f"  {status} {name}: {info.get('protein_count', 'N/A')} 蛋白质")
    
    elif args.command == 'validate':
        print("🔍 验证数据集...")
        results = manager.validate_datasets(dataset_names=args.datasets)
        
        # 显示验证总结
        passed = sum(1 for r in results.values() if r['overall_status'] == 'pass')
        warned = sum(1 for r in results.values() if r['overall_status'] == 'warning')
        failed = sum(1 for r in results.values() if r['overall_status'] == 'fail')
        
        print(f"\n📊 验证结果: {passed} 通过, {warned} 警告, {failed} 失败")
    
    elif args.command == 'test-prediction':
        if not args.datasets:
            print("❌ 测试预测需要指定数据集 (--datasets)")
            return
        
        print(f"🎯 测试预测功能: {args.datasets}")
        results = manager.test_prediction_on_datasets(
            dataset_names=args.datasets,
            config_name=args.config,
            max_proteins=args.max_proteins
        )
        
        # 显示测试总结
        successful_datasets = 0
        for result in results['dataset_results'].values():
            if isinstance(result, dict) and 'summary' in result:
                if result['summary']['successful'] > 0:
                    successful_datasets += 1
        
        print(f"\n📊 测试结果: {successful_datasets}/{len(args.datasets)} 数据集测试成功")
    
    print(f"\n💾 结果保存在: {args.output_dir}")


if __name__ == "__main__":
    main()
