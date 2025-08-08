"""
P2Rank数据加载器 - 处理各种特征计算数据

支持的数据类型:
- 氨基酸倾向性数据 (aa-propensities)
- AAindex数据库 (aaindex)  
- 原子疏水性数据 (atomic-hydrophobicity)
- 配体结合倾向性数据 (ligand-binding-propensities)
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging
import re

logger = logging.getLogger(__name__)


class DataLoader:
    """主数据加载器 - 统一访问所有数据源"""
    
    def __init__(self, data_dir: Optional[Path] = None):
        if data_dir is None:
            # 默认使用相对于此文件的data目录
            data_dir = Path(__file__).parent
        self.data_dir = Path(data_dir)
        
        # 子加载器
        self.aa_props = AAPropertiesLoader(self.data_dir)
        self.aaindex = AAIndexLoader(self.data_dir)
        self.atomic_props = AtomicPropertiesLoader(self.data_dir)
        
        logger.info(f"DataLoader initialized with data_dir: {self.data_dir}")
    
    def load_all_data(self) -> Dict[str, Any]:
        """加载所有可用数据"""
        data = {}
        
        try:
            data['aa_propensities'] = self.aa_props.load_propensities()
            data['aa_shortcuts'] = self.aa_props.load_shortcuts()
            data['atomic_hydrophobicity'] = self.atomic_props.load_hydrophobicity()
            data['aaindex'] = self.aaindex.load_aaindex()
            data['ligand_propensities'] = self.aa_props.load_ligand_propensities()
            
            logger.info("Successfully loaded all data sources")
            return data
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise


class AAPropertiesLoader:
    """氨基酸性质数据加载器"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
    
    def load_propensities(self) -> pd.DataFrame:
        """加载氨基酸倾向性数据"""
        file_path = self.data_dir / "aa-propensities" / "table.txt"
        
        try:
            # 解析固定格式的表格数据
            df = pd.read_csv(file_path, sep=r'\s+', header=0)
            df.columns = ['aa_code', 'CA_x', 'SA_x', 'RA_x']
            
            # 设置氨基酸代码为索引
            df.set_index('aa_code', inplace=True)
            
            logger.info(f"Loaded AA propensities: {len(df)} amino acids")
            return df
        except Exception as e:
            logger.error(f"Error loading AA propensities: {e}")
            raise
    
    def load_shortcuts(self) -> pd.DataFrame:
        """加载氨基酸代码映射"""
        file_path = self.data_dir / "aa-shortcuts.csv"
        
        try:
            df = pd.read_csv(file_path, sep='\t', header=None, 
                           names=['three_letter', 'one_letter', 'full_name', 'empty', 'properties'])
            
            # 清理数据
            df = df.dropna(subset=['three_letter'])  # 移除空行
            df['properties'] = df['properties'].fillna('')
            
            logger.info(f"Loaded AA shortcuts: {len(df)} amino acids")
            return df
        except Exception as e:
            logger.error(f"Error loading AA shortcuts: {e}")
            raise
    
    def load_ligand_propensities(self) -> Dict[str, pd.DataFrame]:
        """加载配体结合倾向性数据"""
        prop_dir = self.data_dir / "ligand-binding-propensities"
        propensities = {}
        
        # 加载各种配体倾向性文件
        files_to_load = [
            '5sasa.valids.csv', '5sasa.invalids.csv',
            'raw.valids.csv', 'raw.invalids.csv'
        ]
        
        for filename in files_to_load:
            file_path = prop_dir / filename
            if file_path.exists():
                try:
                    df = pd.read_csv(file_path)
                    key = filename.replace('.csv', '').replace('.', '_')
                    propensities[key] = df
                    logger.info(f"Loaded {key}: {len(df)} entries")
                except Exception as e:
                    logger.warning(f"Could not load {filename}: {e}")
        
        return propensities


