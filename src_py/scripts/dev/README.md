# P2Rank Python 开发工具

本目录包含P2Rank Python的开发工具，移植并增强自原始的shell脚本。

## 📋 工具概览

| 工具 | 功能 | 原始脚本 |
|------|------|----------|
| `experiment.py` | 实验管理和自动化 | `experiment.sh` |
| `git_tools.py` | Git版本控制工具 | `commit.sh`, `push.sh`, `update.sh` |
| `log_colorizer.py` | 日志着色工具 | `logc.sh` |

## 🧪 实验管理工具

### **快速使用**

```bash
# 运行预测实验
python scripts/dev/experiment.py run \
    --type predict \
    --dataset chen11_test.ds \
    --config default \
    --name my_prediction_test

# 运行训练评估实验
python scripts/dev/experiment.py run \
    --type traineval \
    --training-dataset chen11_train.ds \
    --evaluation-dataset chen11_test.ds \
    --config train_default

# 运行交叉验证
python scripts/dev/experiment.py run \
    --type crossval \
    --dataset chen11.ds \
    --folds 5 \
    --loop 3
```

### **实验类型**

- **predict**: 预测实验 - 在数据集上运行预测
- **train**: 训练实验 - 训练新模型
- **crossval**: 交叉验证 - 运行k折交叉验证
- **traineval**: 训练评估 - 训练并评估模型

### **自动Git推送**

```bash
# 启用自动推送 (需要配置结果仓库)
python scripts/dev/experiment.py run \
    --type predict \
    --dataset test.ds \
    --results-repo ../p2rank-results

# 禁用自动推送
python scripts/dev/experiment.py run \
    --type predict \
    --dataset test.ds \
    --no-push
```

### **Python API**

```python
from scripts.dev import ExperimentManager

# 创建实验管理器
manager = ExperimentManager(
    results_repo_path="../p2rank-results",
    output_dir="./my_experiments"
)

# 运行预测实验
result = manager.run_experiment(
    experiment_type='predict',
    config_name='default',
    dataset='chen11_test.ds',
    experiment_name='my_test',
    threads=8
)

# 检查结果
if result['status'] == 'completed':
    print(f"实验成功! 耗时: {result['duration']:.2f}秒")
else:
    print(f"实验失败: {result['error']}")
```

## 🔧 Git工具

### **快速使用**

```bash
# 提交变更
python scripts/dev/git_tools.py commit -m "添加新功能"

# 推送变更
python scripts/dev/git_tools.py push

# 提交并推送 (组合操作)
python scripts/dev/git_tools.py commit-push -m "修复bug"

# 更新仓库
python scripts/dev/git_tools.py update

# 查看状态
python scripts/dev/git_tools.py status

# 创建标签
python scripts/dev/git_tools.py tag --tag-name v1.0.0 --tag-message "发布版本1.0.0"

# 查看提交日志
python scripts/dev/git_tools.py log --count 5
```

### **高级功能**

```bash
# 只推送当前分支 (不推送所有分支)
python scripts/dev/git_tools.py push --no-all-branches

# 推送时不包含标签
python scripts/dev/git_tools.py push --no-tags

# 更新后不自动构建
python scripts/dev/git_tools.py update --no-build

# 提交时不自动添加所有文件
python scripts/dev/git_tools.py commit -m "部分提交" --no-add
```

### **Python API**

```python
from scripts.dev import GitTools

# 创建Git工具
git = GitTools(repo_path="./my_project")

# 提交变更
success = git.commit("修复重要bug", add_all=True)

# 推送变更
if success:
    git.push(push_all_branches=True, push_tags=True)

# 获取状态
status = git.status()
print(f"当前分支: {status['current_branch']}")
print(f"是否有变更: {status['has_changes']}")

# 更新仓库
git.update(build_after_update=True)

# 创建标签
git.create_tag("v1.1.0", "新版本发布")
```

