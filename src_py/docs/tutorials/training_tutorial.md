# P2Rank Python - 模型训练和优化教程

本文档为希望训练和评估自己的模型或优化算法不同参数的用户提供入门指导。

## 🚀 快速开始示例

```python
# Python API 示例
from p2rank import P2RankTrainer, P2RankPredictor, ConfigLoader

# 1. 训练和评估模型
config = ConfigLoader().load_config("train_default")
trainer = P2RankTrainer(config)

# 训练模型
model = trainer.train_model(training_dataset)

# 评估模型
results = trainer.evaluate_model(model, evaluation_dataset)

# 2. 交叉验证
cv_results = trainer.cross_validate(dataset, folds=5, loop=10, seed=42)

# 3. 参数优化循环
param_results = trainer.parameter_loop(
    training_dataset=training_dataset,
    evaluation_dataset=evaluation_dataset,
    param_grid={'rf_trees': [100, 200, 400], 'rf_depth': [8, 12, 16]}
)
```

```bash
# 命令行示例
python -m p2rank train --config train_default.yaml --training-dataset <dataset> --evaluation-dataset <dataset>
python -m p2rank crossval --config train_default.yaml --dataset <dataset> --folds 5
python -m p2rank param-optimize --config train_default.yaml --param-grid params.yaml
```

## ⚙️ 参数配置

P2Rank Python 使用现代的YAML配置系统。配置可以通过以下方式设置：

### 1. **配置文件方式** (推荐)

```python
from p2rank import ConfigLoader

# 加载预定义配置
config = ConfigLoader().load_config("train_default")

# 加载自定义配置文件
config = ConfigLoader().load_config_file("my_config.yaml")

# 程序中修改参数
config.update({
    'rf_trees': 200,
    'rf_depth': 12,
    'threads': 8
})
```

### 2. **配置文件格式** (YAML)

```yaml
# config/train_default.yaml
_extends: "base"

# 模型参数
model:
  classifier: "RandomForestClassifier"
  rf_trees: 100
  rf_depth: 10
  rf_min_samples_split: 2

# 训练参数  
training:
  loop: 10
  seed: 42
  cache_datasets: true
  fail_fast: false

# 特征参数
features:
  tessellation: 2
  train_tessellation: 2
  neighbourhood_radius: 8.0

# 性能参数
performance:
  threads: 4
  n_jobs: -1
```

### 3. **参数优先级** (后者覆盖前者)

1. 基础默认值 (`config/base.yaml`)
2. 算法默认值 (`config/train_default.yaml`)
3. 自定义配置文件
4. 程序中的直接设置
5. 命令行参数

## 🛠️ 环境准备

### **安装要求**

```bash
# 1. 克隆Python版本
git clone <p2rank-python-repo>
cd p2rank-python

# 2. 安装依赖
pip install -r requirements.txt

# 3. 安装P2Rank Python
pip install -e .

# 4. 准备数据集
# 下载或准备蛋白质数据集文件
```

### **环境配置**

```python
# setup_env.py - 环境优化
import os
import psutil
from p2rank.utils import setup_optimal_environment

def setup_p2rank_env():
    """设置P2Rank Python的最优环境"""
    
    # CPU配置
    cpu_count = psutil.cpu_count()
    os.environ["OMP_NUM_THREADS"] = str(cpu_count)
    
    # 内存配置 (Python自动管理，但可以限制某些操作)
    memory_gb = psutil.virtual_memory().total // (1024**3)
    
    print(f"Environment configured:")
    print(f"  CPU cores: {cpu_count}")
    print(f"  Available memory: {memory_gb}GB")
    print(f"  OMP threads: {os.environ.get('OMP_NUM_THREADS')}")
    
    return {
        'threads': min(cpu_count, 8),  # 合理的线程数
        'memory_limit': max(memory_gb * 0.8, 4),  # 80%内存或最少4GB
        'n_jobs': -1  # scikit-learn自动并行
    }
```

## 🎯 训练和评估

### **基础训练流程**

```python
from p2rank import P2RankTrainer, DatasetLoader
import numpy as np

def train_and_evaluate():
    """完整的训练评估流程"""
    
    # 1. 加载配置
    trainer = P2RankTrainer(config_name="train_default")
    
    # 2. 加载数据集
    train_ds = DatasetLoader().load_dataset("chen11_train.ds")
    test_ds = DatasetLoader().load_dataset("chen11_test.ds")
    
    # 3. 多次训练 (不同随机种子)
    results = []
    for seed in range(42, 52):  # 10次运行
        print(f"Training run {seed-41}/10 (seed={seed})")
        
        # 训练模型
        model = trainer.train_model(
            training_dataset=train_ds,
            seed=seed,
            save_model=True,  # 保存模型文件
            export_features=True,  # 导出特征向量
            calculate_feature_importance=True  # 计算特征重要性
        )
        
        # 评估模型
        result = trainer.evaluate_model(model, test_ds)
        results.append(result)
        
        print(f"  DCA_4_0: {result['DCA_4_0']:.3f}")
        print(f"  DCC_4_0: {result['DCC_4_0']:.3f}")
    
    # 4. 统计结果
    avg_results = {
        metric: np.mean([r[metric] for r in results])
        for metric in results[0].keys()
    }
    
    print(f"\nAverage results (10 runs):")
    for metric, value in avg_results.items():
        print(f"  {metric}: {value:.3f}")
    
    return avg_results
```

