# P2Rank Python 测试脚本

本目录包含P2Rank Python的各种测试脚本，移植自原始的shell脚本。

## 📋 脚本概览

| 脚本 | 功能 | 原始脚本 |
|------|------|----------|
| `benchmark.py` | 性能基准测试 | `benchmark.sh` |
| `standard_benchmarks.py` | 标准基准测试套件 | `standard-benchmarks.sh` |
| `testsets.py` | 测试数据集管理 | `testsets.sh` |

## 🚀 快速使用

### **1. 性能基准测试**

```bash
# 运行标准基准测试套件
python scripts/testing/benchmark.py --mode standard

# 自定义预测基准测试
python scripts/testing/benchmark.py \
    --mode prediction \
    --dataset chen11_test.ds \
    --threads 1 2 4 8 \
    --repetitions 5

# 训练性能测试
python scripts/testing/benchmark.py \
    --mode training \
    --dataset chen11_train.ds \
    --repetitions 3
```

### **2. 标准基准测试套件**

```bash
# 完整标准测试套件
python scripts/testing/standard_benchmarks.py --mode full

# 快速测试套件
python scripts/testing/standard_benchmarks.py --mode quick

# 查看详细帮助
python scripts/testing/standard_benchmarks.py --help
```

### **3. 数据集管理**

```bash
# 发现可用数据集
python scripts/testing/testsets.py discover --datasets-dir ./datasets

# 验证数据集完整性
python scripts/testing/testsets.py validate --datasets chen11 u48

# 测试预测功能
python scripts/testing/testsets.py test-prediction \
    --datasets chen11_test u48 \
    --max-proteins 5
```

## 🔧 Python API 使用

### **基准测试 API**

```python
from scripts.testing import P2RankBenchmark

# 创建基准测试器
benchmark = P2RankBenchmark(output_dir="./my_benchmarks")

# 预测性能测试
results = benchmark.benchmark_prediction(
    dataset_file="chen11_test.ds",
    config_name="default",
    repetitions=5,
    thread_counts=[1, 2, 4, 8],
    label="my_test"
)

# 训练性能测试
training_results = benchmark.benchmark_training(
    training_dataset="chen11_train.ds",
    evaluation_dataset="chen11_test.ds",
    repetitions=3,
    thread_counts=[1, 4, 8]
)
```

### **标准测试套件 API**

```python
from scripts.testing import StandardBenchmarkSuite

# 创建标准测试套件
suite = StandardBenchmarkSuite(output_dir="./standard_tests")

# 运行所有标准测试
results = suite.run_all_standard_tests()

# 分析结果
for test_name, result in results['test_results'].items():
    if 'error' not in result:
        print(f"{test_name}: 测试成功")
    else:
        print(f"{test_name}: 测试失败 - {result['error']}")
```

### **数据集管理 API**

```python
from scripts.testing import TestsetManager

# 创建数据集管理器
manager = TestsetManager(
    datasets_dir="./datasets",
    output_dir="./testset_results"
)

# 发现数据集
datasets = manager.discover_datasets()
print(f"发现 {len(datasets)} 个数据集")

# 验证数据集
validation_results = manager.validate_datasets(['chen11', 'u48'])

# 测试预测
test_results = manager.test_prediction_on_datasets(
    dataset_names=['chen11_test'],
    config_name="default",
    max_proteins=3
)
```

## 📊 输出结果

### **基准测试输出**

```
benchmark_results/
├── my_test_results.json          # 详细结果数据
├── my_test_report.txt            # 人类可读的报告
├── benchmark.log                 # 执行日志
└── comprehensive_benchmark_report.txt  # 综合报告
```

### **标准测试套件输出**

```
standard_benchmark_results/
├── standard_benchmark_suite_results.json  # 完整结果
├── standard_benchmark_suite_report.txt    # 套件报告
├── individual_test_results/               # 各个测试的详细结果
│   ├── quick_prediction_u48_results.json
│   ├── training_performance_results.json
│   └── ...
└── standard_benchmarks.log               # 执行日志
```

### **数据集管理输出**

```
testset_results/
├── discovered_datasets.json              # 发现的数据集
├── dataset_validation_results.json       # 验证结果
├── dataset_validation_report.txt         # 验证报告
├── prediction_test_results.json          # 预测测试结果
├── prediction_test_report.txt            # 预测测试报告
└── testsets.log                          # 执行日志
```

## ⚙️ 配置选项

### **基准测试配置**

- `--repetitions`: 重复次数 (默认: 5)
- `--threads`: 线程数列表 (默认: [1, 2, 4, 8])
- `--config`: P2Rank配置名称 (默认: "default")
- `--output-dir`: 输出目录 (默认: "./benchmark_results")

### **数据集管理配置**

- `--datasets-dir`: 数据集目录 (默认: "./datasets")
- `--max-proteins`: 每数据集最大测试蛋白质数 (默认: 3)
- `--config`: 预测配置 (默认: "default")

## 🧪 测试类型

### **1. 性能基准测试**

- **预测性能**: 测试不同线程数下的预测速度
- **训练性能**: 测试模型训练的时间和并行效率
- **内存使用**: 监控内存消耗模式
- **准确性验证**: 验证预测结果的准确性

### **2. 数据集测试**

- **完整性检查**: 验证数据集文件和蛋白质文件的存在性
- **格式验证**: 检查数据集格式的正确性
- **预测测试**: 在数据集上运行预测以验证功能
- **性能分析**: 分析不同数据集的性能特征

### **3. 标准化测试**

- **回归测试**: 确保新版本不会降低性能
- **兼容性测试**: 验证与不同配置的兼容性
- **压力测试**: 测试极限条件下的表现
- **集成测试**: 验证整个流水线的正确性

## 📈 性能指标

### **时间指标**

- **平均时间**: 多次运行的平均时间
- **标准差**: 时间稳定性指标
- **最小/最大时间**: 性能范围
- **加速比**: 多线程相对于单线程的加速效果

### **准确性指标**

- **DCA_4_0**: 4Å距离阈值下的检测准确率
- **DCC_4_0**: 4Å距离阈值下的检测覆盖率
- **成功率**: 预测成功完成的比例
- **错误率**: 预测失败的比例

### **资源指标**

- **内存使用**: 峰值和平均内存消耗
- **CPU利用率**: 处理器使用效率
- **磁盘I/O**: 文件读写性能
- **并行效率**: 多线程扩展性

## 🔍 故障排除

### **常见问题**

1. **数据集文件不存在**
   ```bash
   # 检查数据集目录
   python scripts/testing/testsets.py discover --datasets-dir /path/to/datasets
   ```

2. **内存不足**
   ```bash
   # 使用内存效率配置
   python scripts/testing/benchmark.py --config memory_efficient
   ```

3. **线程数过多**
   ```bash
   # 限制线程数
   python scripts/testing/benchmark.py --threads 1 2 4
   ```

### **调试模式**

```bash
# 启用详细日志
export PYTHONPATH=/path/to/src_py
python -v scripts/testing/benchmark.py --mode standard

# 查看日志文件
tail -f benchmark_results/benchmark.log
```

## 📚 更多资源

- **API文档**: 查看各个类的详细API文档
- **配置文档**: 了解P2Rank配置系统
- **性能优化**: 参考性能优化指南
- **问题报告**: 通过GitHub Issues报告问题

---

*P2Rank Python 测试脚本 - 确保代码质量和性能*
