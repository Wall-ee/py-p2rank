#!/usr/bin/env python3
"""
P2Rank Python Git工具集
移植自原始的 commit.sh, push.sh, update.sh

提供Git版本控制的便捷工具
"""

import argparse
import subprocess
import sys
import time
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
import os


class GitTools:
    """Git工具集"""
    
    def __init__(self, repo_path: Optional[str] = None):
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()
        
        # 设置日志
        self.setup_logging()
        
        # 验证Git仓库
        if not self._is_git_repo():
            raise ValueError(f"目录不是Git仓库: {self.repo_path}")
    
    def setup_logging(self):
        """设置日志系统"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler()]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def _is_git_repo(self) -> bool:
        """检查是否为Git仓库"""
        git_dir = self.repo_path / ".git"
        return git_dir.exists()
    
    def _run_git_command(self, command: List[str], check: bool = True, 
                        capture_output: bool = False) -> subprocess.CompletedProcess:
        """运行Git命令"""
        
        full_command = ['git'] + command
        self.logger.info(f"🔧 执行: {' '.join(full_command)}")
        
        try:
            result = subprocess.run(
                full_command,
                cwd=self.repo_path,
                check=check,
                capture_output=capture_output,
                text=True
            )
            return result
        except subprocess.CalledProcessError as e:
            self.logger.error(f"❌ Git命令失败: {e}")
            if capture_output and e.stdout:
                self.logger.error(f"stdout: {e.stdout}")
            if capture_output and e.stderr:
                self.logger.error(f"stderr: {e.stderr}")
            raise
    
    def commit(self, message: str = "update", add_all: bool = True) -> bool:
        """
        提交变更
        
        Args:
            message: 提交信息
            add_all: 是否添加所有变更文件
        """
        
        try:
            self.logger.info(f"📝 提交变更: {message}")
            
            if add_all:
                self.logger.info("📋 添加所有变更文件...")
                self._run_git_command(['add', '--all'])
            
            # 检查是否有变更需要提交
            status_result = self._run_git_command(['status', '--porcelain'], capture_output=True)
            
            if not status_result.stdout.strip():
                self.logger.info("ℹ️  没有变更需要提交")
                return True
            
            # 提交变更
            self._run_git_command(['commit', '-m', message])
            
            self.logger.info(f"✅ 提交成功: {message}")
            return True
            
        except subprocess.CalledProcessError:
            self.logger.error(f"❌ 提交失败")
            return False
    
    def push(self, push_all_branches: bool = True, push_tags: bool = True) -> bool:
        """
        推送变更
        
        Args:
            push_all_branches: 是否推送所有分支
            push_tags: 是否推送标签
        """
        
        try:
            self.logger.info("📤 推送变更到远程仓库...")
            
            if push_all_branches:
                self.logger.info("🌿 推送所有分支...")
                self._run_git_command(['push', '--all'])
            else:
                self.logger.info("🌿 推送当前分支...")
                self._run_git_command(['push'])
            
            if push_tags:
                self.logger.info("🏷️  推送标签...")
                self._run_git_command(['push', '--tags'])
            
            self.logger.info("✅ 推送成功")
            return True
            
        except subprocess.CalledProcessError:
            self.logger.error("❌ 推送失败")
            return False
    
    def commit_and_push(self, message: str = "update", 
                       add_all: bool = True,
                       push_all_branches: bool = True, 
                       push_tags: bool = True) -> bool:
        """
        提交并推送变更
        
        组合了commit.sh和push.sh的功能
        """
        
        self.logger.info(f"🚀 提交并推送变更: {message}")
        
        # 先提交
        if not self.commit(message, add_all):
            return False
        
        # 再推送
        if not self.push(push_all_branches, push_tags):
            return False
        
        self.logger.info("🎉 提交并推送完成!")
        return True
    
    def update(self, build_after_update: bool = True) -> bool:
        """
        更新仓库 (类似update.sh)
        
        Args:
            build_after_update: 如果有更新，是否自动构建
        """
        
        try:
            self.logger.info("🔄 更新Git仓库...")
            
            # 获取更新前的HEAD
            head_before = self._get_current_head()
            self.logger.info(f"更新前HEAD: {head_before[:8]}...")
            
            # 拉取更新
            self.logger.info("📥 拉取远程更新...")
            self._run_git_command(['pull'])
            
            # 获取更新后的HEAD
            head_after = self._get_current_head()
            self.logger.info(f"更新后HEAD: {head_after[:8]}...")
            
            # 检查是否有更新
            if head_before != head_after:
                self.logger.info("✨ 检测到新的提交")
                
                if build_after_update:
                    self.logger.info("🔨 开始构建...")
                    success = self._build_project()
                    
                    if success:
                        self.logger.info("✅ 构建成功")
                    else:
                        self.logger.error("❌ 构建失败")
                        return False
                else:
                    self.logger.info("ℹ️  跳过构建 (disabled)")
            else:
                self.logger.info("ℹ️  没有新的更新")
            
            self.logger.info("✅ 更新完成")
            return True
            
        except subprocess.CalledProcessError:
            self.logger.error("❌ 更新失败")
            return False
    
    def _get_current_head(self) -> str:
        """获取当前HEAD的commit hash"""
        result = self._run_git_command(['log', '-n', '1', '--format=%H'], capture_output=True)
        return result.stdout.strip()
    
    def _build_project(self) -> bool:
        """构建项目 (Python版本)"""
        
        try:
            # 检查是否有setup.py
            setup_py = self.repo_path / "setup.py"
            if setup_py.exists():
                self.logger.info("🐍 使用setup.py构建...")
                subprocess.run([sys.executable, 'setup.py', 'build'], 
                             cwd=self.repo_path, check=True)
                return True
            
            # 检查是否有pyproject.toml
            pyproject_toml = self.repo_path / "pyproject.toml"
            if pyproject_toml.exists():
                self.logger.info("📦 使用pip构建...")
                subprocess.run([sys.executable, '-m', 'pip', 'install', '-e', '.'], 
                             cwd=self.repo_path, check=True)
                return True
            
            # 检查是否有requirements.txt
            requirements_txt = self.repo_path / "requirements.txt"
            if requirements_txt.exists():
                self.logger.info("📋 安装依赖...")
                subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                             cwd=self.repo_path, check=True)
                return True
            
            # 如果是P2Rank Python项目，尝试特定的构建流程
            if (self.repo_path / "src_py").exists():
                self.logger.info("🧬 P2Rank Python项目构建...")
                src_py_dir = self.repo_path / "src_py"
                
                # 安装依赖
                requirements = src_py_dir / "requirements.txt"
                if requirements.exists():
                    subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', str(requirements)], 
                                 check=True)
                
                # 开发安装
                if (src_py_dir / "setup.py").exists():
                    subprocess.run([sys.executable, '-m', 'pip', 'install', '-e', '.'], 
                                 cwd=src_py_dir, check=True)
                
                return True
            
            self.logger.warning("⚠️  未找到构建配置，跳过构建")
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"❌ 构建失败: {e}")
            return False
    
    def status(self) -> Dict[str, Any]:
        """获取仓库状态"""
        
        try:
            # 获取状态
            status_result = self._run_git_command(['status', '--porcelain'], capture_output=True)
            
            # 获取分支信息
            branch_result = self._run_git_command(['branch', '--show-current'], capture_output=True)
            current_branch = branch_result.stdout.strip()
            
            # 获取远程状态
            try:
                remote_result = self._run_git_command(['status', '-uno'], capture_output=True)
                remote_status = remote_result.stdout
            except:
                remote_status = "无法获取远程状态"
            
            # 解析文件状态
            file_changes = []
            for line in status_result.stdout.strip().split('\n'):
                if line.strip():
                    status_code = line[:2]
                    file_path = line[3:]
                    file_changes.append({
                        'status': status_code,
                        'file': file_path
                    })
            
            return {
                'current_branch': current_branch,
                'file_changes': file_changes,
                'has_changes': len(file_changes) > 0,
                'remote_status': remote_status
            }
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"❌ 获取状态失败: {e}")
            return {}
    
    def create_tag(self, tag_name: str, message: Optional[str] = None) -> bool:
        """创建标签"""
        
        try:
            self.logger.info(f"🏷️  创建标签: {tag_name}")
            
            if message:
                self._run_git_command(['tag', '-a', tag_name, '-m', message])
            else:
                self._run_git_command(['tag', tag_name])
            
            self.logger.info(f"✅ 标签创建成功: {tag_name}")
            return True
            
        except subprocess.CalledProcessError:
            self.logger.error(f"❌ 标签创建失败: {tag_name}")
            return False
    
    def list_recent_commits(self, count: int = 10) -> List[Dict[str, str]]:
        """列出最近的提交"""
        
        try:
            result = self._run_git_command([
                'log', f'-{count}', '--format=%H|%an|%ad|%s', '--date=short'
            ], capture_output=True)
            
            commits = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    parts = line.split('|', 3)
                    if len(parts) == 4:
                        commits.append({
                            'hash': parts[0][:8],
                            'author': parts[1],
                            'date': parts[2],
                            'message': parts[3]
                        })
            
            return commits
            
        except subprocess.CalledProcessError:
            self.logger.error("❌ 获取提交历史失败")
            return []


def main():
    """主函数"""
    
    parser = argparse.ArgumentParser(description="P2Rank Python Git工具集")
    parser.add_argument('command', choices=['commit', 'push', 'commit-push', 'update', 'status', 'tag', 'log'],
                       help='执行的命令')
    
    # 通用参数
    parser.add_argument('--repo-path', help='Git仓库路径 (默认: 当前目录)')
    
    # commit相关参数
    parser.add_argument('-m', '--message', default='update', help='提交信息')
    parser.add_argument('--no-add', action='store_true', help='不自动添加所有文件')
    
    # push相关参数
    parser.add_argument('--no-all-branches', action='store_true', help='只推送当前分支')
    parser.add_argument('--no-tags', action='store_true', help='不推送标签')
    
    # update相关参数
    parser.add_argument('--no-build', action='store_true', help='更新后不构建')
    
    # tag相关参数
    parser.add_argument('--tag-name', help='标签名称')
    parser.add_argument('--tag-message', help='标签信息')
    
    # log相关参数
    parser.add_argument('--count', type=int, default=10, help='显示的提交数量')
    
    args = parser.parse_args()
    
    try:
        # 创建Git工具
        git_tools = GitTools(repo_path=args.repo_path)
        
        if args.command == 'commit':
            success = git_tools.commit(
                message=args.message,
                add_all=not args.no_add
            )
            sys.exit(0 if success else 1)
        
        elif args.command == 'push':
            success = git_tools.push(
                push_all_branches=not args.no_all_branches,
                push_tags=not args.no_tags
            )
            sys.exit(0 if success else 1)
        
        elif args.command == 'commit-push':
            success = git_tools.commit_and_push(
                message=args.message,
                add_all=not args.no_add,
                push_all_branches=not args.no_all_branches,
                push_tags=not args.no_tags
            )
            sys.exit(0 if success else 1)
        
        elif args.command == 'update':
            success = git_tools.update(build_after_update=not args.no_build)
            sys.exit(0 if success else 1)
        
        elif args.command == 'status':
            status = git_tools.status()
            
            print(f"📂 当前分支: {status.get('current_branch', '未知')}")
            
            if status.get('has_changes', False):
                print("📝 变更文件:")
                for change in status.get('file_changes', []):
                    print(f"  {change['status']} {change['file']}")
            else:
                print("✅ 工作目录干净")
        
        elif args.command == 'tag':
            if not args.tag_name:
                print("❌ 创建标签需要指定标签名称 (--tag-name)")
                sys.exit(1)
            
            success = git_tools.create_tag(args.tag_name, args.tag_message)
            sys.exit(0 if success else 1)
        
        elif args.command == 'log':
            commits = git_tools.list_recent_commits(args.count)
            
            print(f"📜 最近 {len(commits)} 次提交:")
            for commit in commits:
                print(f"  {commit['hash']} - {commit['date']} - {commit['author']}: {commit['message']}")
    
    except ValueError as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
