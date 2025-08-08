# P2Rank Java to Python Model Conversion Guide

## 🎯 概述

本指南说明如何将 P2Rank 的 Java Random Forest 模型转换为 Python scikit-learn 格式，以便在 Python 版本的 P2Rank 中使用。

## 🏗️ 转换工具架构

### 核心组件

1. **`JavaModelAnalyzer`** - 分析 Java 模型文件
2. **`JavaModelConverter`** - 转换模型格式  
3. **`ModelValidator`** - 验证转换正确性
4. **`P2RankModelManager`** - 统一管理接口

### 工具文件结构

```
src_py/tools/
├── __init__.py
├── model_analyzer.py      # Java模型分析器
├── model_converter.py     # 模型转换器
├── model_validator.py     # 模型验证器
└── model_manager.py       # 统一管理接口
```

## 🚀 快速开始

### 1. 安装依赖

```bash
cd src_py
pip install -r requirements.txt
```

### 2. 运行演示

```bash
# 完整演示
python demo_model_conversion.py ../distro/models converted_models/

# 分步演示
python demo_model_conversion.py ../distro/models converted_models/ --demo analysis
python demo_model_conversion.py ../distro/models converted_models/ --demo conversion
python demo_model_conversion.py ../distro/models converted_models/ --demo validation
```

### 3. 使用管理工具

```bash
# 分析所有 Java 模型
python tools/model_manager.py analyze ../distro/models converted_models/

# 转换所有模型
python tools/model_manager.py convert ../distro/models converted_models/

# 验证转换结果
python tools/model_manager.py validate ../distro/models converted_models/

# 完整流水线
python tools/model_manager.py pipeline ../distro/models converted_models/
```

## 📋 详细使用说明

### 模型分析 (model_analyzer.py)

```python
from tools.model_analyzer import JavaModelAnalyzer

# 初始化分析器
analyzer = JavaModelAnalyzer("../distro/models")

# 列出可用模型
models = analyzer.list_available_models()
print(f"可用模型: {models}")

# 分析特定模型
model_info = analyzer.get_model_info("default")
print(f"特征数量: {len(model_info['features'])}")
print(f"模型大小: {model_info['model_size_mb']} MB")

# 生成详细报告
report = analyzer.generate_model_report("default")
```

### 模型转换 (model_converter.py)

```python
from tools.model_converter import JavaModelConverter
import numpy as np

# 初始化转换器
converter = JavaModelConverter("../distro/models", "converted_models")

# 准备训练数据 (可选 - 用于重新训练)
# 如果没有训练数据，将创建结构等效的未训练模型
X_train = np.random.randn(10000, 35)  # 35个特征
y_train = np.random.binomial(1, 0.3, 10000)  # 二分类标签

# 转换模型
model, metadata = converter.convert_model("default", X_train, y_train)

# 转换所有模型
results = converter.convert_all_models()
```

### 模型验证 (model_validator.py)

```python
from tools.model_validator import ModelValidator

# 初始化验证器
validator = ModelValidator("../distro/models", "converted_models")

# 验证特定模型
result = validator.validate_model("default")
print(f"预测相关性: {result.prediction_correlation:.4f}")
print(f"分类准确率: {result.classification_accuracy:.4f}")

# 验证所有模型
results = validator.validate_all_models()

# 生成验证报告
report = validator.generate_validation_report(results, "validation_report.txt")
```

### 统一管理 (model_manager.py)

```python
from tools.model_manager import P2RankModelManager

# 初始化管理器
manager = P2RankModelManager("../distro/models", "converted_models")

# 运行完整流水线
results = manager.full_pipeline()

# 生成总结报告
summary = manager.generate_summary_report(results)
print(summary)

# 安装到分发包
install_results = manager.install_converted_models("distro_py")
```

## ⚙️ 配置参数

### Random Forest 参数映射

| Java P2Rank 参数 | Python scikit-learn 参数 | 默认值 |
|-------------------|---------------------------|--------|
| `rf_trees` | `n_estimators` | 100 |
| `rf_depth` | `max_depth` | 12 |
| `rf_min_split` | `min_samples_split` | 5 |
| `rf_min_leaf` | `min_samples_leaf` | 2 |
| `rf_features` | `max_features` | 'sqrt' |
| `seed` | `random_state` | 42 |

### 特征组映射

| 特征组 | 描述 | 数量 |
|--------|------|------|
| `chem.*` | 化学性质特征 | 24 |
| `volsite.*` | 体积位点特征 | 6 |
| `protrusion.*` | 突出特征 | 1 |
| `bfactor.*` | B因子特征 | 1 |
| `atom_table.*` | 原子表特征 | 3 |

## 📊 转换结果结构

转换后的模型目录结构：

