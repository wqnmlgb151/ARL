# -*- coding: utf-8 -*-
"""
ARL项目基线审计脚本
生成项目当前状态的基线报告
"""

import ast
import io
import os
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple

# 修复Windows编码问题
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# 项目根目录
BASE_DIR = Path(__file__).parent.parent
APP_DIR = BASE_DIR / "app"
REPORTS_DIR = BASE_DIR / "reports"


def count_python_files(directory: Path) -> int:
    """统计Python文件数量"""
    return sum(1 for _ in directory.rglob("*.py"))


def count_lines_of_code(directory: Path) -> Tuple[int, int, int]:
    """
    统计代码行数
    返回：(总代码行, 空行, 注释行)
    """
    total = 0
    blank = 0
    comments = 0

    for py_file in directory.rglob("*.py"):
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                for line in f:
                    total += 1
                    stripped = line.strip()
                    if not stripped:
                        blank += 1
                    elif stripped.startswith("#"):
                        comments += 1
        except Exception:
            pass

    return total, blank, comments


def find_imports(filepath: Path) -> List[str]:
    """查找文件中的导入语句"""
    imports = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
    except Exception:
        pass

    return imports


def find_old_imports(directory: Path) -> Dict[str, List[str]]:
    """
    查找使用旧架构的文件
    返回：{文件路径: [旧导入列表]}
    """
    old_import_patterns = [
        "app.utils.conn.ConnMongo",
        "app.utils.conn.conn_db",
        "app.utils.domain",
        "app.utils.ip",
        "app.utils.user",
    ]

    results = {}

    for py_file in directory.rglob("*.py"):
        imports = find_imports(py_file)
        old_found = []

        for imp in imports:
            for pattern in old_import_patterns:
                if imp.startswith(pattern) or pattern in imp:
                    old_found.append(imp)
                    break

        if old_found:
            rel_path = str(py_file.relative_to(BASE_DIR))
            results[rel_path] = old_found

    return results


def find_duplicate_patterns(directory: Path) -> Dict[str, int]:
    """
    查找重复代码模式
    返回：{模式: 出现次数}
    """
    patterns = defaultdict(int)

    # 定义要查找的重复模式
    duplicate_patterns = [
        "collection.aggregate",
        "collection.bulk_write",
        "collection.insert_many",
        "collection.find_many",
        "collection.find_one",
        "get_statistics",
        "find_by_task",
        "find_by_status",
        "find_by_ip",
        "find_by_url",
        "find_by_domain",
        "to_dict",
    ]

    for py_file in directory.rglob("*.py"):
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()

            for pattern in duplicate_patterns:
                count = content.count(pattern)
                if count > 0:
                    patterns[pattern] += count
        except Exception:
            pass

    return dict(patterns)


def find_todo_comments(directory: Path) -> List[Tuple[str, str]]:
    """查找TODO注释"""
    todos = []

    for py_file in directory.rglob("*.py"):
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                for i, line in enumerate(f, 1):
                    stripped = line.strip()
                    if "TODO" in stripped or "FIXME" in stripped or "HACK" in stripped:
                        rel_path = str(py_file.relative_to(BASE_DIR))
                        todos.append((f"{rel_path}:{i}", stripped))
        except Exception:
            pass

    return todos


def analyze_class_distribution(directory: Path) -> Dict[str, int]:
    """分析类分布"""
    classes = defaultdict(int)

    for py_file in directory.rglob("*.py"):
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    classes[node.name] += 1
        except Exception:
            pass

    return dict(classes)


def analyze_api_endpoints(directory: Path) -> List[Dict[str, str]]:
    """分析API端点"""
    endpoints = []

    for py_file in directory.rglob("*.py"):
        if "routes" not in str(py_file):
            continue

        try:
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()

            # 简单的装饰器检测
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if "@" in line and ("route" in line.lower() or "ns." in line.lower()):
                    endpoints.append({
                        "file": str(py_file.relative_to(BASE_DIR)),
                        "line": i + 1,
                        "content": line.strip()
                    })
        except Exception:
            pass

    return endpoints


