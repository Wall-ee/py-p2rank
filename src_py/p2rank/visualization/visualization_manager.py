#!/usr/bin/env python3
"""
P2Rank Python 可视化管理器

统一管理PyMOL、ChimeraX等可视化工具
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import json
import shutil

from .pymol_visualizer import PyMOLVisualizer
from .chimerax_visualizer import ChimeraXVisualizer


class VisualizationManager:
    """可视化管理器 - 统一接口"""
    
    def __init__(self, output_dir: str = "./visualizations"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        
        # 初始化可视化器
        self.pymol = PyMOLVisualizer()
        self.chimerax = ChimeraXVisualizer()
        
        # 支持的格式
        self.supported_formats = ['pymol', 'chimerax', 'both']
        
    def create_visualization(self, 
                           prediction_result,
                           protein_file: str,
                           output_name: Optional[str] = None,
                           formats: Union[str, List[str]] = 'both',
                           style: str = "surface",
                           **kwargs) -> Dict[str, str]:
        """
        创建可视化脚本
        
        Args:
            prediction_result: P2Rank预测结果
            protein_file: 蛋白质文件路径
            output_name: 输出名称 (默认使用蛋白质文件名)
            formats: 输出格式 ('pymol', 'chimerax', 'both' 或格式列表)
            style: 显示风格
            **kwargs: 其他参数
        
        Returns:
            Dict[str, str]: 生成的脚本文件路径
        """
        
        if not output_name:
            output_name = Path(protein_file).stem
        
        # 标准化格式参数
        if isinstance(formats, str):
            if formats == 'both':
                format_list = ['pymol', 'chimerax']
            else:
                format_list = [formats]
        else:
            format_list = formats
        
        # 验证格式
        for fmt in format_list:
            if fmt not in ['pymol', 'chimerax']:
                raise ValueError(f"不支持的格式: {fmt}")
        
        self.logger.info(f"🎨 创建可视化: {output_name} (格式: {format_list})")
        
        # 创建输出目录
        viz_dir = self.output_dir / output_name
        viz_dir.mkdir(exist_ok=True)
        
        # 复制蛋白质文件到可视化目录
        protein_dest = viz_dir / Path(protein_file).name
        if not protein_dest.exists():
            try:
                shutil.copy2(protein_file, protein_dest)
            except Exception as e:
                self.logger.warning(f"无法复制蛋白质文件: {e}")
        
        generated_files = {}
        
        # 生成PyMOL脚本
        if 'pymol' in format_list:
            pymol_script = viz_dir / f"{output_name}_pymol.pml"
            self.pymol.generate_script(
                prediction_result=prediction_result,
                protein_file=str(protein_dest),
                output_file=str(pymol_script),
                style=style,
                **kwargs
            )
            generated_files['pymol'] = str(pymol_script)
        
        # 生成ChimeraX脚本
        if 'chimerax' in format_list:
            chimerax_script = viz_dir / f"{output_name}_chimerax.cxc"
            self.chimerax.generate_script(
                prediction_result=prediction_result,
                protein_file=str(protein_dest),
                output_file=str(chimerax_script),
                style=style,
                **kwargs
            )
            generated_files['chimerax'] = str(chimerax_script)
        
        # 生成预测结果摘要
        self._generate_prediction_summary(prediction_result, viz_dir / "prediction_summary.json")
        
        # 生成README
        self._generate_readme(generated_files, viz_dir / "README.md", output_name)
        
        self.logger.info(f"✅ 可视化创建完成: {viz_dir}")
        return generated_files
    
    def create_batch_visualization(self, 
                                  prediction_results: List[Any],
                                  protein_files: List[str],
                                  output_names: Optional[List[str]] = None,
                                  formats: Union[str, List[str]] = 'both',
                                  style: str = "surface",
                                  **kwargs) -> List[Dict[str, str]]:
        """批量创建可视化"""
        
        if not output_names:
            output_names = [Path(pf).stem for pf in protein_files]
        
        if len(prediction_results) != len(protein_files) or len(protein_files) != len(output_names):
            raise ValueError("输入列表长度不一致")
        
        self.logger.info(f"🎨 批量创建可视化: {len(prediction_results)} 个结果")
        
        all_generated_files = []
        
        for result, protein_file, output_name in zip(prediction_results, protein_files, output_names):
            try:
                generated_files = self.create_visualization(
                    prediction_result=result,
                    protein_file=protein_file,
                    output_name=output_name,
                    formats=formats,
                    style=style,
                    **kwargs
                )
                all_generated_files.append(generated_files)
            except Exception as e:
                self.logger.error(f"创建可视化失败 {output_name}: {e}")
                all_generated_files.append({})
        
        # 生成批量主脚本
        self._generate_batch_master_scripts(all_generated_files, formats)
        
        return all_generated_files
    
    def create_comparison_visualization(self, 
                                      prediction_results: List[Any],
                                      protein_files: List[str],
                                      method_names: List[str],
                                      output_name: str = "comparison",
                                      formats: Union[str, List[str]] = 'both') -> Dict[str, str]:
        """创建方法比较可视化"""
        
        self.logger.info(f"🔬 创建比较可视化: {output_name}")
        
        # 标准化格式
        if isinstance(formats, str):
            if formats == 'both':
                format_list = ['pymol', 'chimerax']
            else:
                format_list = [formats]
        else:
            format_list = formats
        
        # 创建比较目录
        comp_dir = self.output_dir / output_name
        comp_dir.mkdir(exist_ok=True)
        
        generated_files = {}
        
        # 复制所有蛋白质文件
        dest_protein_files = []
        for protein_file in protein_files:
            dest_file = comp_dir / Path(protein_file).name
            if not dest_file.exists():
                try:
                    shutil.copy2(protein_file, dest_file)
                except Exception as e:
                    self.logger.warning(f"无法复制蛋白质文件: {e}")
            dest_protein_files.append(str(dest_file))
        
        # 生成比较脚本
        if 'pymol' in format_list:
            pymol_script = comp_dir / f"{output_name}_pymol_comparison.pml"
            self.pymol.create_comparison_script(
                prediction_results=prediction_results,
                protein_files=dest_protein_files,
                output_file=str(pymol_script),
                labels=method_names
            )
            generated_files['pymol'] = str(pymol_script)
        
        if 'chimerax' in format_list:
            # ChimeraX比较脚本 (简化版)
            chimerax_script = comp_dir / f"{output_name}_chimerax_comparison.cxc"
            self._generate_chimerax_comparison(
                prediction_results, dest_protein_files, method_names, str(chimerax_script)
            )
            generated_files['chimerax'] = str(chimerax_script)
        
        # 生成比较报告
        self._generate_comparison_report(
            prediction_results, method_names, comp_dir / "comparison_report.md"
        )
        
        return generated_files
    
    def _generate_prediction_summary(self, prediction_result, output_file: Path):
        """生成预测结果摘要"""
        
        summary = {
            'total_pockets': 0,
            'pockets': []
        }
        
        if hasattr(prediction_result, 'pockets') and prediction_result.pockets:
            summary['total_pockets'] = len(prediction_result.pockets)
            
            for i, pocket in enumerate(prediction_result.pockets):
                pocket_info = {
                    'rank': i + 1,
                    'score': getattr(pocket, 'score', 0.0),
                    'probability': getattr(pocket, 'probability', 0.0),
                    'center': getattr(pocket, 'center', [0, 0, 0])
                }
                
                if hasattr(pocket, 'surface_atoms'):
                    pocket_info['surface_atoms_count'] = len(pocket.surface_atoms)
                
                if hasattr(pocket, 'residues'):
                    pocket_info['residues_count'] = len(pocket.residues)
                
                summary['pockets'].append(pocket_info)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
    
    def _generate_readme(self, generated_files: Dict[str, str], output_file: Path, name: str):
        """生成README文件"""
        
        content = f"""# P2Rank Python - {name} 可视化

