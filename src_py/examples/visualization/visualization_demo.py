#!/usr/bin/env python3
"""
P2Rank Python 可视化演示

展示如何使用P2Rank Python可视化系统
"""

import sys
import logging
from pathlib import Path

# 添加p2rank路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from p2rank.visualization import VisualizationManager, PyMOLVisualizer, ChimeraXVisualizer
from p2rank import P2RankPredictor


class MockPocket:
    """模拟口袋对象 (用于演示)"""
    
    def __init__(self, score, center, surface_atoms=None, residues=None):
        self.score = score
        self.probability = score  # 简化
        self.center = center
        self.surface_atoms = surface_atoms or []
        self.residues = residues or []


class MockPredictionResult:
    """模拟预测结果 (用于演示)"""
    
    def __init__(self, pockets):
        self.pockets = pockets


def create_demo_prediction_result():
    """创建演示用的预测结果"""
    
    # 模拟1FBL蛋白质的口袋
    pockets = [
        MockPocket(
            score=0.95,
            center=[70.5, 83.4, -11.5],
            surface_atoms=[32, 33, 651, 658, 659, 664, 670, 676, 679, 692, 700],
            residues=["A_103", "A_180", "A_181", "A_182", "A_183"]
        ),
        MockPocket(
            score=0.75,
            center=[89.2, 98.6, 26.8],
            surface_atoms=[1890, 1891, 1909, 1910, 1926, 1991, 2064],
            residues=["A_337", "A_339", "A_341", "A_348"]
        ),
        MockPocket(
            score=0.65,
            center=[61.1, 70.7, -13.6],
            surface_atoms=[171, 172, 173, 472, 499, 501, 514, 515],
            residues=["A_119", "A_156", "A_160", "A_162"]
        ),
        MockPocket(
            score=0.45,
            center=[90.9, 95.9, 10.8],
            surface_atoms=[1488, 1489, 1490, 1497, 1499, 1513],
            residues=["A_290", "A_291", "A_293", "A_304"]
        )
    ]
    
    return MockPredictionResult(pockets)


def demo_basic_visualization():
    """演示基础可视化功能"""
    
    print("🎨 演示1: 基础可视化功能")
    print("=" * 50)
    
    # 创建可视化管理器
    viz_manager = VisualizationManager(output_dir="./demo_visualizations")
    
    # 模拟预测结果
    prediction_result = create_demo_prediction_result()
    
    # 检查1FBL文件是否存在
    protein_files = [
        "./predict_1fbl/visualizations/data/1fbl.pdb",
        "../distro/test_data/1fbl.pdb",
        "./1fbl.pdb"
    ]
    
    protein_file = None
    for pf in protein_files:
        if Path(pf).exists():
            protein_file = pf
            break
    
    if not protein_file:
        print("⚠️  未找到1FBL蛋白质文件，使用虚拟路径演示")
        protein_file = "./1fbl.pdb"  # 虚拟路径用于演示
    else:
        print(f"✅ 找到蛋白质文件: {protein_file}")
    
    # 创建可视化
    try:
        generated_files = viz_manager.create_visualization(
            prediction_result=prediction_result,
            protein_file=protein_file,
            output_name="1fbl_demo",
            formats='both',  # 生成PyMOL和ChimeraX脚本
            style='surface',
            show_ligands=True,
            color_by_score=True
        )
        
        print("✅ 生成的可视化文件:")
        for format_name, file_path in generated_files.items():
            print(f"  {format_name}: {file_path}")
        
    except Exception as e:
        print(f"❌ 生成可视化失败: {e}")


