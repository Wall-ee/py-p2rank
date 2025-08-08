# P2Rank Python - 教程索引

欢迎使用P2Rank Python教程系统！这里提供了从入门到高级的完整学习资源。

## 📚 教程概览

### 🎯 **核心教程**

| 教程 | 难度 | 预计时间 | 描述 |
|------|------|---------|------|
| [模型训练教程](training_tutorial.md) | 🟢 初级 | 30分钟 | 完整的模型训练和评估流程 |
| [超参数优化](hyperparameter_optimization.md) | 🟡 中级 | 45分钟 | 网格搜索、贝叶斯优化等策略 |
| [特征工程配置](feature_setup.md) | 🟡 中级 | 40分钟 | 特征选择、自定义特征开发 |

### 🛠️ **进阶教程**

| 教程 | 难度 | 预计时间 | 描述 |
|------|------|---------|------|
| 模型部署教程 | 🔴 高级 | 60分钟 | 生产环境部署和优化 |
| API开发指南 | 🔴 高级 | 45分钟 | 构建P2Rank Python API服务 |
| 性能优化指南 | 🔴 高级 | 50分钟 | 内存优化、并行化、GPU加速 |

### 🔬 **专项教程**

| 教程 | 难度 | 预计时间 | 描述 |
|------|------|---------|------|
| 数据集准备 | 🟢 初级 | 20分钟 | 蛋白质数据集的准备和格式化 |
| 可视化教程 | 🟢 初级 | 25分钟 | 结果可视化和ChimeraX/PyMOL脚本 |
| 集成开发 | 🟡 中级 | 35分钟 | 与其他生物信息学工具的集成 |

---

## 🚀 快速开始

### **5分钟快速体验**

```python
# 1. 安装P2Rank Python
pip install p2rank-python

# 2. 基础预测
from p2rank import P2RankPredictor

predictor = P2RankPredictor()
results = predictor.predict("protein.pdb")
print(f"发现 {len(results.pockets)} 个结合位点")

# 3. 保存结果
results.save_visualization("protein_pockets.pml")  # PyMOL脚本
results.save_predictions("protein_predictions.csv")  # 预测结果
```

### **30分钟完整工作流**

```python
# 完整的训练、优化、预测流程
from p2rank import P2RankTrainer, P2RankPredictor, ConfigLoader

# 1. 配置加载
config = ConfigLoader().load_config("train_default")

# 2. 模型训练
trainer = P2RankTrainer(config)
model = trainer.train_model("chen11_train.ds")

# 3. 超参数优化
optimized_params = trainer.optimize_hyperparameters("chen11.ds")

# 4. 最终模型训练
final_model = trainer.train_model("chen11_train.ds", params=optimized_params)

# 5. 预测新蛋白质
predictor = P2RankPredictor(model=final_model)
results = predictor.predict("new_protein.pdb")
```

---

## 🎯 学习路径建议

### **🟢 初学者路径** (2-3小时)

1. **开始**: [模型训练教程](training_tutorial.md)
   - 了解基本概念和工作流程
   - 学会训练和评估模型
   - 掌握配置系统使用

2. **进阶**: 数据集准备教程
   - 学习数据格式和预处理
   - 掌握数据集管理

3. **实践**: 可视化教程
   - 学会结果可视化
   - 掌握PyMOL/ChimeraX使用

### **🟡 中级用户路径** (4-5小时)

1. **特征工程**: [特征工程配置](feature_setup.md)
   - 深入理解特征系统
   - 学会自定义特征开发
   - 掌握特征选择技巧

2. **性能优化**: [超参数优化](hyperparameter_optimization.md)
   - 掌握各种优化策略
   - 学会性能调优
   - 理解模型选择

3. **集成开发**: 集成开发教程
   - 学会工具集成
   - 掌握流水线构建

### **🔴 高级用户路径** (6-8小时)

1. **生产部署**: 模型部署教程
   - 学会生产环境部署
   - 掌握服务化架构
   - 理解监控和维护

2. **API开发**: API开发指南
   - 构建Web API服务
   - 学会微服务架构
   - 掌握容器化部署

3. **性能极致优化**: 性能优化指南
   - GPU加速技术
   - 分布式计算
   - 内存和速度优化

---

## 📖 教程使用说明

### **代码运行环境**

```bash
# 1. 创建虚拟环境
conda create -n p2rank python=3.9
conda activate p2rank

# 2. 安装依赖
cd src_py
pip install -r requirements.txt

# 3. 安装P2Rank Python
pip install -e .

# 4. 验证安装
python -c "import p2rank; print('安装成功!')"
```

### **示例数据下载**

```bash
# 下载示例数据和预训练模型
python -m p2rank download-examples
python -m p2rank download-models

# 数据将保存在当前目录的以下位置:
# ./examples/         # 示例蛋白质文件
# ./models/          # 预训练模型
# ./datasets/        # 示例数据集
```

### **交互式学习**

我们提供了Jupyter Notebook版本的教程：

```bash
# 启动Jupyter环境
pip install jupyter
jupyter notebook

# 在浏览器中打开:
# docs/tutorials/notebooks/
```

---

## 🆘 获取帮助

### **常见问题**

| 问题 | 解决方案 |
|------|---------|
| 导入错误 | 检查虚拟环境和依赖安装 |
| 内存不足 | 参考性能优化教程，调整批处理大小 |
| 训练太慢 | 使用并行训练或减少数据集大小 |
| 结果不理想 | 参考超参数优化教程 |

### **支持渠道**

- 📧 **邮件支持**: p2rank-python@example.com
- 💬 **社区论坛**: [P2Rank Python讨论区](https://github.com/example/p2rank-python/discussions)
- 🐛 **Bug报告**: [GitHub Issues](https://github.com/example/p2rank-python/issues)
- 📚 **API文档**: [在线文档](https://p2rank-python.readthedocs.io)

### **贡献指南**

欢迎贡献新的教程内容！

```bash
# 1. Fork项目
git clone https://github.com/your-username/p2rank-python.git

# 2. 创建教程分支
git checkout -b tutorial/new-feature

# 3. 添加教程内容
# 教程文件格式: docs/tutorials/your_tutorial.md
# 代码示例: examples/your_example.py

# 4. 提交PR
git commit -m "Add new tutorial: Your Tutorial Name"
git push origin tutorial/new-feature
```

---

## 📅 更新日志

### **Version 1.0.0** (当前版本)
- ✅ 核心训练教程
- ✅ 超参数优化教程
- ✅ 特征工程教程
- ✅ 完整代码示例

### **即将发布**
- 🔄 模型部署教程
- 🔄 性能优化指南
- 🔄 API开发指南
- 🔄 Jupyter Notebook版本

---

## 🎉 开始学习

选择适合你水平的教程开始学习吧！

- 🟢 **新手**: 从[模型训练教程](training_tutorial.md)开始
- 🟡 **有经验**: 直接进入[特征工程配置](feature_setup.md)
- 🔴 **专家**: 查看高级优化和部署教程

**祝你学习愉快！** 🚀

---

*P2Rank Python - 现代化的蛋白质结合位点预测工具*