此目录包含 {name} 的P2Rank预测结果可视化文件。

## 文件说明

"""
        
        if 'pymol' in generated_files:
            content += f"""### PyMOL可视化
- **文件**: `{Path(generated_files['pymol']).name}`
- **使用方法**: 
  1. 启动PyMOL
  2. 执行: `@{Path(generated_files['pymol']).name}`
  3. 或者: File -> Run Script -> 选择脚本文件

"""
        
        if 'chimerax' in generated_files:
            content += f"""### ChimeraX可视化
- **文件**: `{Path(generated_files['chimerax']).name}`
- **使用方法**:
  1. 启动ChimeraX
  2. 执行: File -> Open -> 选择 .cxc 文件
  3. 或者: 在命令行中运行: `chimerax {Path(generated_files['chimerax']).name}`

"""
        
        content += """## 预测结果

查看 `prediction_summary.json` 了解详细的预测结果数据。

## 可视化特点

- 🎨 **颜色编码**: 口袋按预测分数着色
- 🔍 **多层次显示**: 支持表面、卡通、棒状模型
- 📊 **标签显示**: 口袋编号和分数标注
- 🎬 **交互性**: 可隐藏/显示特定口袋

## 生成信息

此可视化由P2Rank Python自动生成。

"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _generate_batch_master_scripts(self, all_generated_files: List[Dict[str, str]], formats):
        """生成批量主脚本"""
        
        if isinstance(formats, str):
            if formats == 'both':
                format_list = ['pymol', 'chimerax']
            else:
                format_list = [formats]
        else:
            format_list = formats
        
        # PyMOL主脚本
        if 'pymol' in format_list:
            pymol_master = self.output_dir / "load_all_pymol.pml"
            with open(pymol_master, 'w', encoding='utf-8') as f:
                f.write("# P2Rank Python - Load All PyMOL Visualizations\n\n")
                
                for i, generated in enumerate(all_generated_files):
                    if 'pymol' in generated:
                        script_path = Path(generated['pymol'])
                        rel_path = script_path.relative_to(self.output_dir)
                        f.write(f"@{rel_path}\n")
                
                f.write("\nprint 'All PyMOL visualizations loaded!'\n")
        
        # ChimeraX主脚本
        if 'chimerax' in format_list:
            chimerax_master = self.output_dir / "load_all_chimerax.cxc"
            with open(chimerax_master, 'w', encoding='utf-8') as f:
                f.write("# P2Rank Python - Load All ChimeraX Visualizations\n\n")
                
                for i, generated in enumerate(all_generated_files):
                    if 'chimerax' in generated:
                        script_path = Path(generated['chimerax'])
                        rel_path = script_path.relative_to(self.output_dir)
                        f.write(f"open {rel_path}\n")
                
                f.write("\nlog text 'All ChimeraX visualizations loaded!'\n")
    
    def _generate_chimerax_comparison(self, prediction_results, protein_files, method_names, output_file):
        """生成ChimeraX比较脚本"""
        
        lines = [
            "# P2Rank Python - ChimeraX Method Comparison",
            "# Load multiple prediction results for comparison",
            "",
        ]
        
        # 加载所有蛋白质
        for i, (protein_file, method_name) in enumerate(zip(protein_files, method_names)):
            rel_path = Path(protein_file).name
            lines.extend([
                f"# {method_name}",
                f"open {rel_path} name {method_name.lower()}",
                f"surface #{i+1}",
                f"color #{i+1} lightblue",
                ""
            ])
        
        # 设置比较视图
        lines.extend([
            "# Comparison view",
            "tile",
            "view",
            ""
        ])
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
    
    def _generate_comparison_report(self, prediction_results, method_names, output_file):
        """生成比较报告"""
        
        content = f"""# P2Rank Python - 方法比较报告

比较了 {len(method_names)} 种预测方法的结果。

## 方法列表

"""
        
        for i, method_name in enumerate(method_names):
            result = prediction_results[i] if i < len(prediction_results) else None
            pocket_count = len(result.pockets) if result and hasattr(result, 'pockets') else 0
            
            content += f"""### {method_name}
- 预测口袋数: {pocket_count}
"""
            
            if result and hasattr(result, 'pockets') and result.pockets:
                top_pocket = result.pockets[0]
                top_score = getattr(top_pocket, 'score', 0.0)
                content += f"- 最高分数: {top_score:.3f}\n"
        
        content += """
## 使用说明

1. 使用PyMOL比较脚本查看并排显示
2. 使用ChimeraX比较脚本进行交互式比较
3. 各方法的口袋用不同颜色区分

## 注意事项

- 口袋编号可能在不同方法间不对应
- 建议重点关注高分口袋的位置差异
- 可结合实验数据验证预测准确性

"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def get_visualization_summary(self) -> Dict[str, Any]:
        """获取可视化目录摘要"""
        
        summary = {
            'total_visualizations': 0,
            'by_format': {'pymol': 0, 'chimerax': 0},
            'visualizations': []
        }
        
        for viz_dir in self.output_dir.iterdir():
            if viz_dir.is_dir():
                viz_info = {
                    'name': viz_dir.name,
                    'files': []
                }
                
                # 检查文件类型
                pymol_files = list(viz_dir.glob("*_pymol.pml"))
                chimerax_files = list(viz_dir.glob("*_chimerax.cxc"))
                
                if pymol_files:
                    viz_info['files'].extend([str(f) for f in pymol_files])
                    summary['by_format']['pymol'] += len(pymol_files)
                
                if chimerax_files:
                    viz_info['files'].extend([str(f) for f in chimerax_files])
                    summary['by_format']['chimerax'] += len(chimerax_files)
                
                if viz_info['files']:
                    summary['visualizations'].append(viz_info)
                    summary['total_visualizations'] += 1
        
        return summary


# 便捷函数
def create_visualization(prediction_result, protein_file: str, **kwargs) -> Dict[str, str]:
    """便捷函数：创建可视化"""
    manager = VisualizationManager()
    return manager.create_visualization(prediction_result, protein_file, **kwargs)


def create_visualization_manager(output_dir: str = "./visualizations") -> VisualizationManager:
    """便捷函数：创建可视化管理器"""
    return VisualizationManager(output_dir=output_dir)
