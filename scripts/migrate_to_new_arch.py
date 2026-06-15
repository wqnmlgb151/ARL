# -*- coding: utf-8 -*-
"""
ARL项目架构迁移脚本
从旧架构迁移到新架构

使用方法：
    python scripts/migrate_to_new_arch.py --check    # 检查需要迁移的文件
    python scripts/migrate_to_new_arch.py --migrate  # 执行迁移
    python scripts/migrate_to_new_arch.py --rollback # 回滚迁移
"""

import argparse
import io
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# 修复Windows编码问题
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# 项目根目录
BASE_DIR = Path(__file__).parent.parent
APP_DIR = BASE_DIR / "app"

# 迁移映射表
MIGRATION_MAP = {
    # 旧导入 → 新导入
    "app.utils.conn.ConnMongo": "app.database.connection.DatabaseManager",
    "app.utils.conn.conn_db": "app.database.connection.get_collection",
    "app.utils.conn.init_db": "app.database.connection.init_db",
}

# 需要添加废弃警告的文件
DEPRECATION_TARGETS = [
    "app/utils/domain.py",
    "app/utils/ip.py",
    "app/utils/user.py",
]


def find_files_to_migrate() -> Dict[str, List[str]]:
    """
    查找需要迁移的文件
    返回：{文件路径: [需要替换的导入]}
    """
    results = {}

    for py_file in APP_DIR.rglob("*.py"):
        # 跳过脚本和测试
        if "scripts" in str(py_file) or "tests" in str(py_file):
            continue

        try:
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()

            matches = []
            for old_import in MIGRATION_MAP.keys():
                if old_import in content:
                    matches.append(old_import)

            if matches:
                rel_path = str(py_file.relative_to(BASE_DIR))
                results[rel_path] = matches
        except Exception:
            pass

    return results


def migrate_file(filepath: Path, dry_run: bool = False) -> Tuple[bool, List[str]]:
    """
    迁移单个文件
    返回：(是否修改, [修改详情])
    """
    changes = []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content

        # 替换导入
        for old_import, new_import in MIGRATION_MAP.items():
            if old_import in content:
                # 替换 from app.utils.conn import ConnMongo → from app.database.connection import DatabaseManager
                pattern = rf"from\s+{re.escape(old_import)}\s+import\s+(\w+)"
                replacement = f"from {new_import} import \\1"
                new_content = re.sub(pattern, replacement, content)

                # 替换 import app.utils.conn → import app.database.connection
                if new_content == content:
                    pattern = rf"import\s+{re.escape(old_import)}"
                    replacement = f"import {new_import}"
                    new_content = re.sub(pattern, replacement, content)

                if new_content != content:
                    changes.append(f"  {old_import} → {new_import}")
                    content = new_content

        # 替换 ConnMongo() → DatabaseManager()
        if "ConnMongo()" in content:
            content = content.replace("ConnMongo()", "DatabaseManager()")
            changes.append("  ConnMongo() → DatabaseManager()")

        # 替换 conn_db() → get_collection()
        if "conn_db(" in content:
            content = content.replace("conn_db(", "get_collection(")
            changes.append("  conn_db() → get_collection()")

        # 如果有修改且不是dry_run，写入文件
        if content != original_content and not dry_run:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

        return len(changes) > 0, changes

    except Exception as e:
        return False, [f"错误: {e}"]


def check_migration():
    """检查需要迁移的文件"""
    print("=" * 60)
    print("ARL架构迁移检查")
    print("=" * 60)

    files = find_files_to_migrate()

    if not files:
        print("\n✅ 没有发现需要迁移的文件")
        return

    print(f"\n📋 发现 {len(files)} 个文件需要迁移:\n")

    for filepath, imports in sorted(files.items()):
        print(f"📄 {filepath}")
        for imp in imports:
            new_imp = MIGRATION_MAP.get(imp, "未知")
            print(f"   ↳ {imp}")
            print(f"     → {new_imp}")

    print(f"\n总计: {len(files)} 个文件")
    print("=" * 60)


def run_migration(dry_run: bool = False):
    """执行迁移"""
    print("=" * 60)
    print("ARL架构迁移")
    if dry_run:
        print("【试运行模式】不会实际修改文件")
    print("=" * 60)

    files = find_files_to_migrate()

    if not files:
        print("\n✅ 没有发现需要迁移的文件")
        return

    print(f"\n📋 处理 {len(files)} 个文件:\n")

    success_count = 0
    fail_count = 0

    for filepath, imports in sorted(files.items()):
        full_path = BASE_DIR / filepath
        success, changes = migrate_file(full_path, dry_run=dry_run)

        if changes:
            print(f"📄 {filepath}")
            for change in changes:
                print(change)

            if success:
                success_count += 1
                print("   ✅ 成功")
            else:
                fail_count += 1
                print("   ❌ 失败")
            print()

    print("=" * 60)
    print(f"迁移完成: {success_count} 成功, {fail_count} 失败")
    if dry_run:
        print("【试运行】未实际修改文件")
    print("=" * 60)


def add_deprecation_warnings():
    """为旧文件添加废弃警告"""
    print("=" * 60)
    print("添加废弃警告")
    print("=" * 60)

    deprecation_code = '''
# -*- coding: utf-8 -*-
"""
⚠️ 此模块已废弃，将在v2.8中移除
请使用以下替代方案：
- app.utils.domain → app.core.validators
- app.utils.ip → app.core.validators
- app.utils.user → app.services.user_service
- app.utils.conn.ConnMongo → app.database.connection.DatabaseManager
"""
import warnings

warnings.warn(
    "此模块已废弃，请使用新架构模块",
    DeprecationWarning,
    stacklevel=2
)

'''

    for target in DEPRECATION_TARGETS:
        target_path = BASE_DIR / target
        if target_path.exists():
            print(f"📄 添加废弃警告: {target}")
            # 注意：这里只是打印，实际添加需要谨慎
            print(f"   ⚠️ 请手动添加废弃警告代码")
        else:
            print(f"⚠️ 文件不存在: {target}")

    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="ARL架构迁移脚本")
    parser.add_argument(
        "--check",
        action="store_true",
        help="检查需要迁移的文件"
    )
    parser.add_argument(
        "--migrate",
        action="store_true",
        help="执行迁移"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="试运行，不实际修改文件"
    )
    parser.add_argument(
        "--deprecation",
        action="store_true",
        help="为旧文件添加废弃警告"
    )

    args = parser.parse_args()

    if args.check:
        check_migration()
    elif args.migrate:
        run_migration(dry_run=args.dry_run)
    elif args.deprecation:
        add_deprecation_warnings()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
