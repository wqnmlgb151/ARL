#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python 3.9+ 兼容性检查脚本
检查ARL项目代码是否兼容Python 3.9+特性
"""

import os
import sys
import io
import ast
from pathlib import Path
from typing import List, Dict, Tuple

# 修复Windows编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

class Python39CompatChecker:
    """Python 3.9+ 兼容性检查器"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.issues: List[Dict] = []
        self.suggestions: List[Dict] = []

    def check_all(self):
        """执行所有检查"""
        print("🔍 开始Python 3.9+兼容性检查...")
        print("=" * 60)

        # 检查Python版本
        self.check_python_version()

        # 扫描所有Python文件
        python_files = list(self.project_root.rglob("*.py"))
        print(f"📁 找到 {len(python_files)} 个Python文件")

        for file_path in python_files:
            self.check_file(file_path)

        # 输出结果
        self.print_results()

    def check_python_version(self):
        """检查当前Python版本"""
        version = sys.version_info
        print(f"🐍 当前Python版本: {version.major}.{version.minor}.{version.micro}")

        if version < (3, 9):
            self.issues.append({
                "type": "ERROR",
                "message": f"Python版本过低: {version.major}.{version.minor}.{version.micro}，需要3.9+",
                "file": "系统",
                "line": 0
            })
        else:
            print("✅ Python版本符合要求")

    def check_file(self, file_path: Path):
        """检查单个文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')

            # 检查各种兼容性模式
            self.check_fstring_usage(file_path, lines)
            self.check_type_annotations(file_path, lines)
            self.check_dataclass_usage(file_path, lines)
            self.check_dict_merge_operator(file_path, lines)
            self.check_modern_features(file_path, lines)

        except Exception as e:
            self.issues.append({
                "type": "WARNING",
                "message": f"无法读取文件: {e}",
                "file": str(file_path),
                "line": 0
            })

    def check_fstring_usage(self, file_path: Path, lines: List[str]):
        """检查f-string使用情况（Python 3.6+已支持，但3.9+有增强）"""
        for i, line in enumerate(lines, 1):
            # 检查复杂的f-string表达式
            if 'f"' in line or "f'" in line:
                if '!' in line or ':' in line:
                    # 可能使用了高级f-string特性
                    self.suggestions.append({
                        "type": "INFO",
                        "message": f"第{i}行使用了复杂f-string，确保兼容性",
                        "file": str(file_path),
                        "line": i
                    })

    def check_type_annotations(self, file_path: Path, lines: List[str]):
        """检查类型注解使用情况"""
        has_typing_import = False
        has_type_annotations = False

        for line in lines:
            if 'from typing import' in line or 'import typing' in line:
                has_typing_import = True
            if '-> ' in line or ': ' in line and 'def ' in line:
                has_type_annotations = True

        if not has_type_annotations and file_path.name != '__init__.py':
            self.suggestions.append({
                "type": "IMPROVEMENT",
                "message": "函数缺少类型注解，建议添加",
                "file": str(file_path),
                "line": 0
            })

    def check_dataclass_usage(self, file_path: Path, lines: List[str]):
        """检查是否可以使用dataclass替代简单类"""
        class_lines = []
        for i, line in enumerate(lines, 1):
            if line.strip().startswith('class ') and 'dataclass' not in line:
                # 检查是否是简单的数据类
                if any('self.' in l for l in lines[i:i+10]):
                    class_lines.append(i)

        if class_lines:
            self.suggestions.append({
                "type": "IMPROVEMENT",
                "message": f"发现简单类定义（行{class_lines}），可考虑使用dataclass",
                "file": str(file_path),
                "line": class_lines[0]
            })

    def check_dict_merge_operator(self, file_path: Path, lines: List[str]):
        """检查字典合并操作（Python 3.9+特性）"""
        for i, line in enumerate(lines, 1):
            if '**' in line and '{' in line:
                # 可能使用了字典合并
                self.suggestions.append({
                    "type": "INFO",
                    "message": f"第{i}行使用了字典合并，Python 3.9+支持 | 操作符",
                    "file": str(file_path),
                    "line": i
                })

    def check_modern_features(self, file_path: Path, lines: List[str]):
        """检查现代Python特性使用情况"""
        for i, line in enumerate(lines, 1):
            # 检查match语句（Python 3.10+）- 排除变量赋值和注释
            if (line.strip().startswith('match ') and
                '=' not in line.split('match')[0] and
                '#' not in line):
                self.issues.append({
                    "type": "ERROR",
                    "message": "使用了match语句，需要Python 3.10+",
                    "file": str(file_path),
                    "line": i
                })

            # 检查walrus operator（Python 3.8+）
            if ':=' in line:
                self.suggestions.append({
                    "type": "INFO",
                    "message": f"第{i}行使用了海象运算符",
                    "file": str(file_path),
                    "line": i
                })

    def print_results(self):
        """输出检查结果"""
        print("\n" + "=" * 60)
        print("📊 检查结果汇总")
        print("=" * 60)

        # 统计问题类型
        error_count = len([i for i in self.issues if i['type'] == 'ERROR'])
        warning_count = len([i for i in self.issues if i['type'] == 'WARNING'])
        improvement_count = len([i for i in self.suggestions if i['type'] == 'IMPROVEMENT'])
        info_count = len([i for i in self.suggestions if i['type'] == 'INFO'])

        print(f"❌ 错误: {error_count}")
        print(f"⚠️  警告: {warning_count}")
        print(f"💡 改进建议: {improvement_count}")
        print(f"ℹ️  信息: {info_count}")

        # 输出错误和警告
        if self.issues:
            print("\n❌ 错误和警告:")
            for issue in self.issues:
                print(f"  [{issue['type']}] {issue['file']}:{issue['line']} - {issue['message']}")

        # 输出改进建议
        if self.suggestions:
            print("\n💡 改进建议:")
            for suggestion in self.suggestions[:10]:  # 只显示前10个
                print(f"  [{suggestion['type']}] {suggestion['file']}:{suggestion['line']} - {suggestion['message']}")

            if len(self.suggestions) > 10:
                print(f"  ... 还有 {len(self.suggestions) - 10} 个建议")

        # 兼容性评估
        print("\n" + "=" * 60)
        if error_count == 0:
            print("✅ 代码基本兼容Python 3.9+")
        else:
            print("❌ 发现兼容性问题，需要修复")

        print("=" * 60)

def main():
    """主函数"""
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = os.getcwd()

    checker = Python39CompatChecker(project_root)
    checker.check_all()

if __name__ == '__main__':
    main()
