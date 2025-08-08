# P2Rank Python - 超参数优化教程

P2Rank Python提供现代化的超参数优化功能，支持网格搜索、随机搜索、贝叶斯优化等多种策略。

## 🎯 优化策略对比

| 策略 | 适用场景 | 优点 | 缺点 |
|------|---------|------|------|
| **网格搜索** | 1-3个参数 | 全面覆盖、可视化好 | 计算量大、维度诅咒 |
| **随机搜索** | 3-6个参数 | 效率高、易实现 | 可能错过最优解 |
| **贝叶斯优化** | 6+个参数 | 智能搜索、高效 | 复杂、需要更多依赖 |
| **超参数组合** | 复杂优化 | 综合优势 | 设置复杂 |

## 🔧 1. 网格搜索优化

### **基础网格搜索**

```python
from p2rank.optimization import GridSearchOptimizer
import numpy as np

def basic_grid_search():
    """基础网格搜索示例"""
    
    # 定义参数网格
    param_grid = {
        'rf_trees': [50, 100, 200],
        'rf_depth': [8, 10, 12, 15],
        'neighbourhood_radius': [6.0, 8.0, 10.0],
        'positive_point_ligand_distance': [2.0, 2.5, 3.0]
    }
    
    # 初始化优化器
    optimizer = GridSearchOptimizer(
        base_config="train_default",
        cv_folds=3,           # 3折交叉验证
        n_jobs=2,             # 并行任务数
        scoring='DCA_4_0',    # 优化目标指标
        verbose=True
    )
    
    # 运行优化
    results = optimizer.optimize(
        dataset="chen11.ds",
        param_grid=param_grid,
        save_all_results=True,
        plot_results=True
    )
    
    print(f"最佳参数: {results.best_params_}")
    print(f"最佳得分: {results.best_score_:.3f}")
    
    return results

# 使用示例
if __name__ == "__main__":
    results = basic_grid_search()
```

### **参数类型支持**

```python
# 数值参数 - 范围表达式
numerical_params = {
    'rf_trees': list(range(50, 201, 50)),        # [50, 100, 150, 200]
    'neighbourhood_radius': np.arange(6.0, 12.1, 2.0),  # [6.0, 8.0, 10.0, 12.0]
    'positive_point_ligand_distance': np.linspace(2.0, 4.0, 5)  # [2.0, 2.5, 3.0, 3.5, 4.0]
}

# 布尔参数
boolean_params = {
    'cache_datasets': [True, False],
    'balance_class_weights': [True, False],
    'fail_fast': [True, False]
}

# 字符串参数 
string_params = {
    'classifier': ['RandomForestClassifier', 'ExtraTreesClassifier', 'GradientBoostingClassifier'],
    'weight_function': ['INV_DIST', 'INV_DIST2', 'GAUSS']
}

# 列表参数 (特征组合)
list_params = {
    'feature_groups': [
        ['protrusion', 'bfactor', 'volsite'],
        ['protrusion', 'bfactor'],
        ['protrusion'],
        ['bfactor', 'volsite'],
        []  # 无特征 (仅用于测试)
    ]
}

# 综合参数网格
comprehensive_grid = {
    **numerical_params,
    **boolean_params, 
    **string_params
}
```

### **智能网格生成**

```python
from p2rank.optimization import SmartGridGenerator

def generate_smart_grid():
    """智能参数网格生成"""
    
    generator = SmartGridGenerator()
    
    # 方法1: 基于参数重要性的网格
    important_grid = generator.generate_importance_based_grid(
        base_config="train_default",
        n_top_params=5,        # 选择5个最重要的参数
        resolution='medium'    # 'low', 'medium', 'high'
    )
    
    # 方法2: 基于参数类型的网格
    typed_grid = generator.generate_typed_grid(
        param_types={
            'model_params': ['rf_trees', 'rf_depth'],
            'feature_params': ['neighbourhood_radius', 'tessellation'],
            'threshold_params': ['positive_point_ligand_distance']
        },
        resolutions={
            'model_params': 'high',
            'feature_params': 'medium', 
            'threshold_params': 'low'
        }
    )
    
    # 方法3: 自适应网格 (基于初步结果调整)
    adaptive_grid = generator.generate_adaptive_grid(
        initial_results=None,  # 第一次为None
        expansion_factor=1.5,  # 扩展因子
        refinement_factor=2    # 细化因子
    )
    
    return important_grid, typed_grid, adaptive_grid
```

## 🎲 2. 随机搜索优化

