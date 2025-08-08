# P2Rank Python - 特征工程配置文档

本文档描述了特征向量配置，并介绍如何添加新特征。这对训练和评估新模型非常有用。

## 🧬 特征系统介绍

P2Rank Python基于对SAS (Solvent Accessible Surface)点的特征向量进行评分预测。特征向量本质上是一个实数数组，每个元素都有唯一的名称。

### **核心概念**

- **特征 (Feature)**: 特征计算器，如 `chemical`、`geometric`、`conservation`
- **子特征 (Sub-feature)**: 单个标量数值，如 `chemical.hydrophobicity`、`geometric.protrusion`
- **特征向量 (Feature Vector)**: 所有特征组合成的数值数组
- **特征空间 (Feature Space)**: 所有可能特征的高维空间

```python
# 特征向量示例
feature_vector = {
    'chemical.hydrophobicity': 0.85,
    'chemical.charge': -0.3,
    'geometric.protrusion': 2.1,
    'geometric.curvature': 0.45,
    'conservation.score': 0.78,
    # ... 更多特征
}
```

## ⚙️ 特征配置系统

### **1. 配置方式**

#### **方式1: YAML配置文件** (推荐)

```yaml
# config/features_config.yaml
features:
  # 启用的特征组
  enabled_groups:
    - chemical
    - geometric  
    - conservation
    - bfactor
    - volsite
  
  # 具体特征配置
  chemical:
    hydrophobicity: true
    charge: true
    aromaticity: true
    hbond_donors: true
    hbond_acceptors: true
  
  geometric:
    protrusion: true
    curvature: true
    surface_area: true
    volume: true
  
  conservation:
    pssm_score: true
    entropy: true
    
  # 表格特征
  atom_table_features:
    - hydrophobicity
    - vdw_radius
    - charge
    
  residue_table_features:
    - propensity
    - volume
    - surface_area
```

#### **方式2: Python API配置**

```python
from p2rank.features import FeatureConfig, FeatureManager

# 创建特征配置
config = FeatureConfig()

# 启用特征组
config.enable_feature_groups(['chemical', 'geometric', 'conservation'])

# 细粒度控制
config.enable_features({
    'chemical': ['hydrophobicity', 'charge', 'aromaticity'],
    'geometric': ['protrusion', 'curvature'],
    'conservation': ['pssm_score']
})

# 禁用特定特征
config.disable_features(['chemical.aromaticity'])

# 特征过滤器
config.add_feature_filter(
    filter_type='variance_threshold',
    threshold=0.01
)

# 特征转换
config.add_feature_transform(
    transform_type='standard_scaler'
)
```

#### **方式3: 命令行配置**

```bash
# 启用特征组
python -m p2rank predict --features chemical,geometric,conservation protein.pdb

# 详细配置
python -m p2rank predict \
    --features chemical,geometric \
    --chemical-features hydrophobicity,charge \
    --geometric-features protrusion,curvature \
    protein.pdb
```

### **2. 查看当前特征配置**

```python
from p2rank.features import FeatureManager

def print_feature_config():
    """显示当前特征配置"""
    
    manager = FeatureManager()
    config = manager.get_current_config()
    
    print("🧬 P2Rank Python Feature Configuration")
    print("=" * 50)
    
    print(f"\n📊 Total Features: {config.total_feature_count}")
    print(f"📈 Feature Vector Length: {config.feature_vector_length}")
    
    print(f"\n✅ Enabled Feature Groups:")
    for group in config.enabled_groups:
        features = config.get_group_features(group)
        print(f"  {group}: {len(features)} features")
        for feature in features[:3]:  # 显示前3个
            print(f"    - {feature}")
        if len(features) > 3:
            print(f"    ... and {len(features)-3} more")
    
    print(f"\n🔧 Feature Transformations:")
    for transform in config.transformations:
        print(f"  - {transform['type']}: {transform['params']}")
    
    print(f"\n🚫 Disabled Features: {len(config.disabled_features)}")
    if config.disabled_features:
        print(f"  {list(config.disabled_features)[:5]}")

# 使用示例
if __name__ == "__main__":
    print_feature_config()
```

## 🧪 内置特征计算器

### **1. 化学特征 (Chemical Features)**