### **相关参数**

```python
trainer_config = {
    'delete_models': False,      # 保留训练后的模型文件
    'export_features': True,     # 导出特征向量文件
    'feature_importances': True, # 计算特征重要性 (支持RandomForest)
    'fail_fast': False,         # 遇到错误时继续处理其他数据
    'loop': 10,                 # 重复训练次数
    'seed': 42,                 # 随机种子起始值
}
```

## 💾 内存和性能优化

Python版本的内存管理与Java版本不同，但仍有优化空间：

### **关键参数**

```python
performance_config = {
    # 并行训练
    'n_jobs': -1,              # scikit-learn自动并行 (-1=所有CPU)
    'threads': 8,              # 其他计算的线程数
    
    # 内存管理
    'cache_datasets': True,     # 在内存中缓存数据集
    'batch_size': 1000,        # 批处理大小
    'memory_efficient': False,  # 内存效率模式 (较慢但省内存)
    
    # 模型参数
    'rf_trees': 100,           # 随机森林树的数量
    'rf_depth': 10,            # 树的最大深度  
    'rf_min_samples_split': 2, # 分割所需的最小样本数
}
```

### **内存优化策略**

```python
def optimize_for_large_datasets():
    """大数据集优化配置"""
    return {
        'cache_datasets': False,     # 不缓存数据集
        'memory_efficient': True,    # 启用内存效率模式
        'batch_size': 500,          # 较小的批处理
        'n_jobs': 4,                # 限制并行度
        'rf_trees': 50,             # 减少树的数量
    }

def optimize_for_speed():
    """速度优化配置"""
    return {
        'cache_datasets': True,      # 缓存数据集
        'memory_efficient': False,   # 关闭内存效率模式
        'batch_size': 2000,         # 大批处理
        'n_jobs': -1,               # 最大并行度
        'rf_trees': 200,            # 更多树 (更好性能)
    }
```

## 📊 交叉验证

```python
def run_crossvalidation():
    """运行交叉验证"""
    
    trainer = P2RankTrainer(config_name="train_default")
    dataset = DatasetLoader().load_dataset("chen11.ds")
    
    # 运行5折交叉验证，重复10次
    cv_results = trainer.cross_validate(
        dataset=dataset,
        folds=5,           # 5折交叉验证
        loop=10,           # 重复10次  
        seed=42,           # 随机种子
        parallel_folds=2,  # 并行处理的折数 (内存允许的情况下)
        save_models=False, # 不保存每个fold的模型
    )
    
    print("Cross-validation results:")
    for metric, values in cv_results.items():
        mean_val = np.mean(values)
        std_val = np.std(values)
        print(f"  {metric}: {mean_val:.3f} ± {std_val:.3f}")
    
    return cv_results
```

## 🔬 超参数优化

```python
from p2rank import ParameterOptimizer
from sklearn.model_selection import ParameterGrid

def optimize_hyperparameters():
    """超参数网格搜索"""
    
    # 定义参数搜索空间
    param_grid = {
        'rf_trees': [50, 100, 200],
        'rf_depth': [8, 10, 12],
        'neighbourhood_radius': [6.0, 8.0, 10.0],
        'positive_point_ligand_distance': [2.0, 2.5, 3.0],
    }
    
    optimizer = ParameterOptimizer(
        base_config="train_default",
        param_grid=param_grid,
        cv_folds=3,        # 3折验证 (为了速度)
        n_jobs=2,          # 并行优化
        verbose=True
    )
    
    # 运行优化
    best_params, best_score, all_results = optimizer.optimize(
        dataset="chen11.ds",
        metric="DCA_4_0",  # 优化目标指标
        maximize=True      # 最大化指标
    )
    
    print(f"Best parameters: {best_params}")
    print(f"Best score: {best_score:.3f}")
    
    return best_params

# 使用优化后的参数
def use_optimized_params():
    """使用优化后的参数训练最终模型"""
    
    best_params = optimize_hyperparameters()
    
    # 创建优化配置
    config = ConfigLoader().load_config("train_default")
    config.update(best_params)
    
    # 训练最终模型
    trainer = P2RankTrainer(config)
    final_model = trainer.train_model(
        training_dataset="chen11_train.ds",
        seed=42,
        save_model=True,
        model_name="optimized_model"
    )
    
    return final_model
```

## 🏗️ 机器学习算法选择

P2Rank Python支持多种scikit-learn算法：