```python
from p2rank.optimization import RandomSearchOptimizer
from scipy.stats import uniform, randint

def random_search_optimization():
    """随机搜索优化"""
    
    # 定义参数分布
    param_distributions = {
        # 整数参数
        'rf_trees': randint(50, 301),           # 50-300之间的整数
        'rf_depth': randint(8, 21),             # 8-20之间的整数
        
        # 连续参数  
        'neighbourhood_radius': uniform(6.0, 6.0),    # 6.0-12.0之间的浮点数
        'positive_point_ligand_distance': uniform(2.0, 2.0),  # 2.0-4.0之间
        
        # 离散选择
        'classifier': ['RandomForestClassifier', 'ExtraTreesClassifier', 'GradientBoostingClassifier'],
        'weight_function': ['INV_DIST', 'INV_DIST2', 'GAUSS']
    }
    
    optimizer = RandomSearchOptimizer(
        base_config="train_default",
        cv_folds=3,
        n_iter=100,           # 随机尝试100组参数
        n_jobs=4,
        scoring='DCA_4_0',
        random_state=42
    )
    
    results = optimizer.optimize(
        dataset="chen11.ds",
        param_distributions=param_distributions,
        early_stopping=True,    # 早停机制
        patience=10            # 10次无改进后停止
    )
    
    return results
```

## 🧠 3. 贝叶斯优化

```python
from p2rank.optimization import BayesianOptimizer
from skopt import gp_minimize
from skopt.space import Real, Integer, Categorical

def bayesian_optimization():
    """贝叶斯优化 - 智能超参数搜索"""
    
    # 定义搜索空间
    search_space = [
        Integer(50, 300, name='rf_trees'),
        Integer(8, 20, name='rf_depth'),
        Real(6.0, 12.0, name='neighbourhood_radius'),
        Real(2.0, 4.0, name='positive_point_ligand_distance'),
        Categorical(['RandomForestClassifier', 'ExtraTreesClassifier'], name='classifier'),
        Real(0.1, 1.0, name='target_class_ratio'),
        Integer(1, 4, name='tessellation')
    ]
    
    optimizer = BayesianOptimizer(
        base_config="train_default",
        search_space=search_space,
        cv_folds=3,
        acquisition_function='EI',  # Expected Improvement
        n_initial_points=10,        # 初始随机点数
        random_state=42
    )
    
    # 运行贝叶斯优化
    results = optimizer.optimize(
        dataset="chen11.ds",
        n_calls=50,              # 总优化步数
        callback=optimizer.checkpoint_callback,  # 保存中间结果
        verbose=True
    )
    
    # 分析优化过程
    optimizer.plot_convergence()      # 收敛图
    optimizer.plot_objective()        # 目标函数图
    optimizer.plot_evaluations()      # 参数评估图
    
    return results

def advanced_bayesian_optimization():
    """高级贝叶斯优化 - 多目标优化"""
    
    from p2rank.optimization import MultiObjectiveBayesianOptimizer
    
    # 多目标优化 (例如: 同时优化DCA和速度)
    optimizer = MultiObjectiveBayesianOptimizer(
        base_config="train_default",
        objectives=['DCA_4_0', 'training_time'],  # 多个目标
        objective_weights=[0.8, -0.2],           # 权重 (负权重表示最小化)
        cv_folds=3
    )
    
    results = optimizer.optimize(
        dataset="chen11.ds",
        search_space=search_space,
        n_calls=50,
        pareto_analysis=True    # 帕累托前沿分析
    )
    
    return results
```

## 📊 4. 结果可视化和分析

```python
from p2rank.optimization import OptimizationAnalyzer
import matplotlib.pyplot as plt
import seaborn as sns

def analyze_optimization_results(results):
    """优化结果分析和可视化"""
    
    analyzer = OptimizationAnalyzer(results)
    
    # 1. 参数重要性分析
    param_importance = analyzer.analyze_parameter_importance()
    
    plt.figure(figsize=(10, 6))
    plt.barh(param_importance.index, param_importance.values)
    plt.title('Parameter Importance')
    plt.xlabel('Importance Score')
    plt.tight_layout()
    plt.savefig('param_importance.png')
    plt.show()
    
    # 2. 参数相关性分析
    correlation_matrix = analyzer.analyze_parameter_correlations()
    
    plt.figure(figsize=(8, 6))
    sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0)
    plt.title('Parameter Correlations')
    plt.tight_layout()
    plt.savefig('param_correlations.png')
    plt.show()
    
    # 3. 优化路径可视化
    analyzer.plot_optimization_path()
    plt.savefig('optimization_path.png')
    
    # 4. 参数vs性能散点图
    analyzer.plot_parameter_vs_performance('rf_trees', 'DCA_4_0')
    plt.savefig('trees_vs_performance.png')
    
    # 5. 收敛分析
    analyzer.plot_convergence_analysis()
    plt.savefig('convergence_analysis.png')
    
    return analyzer

def generate_optimization_report(results):
    """生成优化报告"""
    
    analyzer = OptimizationAnalyzer(results)
    
    report = {
        'best_params': results.best_params_,
        'best_score': results.best_score_,
        'total_evaluations': len(results.cv_results_),
        'optimization_time': results.total_time_,
        'parameter_importance': analyzer.analyze_parameter_importance().to_dict(),
        'stability_analysis': analyzer.analyze_result_stability(),
        'recommendations': analyzer.generate_recommendations()
    }
    
    # 保存报告
    import json
    with open('optimization_report.json', 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print("📊 Optimization Report Generated:")
    print(f"  Best Score: {report['best_score']:.3f}")
    print(f"  Total Evaluations: {report['total_evaluations']}")
    print(f"  Optimization Time: {report['optimization_time']}")
    print(f"  Top 3 Important Params: {list(report['parameter_importance'].keys())[:3]}")
    
    return report
```