```python
class ChemicalFeatures:
    """化学特征计算器"""
    
    def __init__(self):
        self.feature_names = [
            'hydrophobicity',      # 疏水性
            'charge',              # 电荷
            'aromaticity',         # 芳香性
            'hbond_donors',        # 氢键供体数
            'hbond_acceptors',     # 氢键受体数
            'polar_surface_area',  # 极性表面积
            'molecular_weight',    # 分子量
        ]
    
    def calculate(self, atoms, point):
        """计算化学特征"""
        nearby_atoms = self._get_nearby_atoms(atoms, point, radius=8.0)
        
        features = {}
        features['hydrophobicity'] = self._calc_hydrophobicity(nearby_atoms)
        features['charge'] = self._calc_charge(nearby_atoms)
        features['aromaticity'] = self._calc_aromaticity(nearby_atoms)
        # ... 更多特征计算
        
        return features

# 使用示例
chemical_calc = ChemicalFeatures()
features = chemical_calc.calculate(protein_atoms, surface_point)
```

### **2. 几何特征 (Geometric Features)**

```python
class GeometricFeatures:
    """几何特征计算器"""
    
    def __init__(self):
        self.feature_names = [
            'protrusion',          # 突出度
            'curvature',           # 曲率
            'surface_area',        # 表面积
            'volume',              # 体积
            'pocket_depth',        # 口袋深度
            'convexity',           # 凸性
            'sphericity',          # 球形度
        ]
    
    def calculate(self, surface, point):
        """计算几何特征"""
        features = {}
        
        # 突出度计算
        features['protrusion'] = self._calc_protrusion(surface, point)
        
        # 曲率计算
        features['curvature'] = self._calc_curvature(surface, point)
        
        # 表面积计算
        features['surface_area'] = self._calc_local_surface_area(surface, point)
        
        return features
    
    def _calc_protrusion(self, surface, point):
        """计算突出度 - 点到凸包的距离"""
        from scipy.spatial import ConvexHull
        
        nearby_points = self._get_nearby_points(surface, point, radius=10.0)
        hull = ConvexHull(nearby_points)
        
        # 计算点到凸包的距离
        protrusion = self._point_to_hull_distance(point, hull)
        return protrusion
```

### **3. 进化保守性特征 (Conservation Features)**

```python
class ConservationFeatures:
    """进化保守性特征计算器"""
    
    def __init__(self, pssm_data=None, hmm_data=None):
        self.pssm_data = pssm_data  # Position-Specific Scoring Matrix
        self.hmm_data = hmm_data    # Hidden Markov Model data
        
        self.feature_names = [
            'pssm_score',          # PSSM保守性评分
            'entropy',             # 序列熵
            'mutual_information',  # 互信息
            'relative_entropy',    # 相对熵
            'conservation_index',  # 保守性指数
        ]
    
    def calculate(self, residue, position):
        """计算保守性特征"""
        features = {}
        
        if self.pssm_data:
            features['pssm_score'] = self._calc_pssm_score(residue, position)
            features['entropy'] = self._calc_sequence_entropy(position)
        
        if self.hmm_data:
            features['conservation_index'] = self._calc_hmm_conservation(position)
        
        return features
```

### **4. B因子特征 (B-Factor Features)**

```python
class BFactorFeatures:
    """B因子(温度因子)特征计算器"""
    
    def __init__(self):
        self.feature_names = [
            'bfactor_mean',        # 平均B因子
            'bfactor_std',         # B因子标准差
            'bfactor_min',         # 最小B因子
            'bfactor_max',         # 最大B因子
            'normalized_bfactor',  # 归一化B因子
        ]
    
    def calculate(self, atoms, point):
        """计算B因子特征"""
        nearby_atoms = self._get_nearby_atoms(atoms, point, radius=6.0)
        bfactors = [atom.bfactor for atom in nearby_atoms]
        
        features = {}
        features['bfactor_mean'] = np.mean(bfactors)
        features['bfactor_std'] = np.std(bfactors)
        features['bfactor_min'] = np.min(bfactors)
        features['bfactor_max'] = np.max(bfactors)
        features['normalized_bfactor'] = self._normalize_bfactor(features['bfactor_mean'])
        
        return features
```

### **5. 体积位点特征 (Volume Site Features)**

```python
class VolumeSiteFeatures:
    """体积位点特征计算器"""
    
    def __init__(self):
        self.feature_names = [
            'pocket_volume',       # 口袋体积
            'pocket_surface_area', # 口袋表面积
            'shape_index',         # 形状指数
            'druggability_score',  # 可药性评分
            'binding_site_score',  # 结合位点评分
        ]
    
    def calculate(self, pocket_points, point):
        """计算体积位点特征"""
        features = {}
        
        # 使用Delaunay三角剖分计算体积
        features['pocket_volume'] = self._calc_pocket_volume(pocket_points)
        
        # 计算表面积
        features['pocket_surface_area'] = self._calc_pocket_surface_area(pocket_points)
        
        # 形状描述符
        features['shape_index'] = self._calc_shape_index(pocket_points, point)
        
        return features
```

