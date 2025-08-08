# P2Rank Distro 目录分析报告

## 📁 Distro 目录作用概述

`distro` 目录是 P2Rank 的**分发包**（Distribution Package），包含了可以直接运行的 P2Rank 完整版本，用户下载后无需编译源码即可使用。这是一个**开箱即用**的完整产品包。

## 🏗️ Distro 目录结构分析

```
distro/
├── prank              # Linux/Mac 启动脚本 (Java)
├── prank.bat          # Windows 启动脚本 (Java)
├── LICENSE.txt        # 许可证文件
├── config/            # 配置文件目录 (Groovy 格式)
│   ├── default.groovy           # 默认预测配置
│   ├── default_rescore.groovy   # 默认重评分配置
│   ├── alphafold.groovy         # AlphaFold 模型配置
│   ├── conservation_hmm.groovy  # 保守性HMM配置
│   ├── rescore_2024.groovy      # 2024重评分配置
│   └── ...
├── models/            # 预训练模型目录
│   ├── default/               # 默认模型
│   │   ├── model.zst         # 压缩的模型文件 (22MB)
│   │   └── features.txt      # 特征列表文件
│   ├── alphafold/            # AlphaFold专用模型
│   ├── conservation_hmm/     # 保守性HMM模型
│   ├── rescore_2024/        # 2024重评分模型
│   └── _score_transform/    # 分数转换器
├── test_data/         # 测试数据和数据集
│   ├── *.pdb, *.cif         # 测试蛋白质结构
│   ├── *.ds                 # 数据集定义文件
│   ├── clean/               # 清洁的蛋白质结构
│   ├── liganated/          # 含配体的蛋白质结构
│   ├── predictions/        # 预测结果示例
│   └── apoholo/           # APO-HOLO 配对数据
└── doc/               # 文档目录
    └── dataset-file-format.md
```

## 🔄 需要移植到 Python 版本的内容

### ✅ 1. 启动脚本 (高优先级)

#### 原始 Java 版本
```bash
# distro/prank (Bash)
export JAVA_OPTS="$JAVA_OPTS -Xmx2048m"
CLASSPATH="${INSTALL_DIR}/bin/p2rank.jar${PATH_SEPARATOR}${INSTALL_DIR}/bin/lib/*"
"$JAVACMD" $JAVA_OPTS -cp "${CLASSPATH}" cz.siret.prank.program.Main "$@"
```

#### 需要创建的 Python 版本
- **`src_py/distro_py/p2rank_py`** - Linux/Mac Python 启动脚本
- **`src_py/distro_py/p2rank_py.bat`** - Windows Python 启动脚本
- **`src_py/distro_py/p2rank_py.py`** - 跨平台 Python 启动器

### ✅ 2. 配置文件系统 (高优先级)

#### 原始 Groovy 配置格式
```groovy
import cz.siret.prank.program.params.Params
(params as Params).with {
    model = "default"
    seed = 42
    parallel = true
    threads = Runtime.getRuntime().availableProcessors() + 1
    features = ["chem","volsite","protrusion","bfactor"]
}
```

#### 需要转换为 YAML 格式
```yaml
# src_py/distro_py/config/default.yaml
model: "default"
seed: 42
parallel: true
threads: -1  # -1 表示自动检测CPU核心数
features:
  - "chem"
  - "volsite"
  - "protrusion" 
  - "bfactor"
```

### ✅ 3. 模型文件适配 (中优先级)

#### 当前模型格式
- **模型文件**: `model.zst` (压缩的 Java 序列化格式)
- **特征文件**: `features.txt` (纯文本列表)

#### 需要适配的内容
- **模型加载器**: 创建从 Java 模型到 Python 模型的转换器
- **特征映射**: 确保特征提取的一致性
- **模型格式**: 可能需要转换为 `.pkl`, `.joblib` 或 `.json` 格式

### ✅ 4. 测试数据集成 (低优先级)

#### 当前数据格式
- **数据集文件**: `.ds` 格式（简单的文件路径列表）
- **蛋白质结构**: `.pdb`, `.cif` 格式
- **压缩格式**: `.gz`, `.zst` 压缩

#### Python 版本适配
- 保持相同的数据格式（无需修改）
- 确保 Python 版本能正确解析 `.ds` 文件
- 添加压缩文件支持

## 🚀 Python Distro 创建计划