## 🎯 5. 专项优化场景

### **快速原型优化**

```python
def quick_prototype_optimization():
    """快速原型优化 - 5分钟内获得不错的参数"""
    
    from p2rank.optimization import QuickOptimizer
    
    optimizer = QuickOptimizer(
        base_config="train_default",
        time_budget=300,        # 5分钟时间预算
        quality_target=0.85     # 达到85%最优性能即停止
    )
    
    # 自动选择重要参数和优化策略
    results = optimizer.auto_optimize(
        dataset="chen11.ds",
        strategy='adaptive',    # 自适应策略
        verbose=True
    )
    
    print(f"⚡ Quick optimization completed in {results.optimization_time:.1f} seconds")
    print(f"🎯 Achieved {results.quality_ratio:.1%} of estimated optimal performance")
    
    return results

def production_optimization():
    """生产环境优化 - 追求最佳性能"""
    
    from p2rank.optimization import ProductionOptimizer
    
    optimizer = ProductionOptimizer(
        base_config="train_default",
        cv_folds=5,             # 更严格的验证
        n_repeats=3,            # 重复验证
        ensemble_evaluation=True # 集成评估
    )
    
    # 多阶段优化策略
    results = optimizer.multi_stage_optimize(
        dataset="chen11.ds",
        stages=[
            {'method': 'random', 'n_iter': 50},      # 阶段1: 随机搜索
            {'method': 'bayesian', 'n_iter': 100},   # 阶段2: 贝叶斯优化
            {'method': 'local_search', 'n_iter': 20} # 阶段3: 局部搜索
        ]
    )
    
    return results
```

### **内存受限优化**

```python
def memory_constrained_optimization():
    """内存受限环境的优化策略"""
    
    # 内存友好的参数网格
    memory_friendly_grid = {
        'rf_trees': [50, 100],           # 减少树的数量
        'rf_depth': [8, 10],             # 限制深度
        'cache_datasets': [False],       # 禁用缓存
        'batch_size': [500, 1000],       # 小批处理
        'memory_efficient': [True],      # 启用内存效率模式
    }
    
    optimizer = GridSearchOptimizer(
        base_config="train_default",
        cv_folds=2,              # 减少折数
        n_jobs=1,                # 串行处理
        memory_limit='4GB'       # 内存限制
    )
    
    results = optimizer.optimize(
        dataset="chen11_small.ds",  # 使用较小的数据集
        param_grid=memory_friendly_grid,
        progressive_evaluation=True  # 渐进式评估
    )
    
    return results
```

## 📈 6. 实际优化工作流