## 🛠️ 自定义特征开发

### **1. 创建自定义特征计算器**

```python
from p2rank.features.base import BaseFeatureCalculator
import numpy as np

class CustomElectrostaticFeatures(BaseFeatureCalculator):
    """自定义静电特征计算器"""
    
    def __init__(self, config=None):
        super().__init__(config)
        self.feature_names = [
            'electrostatic_potential',
            'electric_field_magnitude',
            'electric_field_x',
            'electric_field_y', 
            'electric_field_z',
            'dipole_moment',
        ]
    
    def calculate_features(self, atoms, point, **kwargs):
        """计算静电特征"""
        
        # 1. 计算静电势
        potential = self._calculate_electrostatic_potential(atoms, point)
        
        # 2. 计算电场
        electric_field = self._calculate_electric_field(atoms, point)
        
        # 3. 计算偶极矩
        dipole = self._calculate_dipole_moment(atoms, point)
        
        return {
            'electrostatic_potential': potential,
            'electric_field_magnitude': np.linalg.norm(electric_field),
            'electric_field_x': electric_field[0],
            'electric_field_y': electric_field[1],
            'electric_field_z': electric_field[2],
            'dipole_moment': dipole,
        }
    
    def _calculate_electrostatic_potential(self, atoms, point):
        """计算静电势"""
        potential = 0.0
        for atom in atoms:
            distance = np.linalg.norm(point - atom.coords)
            if distance > 0:
                potential += atom.charge / distance
        return potential
    
    def _calculate_electric_field(self, atoms, point):
        """计算电场向量"""
        field = np.zeros(3)
        for atom in atoms:
            r_vec = point - atom.coords
            distance = np.linalg.norm(r_vec)
            if distance > 0:
                field += atom.charge * r_vec / (distance ** 3)
        return field

# 注册自定义特征
from p2rank.features import FeatureRegistry

FeatureRegistry.register('electrostatic', CustomElectrostaticFeatures)
```

### **2. 集成外部特征**

```python
class ExternalFeatureIntegrator:
    """集成外部特征计算工具"""
    
    def __init__(self):
        self.fpocket_features = self._setup_fpocket()
        self.caver_features = self._setup_caver()
        self.rosetta_features = self._setup_rosetta()
    
    def calculate_fpocket_features(self, protein_file, point):
        """集成FPocket特征"""
        # 调用FPocket
        fpocket_result = self._run_fpocket(protein_file)
        
        # 提取特征
        features = {
            'fpocket_druggability': fpocket_result.druggability_score,
            'fpocket_volume': fpocket_result.pocket_volume,
            'fpocket_score': fpocket_result.pocket_score,
        }
        
        return features
    
    def calculate_rosetta_features(self, protein_file, point):
        """集成Rosetta特征"""
        rosetta_result = self._run_rosetta_features(protein_file)
        
        features = {
            'rosetta_energy': rosetta_result.total_energy,
            'rosetta_sasa': rosetta_result.sasa,
            'rosetta_hbonds': rosetta_result.hbond_count,
        }
        
        return features

# 使用示例
integrator = ExternalFeatureIntegrator()
external_features = integrator.calculate_fpocket_features("protein.pdb", point)
```

## 🔍 特征选择和过滤

### **1. 特征过滤器**

```python
from p2rank.features.filters import FeatureFilter
from sklearn.feature_selection import VarianceThreshold, SelectKBest, f_classif

class AdvancedFeatureFilter:
    """高级特征过滤器"""
    
    def __init__(self):
        self.filters = []
    
    def add_variance_filter(self, threshold=0.01):
        """添加方差过滤器 - 移除低方差特征"""
        filter_obj = VarianceThreshold(threshold=threshold)
        self.filters.append(('variance', filter_obj))
    
    def add_correlation_filter(self, threshold=0.95):
        """添加相关性过滤器 - 移除高度相关的特征"""
        def correlation_filter(X):
            corr_matrix = np.corrcoef(X.T)
            high_corr_pairs = np.where(np.abs(corr_matrix) > threshold)
            # 移除高相关特征的逻辑
            return X  # 简化示例
        
        self.filters.append(('correlation', correlation_filter))
    
    def add_univariate_filter(self, k=50):
        """添加单变量特征选择"""
        filter_obj = SelectKBest(score_func=f_classif, k=k)
        self.filters.append(('univariate', filter_obj))
    
    def apply_filters(self, X, y=None):
        """应用所有过滤器"""
        filtered_X = X.copy()
        
        for filter_name, filter_obj in self.filters:
            print(f"Applying {filter_name} filter...")
            if hasattr(filter_obj, 'fit_transform'):
                filtered_X = filter_obj.fit_transform(filtered_X, y)
            else:
                filtered_X = filter_obj(filtered_X)
            
            print(f"  Features after {filter_name}: {filtered_X.shape[1]}")
        
        return filtered_X

# 使用示例
feature_filter = AdvancedFeatureFilter()
feature_filter.add_variance_filter(threshold=0.01)
feature_filter.add_correlation_filter(threshold=0.95)
feature_filter.add_univariate_filter(k=100)

filtered_features = feature_filter.apply_filters(feature_matrix, labels)
```

