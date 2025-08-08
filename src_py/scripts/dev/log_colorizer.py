#!/usr/bin/env python3
"""
P2Rank Python 日志着色工具
移植自原始的 logc.sh

为日志输出添加颜色，提高可读性
"""

import argparse
import sys
import re
from typing import TextIO, Optional
from enum import Enum


class Color(Enum):
    """ANSI颜色代码"""
    
    # 基础颜色
    BLACK = '\033[0;30m'
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[0;33m'
    BLUE = '\033[0;34m'
    MAGENTA = '\033[0;35m'
    CYAN = '\033[0;36m'
    WHITE = '\033[0;37m'
    
    # 高亮颜色
    BRIGHT_BLACK = '\033[1;30m'
    BRIGHT_RED = '\033[1;31m'
    BRIGHT_GREEN = '\033[1;32m'
    BRIGHT_YELLOW = '\033[1;33m'
    BRIGHT_BLUE = '\033[1;34m'
    BRIGHT_MAGENTA = '\033[1;35m'
    BRIGHT_CYAN = '\033[1;36m'
    BRIGHT_WHITE = '\033[1;37m'
    
    # 重置
    RESET = '\033[0m'


class LogColorizer:
    """日志着色器"""
    
    def __init__(self, 
                 enable_colors: bool = True,
                 custom_patterns: Optional[dict] = None):
        self.enable_colors = enable_colors and self._supports_color()
        
        # 默认的日志级别模式
        self.default_patterns = {
            r'\bFATAL\b': Color.BRIGHT_RED,
            r'\bERROR\b': Color.BRIGHT_RED,
            r'\bWARN\b|\bWARNING\b': Color.BRIGHT_YELLOW,
            r'\bINFO\b': Color.BRIGHT_WHITE,
            r'\bDEBUG\b': Color.BRIGHT_CYAN,
            r'\bTRACE\b': Color.BRIGHT_GREEN,
            r'\bALL\b': Color.BRIGHT_WHITE,
        }
        
        # P2Rank特定模式
        self.p2rank_patterns = {
            # 进度指示
            r'(\d+/\d+)': Color.BRIGHT_BLUE,
            r'(\d+\.\d+%)': Color.BRIGHT_BLUE,
            
            # 时间相关
            r'(\d+:\d+:\d+)': Color.CYAN,
            r'(\d+\.\d+s)': Color.CYAN,
            r'(\d+ms)': Color.CYAN,
            
            # 文件路径
            r'(\.pdb|\.cif|\.mmcif)': Color.GREEN,
            r'(\.ds|\.csv|\.txt)': Color.GREEN,
            
            # 分数和指标
            r'(DCA_\d+_\d+|DCC_\d+_\d+)': Color.BRIGHT_MAGENTA,
            r'(\d+\.\d+)(?=\s*(DCA|DCC|AUC))': Color.BRIGHT_MAGENTA,
            
            # 成功/失败指示
            r'\b(SUCCESS|COMPLETED|DONE)\b': Color.BRIGHT_GREEN,
            r'\b(FAILED|ERROR|EXCEPTION)\b': Color.BRIGHT_RED,
            r'\b(SKIPPED|IGNORED)\b': Color.YELLOW,
            
            # 阶段标识
            r'\b(TRAINING|PREDICTION|EVALUATION|VALIDATION)\b': Color.BRIGHT_BLUE,
            r'\b(LOADING|SAVING|PROCESSING)\b': Color.BLUE,
        }
        
        # 合并自定义模式
        if custom_patterns:
            self.custom_patterns = custom_patterns
        else:
            self.custom_patterns = {}
        
        # 编译所有正则表达式
        self.compiled_patterns = self._compile_patterns()
    
    def _supports_color(self) -> bool:
        """检查终端是否支持颜色"""
        # 检查是否在TTY中
        if not sys.stdout.isatty():
            return False
        
        # 检查环境变量
        import os
        term = os.environ.get('TERM', '')
        if 'color' in term or term.endswith('256'):
            return True
        
        # 检查常见的支持颜色的终端
        color_terms = ['xterm', 'linux', 'screen', 'tmux']
        return any(color_term in term for color_term in color_terms)
    
    def _compile_patterns(self) -> list:
        """编译所有模式"""
        compiled = []
        
        # 按优先级合并模式
        all_patterns = {
            **self.default_patterns,
            **self.p2rank_patterns,
            **self.custom_patterns
        }
        
        for pattern, color in all_patterns.items():
            try:
                compiled.append((re.compile(pattern, re.IGNORECASE), color))
            except re.error as e:
                print(f"警告: 无效的正则表达式 '{pattern}': {e}", file=sys.stderr)
        
        return compiled
    
    def colorize_line(self, line: str) -> str:
        """为单行添加颜色"""
        if not self.enable_colors:
            return line
        
        # 移除行末的换行符，稍后重新添加
        has_newline = line.endswith('\n')
        if has_newline:
            line = line[:-1]
        
        # 应用颜色模式
        colored_line = line
        
        for pattern, color in self.compiled_patterns:
            def replace_func(match):
                matched_text = match.group(0)
                return f"{color.value}{matched_text}{Color.RESET.value}"
            
            colored_line = pattern.sub(replace_func, colored_line)
        
        # 重新添加换行符
        if has_newline:
            colored_line += '\n'
        
        return colored_line
    
    def colorize_stream(self, 
                       input_stream: TextIO = sys.stdin,
                       output_stream: TextIO = sys.stdout) -> None:
        """为流中的所有行添加颜色"""
        
        try:
            for line in input_stream:
                colored_line = self.colorize_line(line)
                output_stream.write(colored_line)
                output_stream.flush()
        
        except KeyboardInterrupt:
            # 优雅处理Ctrl+C
            pass
        except BrokenPipeError:
            # 处理管道中断
            pass
    
    def colorize_file(self, input_file: str, output_file: Optional[str] = None) -> None:
        """为文件内容添加颜色"""
        
        with open(input_file, 'r', encoding='utf-8') as infile:
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as outfile:
                    self.colorize_stream(infile, outfile)
            else:
                self.colorize_stream(infile, sys.stdout)


class P2RankLogColorizer(LogColorizer):
    """P2Rank专用日志着色器"""
    
    def __init__(self, enable_colors: bool = True):
        # P2Rank特有的额外模式
        p2rank_specific = {
            # 蛋白质相关
            r'\b(protein|structure|chain)\s+\w+': Color.GREEN,
            r'\b\d+\s+(residues?|atoms?)\b': Color.BLUE,
            
            # 口袋相关
            r'\b(pocket|binding\s+site)\s+\d+': Color.MAGENTA,
            r'\b\d+\s+(pockets?|sites?)\b': Color.MAGENTA,
            
            # 特征相关
            r'\b(features?|descriptors?)\b': Color.CYAN,
            r'\b\d+\s+features?\b': Color.CYAN,
            
            # 模型相关
            r'\b(model|classifier|forest)\b': Color.YELLOW,
            r'\b(training|prediction|evaluation)\s+(time|phase)\b': Color.YELLOW,
            
            # 数据集相关
            r'\b(dataset|training\s+set|test\s+set)\b': Color.BLUE,
            r'\b\d+\s+(proteins?|structures?)\b': Color.BLUE,
            
            # 性能指标
            r'\b(accuracy|precision|recall|f1|auc)\b': Color.BRIGHT_MAGENTA,
            r'\b(threads?|parallel|concurrent)\b': Color.BRIGHT_CYAN,
        }
        
        super().__init__(enable_colors=enable_colors, custom_patterns=p2rank_specific)


def create_demo_log() -> str:
    """创建演示日志内容"""
    
    demo_log = """
2024-01-15 10:30:15 INFO  Starting P2Rank prediction
2024-01-15 10:30:15 DEBUG Loading protein structure: 1fbl.pdb
2024-01-15 10:30:16 INFO  Loaded 1247 atoms, 156 residues
2024-01-15 10:30:16 WARN  Missing some B-factor values, using default
2024-01-15 10:30:17 INFO  Extracting 128 features for 2341 surface points
2024-01-15 10:30:18 DEBUG Feature extraction completed in 1.23s
2024-01-15 10:30:18 INFO  PREDICTION phase starting
2024-01-15 10:30:19 INFO  Using RandomForest model with 100 trees
2024-01-15 10:30:20 INFO  Processing 1/1 proteins (100.0%)
2024-01-15 10:30:21 INFO  Found 5 pockets with scores: [0.85, 0.72, 0.68, 0.45, 0.31]
2024-01-15 10:30:21 INFO  PREDICTION COMPLETED successfully in 5.67s
2024-01-15 10:30:21 INFO  Results saved to: output/1fbl_predictions.csv
2024-01-15 10:30:22 ERROR Failed to process 2abc.pdb: FileNotFoundError
2024-01-15 10:30:22 FATAL Critical error in main pipeline
2024-01-15 10:30:22 TRACE Detailed stack trace information
2024-01-15 10:30:22 ALL   Complete debug information
"""
    
    return demo_log.strip()


def main():
    """主函数"""
    
    parser = argparse.ArgumentParser(description="P2Rank Python 日志着色工具")
    parser.add_argument('--input', '-i', help='输入文件路径 (默认: stdin)')
    parser.add_argument('--output', '-o', help='输出文件路径 (默认: stdout)')
    parser.add_argument('--no-color', action='store_true', help='禁用颜色输出')
    parser.add_argument('--p2rank', action='store_true', help='使用P2Rank专用着色模式')
    parser.add_argument('--demo', action='store_true', help='显示着色演示')
    parser.add_argument('--patterns', help='自定义模式文件 (JSON格式)')
    
    args = parser.parse_args()
    
    # 加载自定义模式
    custom_patterns = {}
    if args.patterns:
        try:
            import json
            with open(args.patterns, 'r', encoding='utf-8') as f:
                patterns_data = json.load(f)
                
            # 转换颜色名称为Color枚举
            for pattern, color_name in patterns_data.items():
                try:
                    color = getattr(Color, color_name.upper())
                    custom_patterns[pattern] = color
                except AttributeError:
                    print(f"警告: 未知的颜色名称 '{color_name}'", file=sys.stderr)
        
        except Exception as e:
            print(f"错误: 无法加载自定义模式文件 '{args.patterns}': {e}", file=sys.stderr)
            sys.exit(1)
    
    # 创建着色器
    if args.p2rank:
        colorizer = P2RankLogColorizer(enable_colors=not args.no_color)
    else:
        colorizer = LogColorizer(
            enable_colors=not args.no_color,
            custom_patterns=custom_patterns
        )
    
    # 演示模式
    if args.demo:
        print("🎨 日志着色演示:")
        print("=" * 50)
        
        demo_log = create_demo_log()
        for line in demo_log.split('\n'):
            if line.strip():
                colored_line = colorizer.colorize_line(line + '\n')
                sys.stdout.write(colored_line)
        
        print("\n" + "=" * 50)
        print("演示完成! 您可以通过管道使用此工具:")
        print("  cat logfile.txt | python log_colorizer.py")
        print("  python your_script.py 2>&1 | python log_colorizer.py --p2rank")
        return
    
    # 处理输入输出
    if args.input:
        # 文件输入
        colorizer.colorize_file(args.input, args.output)
    else:
        # 流输入
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as outfile:
                colorizer.colorize_stream(sys.stdin, outfile)
        else:
            colorizer.colorize_stream(sys.stdin, sys.stdout)


if __name__ == "__main__":
    main()