### 阶段 1: 基础分发结构
```bash
src_py/distro_py/
├── p2rank_py                    # 主启动脚本
├── p2rank_py.bat               # Windows启动脚本
├── p2rank_py.py                # Python启动器
├── LICENSE.txt                 # 许可证
├── requirements.txt            # Python依赖
├── config/                     # YAML配置文件
│   ├── default.yaml
│   ├── alphafold.yaml
│   ├── conservation_hmm.yaml
│   └── ...
├── models/                     # Python模型文件
│   ├── default/
│   │   ├── model.pkl          # Python模型格式
│   │   ├── scaler.pkl         # 特征缩放器
│   │   └── features.yaml      # 特征配置
│   └── ...
├── test_data/                  # 测试数据（符号链接）
└── doc/                        # 文档
```

### 阶段 2: 配置文件转换

#### 需要转换的配置文件
1. **`default.groovy`** → **`default.yaml`**
2. **`alphafold.groovy`** → **`alphafold.yaml`**
3. **`conservation_hmm.groovy`** → **`conservation_hmm.yaml`**
4. **`rescore_2024.groovy`** → **`rescore_2024.yaml`**

#### 转换示例
```python
# 配置文件转换工具
def convert_groovy_to_yaml(groovy_file: str, yaml_file: str):
    # 解析 Groovy 配置
    # 转换为 YAML 格式
    # 保存 Python 兼容的配置
```

### 阶段 3: 模型文件适配

#### 模型转换需求
1. **Java Random Forest** → **scikit-learn RandomForest**
2. **特征提取器** → Python 特征提取管道
3. **分数转换器** → Python 分数变换器

#### 模型转换工具
```python
# tools/convert_models.py
class ModelConverter:
    def convert_java_model(self, java_model_path: str, python_model_path: str):
        # 读取 Java 模型
        # 转换为 Python 格式
        # 保存为 .pkl 或 .joblib
```

### 阶段 4: 启动脚本创建

#### Linux/Mac 启动脚本
```bash
#!/usr/bin/env bash
# src_py/distro_py/p2rank_py

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH}"

# 检查 Python 版本
python3 -c "import sys; sys.exit(0 if sys.version_info >= (3,8) else 1)" || {
    echo "Error: Python 3.8+ is required"
    exit 1
}

# 运行 Python 版本的 P2Rank
python3 "${SCRIPT_DIR}/p2rank_py.py" "$@"
```

#### Python 启动器
```python
#!/usr/bin/env python3
# src_py/distro_py/p2rank_py.py

import sys
import os
from pathlib import Path

# 添加 P2Rank 到 Python 路径
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

# 导入并运行主程序
from p2rank.program.main import main

if __name__ == "__main__":
    main()
```

## 📋 实施优先级

### 🔴 高优先级 (立即实施)
1. **启动脚本创建** - 用户运行 Python 版本的入口
2. **基础配置转换** - 从 Groovy 转为 YAML
3. **目录结构建立** - 创建 Python 分发目录

### 🟡 中优先级 (后续实施)
1. **模型文件转换** - Java 模型适配为 Python
2. **高级配置支持** - 复杂参数的完整转换
3. **分数转换器** - 输出分数标准化

### 🟢 低优先级 (可选实施)
1. **测试数据优化** - 压缩和索引优化
2. **文档完善** - Python 版本的使用文档
3. **打包脚本** - 自动化分发包生成

## 🎯 预期效果

完成 Python Distro 后，用户将能够：

1. **快速部署**: `wget` 下载即用，无需安装开发环境
2. **简单运行**: `./p2rank_py predict -f protein.pdb`
3. **配置灵活**: YAML 配置文件，易于理解和修改
4. **模型兼容**: 与原始 Java 版本输出结果一致
5. **性能优化**: 利用 Python 科学计算生态的性能优势

## 📊 与原版对比

| 方面 | Java 版本 | Python 版本 | 优势 |
|------|-----------|-------------|------|
| **启动方式** | `./prank predict` | `./p2rank_py predict` | 统一接口 |
| **配置格式** | Groovy | YAML | 更易读写 |
| **依赖管理** | JAR 包 | pip/conda | 生态丰富 |
| **模型格式** | Java 序列化 | Python pickle | 原生支持 |
| **性能** | JVM 优化 | NumPy/SciPy | 向量化计算 |
| **扩展性** | Java 生态 | Python 生态 | ML/科学计算 |

这个分析显示了将 distro 目录适配到 Python 版本的完整路径和优先级，为后续的实施提供了清晰的指导。 