### **2. 特征重要性分析**

```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
import matplotlib.pyplot as plt

class FeatureImportanceAnalyzer:
    """特征重要性分析器"""
    
    def __init__(self, model=None):
        self.model = model or RandomForestClassifier(n_estimators=100, random_state=42)
    
    def analyze_importance(self, X, y, feature_names):
        """分析特征重要性"""
        
        # 训练模型
        self.model.fit(X, y)
        
        # 1. 基于不纯度的重要性
        impurity_importance = self.model.feature_importances_
        
        # 2. 基于排列的重要性
        perm_importance = permutation_importance(
            self.model, X, y, n_repeats=10, random_state=42
        )
        
        # 3. 创建重要性DataFrame
        importance_df = pd.DataFrame({
            'Feature': feature_names,
            'Impurity_Importance': impurity_importance,
            'Permutation_Importance': perm_importance.importances_mean,
            'Permutation_Std': perm_importance.importances_std,
        })
        
        # 按重要性排序
        importance_df = importance_df.sort_values(
            'Permutation_Importance', ascending=False
        )
        
        return importance_df
    
    def plot_importance(self, importance_df, top_k=20):
        """绘制特征重要性图"""
        
        top_features = importance_df.head(top_k)
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 8))
        
        # 不纯度重要性
        ax1.barh(top_features['Feature'], top_features['Impurity_Importance'])
        ax1.set_title('Feature Importance (Impurity-based)')
        ax1.set_xlabel('Importance')
        
        # 排列重要性
        ax2.barh(top_features['Feature'], top_features['Permutation_Importance'])
        ax2.set_title('Feature Importance (Permutation-based)')
        ax2.set_xlabel('Importance')
        
        plt.tight_layout()
        plt.savefig('feature_importance.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        return fig

# 使用示例
analyzer = FeatureImportanceAnalyzer()
importance_df = analyzer.analyze_importance(X, y, feature_names)
analyzer.plot_importance(importance_df)
```

## 📊 特征工程流水线

### **完整特征工程流水线**

```python
from p2rank.features import FeaturePipeline
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.decomposition import PCA

class P2RankFeaturePipeline:
    """P2Rank特征工程流水线"""
    
    def __init__(self, config_file=None):
        self.config = self._load_config(config_file)
        self.feature_calculators = self._setup_calculators()
        self.preprocessors = self._setup_preprocessors()
        self.feature_selectors = self._setup_selectors()
    
    def extract_features(self, proteins, surface_points):
        """提取特征"""
        print("🧬 Extracting features...")
        
        all_features = []
        
        for protein, points in zip(proteins, surface_points):
            protein_features = []
            
            for point in points:
                # 计算所有特征
                point_features = {}
                
                for calc_name, calculator in self.feature_calculators.items():
                    try:
                        features = calculator.calculate(protein, point)
                        point_features.update(features)
                    except Exception as e:
                        print(f"Warning: Failed to calculate {calc_name} features: {e}")
                
                protein_features.append(point_features)
            
            all_features.extend(protein_features)
        
        # 转换为数值矩阵
        feature_matrix, feature_names = self._convert_to_matrix(all_features)
        
        return feature_matrix, feature_names
    
    def preprocess_features(self, X, y=None, fit=True):
        """特征预处理"""
        print("🔧 Preprocessing features...")
        
        processed_X = X.copy()
        
        for name, preprocessor in self.preprocessors.items():
            print(f"  Applying {name}...")
            
            if fit:
                processed_X = preprocessor.fit_transform(processed_X)
            else:
                processed_X = preprocessor.transform(processed_X)
        
        return processed_X
    
    def select_features(self, X, y, fit=True):
        """特征选择"""
        print("🎯 Selecting features...")
        
        selected_X = X.copy()
        selected_feature_indices = None
        
        for name, selector in self.feature_selectors.items():
            print(f"  Applying {name}...")
            
            if fit:
                selected_X = selector.fit_transform(selected_X, y)
                if hasattr(selector, 'get_support'):
                    selected_feature_indices = selector.get_support(indices=True)
            else:
                selected_X = selector.transform(selected_X)
        
        return selected_X, selected_feature_indices
    
    def full_pipeline(self, proteins, surface_points, labels=None):
        """完整的特征工程流水线"""
        
        print("🚀 Starting full feature engineering pipeline...")
        
        # 1. 特征提取
        X, feature_names = self.extract_features(proteins, surface_points)
        print(f"  Extracted features: {X.shape}")
        
        # 2. 特征预处理
        X_preprocessed = self.preprocess_features(X, labels, fit=True)
        print(f"  Preprocessed features: {X_preprocessed.shape}")
        
        # 3. 特征选择
        if labels is not None:
            X_selected, selected_indices = self.select_features(X_preprocessed, labels, fit=True)
            selected_feature_names = [feature_names[i] for i in selected_indices]
            print(f"  Selected features: {X_selected.shape}")
        else:
            X_selected = X_preprocessed
            selected_feature_names = feature_names
        
        # 4. 保存流水线
        self.save_pipeline('feature_pipeline.pkl')
        
        print("✅ Feature engineering pipeline completed!")
        
        return X_selected, selected_feature_names

# 使用示例
pipeline = P2RankFeaturePipeline(config_file='feature_config.yaml')
features, feature_names = pipeline.full_pipeline(proteins, surface_points, labels)
```

