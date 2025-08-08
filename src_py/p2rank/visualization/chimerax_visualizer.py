#!/usr/bin/env python3
"""
P2Rank Python ChimeraX可视化器

生成ChimeraX脚本用于蛋白质和结合位点可视化
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import colorsys
import math


class ChimeraXVisualizer:
    """ChimeraX可视化脚本生成器"""
    
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
        
        # ChimeraX设置
        self.default_settings = {
            'background_color': 'white',
            'silhouette_edges': True,
            'surface_transparency': 30,
            'lighting_mode': 'full'
        }
    
    def generate_script(self, 
                       prediction_result,
                       protein_file: str,
                       output_file: str,
                       style: str = "surface",
                       show_ligands: bool = True,
                       color_by_score: bool = True) -> str:
        """
        生成ChimeraX可视化脚本
        
        Args:
            prediction_result: P2Rank预测结果对象
            protein_file: 蛋白质结构文件路径
            output_file: 输出脚本文件路径
            style: 显示风格 ('surface', 'cartoon', 'sticks')
            show_ligands: 是否显示配体
            color_by_score: 是否按分数着色
        """
        
        self.logger.info(f"🎨 生成ChimeraX脚本: {output_file}")
        
        script_lines = []
        
        # 头部注释
        script_lines.extend(self._generate_header())
        
        # 加载蛋白质结构
        script_lines.extend(self._generate_protein_loading(protein_file))
        
        # 基本显示设置
        script_lines.extend(self._generate_basic_display(style))
        
        # 配体处理
        if show_ligands:
            script_lines.extend(self._generate_ligand_setup())
        
        # 口袋可视化
        if hasattr(prediction_result, 'pockets') and prediction_result.pockets:
            script_lines.extend(self._generate_pocket_visualization(
                prediction_result.pockets, color_by_score
            ))
        
        # 视图和相机设置
        script_lines.extend(self._generate_view_settings())
        
        # 保存脚本
        script_content = '\n'.join(script_lines)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        self.logger.info(f"✅ ChimeraX脚本已保存: {output_file}")
        return script_content
    
    def _generate_header(self) -> List[str]:
        """生成脚本头部"""
        
        lines = [
            "# P2Rank Python - ChimeraX Visualization Script",
            "# Generated automatically",
            "# Run this script in ChimeraX: File -> Open -> select this .cxc file",
            "",
        ]
        
        return lines
    
    def _generate_protein_loading(self, protein_file: str) -> List[str]:
        """生成蛋白质加载代码"""
        
        # 确保使用相对路径以提高可移植性
        rel_protein_file = Path(protein_file).name
        
        lines = [
            f"# Load protein structure",
            f"open {rel_protein_file}",
            "",
            "# Clean up structure",
            "delete solvent",
            "delete ~protein",
            ""
        ]
        
        return lines
    
    def _generate_basic_display(self, style: str) -> List[str]:
        """生成基本显示设置"""
        
        lines = [
            "# Basic display settings",
            f"set bg_color {self.default_settings['background_color']}",
            ""
        ]
        
        # 根据风格设置显示
        if style == "surface":
            lines.extend([
                "# Surface representation",
                "surface",
                "hide ~protein",
                "color protein #d9d9ff",
                f"transparency {self.default_settings['surface_transparency']}",
                ""
            ])
        elif style == "cartoon":
            lines.extend([
                "# Cartoon representation",
                "cartoon",
                "hide atoms",
                "color protein lightblue",
                ""
            ])
        elif style == "sticks":
            lines.extend([
                "# Stick representation", 
                "show atoms",
                "style stick",
                "color protein lightblue",
                ""
            ])
        
        # 光照设置
        if self.default_settings['silhouette_edges']:
            lines.append("graphics silhouettes true")
        
        lines.append("")
        
        return lines
    
    def _generate_ligand_setup(self) -> List[str]:
        """生成配体设置代码"""
        
        lines = [
            "# Ligand setup",
            "select ligand",
            "color ligand magenta",
            "style ligand stick",
            "size ligand stickRadius 0.2",
            ""
        ]
        
        return lines
    
    def _generate_pocket_visualization(self, pockets: List[Any], color_by_score: bool) -> List[str]:
        """生成口袋可视化代码"""
        
        lines = [
            "# Pocket visualization",
            ""
        ]
        
        # 定义颜色
        for i, pocket in enumerate(pockets):
            if color_by_score:
                color = self._score_to_color(pocket.score if hasattr(pocket, 'score') else 0.5)
            else:
                color = self.pocket_colors[i % len(self.pocket_colors)]
            
            color_name = f"color_pocket{i+1}"
            lines.append(f"color name {color_name} {color}")
        
        lines.append("")
        
        # 为每个口袋创建选择和着色
        for i, pocket in enumerate(pockets):
            pocket_name = f"pocket{i+1}"
            color_name = f"color_pocket{i+1}"
            
            lines.append(f"# Pocket {i+1}")
            
            # 创建原子选择
            atom_selections = []
            
            if hasattr(pocket, 'surface_atoms') and pocket.surface_atoms:
                # 使用表面原子
                atom_list = " ".join([f"@@serial_number={atom_id}" for atom_id in pocket.surface_atoms])
                lines.append(f"name {pocket_name}_atoms {atom_list}")
                
            elif hasattr(pocket, 'residues') and pocket.residues:
                # 使用残基
                residue_list = " ".join([f":{res}" for res in pocket.residues])
                lines.append(f"name {pocket_name}_atoms {residue_list}")
            
            # 着色口袋
            lines.extend([
                f"color {pocket_name}_atoms {color_name}",
                ""
            ])
        
        # 添加口袋中心和标签
        lines.append("# Pocket centers and labels")
        
        for i, pocket in enumerate(pockets):
            if hasattr(pocket, 'center') and pocket.center:
                center = pocket.center
                score = getattr(pocket, 'score', 0.0)
                
                lines.extend([
                    f"shape sphere center {center[0]:.3f},{center[1]:.3f},{center[2]:.3f} radius 1.0 color {self.pocket_colors[i % len(self.pocket_colors)]}",
                    f"2dlabels create pocket{i+1} text 'P{i+1} ({score:.2f})' xpos 0.1 ypos {0.9 - i*0.05} color black size 14",
                ])
        
        lines.append("")
        
        return lines
    
    def _generate_view_settings(self) -> List[str]:
        """生成视图设置"""
        
        lines = [
            "# View settings",
            "view",
            "center",
            "",
            "# Lighting",
            f"lighting {self.default_settings['lighting_mode']}",
            "",
            "# Optional: Save session",
            "# save session protein_pockets.cxs",
            "",
            "# Optional: Save high-quality image",
            "# set bg_color white",
            "# graphics quality higher",
            "# save image protein_pockets.png width 2400 height 2400 supersample 3",
            "",
            "log text 'P2Rank Python ChimeraX visualization loaded successfully!'"
        ]
        
        return lines
    
    def _score_to_color(self, score: float) -> str:
        """将分数转换为颜色"""
        # 使用HSV颜色空间：红色(低分) -> 黄色(中分) -> 绿色(高分) 
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
    
    def generate_batch_script(self, 
                             prediction_results: List[Any],
                             protein_files: List[str],
                             output_dir: str,
                             style: str = "surface") -> List[str]:
        """批量生成ChimeraX脚本"""
        
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        generated_scripts = []
        
        for i, (result, protein_file) in enumerate(zip(prediction_results, protein_files)):
            protein_name = Path(protein_file).stem
            script_file = output_dir / f"{protein_name}_chimerax.cxc"
            
            self.generate_script(
                prediction_result=result,
                protein_file=protein_file,
                output_file=str(script_file),
                style=style
            )
            
            generated_scripts.append(str(script_file))
        
        # 生成主脚本
        master_script = output_dir / "load_all_visualizations.cxc"
        with open(master_script, 'w', encoding='utf-8') as f:
            f.write("# P2Rank Python - Master ChimeraX Visualization Script\n")
            f.write("# Load all generated visualizations\n\n")
            
            for script_file in generated_scripts:
                f.write(f"open {Path(script_file).name}\n")
            
            f.write("\nlog text 'All P2Rank visualizations loaded!'\n")
        
        generated_scripts.append(str(master_script))
        
        self.logger.info(f"✅ 批量生成完成: {len(generated_scripts)} 个脚本")
        return generated_scripts
    
    def create_interactive_session(self, 
                                  prediction_result,
                                  protein_file: str,
                                  output_file: str) -> str:
        """创建交互式会话脚本"""
        
        self.logger.info(f"🎮 生成交互式脚本: {output_file}")
        
        script_lines = []
        
        # 头部
        script_lines.extend(self._generate_header())
        
        # 基础加载
        script_lines.extend(self._generate_protein_loading(protein_file))
        script_lines.extend(self._generate_basic_display("surface"))
        
        # 交互式控制
        script_lines.extend([
            "# Interactive controls",
            "# Key bindings for pocket visualization",
            "",
            "# Press '1'-'8' to toggle individual pockets",
        ])
        
        if hasattr(prediction_result, 'pockets') and prediction_result.pockets:
            for i, pocket in enumerate(prediction_result.pockets[:8]):  # 最多8个口袋
                key = str(i + 1)
                color = self.pocket_colors[i % len(self.pocket_colors)]
                
                script_lines.extend([
                    f"# Pocket {i+1} controls",
                    f"key {key} 'select pocket{i+1}_atoms; color sel {color}; ~select'",
                ])
        
        script_lines.extend([
            "",
            "# Press 'a' to show all pockets",
            "key a 'show; style stick'",
            "",
            "# Press 'h' to hide all pockets", 
            "key h 'hide atoms; surface'",
            "",
            "# Press 's' to save current view",
            "key s 'save session current_view.cxs'",
        ])
        
        # 保存脚本
        script_content = '\n'.join(script_lines)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        return script_content
    
    def create_animation_script(self, 
                               prediction_result,
                               protein_file: str,
                               output_file: str,
                               animation_type: str = "rotate") -> str:
        """创建动画脚本"""
        
        self.logger.info(f"🎬 生成动画脚本: {output_file}")
        
        script_lines = []
        
        # 头部
        script_lines.extend(self._generate_header())
        
        # 基础设置
        script_lines.extend(self._generate_protein_loading(protein_file))
        script_lines.extend(self._generate_basic_display("surface"))
        
        if hasattr(prediction_result, 'pockets') and prediction_result.pockets:
            script_lines.extend(self._generate_pocket_visualization(
                prediction_result.pockets, color_by_score=True
            ))
        
        # 动画设置
        script_lines.extend([
            "",
            "# Animation settings",
            "set bg_color white",
            "graphics quality higher",
            ""
        ])
        
        if animation_type == "rotate":
            script_lines.extend([
                "# Rotation animation",
                "movie record",
                "turn y 3 360",  # 360度旋转，每帧3度
                "wait 120",      # 等待120帧
                "movie stop",
                "movie encode output animation.mp4 format mp4",
            ])
        elif animation_type == "pocket_reveal":
            script_lines.extend([
                "# Pocket reveal animation",
                "movie record",
                "hide all",
                "wait 30",
            ])
            
            # 逐个显示口袋
            for i in range(len(prediction_result.pockets)):
                script_lines.extend([
                    f"show pocket{i+1}_atoms",
                    "wait 30",
                ])
            
            script_lines.extend([
                "wait 60",
                "movie stop",
                "movie encode output pocket_reveal.mp4 format mp4",
            ])
        
        # 保存脚本
        script_content = '\n'.join(script_lines)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        return script_content


# 便捷函数
def generate_chimerax_script(prediction_result, protein_file: str, output_file: str, **kwargs) -> str:
    """便捷函数：生成ChimeraX脚本"""
    visualizer = ChimeraXVisualizer()
    return visualizer.generate_script(prediction_result, protein_file, output_file, **kwargs)


def create_chimerax_visualizer(**kwargs) -> ChimeraXVisualizer:
    """便捷函数：创建ChimeraX可视化器"""
    return ChimeraXVisualizer(**kwargs)
