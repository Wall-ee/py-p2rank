#!/usr/bin/env python3
"""
P2Rank Python PyMOL可视化器

生成PyMOL脚本用于蛋白质和结合位点可视化
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import colorsys
import math


class PyMOLVisualizer:
    """PyMOL可视化脚本生成器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 默认颜色主题
        self.pocket_colors = [
            "#5c93e6",  # 蓝色
            "#7d47b3",  # 紫色
            "#e65cae",  # 粉色
            "#b36847",  # 棕色
            "#47b368",  # 绿色
            "#e6935c",  # 橙色
            "#93e65c",  # 青绿色
            "#e65c93",  # 玫瑰色
        ]
        
        # PyMOL设置
        self.default_settings = {
            'depth_cue': 1,
            'fog_start': 0.4,
            'spec_power': 200,
            'spec_refl': 0,
            'bg_gradient': True,
            'surface_transparency': 0.15
        }
    
    def generate_script(self, 
                       prediction_result,
                       protein_file: str,
                       output_file: str,
                       style: str = "surface",
                       show_ligands: bool = True,
                       color_by_score: bool = True) -> str:
        """
        生成PyMOL可视化脚本
        
        Args:
            prediction_result: P2Rank预测结果对象
            protein_file: 蛋白质结构文件路径
            output_file: 输出脚本文件路径
            style: 显示风格 ('surface', 'cartoon', 'sticks')
            show_ligands: 是否显示配体
            color_by_score: 是否按分数着色
        """
        
        self.logger.info(f"🎨 生成PyMOL脚本: {output_file}")
        
        script_lines = []
        
        # 头部设置
        script_lines.extend(self._generate_header())
        
        # 加载蛋白质结构
        script_lines.extend(self._generate_protein_loading(protein_file))
        
        # 配体处理
        if show_ligands:
            script_lines.extend(self._generate_ligand_setup())
        
        # 基本显示设置
        script_lines.extend(self._generate_basic_display(style))
        
        # 口袋可视化
        if hasattr(prediction_result, 'pockets') and prediction_result.pockets:
            script_lines.extend(self._generate_pocket_visualization(
                prediction_result.pockets, color_by_score
            ))
        
        # 相机和视图设置
        script_lines.extend(self._generate_view_settings())
        
        # 保存脚本
        script_content = '\n'.join(script_lines)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        self.logger.info(f"✅ PyMOL脚本已保存: {output_file}")
        return script_content
    
    def _generate_header(self) -> List[str]:
        """生成脚本头部"""
        
        lines = [
            "# P2Rank Python - PyMOL Visualization Script",
            "# Generated automatically",
            "",
            "from pymol import cmd, stored",
            "",
            "# Basic settings",
            f"set depth_cue, {self.default_settings['depth_cue']}",
            f"set fog_start, {self.default_settings['fog_start']}",
            "",
            "# Background gradient",
            "set_color b_col, [36,36,85]",
            "set_color t_col, [10,10,10]",
            "set bg_rgb_bottom, b_col",
            "set bg_rgb_top, t_col",
            "set bg_gradient" if self.default_settings['bg_gradient'] else "# set bg_gradient",
            "",
            "# Surface properties",
            f"set spec_power = {self.default_settings['spec_power']}",
            f"set spec_refl = {self.default_settings['spec_refl']}",
            ""
        ]
        
        return lines
    
    def _generate_protein_loading(self, protein_file: str) -> List[str]:
        """生成蛋白质加载代码"""
        
        # 确保使用相对路径以提高可移植性
        rel_protein_file = Path(protein_file).name
        
        lines = [
            f"# Load protein structure",
            f'load "{rel_protein_file}", protein',
            "",
            "# Clean up structure",
            "remove solvent",
            "remove inorganic",
            ""
        ]
        
        return lines
    
    def _generate_ligand_setup(self) -> List[str]:
        """生成配体设置代码"""
        
        lines = [
            "# Ligand setup",
            "create ligands, protein and organic",
            "select xlig, protein and organic",
            "delete xlig",
            ""
        ]
        
        return lines
    
    def _generate_basic_display(self, style: str) -> List[str]:
        """生成基本显示设置"""
        
        lines = [
            "# Basic display settings",
            "hide everything, all",
            "",
            "# Protein coloring",
            "color white, elem c",
            "color bluewhite, protein",
            ""
        ]
        
        # 根据风格添加显示命令
        if style == "surface":
            lines.extend([
                "# Surface representation",
                "show surface, protein",
                f"set transparency, {self.default_settings['surface_transparency']}, protein",
                ""
            ])
        elif style == "cartoon":
            lines.extend([
                "# Cartoon representation", 
                "show cartoon, protein",
                "set cartoon_transparency, 0.1, protein",
                ""
            ])
        elif style == "sticks":
            lines.extend([
                "# Stick representation",
                "show sticks, protein",
                ""
            ])
        
        # 配体显示
        lines.extend([
            "# Ligand display",
            "show sticks, ligands",
            "set stick_color, magenta, ligands",
            ""
        ])
        
        return lines
    
    def _generate_pocket_visualization(self, pockets: List[Any], color_by_score: bool) -> List[str]:
        """生成口袋可视化代码"""
        
        lines = [
            "# Pocket visualization",
            "# Define pocket colors"
        ]
        
        # 定义颜色
        for i, pocket in enumerate(pockets):
            if color_by_score:
                color = self._score_to_color(pocket.score if hasattr(pocket, 'score') else 0.5)
            else:
                color = self.pocket_colors[i % len(self.pocket_colors)]
            
            color_name = f"color_pocket{i+1}"
            rgb = self._hex_to_rgb(color)
            
            lines.append(f"set_color {color_name}, [{rgb[0]},{rgb[1]},{rgb[2]}]")
        
        lines.append("")
        
        # 为每个口袋创建选择和着色
        for i, pocket in enumerate(pockets):
            pocket_name = f"pocket{i+1}"
            color_name = f"color_pocket{i+1}"
            
            lines.extend([
                f"# Pocket {i+1}",
                f"select {pocket_name}_atoms, none",
            ])
            
            # 添加口袋原子
            if hasattr(pocket, 'surface_atoms') and pocket.surface_atoms:
                atom_selection = " or ".join([f"id {atom_id}" for atom_id in pocket.surface_atoms])
                lines.append(f"select {pocket_name}_atoms, {atom_selection}")
            elif hasattr(pocket, 'residues') and pocket.residues:
                residue_selection = " or ".join([f"resi {res}" for res in pocket.residues])
                lines.append(f"select {pocket_name}_atoms, {residue_selection}")
            
            lines.extend([
                f"color {color_name}, {pocket_name}_atoms",
                f"show spheres, {pocket_name}_atoms",
                f"set sphere_scale, 0.3, {pocket_name}_atoms",
                ""
            ])
        
        # 添加口袋标签
        lines.extend([
            "# Pocket labels",
            "set label_size, 20",
            "set label_color, white",
            ""
        ])
        
        for i, pocket in enumerate(pockets):
            if hasattr(pocket, 'center') and pocket.center:
                center = pocket.center
                score = getattr(pocket, 'score', 0.0)
                lines.append(f'pseudoatom pocket{i+1}_center, pos=[{center[0]:.3f},{center[1]:.3f},{center[2]:.3f}]')
                lines.append(f'label pocket{i+1}_center, "P{i+1} ({score:.2f})"')
        
        return lines
    
    def _generate_view_settings(self) -> List[str]:
        """生成视图设置"""
        
        lines = [
            "",
            "# View settings",
            "zoom protein",
            "orient protein",
            "",
            "# Ray tracing settings (for high-quality images)",
            "set ray_trace_mode, 1",
            "set ray_shadows, 1",
            "set antialias, 2",
            "",
            "# Uncomment to save high-quality image:",
            "# ray 1200, 1200",
            "# png protein_pockets.png, dpi=300",
            "",
            "print 'P2Rank Python visualization loaded successfully!'"
        ]
        
        return lines
    
    def _score_to_color(self, score: float) -> str:
        """将分数转换为颜色"""
        # 使用HSV颜色空间：红色(低分) -> 黄色(中分) -> 绿色(高分)
        # H: 0(红) -> 120(绿), S: 1, V: 1
        hue = min(120, max(0, score * 120)) / 360.0
        saturation = 1.0
        value = 1.0
        
        rgb = colorsys.hsv_to_rgb(hue, saturation, value)
        hex_color = '#{:02x}{:02x}{:02x}'.format(
            int(rgb[0] * 255),
            int(rgb[1] * 255), 
            int(rgb[2] * 255)
        )
        
        return hex_color
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """将十六进制颜色转换为RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def generate_batch_script(self, 
                             prediction_results: List[Any],
                             protein_files: List[str],
                             output_dir: str,
                             style: str = "surface") -> List[str]:
        """批量生成PyMOL脚本"""
        
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        generated_scripts = []
        
        for i, (result, protein_file) in enumerate(zip(prediction_results, protein_files)):
            protein_name = Path(protein_file).stem
            script_file = output_dir / f"{protein_name}_pymol.pml"
            
            self.generate_script(
                prediction_result=result,
                protein_file=protein_file,
                output_file=str(script_file),
                style=style
            )
            
            generated_scripts.append(str(script_file))
        
        # 生成主脚本
        master_script = output_dir / "load_all_visualizations.pml"
        with open(master_script, 'w', encoding='utf-8') as f:
            f.write("# P2Rank Python - Master Visualization Script\n")
            f.write("# Load all generated visualizations\n\n")
            
            for script_file in generated_scripts:
                f.write(f"@{Path(script_file).name}\n")
            
            f.write("\nprint 'All P2Rank visualizations loaded!'\n")
        
        generated_scripts.append(str(master_script))
        
        self.logger.info(f"✅ 批量生成完成: {len(generated_scripts)} 个脚本")
        return generated_scripts
    
    def create_comparison_script(self, 
                                prediction_results: List[Any],
                                protein_files: List[str],
                                output_file: str,
                                labels: Optional[List[str]] = None) -> str:
        """创建多个预测结果的比较脚本"""
        
        self.logger.info(f"🔬 生成比较脚本: {output_file}")
        
        if not labels:
            labels = [f"Method_{i+1}" for i in range(len(prediction_results))]
        
        script_lines = []
        
        # 头部
        script_lines.extend(self._generate_header())
        
        # 加载所有蛋白质
        for i, (protein_file, label) in enumerate(zip(protein_files, labels)):
            rel_path = Path(protein_file).name
            object_name = f"protein_{label.lower()}"
            
            script_lines.extend([
                f"# Load {label}",
                f'load "{rel_path}", {object_name}',
                f"hide everything, {object_name}",
                f"show cartoon, {object_name}",
                ""
            ])
        
        # 设置比较视图
        grid_size = math.ceil(math.sqrt(len(prediction_results)))
        
        script_lines.extend([
            "# Comparison view setup",
            f"set grid_mode, 1",
            f"set grid_slot, 1, protein_{labels[0].lower()}",
        ])
        
        for i, label in enumerate(labels[1:], 2):
            script_lines.append(f"set grid_slot, {i}, protein_{label.lower()}")
        
        script_lines.extend([
            "",
            "zoom all",
            "print 'P2Rank comparison visualization loaded!'"
        ])
        
        # 保存脚本
        script_content = '\n'.join(script_lines)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        return script_content


# 便捷函数
def generate_pymol_script(prediction_result, protein_file: str, output_file: str, **kwargs) -> str:
    """便捷函数：生成PyMOL脚本"""
    visualizer = PyMOLVisualizer()
    return visualizer.generate_script(prediction_result, protein_file, output_file, **kwargs)


def create_pymol_visualizer(**kwargs) -> PyMOLVisualizer:
    """便捷函数：创建PyMOL可视化器"""
    return PyMOLVisualizer(**kwargs)