```
converted_models/
├── default/
│   ├── model.pkl              # scikit-learn 模型
│   ├── model.joblib           # 备用格式
│   ├── metadata.json          # 转换元数据
│   ├── features.yaml          # 特征列表
│   └── feature_mapping.json   # 特征映射
├── alphafold/
│   └── ...
└── ...
```

### 元数据格式

```json
{
  "original_model_name": "default",
  "original_file_path": "../distro/models/default/model.zst",
  "features": ["chem.hydrophobic", "chem.hydrophilic", ...],
  "n_features": 35,
  "n_trees": 100,
  "model_type": "RandomForestClassifier",
  "conversion_date": "2024-01-15T10:30:00",
  "converter_version": "1.0.0",
  "notes": "Converted using retrained method"
}
```

## 🧪 验证指标

### 关键指标

1. **特征一致性** - 确保特征数量匹配
2. **预测相关性** - Python 与 Java 模型预测的相关性
3. **预测误差** - RMSE 和 MAE
4. **分类性能** - 准确率、F1 分数

### 解释标准

| 指标 | 优秀 | 良好 | 需要改进 |
|------|------|------|----------|
| 预测相关性 | > 0.9 | > 0.8 | < 0.8 |
| 分类准确率 | > 0.85 | > 0.75 | < 0.75 |
| RMSE | < 0.1 | < 0.2 | > 0.2 |

## 🔧 故障排除

### 常见问题

1. **Java 模型无法解压**
   ```
   错误: Could not decompress model
   解决: 安装 zstandard: pip install zstandard
   ```

2. **特征数量不匹配**
   ```
   错误: Feature count mismatch
   解决: 检查 features.txt 文件和特征提取代码
   ```

3. **预测相关性低**
   ```
   问题: Correlation < 0.8
   解决: 提供更好的训练数据，或调整模型参数
   ```

4. **内存不足**
   ```
   错误: MemoryError during conversion
   解决: 减少训练数据量，或增加系统内存
   ```

### 调试模式

```bash
# 启用详细日志
python demo_model_conversion.py ../distro/models converted_models/ --verbose

# 查看具体错误
python tools/model_manager.py analyze ../distro/models converted_models/ -v
```

## 📈 性能优化

### 加速转换

1. **并行处理**
   ```python
   # 使用多线程
   model = RandomForestClassifier(n_jobs=-1)
   ```

2. **数据预处理**
   ```python
   # 标准化特征
   from sklearn.preprocessing import StandardScaler
   scaler = StandardScaler()
   X_scaled = scaler.fit_transform(X)
   ```

3. **模型压缩**
   ```python
   # 使用 joblib 压缩
   joblib.dump(model, "model.pkl", compress=3)
   ```

### 内存优化

```python
# 分批处理大数据集
chunk_size = 10000
for i in range(0, len(X), chunk_size):
    X_chunk = X[i:i+chunk_size]
    predictions = model.predict(X_chunk)
```

## 🔮 高级功能

### 自定义特征处理

```python
# 创建特征预处理管道
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('classifier', RandomForestClassifier())
])
```

### 模型集成

```python
# 集成多个模型
from sklearn.ensemble import VotingClassifier

ensemble = VotingClassifier([
    ('default', default_model),
    ('alphafold', alphafold_model)
], voting='soft')
```

### 增量学习

```python
# 使用部分训练数据更新模型
model.fit(X_new, y_new)
```

## 📚 集成到 P2Rank Python

### 1. 加载转换后的模型

```python
from sklearn.externals import joblib

# 加载模型
model = joblib.load("converted_models/default/model.pkl")

# 加载元数据
import json
with open("converted_models/default/metadata.json") as f:
    metadata = json.load(f)
```

### 2. 集成到预测流程

```python
def predict_pockets(protein_features):
    """使用转换后的模型预测口袋"""
    
    # 确保特征顺序正确
    features_ordered = reorder_features(protein_features, metadata['features'])
    
    # 预测
    pocket_probabilities = model.predict_proba(features_ordered)[:, 1]
    pocket_predictions = model.predict(features_ordered)
    
    return pocket_predictions, pocket_probabilities
```

### 3. 配置文件更新

在 YAML 配置中指定 Python 模型：

```yaml
# config/default.yaml
model: "default"
model_format: "python"  # 新增字段
model_path: "models/default/model.pkl"
```

## 🎯 总结

Java 到 Python 模型转换流程：

1. **分析** Java 模型结构和特征
2. **转换** 为 scikit-learn 格式
3. **验证** 转换正确性
4. **集成** 到 Python P2Rank

这个转换系统确保了 Python 版本能够获得与 Java 版本一致的预测性能，同时利用了 Python 科学计算生态系统的优势。

有关更多技术细节，请参考各工具模块的源代码和文档字符串。