class AAIndexLoader:
    """AAindex数据库加载器"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
    
    def load_aaindex(self) -> Dict[str, Dict[str, Any]]:
        """加载AAindex数据库"""
        file_path = self.data_dir / "aaindex" / "aaindex1.txt"
        
        try:
            aaindex_data = {}
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 按记录分割（以//结尾）
            records = content.split('//')
            
            for record in records:
                if not record.strip():
                    continue
                
                parsed_record = self._parse_aaindex_record(record)
                if parsed_record:
                    aaindex_data[parsed_record['id']] = parsed_record
            
            logger.info(f"Loaded AAindex: {len(aaindex_data)} indices")
            return aaindex_data
        except Exception as e:
            logger.error(f"Error loading AAindex: {e}")
            raise
    
    def _parse_aaindex_record(self, record: str) -> Optional[Dict[str, Any]]:
        """解析单个AAindex记录"""
        lines = [line.strip() for line in record.strip().split('\n') if line.strip()]
        
        if not lines:
            return None
        
        parsed = {}
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            if line.startswith('H '):
                parsed['id'] = line[2:].strip()
            elif line.startswith('D '):
                parsed['description'] = line[2:].strip()
            elif line.startswith('R '):
                parsed['reference'] = line[2:].strip()
            elif line.startswith('A '):
                parsed['authors'] = line[2:].strip()
            elif line.startswith('T '):
                # 处理多行标题
                title_lines = [line[2:].strip()]
                i += 1
                while i < len(lines) and not lines[i][0].isupper():
                    title_lines.append(lines[i].strip())
                    i += 1
                parsed['title'] = ' '.join(title_lines)
                i -= 1  # 回退一行
            elif line.startswith('J '):
                parsed['journal'] = line[2:].strip()
            elif line.startswith('C '):
                parsed['correlations'] = line[2:].strip()
            elif line.startswith('I '):
                # 解析数值数据
                data_lines = [line[2:].strip()]
                i += 1
                while i < len(lines) and not lines[i].startswith(('H ', 'D ', 'R ', 'A ', 'T ', 'J ', 'C ', 'I ')):
                    data_lines.append(lines[i].strip())
                    i += 1
                parsed['values'] = self._parse_aaindex_values(data_lines)
                i -= 1  # 回退一行
            
            i += 1
        
        return parsed if 'id' in parsed else None
    
    def _parse_aaindex_values(self, data_lines: List[str]) -> Dict[str, float]:
        """解析AAindex数值数据"""
        values = {}
        
        # 标准氨基酸顺序
        aa_order = ['A', 'R', 'N', 'D', 'C', 'Q', 'E', 'G', 'H', 'I', 
                   'L', 'K', 'M', 'F', 'P', 'S', 'T', 'W', 'Y', 'V']
        
        # 合并所有数据行
        all_values_text = ' '.join(data_lines)
        
        # 提取数值（跳过氨基酸对标记如A/L）
        numbers = re.findall(r'-?\d+\.?\d*', all_values_text)
        
        try:
            # 转换为浮点数
            float_values = [float(x) for x in numbers if x]
            
            # 映射到氨基酸
            for i, aa in enumerate(aa_order):
                if i < len(float_values):
                    values[aa] = float_values[i]
                else:
                    values[aa] = np.nan
                    
        except ValueError as e:
            logger.warning(f"Error parsing AAindex values: {e}")
        
        return values


class AtomicPropertiesLoader:
    """原子性质数据加载器"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
    
    def load_hydrophobicity(self) -> pd.DataFrame:
        """加载原子疏水性数据"""
        file_path = self.data_dir / "atomic-binary-hydrophobicity" / "atomic-hydrophobicity.csv"
        
        try:
            df = pd.read_csv(file_path, header=None, names=['atom_type', 'hydrophobicity'])
            
            # 分离氨基酸和原子类型
            df[['residue', 'atom']] = df['atom_type'].str.split('.', expand=True)
            
            # 转换疏水性值为数值
            df['hydrophobicity'] = pd.to_numeric(df['hydrophobicity'])
            
            logger.info(f"Loaded atomic hydrophobicity: {len(df)} atom types")
            return df
        except Exception as e:
            logger.error(f"Error loading atomic hydrophobicity: {e}")
            raise
    
    def get_atom_hydrophobicity(self, residue: str, atom: str) -> Optional[float]:
        """获取特定原子的疏水性值"""
        df = self.load_hydrophobicity()
        result = df[(df['residue'] == residue) & (df['atom'] == atom)]
        
        if not result.empty:
            return result.iloc[0]['hydrophobicity']
        return None


# 便捷函数
def get_default_data_loader() -> DataLoader:
    """获取默认的数据加载器实例"""
    return DataLoader()


def load_aa_propensities() -> pd.DataFrame:
    """快速加载氨基酸倾向性数据"""
    loader = get_default_data_loader()
    return loader.aa_props.load_propensities()


def load_aaindex() -> Dict[str, Dict[str, Any]]:
    """快速加载AAindex数据"""
    loader = get_default_data_loader()
    return loader.aaindex.load_aaindex()


def load_atomic_hydrophobicity() -> pd.DataFrame:
    """快速加载原子疏水性数据"""
    loader = get_default_data_loader()
    return loader.atomic_props.load_hydrophobicity()


if __name__ == "__main__":
    # 测试数据加载器
    logging.basicConfig(level=logging.INFO)
    
    print("Testing P2Rank DataLoader...")
    
    try:
        loader = DataLoader()
        
        # 测试各个组件
        print("\n1. Testing AA propensities...")
        aa_props = loader.aa_props.load_propensities()
        print(f"Loaded {len(aa_props)} amino acid propensities")
        print(aa_props.head())
        
        print("\n2. Testing AA shortcuts...")
        aa_shortcuts = loader.aa_props.load_shortcuts()
        print(f"Loaded {len(aa_shortcuts)} amino acid mappings")
        print(aa_shortcuts.head())
        
        print("\n3. Testing atomic hydrophobicity...")
        atomic_hydro = loader.atomic_props.load_hydrophobicity()
        print(f"Loaded {len(atomic_hydro)} atomic hydrophobicity values")
        print(atomic_hydro.head())
        
        print("\n4. Testing AAindex (sample)...")
        aaindex = loader.aaindex.load_aaindex()
        print(f"Loaded {len(aaindex)} AAindex entries")
        
        # 显示第一个条目
        first_key = list(aaindex.keys())[0]
        print(f"Sample entry '{first_key}':")
        for k, v in aaindex[first_key].items():
            if k != 'values':
                print(f"  {k}: {v}")
        
        print("\n✅ All data loading tests passed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise
