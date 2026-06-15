# -*- coding: utf-8 -*-
"""
批量修复裸except脚本
将没有日志记录的 except Exception 添加日志
"""

import re
import sys
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).parent.parent
APP_DIR = BASE_DIR / "app"


def fix_file(filepath: Path) -> int:
    """修复单个文件中的裸except"""
    changes = 0

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # 匹配 except Exception as e: 后面没有日志的情况
        # 模式1: except Exception as e:\n            pass
        # 模式2: except Exception as e:\n            <没有logger的行>

        # 简单的替换策略：在 except 块开头添加日志
        lines = content.split('\n')
        new_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]
            new_lines.append(line)

            # 检查是否是 except Exception 行
            if re.match(r'\s*except\s+Exception\s+as\s+\w+\s*:', line):
                # 检查下一行是否已经有日志
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    # 如果下一行不是日志且不是pass，添加日志
                    if 'logger' not in next_line and 'raise' not in next_line and 'pass' not in next_line:
                        # 获取缩进
                        indent = len(line) - len(line.lstrip())
                        indent_str = ' ' * (indent + 4)
                        # 获取异常变量名
                        match = re.search(r'except\s+Exception\s+as\s+(\w+)', line)
                        if match:
                            var_name = match.group(1)
                            new_lines.append(f'{indent_str}import logging')
                            new_lines.append(f'{indent_str}logging.getLogger(__name__).exception(f"Error in {{__name__}}: {{{var_name}}}")')
                            changes += 1

            i += 1

        new_content = '\n'.join(new_lines)

        if new_content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)

    except Exception as e:
        print(f"Error processing {filepath}: {e}", file=sys.stderr)

    return changes


def main():
    print("=" * 60)
    print("批量修复裸except")
    print("=" * 60)

    total_changes = 0
    files_changed = 0

    for py_file in APP_DIR.rglob("*.py"):
        # 跳过__pycache__
        if "__pycache__" in str(py_file):
            continue

        try:
            changes = fix_file(py_file)
            if changes > 0:
                files_changed += 1
                total_changes += changes
                print(f"  {py_file.relative_to(BASE_DIR)}: {changes} changes")
        except Exception as e:
            print(f"  Error: {py_file.relative_to(BASE_DIR)} - {e}")

    print("=" * 60)
    print(f"总计: {files_changed} 文件, {total_changes} 处修改")
    print("=" * 60)


if __name__ == "__main__":
    main()
