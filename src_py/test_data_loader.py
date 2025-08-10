#!/usr/bin/env python3
"""
P2Rank数据加载器测试脚本
验证所有数据源能够正确加载和解析
"""

import sys
import logging
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from p2rank.data import DataLoader, load_aa_propensities, load_aaindex, load_atomic_hydrophobicity

def test_data_loading():
    """完整的数据加载测试"""
    print("🧪 P2Rank Data Loader Testing")
    print("=" * 50)
    
    try:
        # 1. 初始化数据加载器
        print("\n📂 Initializing DataLoader...")
        loader = DataLoader()
        print(f"✅ DataLoader initialized, data_dir: {loader.data_dir}")
        
        # 2. 测试氨基酸倾向性数据
        print("\n🧬 Testing AA Propensities...")
        aa_props = loader.aa_props.load_propensities()
        print(f"✅ Loaded {len(aa_props)} amino acid propensities")
        print("📊 Sample data:")
        print(aa_props.head())
        print(f"📈 Columns: {list(aa_props.columns)}")
        
        # 3. 测试氨基酸映射
        print("\n🔤 Testing AA Shortcuts...")
        aa_shortcuts = loader.aa_props.load_shortcuts()
        print(f"✅ Loaded {len(aa_shortcuts)} amino acid mappings")
        print("📊 Sample data:")
        print(aa_shortcuts.head(3))
        
        # 4. 测试原子疏水性数据
        print("\n⚛️  Testing Atomic Hydrophobicity...")
        atomic_hydro = loader.atomic_props.load_hydrophobicity()
        print(f"✅ Loaded {len(atomic_hydro)} atomic hydrophobicity values")
        print("📊 Sample data:")
        print(atomic_hydro.head())
        
        # 5. 测试AAindex数据库
        print("\n📚 Testing AAindex Database...")
        aaindex = loader.aaindex.load_aaindex()
        print(f"✅ Loaded {len(aaindex)} AAindex entries")
        
        # 显示几个示例条目
        sample_keys = list(aaindex.keys())[:3]
        for key in sample_keys:
            entry = aaindex[key]
            print(f"\n📖 Entry '{key}':")
            print(f"  📝 Description: {entry.get('description', 'N/A')}")
            if 'values' in entry and entry['values']:
                aa_values = list(entry['values'].items())[:5]  # 显示前5个
                print(f"  📊 Values (sample): {aa_values}")
        
        # 6. 测试配体结合倾向性
        print("\n🔗 Testing Ligand Binding Propensities...")
        ligand_props = loader.aa_props.load_ligand_propensities()
        print(f"✅ Loaded {len(ligand_props)} ligand propensity datasets")
        for key, df in ligand_props.items():
            print(f"  📊 {key}: {len(df)} entries")
        
        # 7. 测试便捷函数
        print("\n⚡ Testing Convenience Functions...")
        
        # 快速加载函数测试
        quick_aa = load_aa_propensities()
        quick_aaindex = load_aaindex()
        quick_atomic = load_atomic_hydrophobicity()
        
        print(f"✅ Quick AA propensities: {len(quick_aa)} entries")
        print(f"✅ Quick AAindex: {len(quick_aaindex)} entries")
        print(f"✅ Quick atomic hydrophobicity: {len(quick_atomic)} entries")
        
        # 8. 数据完整性检查
        print("\n🔍 Data Integrity Checks...")
        
        # 检查氨基酸倾向性是否包含20种标准氨基酸
        standard_aa = set('ACDEFGHIKLMNPQRSTVWY')
        loaded_aa = set(aa_props.index)
        missing_aa = standard_aa - loaded_aa
        extra_aa = loaded_aa - standard_aa
        
        if not missing_aa:
            print("✅ All 20 standard amino acids present in propensities")
        else:
            print(f"⚠️  Missing amino acids in propensities: {missing_aa}")
        
        if extra_aa:
            print(f"ℹ️  Extra amino acids in propensities: {extra_aa}")
        
        # 检查原子疏水性数据的氨基酸覆盖
        hydro_residues = set(atomic_hydro['residue'].unique())
        hydro_missing = standard_aa - hydro_residues
        
        if not hydro_missing:
            print("✅ All 20 standard amino acids present in hydrophobicity data")
        else:
            print(f"⚠️  Missing amino acids in hydrophobicity: {hydro_missing}")
        
        # 9. 性能统计
        print("\n📈 Data Statistics:")
        print(f"  🧬 AA propensities features: {len(aa_props.columns)}")
        print(f"  ⚛️  Unique atom types: {len(atomic_hydro)}")
        print(f"  🧮 Unique residue types in hydrophobicity: {len(hydro_residues)}")
        print(f"  📚 AAindex database size: {len(aaindex)} indices")
        print(f"  🔗 Ligand propensity datasets: {len(ligand_props)}")
        
        print("\n🎉 All data loading tests PASSED!")
        assert True
        
    except Exception as e:
        print(f"\n❌ Data loading test FAILED: {e}")
        import traceback
        traceback.print_exc()
        assert False, f"Data loading test failed: {e}"


def demonstrate_usage():
    """演示数据加载器的实际使用"""
    print("\n" + "=" * 50)
    print("📚 Data Loader Usage Examples")
    print("=" * 50)
    
    try:
        loader = DataLoader()
        
        # 示例1: 获取特定氨基酸的倾向性
        print("\n🔍 Example 1: Get AA propensities for Alanine (A)")
        aa_props = loader.aa_props.load_propensities()
        if 'A' in aa_props.index:
            ala_props = aa_props.loc['A']
            print(f"  Alanine properties: {dict(ala_props)}")
        
        # 示例2: 查找特定原子的疏水性
        print("\n🔍 Example 2: Get hydrophobicity for Ala.CA")
        hydro_value = loader.atomic_props.get_atom_hydrophobicity('Ala', 'CA')
        print(f"  Ala.CA hydrophobicity: {hydro_value}")
        
        # 示例3: 使用AAindex查找特定属性
        print("\n🔍 Example 3: AAindex hydrophobicity scales")
        aaindex = loader.aaindex.load_aaindex()
        
        # 查找疏水性相关的条目
        hydrophobic_indices = []
        for key, entry in aaindex.items():
            desc = entry.get('description', '').lower()
            if 'hydrophob' in desc:
                hydrophobic_indices.append((key, entry.get('description', '')))
        
        print(f"  Found {len(hydrophobic_indices)} hydrophobicity-related indices:")
        for key, desc in hydrophobic_indices[:3]:  # 显示前3个
            print(f"    {key}: {desc}")
        
        print("\n✅ Usage examples completed!")
        
    except Exception as e:
        print(f"\n❌ Usage examples failed: {e}")


if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    print("🚀 Starting P2Rank Data Loader Tests...")
    
    # 运行主要测试
    success = test_data_loading()
    
    if success:
        # 运行使用示例
        demonstrate_usage()
        
        print("\n" + "=" * 50)
        print("🎉 P2Rank Data Loader - ALL TESTS PASSED! 🎉")
        print("💡 Data loading infrastructure is ready for use!")
        print("=" * 50)
    else:
        print("\n❌ Tests failed. Please check the data files and try again.")
        sys.exit(1)
