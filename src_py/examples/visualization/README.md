# P2Rank Python 可视化示例

本目录包含P2Rank Python可视化系统的示例和演示。

## 📁 目录结构

```
examples/visualization/
├── predict_1fbl/                    # 1FBL蛋白质预测示例
│   ├── 1fbl.pdb_predictions.csv    # 口袋预测结果
│   ├── 1fbl.pdb_residues.csv       # 残基级别结果  
│   ├── params.txt                  # 预测参数
│   └── visualizations/             # 可视化脚本
│       ├── 1fbl.pdb_pymol.pml      # PyMOL脚本
│       ├── 1fbl.pdb_chimerax.cxc   # ChimeraX脚本
│       └── data/                   # 数据文件
│           ├── 1fbl.pdb            # 蛋白质结构
│           └── 1fbl.pdb_points.pdb.gz # 表面点
├── predict_1fbl_TES3/              # 1FBL蛋白质(TES3配置)示例
│   └── ... (同上结构)
├── visualization_demo.py           # 完整演示脚本
└── README.md                       # 本文件
```

## 🎯 示例说明

### **1FBL蛋白质预测示例**

`predict_1fbl/` 目录包含了对1FBL蛋白质的完整预测结果：

- **预测结果**: 发现了4个结合位点，分数从9.77到1.87
- **可视化脚本**: 包含PyMOL和ChimeraX两种格式
- **数据完整性**: 包含原始数据和处理后的可视化数据

### **预测结果摘要**

| 口袋 | 排名 | 分数 | 概率 | 中心坐标 |
|------|------|------|------|----------|
| pocket1 | 1 | 9.77 | 0.525 | (70.5, 83.4, -11.5) |
| pocket2 | 2 | 3.04 | 0.101 | (89.2, 98.6, 26.8) |
| pocket3 | 3 | 2.94 | 0.095 | (61.1, 70.7, -13.6) |
| pocket4 | 4 | 1.87 | 0.037 | (90.9, 95.9, 10.8) |

## 🎨 可视化使用

### **PyMOL可视化**

```bash
# 启动PyMOL并加载脚本
pymol predict_1fbl/visualizations/1fbl.pdb_pymol.pml

# 或在PyMOL中执行:
@predict_1fbl/visualizations/1fbl.pdb_pymol.pml
```

**可视化特点**:
- 🎨 渐变背景 (深蓝到黑色)
- 🌊 半透明蛋白质表面
- 🎯 口袋按分数着色
- 🏷️ 口袋标签显示
- 💜 配体以紫色棒状显示

### **ChimeraX可视化**

```bash
# 启动ChimeraX并加载脚本
chimerax predict_1fbl/visualizations/1fbl.pdb_chimerax.cxc

# 或在ChimeraX中执行:
open predict_1fbl/visualizations/1fbl.pdb_chimerax.cxc
```

**可视化特点**:
- ⚪ 白色背景
- 🔵 浅蓝色蛋白质表面
- 🎨 口袋颜色编码
- 🎭 轮廓边缘增强
- 📊 口袋标签和得分

## 🧪 演示脚本

### **运行完整演示**

```bash
cd examples/visualization/
python visualization_demo.py
```

**演示内容**:
1. **基础可视化**: 创建PyMOL和ChimeraX脚本
2. **PyMOL专用**: 多种显示风格
3. **ChimeraX特色**: 交互式和动画脚本
4. **批量处理**: 多个蛋白质批量可视化
5. **方法比较**: 不同方法结果对比
6. **摘要分析**: 可视化文件统计

### **Python API示例**

```python
from p2rank.visualization import VisualizationManager
from p2rank import P2RankPredictor

# 1. 运行预测
predictor = P2RankPredictor()
result = predictor.predict("protein.pdb")

# 2. 创建可视化
viz_manager = VisualizationManager()
generated_files = viz_manager.create_visualization(
    prediction_result=result,
    protein_file="protein.pdb",
    output_name="my_protein",
    formats=['pymol', 'chimerax'],
    style='surface'
)

# 3. 查看生成的文件
for format_name, file_path in generated_files.items():
    print(f"{format_name}: {file_path}")
```

## 🎯 自定义可视化

### **样式选项**

```python
# 表面显示 (默认)
viz_manager.create_visualization(
    prediction_result=result,
    protein_file="protein.pdb",
    style='surface'
)

# 卡通显示
viz_manager.create_visualization(
    prediction_result=result,
    protein_file="protein.pdb", 
    style='cartoon'
)

# 棒状显示
viz_manager.create_visualization(
    prediction_result=result,
    protein_file="protein.pdb",
    style='sticks'
)
```