def generate_report():
    """生成基线报告"""
    REPORTS_DIR.mkdir(exist_ok=True)

    print("=" * 60)
    print("ARL项目基线审计报告")
    print(f"生成时间: {datetime.now().isoformat()}")
    print("=" * 60)

    # 1. 文件统计
    print("\n📊 文件统计")
    print("-" * 40)
    total_files = count_python_files(APP_DIR)
    print(f"Python文件总数: {total_files}")

    # 2. 代码行数
    print("\n📝 代码行数")
    print("-" * 40)
    total_lines, blank_lines, comment_lines = count_lines_of_code(APP_DIR)
    print(f"总代码行数: {total_lines}")
    print(f"空行数: {blank_lines}")
    print(f"注释行数: {comment_lines}")
    print(f"实际代码行数: {total_lines - blank_lines - comment_lines}")

    # 3. 旧架构使用情况
    print("\n🏚️ 旧架构使用情况")
    print("-" * 40)
    old_imports = find_old_imports(APP_DIR)
    print(f"使用旧架构的文件数: {len(old_imports)}")
    for filepath, imports in sorted(old_imports.items()):
        print(f"  📄 {filepath}")
        for imp in imports:
            print(f"     ↳ {imp}")

    # 4. 重复代码模式
    print("\n🔄 重复代码模式")
    print("-" * 40)
    duplicates = find_duplicate_patterns(APP_DIR)
    for pattern, count in sorted(duplicates.items(), key=lambda x: -x[1]):
        bar = "█" * min(count // 10, 20)
        print(f"  {pattern:<30} {count:>4} 次 {bar}")

    # 5. TODO注释
    print("\n📋 TODO/FIXME注释")
    print("-" * 40)
    todos = find_todo_comments(APP_DIR)
    print(f"TODO/FIXME总数: {len(todos)}")
    for location, content in todos[:10]:  # 只显示前10个
        print(f"  📍 {location}")
        print(f"     {content}")
    if len(todos) > 10:
        print(f"  ... 还有 {len(todos) - 10} 个")

    # 6. 类分布
    print("\n🏗️ 类分布")
    print("-" * 40)
    classes = analyze_class_distribution(APP_DIR)
    for class_name, count in sorted(classes.items(), key=lambda x: -x[1])[:20]:
        print(f"  {class_name:<40} {count}")

    # 7. API端点
    print("\n🌐 API端点")
    print("-" * 40)
    endpoints = analyze_api_endpoints(APP_DIR)
    print(f"检测到的API端点数: {len(endpoints)}")
    for ep in endpoints[:15]:
        print(f"  📍 {ep['file']}:{ep['line']}")
        print(f"     {ep['content']}")
    if len(endpoints) > 15:
        print(f"  ... 还有 {len(endpoints) - 15} 个")

    # 8. 目录结构
    print("\n📁 目录结构")
    print("-" * 40)
    for dirpath, dirnames, filenames in os.walk(APP_DIR):
        level = dirpath.replace(str(APP_DIR), "").count(os.sep)
        indent = " " * 2 * level
        dir_name = os.path.basename(dirpath)
        if dir_name.startswith("__"):
            continue
        print(f"{indent}📁 {dir_name}/")
        sub_indent = " " * 2 * (level + 1)
        for file in filenames[:5]:  # 只显示前5个文件
            if file.endswith(".py") and not file.startswith("__"):
                print(f"{sub_indent}📄 {file}")
        if len(filenames) > 5:
            print(f"{sub_indent}... 还有 {len(filenames) - 5} 个文件")

    # 生成JSON报告
    report = {
        "timestamp": datetime.now().isoformat(),
        "statistics": {
            "total_files": total_files,
            "total_lines": total_lines,
            "blank_lines": blank_lines,
            "comment_lines": comment_lines,
        },
        "old_architecture": {
            "files_using_old_imports": len(old_imports),
            "details": old_imports,
        },
        "duplicates": duplicates,
        "todos": len(todos),
        "classes": classes,
        "endpoints": len(endpoints),
    }

    import json
    report_file = REPORTS_DIR / "baseline_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 报告已保存到: {report_file}")
    print("=" * 60)


if __name__ == "__main__":
    generate_report()