## 🎨 日志着色工具

### **基础使用**

```bash
# 从管道读取并着色
cat logfile.txt | python scripts/dev/log_colorizer.py

# P2Rank专用着色模式
python your_script.py 2>&1 | python scripts/dev/log_colorizer.py --p2rank

# 处理文件
python scripts/dev/log_colorizer.py --input logfile.txt --output colored_log.txt

# 禁用颜色 (用于重定向)
cat logfile.txt | python scripts/dev/log_colorizer.py --no-color > output.txt
```

### **着色演示**

```bash
# 查看着色效果演示
python scripts/dev/log_colorizer.py --demo

# P2Rank专用演示
python scripts/dev/log_colorizer.py --demo --p2rank
```

### **自定义着色模式**

```json
# custom_patterns.json
{
    "\\bCUSTOM\\b": "BRIGHT_GREEN",
    "\\d+\\.\\d+ms": "CYAN",
    "\\berror\\b": "BRIGHT_RED"
}
```

```bash
python scripts/dev/log_colorizer.py --patterns custom_patterns.json
```

### **支持的日志级别**

- **FATAL**: 亮红色
- **ERROR**: 亮红色
- **WARN/WARNING**: 亮黄色
- **INFO**: 亮白色
- **DEBUG**: 亮青色
- **TRACE**: 亮绿色

### **P2Rank特有模式**

- **进度指示**: `1/10`, `50.0%` - 亮蓝色
- **时间信息**: `10:30:15`, `1.23s`, `500ms` - 青色
- **文件格式**: `.pdb`, `.cif`, `.ds` - 绿色
- **性能指标**: `DCA_4_0`, `DCC_4_0` - 亮紫色
- **状态指示**: `SUCCESS`, `FAILED` - 绿色/红色
- **阶段标识**: `TRAINING`, `PREDICTION` - 亮蓝色

### **Python API**

```python
from scripts.dev import LogColorizer, P2RankLogColorizer

# 基础着色器
colorizer = LogColorizer(enable_colors=True)
colored_line = colorizer.colorize_line("2024-01-15 INFO Processing...")

# P2Rank专用着色器
p2rank_colorizer = P2RankLogColorizer()
p2rank_colorizer.colorize_stream()  # 从stdin读取

# 自定义模式
custom_patterns = {
    r'\bMY_PATTERN\b': Color.BRIGHT_MAGENTA
}
custom_colorizer = LogColorizer(custom_patterns=custom_patterns)
```

## 📊 输出结果

### **实验结果目录结构**

```
experiment_results/
├── my_prediction_test/
│   ├── experiment_metadata.json      # 实验元数据
│   ├── experiment_report.txt         # 人类可读报告
│   ├── protein1_predictions.csv      # 预测结果
│   ├── protein2_predictions.csv
│   └── ...
├── crossval_test/
│   ├── experiment_metadata.json
│   ├── crossvalidation_results.json  # 交叉验证详细结果
│   └── experiment_report.txt
└── training_experiment/
    ├── experiment_metadata.json
    ├── trained_model.pkl              # 训练的模型
    ├── evaluation_results.json        # 评估结果
    └── experiment_report.txt
```

### **Git操作状态反馈**

```bash
$ python scripts/dev/git_tools.py status
📂 当前分支: develop
📝 变更文件:
  M  src_py/p2rank/prediction/predictor.py
  A  src_py/new_feature.py
  D  old_file.py

$ python scripts/dev/git_tools.py commit-push -m "添加新功能"
🔧 执行: git add --all
📝 提交变更: 添加新功能
🔧 执行: git commit -m 添加新功能
📤 推送变更到远程仓库...
🌿 推送所有分支...
🏷️  推送标签...
✅ 推送成功
🎉 提交并推送完成!
```

## ⚙️ 配置选项

### **实验管理配置**