## 📋 最佳实践建议

### **特征工程最佳实践**

```python
class FeatureEngineeringBestPractices:
    """特征工程最佳实践指南"""
    
    @staticmethod
    def recommend_feature_set(use_case, computational_budget):
        """根据使用场景推荐特征集"""
        
        recommendations = {
            'quick_screening': {
                'features': ['chemical', 'geometric'],
                'budget': 'low',
                'accuracy': 'medium'
            },
            'research_quality': {
                'features': ['chemical', 'geometric', 'conservation', 'bfactor'],
                'budget': 'medium',
                'accuracy': 'high'
            },
            'production_quality': {
                'features': ['chemical', 'geometric', 'conservation', 'bfactor', 'volsite'],
                'budget': 'high',
                'accuracy': 'very_high'
            }
        }
        
        return recommendations.get(use_case, recommendations['research_quality'])
    
    @staticmethod
    def validate_feature_quality(X, y, feature_names):
        """验证特征质量"""
        
        print("🔍 Validating feature quality...")
        
        # 1. 检查缺失值
        missing_ratio = np.isnan(X).mean(axis=0)
        high_missing = missing_ratio > 0.1
        if high_missing.any():
            print(f"⚠️  Features with >10% missing values: {np.array(feature_names)[high_missing]}")
        
        # 2. 检查常数特征
        constant_features = np.var(X, axis=0) < 1e-10
        if constant_features.any():
            print(f"⚠️  Constant features detected: {np.array(feature_names)[constant_features]}")
        
        # 3. 检查特征分布
        skewed_features = []
        for i, name in enumerate(feature_names):
            skewness = scipy.stats.skew(X[:, i])
            if abs(skewness) > 2:
                skewed_features.append((name, skewness))
        
        if skewed_features:
            print(f"⚠️  Highly skewed features (|skew| > 2): {len(skewed_features)}")
        
        # 4. 特征相关性分析
        corr_matrix = np.corrcoef(X.T)
        high_corr_pairs = []
        for i in range(len(feature_names)):
            for j in range(i+1, len(feature_names)):
                if abs(corr_matrix[i, j]) > 0.95:
                    high_corr_pairs.append((feature_names[i], feature_names[j], corr_matrix[i, j]))
        
        if high_corr_pairs:
            print(f"⚠️  Highly correlated feature pairs (|r| > 0.95): {len(high_corr_pairs)}")
        
        return {
            'missing_features': np.array(feature_names)[high_missing].tolist(),
            'constant_features': np.array(feature_names)[constant_features].tolist(),
            'skewed_features': skewed_features,
            'correlated_pairs': high_corr_pairs
        }
```

---

## 🎯 总结

P2Rank Python的特征系统提供了：

- ✅ **丰富的内置特征**: 化学、几何、保守性、B因子等特征计算器
- ✅ **灵活的配置系统**: YAML配置、Python API、命令行参数
- ✅ **可扩展的架构**: 易于添加自定义特征计算器
- ✅ **智能特征选择**: 方差过滤、相关性分析、重要性评估
- ✅ **完整的处理流水线**: 从特征提取到选择的端到端流程

通过合理配置和选择特征，可以显著提升P2Rank模型的预测性能和计算效率！

---

*更多详细信息请参考特征计算器API文档和示例代码*