def demo_pymol_only():
    """演示PyMOL专用功能"""
    
    print("\n🐍 演示2: PyMOL专用功能")
    print("=" * 50)
    
    # 创建PyMOL可视化器
    pymol_viz = PyMOLVisualizer()
    
    prediction_result = create_demo_prediction_result()
    protein_file = "./1fbl.pdb"  # 虚拟路径
    
    try:
        # 基础脚本
        basic_script = pymol_viz.generate_script(
            prediction_result=prediction_result,
            protein_file=protein_file,
            output_file="./demo_visualizations/1fbl_pymol_basic.pml",
            style="surface"
        )
        print("✅ 生成基础PyMOL脚本")
        
        # 卡通风格
        cartoon_script = pymol_viz.generate_script(
            prediction_result=prediction_result,
            protein_file=protein_file,
            output_file="./demo_visualizations/1fbl_pymol_cartoon.pml",
            style="cartoon"
        )
        print("✅ 生成卡通风格PyMOL脚本")
        
        print("\n📄 PyMOL脚本预览 (前10行):")
        print("-" * 30)
        lines = basic_script.split('\n')[:10]
        for line in lines:
            print(line)
        
    except Exception as e:
        print(f"❌ 生成PyMOL脚本失败: {e}")


def demo_chimerax_features():
    """演示ChimeraX特色功能"""
    
    print("\n🔬 演示3: ChimeraX特色功能")
    print("=" * 50)
    
    # 创建ChimeraX可视化器
    chimerax_viz = ChimeraXVisualizer()
    
    prediction_result = create_demo_prediction_result()
    protein_file = "./1fbl.pdb"
    
    try:
        # 基础脚本
        basic_script = chimerax_viz.generate_script(
            prediction_result=prediction_result,
            protein_file=protein_file,
            output_file="./demo_visualizations/1fbl_chimerax_basic.cxc",
            style="surface"
        )
        print("✅ 生成基础ChimeraX脚本")
        
        # 交互式脚本
        interactive_script = chimerax_viz.create_interactive_session(
            prediction_result=prediction_result,
            protein_file=protein_file,
            output_file="./demo_visualizations/1fbl_chimerax_interactive.cxc"
        )
        print("✅ 生成交互式ChimeraX脚本")
        
        # 动画脚本
        animation_script = chimerax_viz.create_animation_script(
            prediction_result=prediction_result,
            protein_file=protein_file,
            output_file="./demo_visualizations/1fbl_chimerax_animation.cxc",
            animation_type="rotate"
        )
        print("✅ 生成动画ChimeraX脚本")
        
        print("\n📄 ChimeraX脚本预览 (前8行):")
        print("-" * 30)
        lines = basic_script.split('\n')[:8]
        for line in lines:
            print(line)
        
    except Exception as e:
        print(f"❌ 生成ChimeraX脚本失败: {e}")


def demo_batch_processing():
    """演示批量处理功能"""
    
    print("\n📦 演示4: 批量处理功能")
    print("=" * 50)
    
    viz_manager = VisualizationManager(output_dir="./demo_visualizations")
    
    # 模拟多个预测结果
    prediction_results = [
        create_demo_prediction_result(),
        create_demo_prediction_result(),  # 实际应该是不同的结果
        create_demo_prediction_result()
    ]
    
    protein_files = ["./1fbl.pdb", "./2abc.pdb", "./3xyz.pdb"]  # 虚拟路径
    output_names = ["protein_1", "protein_2", "protein_3"]
    
    try:
        all_generated = viz_manager.create_batch_visualization(
            prediction_results=prediction_results,
            protein_files=protein_files,
            output_names=output_names,
            formats=['pymol'],  # 只生成PyMOL脚本以节省时间
            style='surface'
        )
        
        print(f"✅ 批量生成完成: {len(all_generated)} 组可视化")
        
        for i, generated in enumerate(all_generated):
            if generated:
                print(f"  {output_names[i]}: {list(generated.keys())}")
        
    except Exception as e:
        print(f"❌ 批量生成失败: {e}")