- `--output-dir`: 实验结果输出目录
- `--results-repo`: 结果Git仓库路径 (用于自动推送)
- `--no-push`: 禁用自动Git推送
- `--config`: P2Rank配置名称
- `--threads`: 线程数

### **Git工具配置**

- `--repo-path`: Git仓库路径
- `--no-add`: 提交时不自动添加文件
- `--no-all-branches`: 只推送当前分支
- `--no-tags`: 不推送标签
- `--no-build`: 更新后不构建

### **日志着色配置**

- `--no-color`: 禁用颜色输出
- `--p2rank`: 使用P2Rank专用着色模式
- `--patterns`: 自定义模式文件路径

## 🔄 与原始脚本的对应关系

### **experiment.sh → experiment.py**

**原始功能**:
```bash
./prank.sh "$@"
if [ $? -eq 0 ]; then
    echo EXPERIMENT WENT OK. Pushing results to git...
    ( cd ../p2rank-results && git-push )
fi
```

**Python增强**:
- 支持多种实验类型 (predict, train, crossval, traineval)
- 详细的实验元数据记录
- 自动生成实验报告
- 智能错误处理和恢复
- 灵活的配置参数传递

### **commit.sh + push.sh → git_tools.py**

**原始功能**:
```bash
# commit.sh
git commit -m "$MSG"

# push.sh
git add --all
./commit.sh "$1"
git push --all
git push --tags
```

**Python增强**:
- 组合操作 (commit-push)
- 智能状态检查
- 更好的错误处理
- 支持部分提交和推送
- 详细的操作反馈

### **update.sh → git_tools.py**

**原始功能**:
```bash
git pull
HEAD2=`git log -n 1 | head -n 1`
if [ "$HEAD1" != "$HEAD2" ]; then 
    ./gradlew clean assemble
fi
```

**Python增强**:
- 智能构建检测 (setup.py, pyproject.toml, requirements.txt)
- P2Rank项目特定构建流程
- 更好的错误处理和日志
- 可配置的构建行为

### **logc.sh → log_colorizer.py**

**原始功能**:
```bash
cat | awk -W interactive '
/ERROR/ { print "\033[1;31m" $0 "\033[0m"; next; }
/WARN/  { print "\033[1;33m" $0 "\033[0m"; next; }
# ...
'
```

**Python增强**:
- 更丰富的着色模式
- P2Rank专用模式
- 自定义模式支持
- 更好的正则表达式支持
- 演示和测试功能

## 🛠️ 开发者指南

### **添加新的实验类型**

```python
# 在 ExperimentManager 中添加新方法
def _run_custom_experiment(self, config_name: str, dataset: str,
                          output_dir: Path, **kwargs) -> Dict[str, Any]:
    # 实现自定义实验逻辑
    pass

# 在 run_experiment 中添加分支
elif experiment_type == 'custom':
    result = self._run_custom_experiment(
        config_name, dataset, experiment_output, **kwargs
    )
```

### **扩展Git工具功能**

```python
# 在 GitTools 中添加新方法
def advanced_operation(self, param: str) -> bool:
    """高级Git操作"""
    try:
        self._run_git_command(['custom-command', param])
        return True
    except subprocess.CalledProcessError:
        return False
```

### **自定义日志着色模式**

```python
# 创建项目特定的着色器
class MyProjectColorizer(LogColorizer):
    def __init__(self):
        custom_patterns = {
            r'\bMY_KEYWORD\b': Color.BRIGHT_GREEN,
            r'\d+\.\d+MB': Color.CYAN
        }
        super().__init__(custom_patterns=custom_patterns)
```

## 📚 更多资源

- **实验管理**: 查看 `experiment.py` 的详细API文档
- **Git工具**: 参考 `git_tools.py` 的使用示例
- **日志着色**: 查看 `log_colorizer.py` 的模式定义
- **问题报告**: 通过GitHub Issues报告问题

---

*P2Rank Python 开发工具 - 提升开发效率和体验*
