## P2Rank Java → Python 模型迁移报告（FasterForest/快速森林推理）

### 目标
- 以“数据到数据、代码到代码”的方式重放 Java 已训练模型（FasterForest 快速森林版），实现纯 Python 推理，与 Java/黄金输出严格一致。

### 核心步骤
1) 参数导出（JPype → NPZ）
- 通过 JPype 加载 Java `.zst` 模型，反射提取：`childLeft`, `childRight`, `attributeIndex`, `splitPoint`。
- Legacy 情况读取 `classProbs`（二维 `[negCount,posCount]`）到 `leaf_class0/leaf_class1`。
- 修正：叶索引使用 `-child`（不减 1）；特征维度为 `max(attributeIndex)+1`。
- 保存 `.npz`：包含上述数组和 `roots`/`num_trees`。

2) 纯 Python 推理器（FlatBinaryForestPy）
- 遍历规则：严格 `x[feat] < splitPoint`。
- Legacy 推理：跨树累加 `c0/c1`，最终一次性归一化 `p = sum(c1)/[sum(c0)+sum(c1)]`。
- 非 Legacy：逐树 `node_prob` 平均。

3) 口袋聚合（PocketPredictor）
- 单链接聚类（距离 `pred_clustering_dist`），过滤簇大小 `pred_min_cluster_size`。
- 点过滤 `predicted`，分数使用 `transformed_score`（幂变换），支持 `balance_density` 与 `score_point_limit`。
- 口袋得分为簇内点分数和；排序输出 Top-N。

### 关键文件
- `src_py/tools/export_flatforest.py`：参数导出（JPype）
- `src_py/p2rank/ml/flat_forest.py`：Python 推理
- `src_py/p2rank/prediction/pocket_predictor.py`：聚类与口袋聚合
- `src_py/p2rank/program/main.py`：纯 Python 路径串接与 CSV 输出
- 测试：`tests/integration/test_point_level_equivalence.py`、`tests/integration/test_pure_python_against_gold.py`

### 字段说明
- 快速森林数组：
  - `child_left`/`child_right`：子结点索引（负值表示叶）。
  - `feature_index`：分裂特征索引。
  - `split_point`：分裂阈值。
  - `left_leaf_id`/`right_leaf_id`：若为叶，则取 `-child`（不减 1）；否则 -1。
  - `leaf_class0/leaf_class1`：每个叶子的负/正计数（Legacy）。
  - `num_trees`/`roots`：森林信息。
  - `num_attributes`：`max(attributeIndex)+1`。

### 流程图（简化）

```mermaid
graph TD
  A[Java .zst 模型] --> B[JPype 反射提取 arrays]
  B --> C[导出 .npz (child/feat/threshold/leaf c0,c1,...)]
  C --> D[Python 推理器: 严格 < 分支, 累积 c0/c1 → 归一化]
  D --> E[点级分数]
  E --> F[单链接聚类 + 过滤]
  F --> G[变换/密度/限点 → 口袋分数和]
  G --> H[CSV 输出与金标对齐]
```

### 试错与关键坑点
- 叶索引：Legacy 使用 `classProbs[-node]`，若额外减 1 会导致彻底错位。
- 分支方向：Java 字节码为 `dcmpg ifge → 右分支`，需用严格 `<`。
- 特征维度：`getNumAttributes()` 包含类列，必须用 `max(attributeIndex)+1`。
- 叶值解释：`classProbs` 是计数，需跨树累加后统一归一；简单平均或多数投票均不等价。
- 特征顺序：必须按模型 `features.txt` 配置 `features/feature_filters`，确保特征对齐。

### 验证
- 点级：与 Java 同一批向量并行预测，`max abs diff = 0.0`。
- 口袋级：`test_pure_python_against_gold.py` 通过（Top-3 分数/排序一致）。

### 复现命令
```bash
# 导出 npz
python src_py/tools/export_flatforest.py \
  --model-dir distro/models/default \
  --out-npz   src_py/converted_models_final/default_flatforest.npz

# 运行对齐测试
pytest -q -k point_level_equivalence src_py
pytest -q -k pure_python_against_gold src_py
```