```python
# 可用的分类器
classifiers = {
    # 随机森林 (默认推荐)
    'RandomForestClassifier': {
        'n_estimators': 100,
        'max_depth': 10,
        'min_samples_split': 2,
        'n_jobs': -1
    },
    
    # 极端随机树 (更快)
    'ExtraTreesClassifier': {
        'n_estimators': 100,
        'max_depth': 10,
        'n_jobs': -1
    },
    
    # 梯度提升 (可能更好的性能)
    'GradientBoostingClassifier': {
        'n_estimators': 100,
        'max_depth': 8,
        'learning_rate': 0.1
    },
    
    # XGBoost (需要安装 xgboost)
    'XGBClassifier': {
        'n_estimators': 100,
        'max_depth': 10,
        'learning_rate': 0.1,
        'n_jobs': -1
    }
}

# 配置中指定分类器
config = {
    'classifier': 'RandomForestClassifier',
    'classifier_params': classifiers['RandomForestClassifier']
}
```

### **性能比较**

| 分类器 | 训练速度 | 预测速度 | 内存使用 | 性能 |
|-------|---------|---------|---------|-----|
| RandomForest | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| ExtraTrees | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| GradientBoosting | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| XGBoost | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

## 📈 特征重要性分析

```python
def analyze_feature_importance():
    """特征重要性分析"""
    
    trainer = P2RankTrainer(config_name="train_default")
    
    # 训练模型并计算特征重要性
    model = trainer.train_model(
        training_dataset="chen11_train.ds",
        calculate_feature_importance=True,
        feature_importance_method='permutation'  # 'impurity' 或 'permutation'
    )
    
    # 获取特征重要性
    feature_names = trainer.get_feature_names()
    importance_scores = model.feature_importances_
    
    # 排序并显示
    feature_importance = list(zip(feature_names, importance_scores))
    feature_importance.sort(key=lambda x: x[1], reverse=True)
    
    print("Top 10 most important features:")
    for i, (feature, score) in enumerate(feature_importance[:10]):
        print(f"{i+1:2d}. {feature:30s} {score:.4f}")
    
    # 保存结果
    import pandas as pd
    df = pd.DataFrame(feature_importance, columns=['Feature', 'Importance'])
    df.to_csv('feature_importances.csv', index=False)
    
    return feature_importance
```

## 🎯 类别不平衡处理

处理正负样本不平衡问题：

```python
class_balance_config = {
    # 采样策略
    'subsample': True,           # 启用子采样
    'supersample': False,        # 禁用超采样
    'target_class_ratio': 0.3,   # 目标正负样本比例
    
    # 权重平衡
    'balance_class_weights': True,     # 启用类别权重平衡
    'target_class_weight_ratio': 2.0,  # 正样本权重倍数
    
    # 采样密度
    'tessellation': 2,                    # 表面点密度
    'train_tessellation_negatives': 1,    # 负样本训练密度
    
    # 距离阈值
    'positive_point_ligand_distance': 2.5,  # 正样本距离阈值
    'neutral_points_margin': 1.0,           # 中性点边际
}
```

## 📂 输出目录组织

```python
output_config = {
    'output_base_dir': './results',      # 基础输出目录
    'out_subdir': 'training_runs',       # 子目录
    'out_prefix_date': True,             # 添加时间戳前缀
    'label': 'experiment_1',             # 实验标签
    'save_predictions': True,            # 保存预测结果
    'save_visualizations': True,         # 保存可视化文件
}

# 最终输出路径示例:
# ./results/training_runs/20241208_150423_experiment_1/
```

## 🚀 完整工作流示例

```python
#!/usr/bin/env python3
"""
P2Rank Python 完整训练工作流示例
"""

from p2rank import P2RankTrainer, ConfigLoader, DatasetLoader
import logging

def main():
    """主要训练工作流"""
    
    # 1. 设置日志
    logging.basicConfig(level=logging.INFO)
    
    # 2. 加载和自定义配置
    config = ConfigLoader().load_config("train_default")
    config.update({
        'rf_trees': 200,
        'loop': 5,
        'threads': 8,
        'output_base_dir': './my_training_results'
    })
    
    # 3. 初始化训练器
    trainer = P2RankTrainer(config)
    
    # 4. 加载数据集
    train_ds = DatasetLoader().load_dataset("chen11_train.ds")
    test_ds = DatasetLoader().load_dataset("chen11_test.ds")
    
    print("🚀 Starting P2Rank Python training...")
    
    # 5. 运行训练和评估
    results = trainer.train_and_evaluate(
        training_dataset=train_ds,
        evaluation_dataset=test_ds,
        save_models=True,
        calculate_feature_importance=True
    )
    
    # 6. 显示结果
    print(f"\n🎉 Training completed!")
    print(f"📊 Final results:")
    for metric, value in results.items():
        print(f"  {metric}: {value:.3f}")
    
    # 7. 保存最佳模型
    best_model = trainer.get_best_model()
    trainer.save_model(best_model, "final_model.pkl")
    
    print(f"💾 Best model saved as 'final_model.pkl'")

if __name__ == "__main__":
    main()
```

---

## 📚 更多资源

- **配置参考**: 查看 `config/` 目录下的YAML配置文件
- **API文档**: 查看 `docs/api/` 目录
- **示例脚本**: 查看 `examples/` 目录  
- **特征工程**: 参考 `feature_setup.md`
- **超参数优化**: 参考 `hyperparameter_optimization.md`

---

*P2Rank Python - 现代化的蛋白质结合位点预测工具*