```python
#!/usr/bin/env python3
"""
P2Rank Python 完整超参数优化工作流
"""

from p2rank.optimization import OptimizationPipeline
import logging

def main_optimization_workflow():
    """完整的优化工作流"""
    
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    print("🚀 Starting P2Rank Python Hyperparameter Optimization")
    
    # 1. 初始化优化管道
    pipeline = OptimizationPipeline(
        base_config="train_default",
        dataset="chen11.ds",
        output_dir="./optimization_results"
    )
    
    # 2. 第一阶段: 快速筛选
    print("\n📋 Phase 1: Quick Parameter Screening...")
    phase1_results = pipeline.run_quick_screening(
        n_random_samples=20,
        important_params_only=True
    )
    
    # 3. 第二阶段: 精细优化  
    print("\n🎯 Phase 2: Fine-grained Optimization...")
    phase2_results = pipeline.run_bayesian_optimization(
        initial_points=phase1_results.get_top_k(5),
        n_calls=50,
        acquisition_function='EI'
    )
    
    # 4. 第三阶段: 稳定性验证
    print("\n🔍 Phase 3: Stability Validation...")
    final_results = pipeline.validate_stability(
        best_params=phase2_results.best_params_,
        n_repeats=10,
        cv_folds=5
    )
    
    # 5. 结果分析和报告
    print("\n📊 Generating comprehensive report...")
    report = pipeline.generate_full_report(
        include_plots=True,
        include_recommendations=True,
        save_models=True
    )
    
    # 6. 最终模型训练
    print("\n🏗️ Training final optimized model...")
    final_model = pipeline.train_final_model(
        params=final_results.best_params_,
        full_dataset=True,
        save_model=True
    )
    
    print(f"\n🎉 Optimization completed!")
    print(f"📈 Best Score: {final_results.best_score_:.3f}")
    print(f"⏱️  Total Time: {pipeline.total_time_:.1f} seconds")
    print(f"💾 Results saved to: {pipeline.output_dir}")
    
    return final_results, final_model

if __name__ == "__main__":
    results, model = main_optimization_workflow()
```

## 🛠️ 7. 配置文件优化

### **优化配置模板**

```yaml
# optimization_config.yaml
optimization:
  # 基础设置
  base_config: "train_default"
  dataset: "chen11.ds"
  scoring: "DCA_4_0"
  cv_folds: 3
  n_jobs: 4
  random_state: 42
  
  # 搜索策略
  strategy: "bayesian"  # grid, random, bayesian, adaptive
  
  # 参数空间定义
  param_space:
    rf_trees: 
      type: "integer"
      range: [50, 300]
      distribution: "uniform"
    
    rf_depth:
      type: "integer" 
      range: [8, 20]
      
    neighbourhood_radius:
      type: "real"
      range: [6.0, 12.0]
      
    classifier:
      type: "categorical"
      choices: ["RandomForestClassifier", "ExtraTreesClassifier"]
  
  # 优化设置
  grid_search:
    exhaustive: false
    max_combinations: 1000
    
  random_search:
    n_iter: 100
    early_stopping: true
    patience: 10
    
  bayesian_search:
    n_calls: 50
    n_initial_points: 10
    acquisition_function: "EI"
    
  # 结果设置
  output:
    save_all_results: true
    plot_results: true
    generate_report: true
    save_best_model: true

# 使用配置文件
from p2rank.optimization import ConfigurableOptimizer

optimizer = ConfigurableOptimizer.from_yaml("optimization_config.yaml")
results = optimizer.run()
```

## 📋 8. 最佳实践建议

### **优化策略选择**

```python
def choose_optimization_strategy(n_params, time_budget, quality_requirement):
    """根据条件选择最佳优化策略"""
    
    if n_params <= 2 and time_budget > 3600:  # 1小时+
        return "grid_search"
    elif n_params <= 5 and time_budget > 1800:  # 30分钟+
        return "random_search" 
    elif n_params > 5 or quality_requirement > 0.95:
        return "bayesian_optimization"
    else:
        return "quick_prototype"

# 参数重要性指导
PARAMETER_IMPORTANCE = {
    'critical': ['rf_trees', 'rf_depth', 'neighbourhood_radius'],
    'important': ['positive_point_ligand_distance', 'tessellation'],
    'moderate': ['weight_function', 'target_class_ratio'],
    'minor': ['cache_datasets', 'fail_fast']
}

def prioritize_parameters(time_budget):
    """根据时间预算确定优化参数优先级"""
    
    if time_budget < 600:  # 10分钟以内
        return PARAMETER_IMPORTANCE['critical'][:2]
    elif time_budget < 1800:  # 30分钟以内
        return PARAMETER_IMPORTANCE['critical'] + PARAMETER_IMPORTANCE['important'][:1]
    else:
        return PARAMETER_IMPORTANCE['critical'] + PARAMETER_IMPORTANCE['important']
```

---

## 🎯 总结

P2Rank Python的超参数优化系统提供了：

- ✅ **多种优化策略**: 网格搜索、随机搜索、贝叶斯优化
- ✅ **智能参数选择**: 基于重要性的自动参数筛选
- ✅ **丰富的可视化**: 优化过程、参数关系、收敛分析
- ✅ **生产就绪**: 稳定性验证、完整报告、模型保存
- ✅ **灵活配置**: YAML配置文件、多种API接口

通过合理选择优化策略和参数，可以显著提升P2Rank模型的预测性能！

---

*更多详细信息请参考API文档和示例代码*