def demo_comparison_visualization():
    """演示方法比较可视化"""
    
    print("\n🔬 演示5: 方法比较可视化")
    print("=" * 50)
    
    viz_manager = VisualizationManager(output_dir="./demo_visualizations")
    
    # 模拟不同方法的预测结果
    method1_result = create_demo_prediction_result()
    
    # 模拟第二种方法 (稍微不同的结果)
    method2_pockets = [
        MockPocket(score=0.92, center=[70.0, 83.0, -11.0]),
        MockPocket(score=0.78, center=[89.5, 98.0, 27.0]),
        MockPocket(score=0.63, center=[61.5, 71.0, -13.0])
    ]
    method2_result = MockPredictionResult(method2_pockets)
    
    prediction_results = [method1_result, method2_result]
    protein_files = ["./1fbl.pdb", "./1fbl.pdb"]  # 同一个蛋白质
    method_names = ["P2Rank_Default", "P2Rank_Optimized"]
    
    try:
        comparison_files = viz_manager.create_comparison_visualization(
            prediction_results=prediction_results,
            protein_files=protein_files,
            method_names=method_names,
            output_name="method_comparison",
            formats=['pymol']
        )
        
        print("✅ 生成比较可视化:")
        for format_name, file_path in comparison_files.items():
            print(f"  {format_name}: {file_path}")
        
    except Exception as e:
        print(f"❌ 生成比较可视化失败: {e}")


def demo_visualization_summary():
    """演示可视化摘要功能"""
    
    print("\n📊 演示6: 可视化摘要")
    print("=" * 50)
    
    viz_manager = VisualizationManager(output_dir="./demo_visualizations")
    
    try:
        summary = viz_manager.get_visualization_summary()
        
        print("📈 可视化目录摘要:")
        print(f"  总可视化数: {summary['total_visualizations']}")
        print(f"  PyMOL脚本: {summary['by_format']['pymol']}")
        print(f"  ChimeraX脚本: {summary['by_format']['chimerax']}")
        
        if summary['visualizations']:
            print("\n📁 可视化列表:")
            for viz in summary['visualizations'][:5]:  # 显示前5个
                print(f"  - {viz['name']}: {len(viz['files'])} 个文件")
        
    except Exception as e:
        print(f"❌ 获取摘要失败: {e}")


def display_usage_guide():
    """显示使用指南"""
    
    print("\n📚 使用指南")
    print("=" * 50)
    print("""
🎯 如何使用生成的可视化脚本:

PyMOL脚本 (.pml):
1. 启动PyMOL
2. 执行: @script_name.pml
3. 或: File -> Run Script -> 选择.pml文件

ChimeraX脚本 (.cxc):
1. 启动ChimeraX  
2. 执行: File -> Open -> 选择.cxc文件
3. 或命令行: chimerax script_name.cxc

🎨 可视化特色:
- 口袋按预测分数着色 (红->黄->绿)
- 支持表面、卡通、棒状显示
- 口袋中心标记和分数标签
- 交互式口袋显示/隐藏
- 高质量图像输出设置

📁 输出文件结构:
demo_visualizations/
├── protein_name/
│   ├── protein.pdb           # 蛋白质文件副本
│   ├── protein_pymol.pml     # PyMOL脚本
│   ├── protein_chimerax.cxc  # ChimeraX脚本
│   ├── prediction_summary.json # 预测摘要
│   └── README.md             # 使用说明
└── load_all_pymol.pml        # 批量加载脚本

🚀 实际使用中，请:
1. 替换虚拟蛋白质路径为真实文件
2. 使用真实的P2Rank预测结果
3. 根据需要调整可视化参数
""")


def main():
    """主函数"""
    
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    print("🎨 P2Rank Python 可视化系统演示")
    print("=" * 60)
    print("本演示展示P2Rank Python可视化系统的各种功能")
    print("注意: 使用模拟数据进行演示，实际使用时请提供真实数据\n")
    
    # 创建输出目录
    Path("./demo_visualizations").mkdir(exist_ok=True)
    
    # 运行各个演示
    try:
        demo_basic_visualization()
        demo_pymol_only()
        demo_chimerax_features()
        demo_batch_processing()
        demo_comparison_visualization()
        demo_visualization_summary()
        
        display_usage_guide()
        
        print("\n🎉 可视化演示完成!")
        print("📁 生成的文件保存在: ./demo_visualizations/")
        print("📖 查看各目录下的README.md了解使用方法")
        
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
