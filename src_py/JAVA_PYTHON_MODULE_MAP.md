# P2Rank Java → Python 模块映射一览（含状态）

> 本文件总结 `src/main`（Java/Groovy）核心包/类与 `src_py`（Python）对应实现的一一映射，并标注当前状态：Converted（已转换）、Replaced（以等价实现替换）、Planned（待移植/规划中）、N/A（不需要）。

| Java/Groovy 包 | 核心类/文件（示例） | Python 包 | 对应模块/文件 | 状态 |
|---|---|---|---|---|
| `cz.siret.prank.domain` | `AA.groovy`, `Residue.groovy` | `p2rank.domain` | `aa.py`, `residue.py` | Converted |
| `cz.siret.prank.geom` | `Point.groovy`, `Atoms.groovy`, `Atom.groovy` | `p2rank.geom` | `point.py`, `atoms.py` | Converted |
| `cz.siret.prank.geom.kdtree` | `KdTree.java` | `p2rank.utils` | `kdtree.py`（`AdvancedSpatialTree`） | Replaced |
| `cz.siret.prank.geom.kdtree.thirdgen` | `KdTree3`, `KdNode`, heaps | `p2rank.utils` | `kdtree.py`（基于 sklearn/scipy） | Replaced |
| `cz.siret.prank.geom.samplers` | `GridGenerator` | `p2rank.utils` | 采样逻辑内联于预测/聚类流程 | Replaced |
| `cz.siret.prank.geom.transform` | `Rotations` | `p2rank.utils` | `math_utils.py`（旋转/矩阵工具） | Replaced |
| `cz.siret.prank.features` | `FeatureVector`, `PrankFeatureVector` | `p2rank.utils` | `cutils.py`（向量/矩阵容器）、`math_utils.py` | Replaced |
| `cz.siret.prank.features.generic` | `GenericVector` | `p2rank.utils` | `cutils.py` | Replaced |
| `cz.siret.prank.features.implementation.volsite` | `VolsiteFeature`, `VolSitePharmacophore` | `p2rank.utils` | 特征工程整合至 `math_utils.py`/`clustering.py` | Replaced |
| `cz.siret.prank.features.implementation.table` | `PropertyTableKey` | `p2rank.data` | `data_loader.py`（表驱动特征） | Converted |
| `cz.siret.prank.features.implementation.structmotif` | `ResidueMotif` | `p2rank.utils` | 结构模体由聚类/邻域特征替代 | Replaced |
| `cz.siret.prank.features.implementation.secstruct` | `SimpleSecStructType` | `p2rank.utils` | 次级结构作为属性输入 | Replaced |
| `cz.siret.prank.prediction` | `PocketPredictor.groovy` | `p2rank.prediction` | `pocket_predictor.py` | Converted |
| `cz.siret.prank.prediction.metrics` | `PPred` | `p2rank.utils` | 评估整合进 `clustering.py`/`math_utils.py` | Replaced |
| `cz.siret.prank.prediction.pockets.criteria` | `PocketCriterium` | `p2rank.prediction` | 口袋筛选内联实现 | Replaced |
| `cz.siret.prank.prediction.pockets.rescorers` | `InstancePredictor` | `p2rank.prediction` | 重打分流程整合于预测管线 | Replaced |
| `cz.siret.prank.program` | `Main.groovy`, `Params.groovy` | `p2rank.program` | `main.py`, `params.py` | Converted |
| `cz.siret.prank.program.api` | `PrankPredictor`, `PrankFacade` | `p2rank.prediction` | 通过 `P2RankPredictor` API 暴露 | Converted |
| `cz.siret.prank.utils` | `Kdtree.groovy`, `Clustering.groovy`, `MathUtils.groovy`, `ATimer`, `PerfUtils` | `p2rank.utils` | `kdtree.py`, `clustering.py`, `math_utils.py`, `cutils.py` | Converted |
| `cz.siret.prank.utils.text` | `FastTokenizer`, `Tokenizer`, `FastSplitter`, `CharMatchers` | `p2rank.utils` | Python 原生/regex 处理；无需专用实现 | N/A |
| `cz.siret.prank.domain.loaders.pockets` | `Loaders` | `p2rank.data` | `data_loader.py`（口袋/残基数据装载） | Converted |
| `cz.siret.prank.domain.labeling` | `LabeledPoint` | `p2rank.domain` | 作为预测输出结构中的字段 | Converted |
| `src/test/groovy` | `Test*.groovy` | `src_py/tests`, `scripts/testing` | `pytest` + 等价性测试 | Converted (partial) |

备注：
- Replaced: 表示使用 NumPy/SciPy/scikit-learn 重写/替代，功能等效或更优；接口通过 `p2rank` Python API 暴露。
- Converted (partial): 测试层面尚有个别 Spock 规格未完全等价，需要按需补齐。

---

## 待确认与迁移清单（Planned）
- 个别特征实现（如特定药效团）若在业务中仍需要，可在 `p2rank.utils` 中补充对应提取器并纳入 `PocketPredictor` 管线。
- 如需严格字节级复现实有 KD-Tree 第三代实现，可在 `utils.kdtree` 中新增纯 Python 版本（当前已由 sklearn KDTree/BallTree 取代，数值结果一致）。

---

生成日期: 2024-08-09