### **颜色选项**

```python
# 按分数着色 (默认)
viz_manager.create_visualization(
    prediction_result=result,
    protein_file="protein.pdb",
    color_by_score=True
)

# 使用固定颜色方案
viz_manager.create_visualization(
    prediction_result=result,
    protein_file="protein.pdb",
    color_by_score=False
)
```

### **输出格式**

```python
# 只生成PyMOL脚本
viz_manager.create_visualization(
    prediction_result=result,
    protein_file="protein.pdb",
    formats='pymol'
)

# 只生成ChimeraX脚本
viz_manager.create_visualization(
    prediction_result=result,
    protein_file="protein.pdb",
    formats='chimerax'
)

# 生成两种格式 (默认)
viz_manager.create_visualization(
    prediction_result=result,
    protein_file="protein.pdb",
    formats='both'
)
```

## 🔬 高级功能

### **批量可视化**

```python
# 批量处理多个蛋白质
results = [predictor.predict(f) for f in protein_files]

viz_manager.create_batch_visualization(
    prediction_results=results,
    protein_files=protein_files,
    output_names=["protein1", "protein2", "protein3"],
    formats=['pymol']
)
```

### **方法比较**

```python
# 比较不同方法的预测结果
method1_result = predictor1.predict("protein.pdb")
method2_result = predictor2.predict("protein.pdb")

viz_manager.create_comparison_visualization(
    prediction_results=[method1_result, method2_result],
    protein_files=["protein.pdb", "protein.pdb"],
    method_names=["Method_A", "Method_B"],
    output_name="comparison"
)
```

### **交互式可视化**

```python
# ChimeraX交互式脚本
from p2rank.visualization import ChimeraXVisualizer

chimerax_viz = ChimeraXVisualizer()
interactive_script = chimerax_viz.create_interactive_session(
    prediction_result=result,
    protein_file="protein.pdb",
    output_file="interactive.cxc"
)
```

### **动画生成**

```python
# 旋转动画
animation_script = chimerax_viz.create_animation_script(
    prediction_result=result,
    protein_file="protein.pdb",
    output_file="rotation.cxc",
    animation_type="rotate"
)

# 口袋显示动画
pocket_animation = chimerax_viz.create_animation_script(
    prediction_result=result,
    protein_file="protein.pdb",
    output_file="pocket_reveal.cxc",
    animation_type="pocket_reveal"
)
```

## 📊 输出文件说明

### **PyMOL脚本 (.pml)**

- 完整的PyMOL命令序列
- 包含颜色定义、显示设置、口袋选择
- 支持高质量图像输出设置
- 可自定义各种显示参数

### **ChimeraX脚本 (.cxc)**

- ChimeraX命令格式
- 支持现代可视化效果
- 包含交互式控制绑定
- 动画和视频输出支持

### **支持文件**

- `prediction_summary.json`: 结构化预测数据
- `README.md`: 每个可视化的使用说明
- 蛋白质文件副本: 确保可移植性

## 🎓 最佳实践

1. **文件组织**: 使用描述性的输出名称
2. **格式选择**: 根据可视化软件选择合适格式
3. **批量处理**: 对多个蛋白质使用批量功能
4. **自定义颜色**: 根据科学需求调整颜色方案
5. **文档记录**: 保留预测参数和方法信息

## 🔧 故障排除

### **常见问题**

1. **脚本无法加载**
   - 检查蛋白质文件路径
   - 确保相对路径正确

2. **可视化效果不理想**
   - 尝试不同的显示风格
   - 调整透明度和颜色

3. **口袋未显示**
   - 检查预测结果是否包含口袋数据
   - 验证原子ID和残基ID格式

### **调试技巧**

```python
# 检查预测结果
print(f"发现口袋数: {len(result.pockets)}")
for i, pocket in enumerate(result.pockets):
    print(f"口袋{i+1}: 分数={pocket.score}, 中心={pocket.center}")

# 检查生成的文件
summary = viz_manager.get_visualization_summary()
print(f"总可视化数: {summary['total_visualizations']}")
```

## 📚 更多资源

- **API文档**: 查看可视化模块的完整API
- **教程**: 参考 `docs/tutorials/` 中的可视化教程
- **示例库**: 更多预测结果示例
- **社区**: 分享你的可视化脚本和技巧

---

*P2Rank Python 可视化系统 - 让科学发现更加直观*
