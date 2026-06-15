# -*- coding: utf-8 -*-
"""
MD5到bcrypt密码哈希迁移脚本

使用方法：
    python scripts/migrate_md5_to_bcrypt.py --check    # 需要迁移的用户
    python scripts/migrate_md5_to_bcrypt.py --migrate  # 执行迁移
    python scripts/migrate_md5_to_bcrypt.py --verify   # 验证迁移
"""

import argparse
import io
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# 修复Windows编码问题
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# 项目根目录
BASE_DIR = Path(__file__).parent.parent
APP_DIR = BASE_DIR / "app"


def find_md5_users() -> List[Dict]:
    """
    查找使用MD5密码哈希的用户
    返回：[{username, password_hash, is_md5}]
    """
    from app.database.connection import get_collection

    collection = get_collection("user")
    users = []

    for user in collection.find():
        password_hash = user.get("password", "")

        # 检查是否是MD5哈希（32位十六进制）
        if len(password_hash) == 32 and all(c in "0123456789abcdef" for c in password_hash.lower()):
            users.append({
                "username": user.get("username"),
                "password_hash": password_hash,
                "is_md5": True,
            })
        # 检查是否是旧格式（hex_md5）
        elif user.get("password_hash") == "hex_md5":
            users.append({
                "username": user.get("username"),
                "password_hash": password_hash,
                "is_md5": True,
            })

    return users


def check_migration_needed() -> Tuple[int, int]:
    """
    检查需要迁移的用户数量
    返回：(md5用户数, 总用户数）
    """
    from app.database.connection import get_collection

    collection = get_collection("user")
    total_users = collection.count_documents({})

    md5_users = find_md5_users()
    md5_count = len(md5_users)

    return md5_count, total_users


def migrate_user(username: str, password_hash: str) -> bool:
    """
    迁移单个用户的密码哈希
    返回：是否成功
    """
    from app.database.connection import get_collection
    from app.services.user_service import hash_password

    collection = get_collection("user")

    # 生成新的bcrypt哈希
    # 注意：由于无法获取原始密码，需要用户重新设置密码
    # 这里只是标记需要迁移
    result = collection.update_one(
        {"username": username},
        {
            "$set": {
                "password_hash": None,  # 清除旧哈希
                "password_migrated": False,
                "password_reset_required": True,
            }
        }
    )

    return result.modified_count > 0


def run_migration(dry_run: bool = False) -> Tuple[int, int]:
    """
    执行密码哈希迁移
    返回：(成功数, 失败数）
    """
    md5_users = find_md5_users()

    if not md5_users:
        print("没有发现使用MD5的用户")
        return 0, 0

    print(f"发现 {len(md5_users)} 个使用MD5的用户")

    success_count = 0
    fail_count = 0

    for user in md5_users:
        username = user["username"]

        if dry_run:
            print(f"[试运行] 将迁移用户: {username}")
            success_count += 1
            continue

        try:
            if migrate_user(username, user["password_hash"]):
                print(f"成功标记用户: {username}")
                success_count += 1
            else:
                print(f"标记失败: {username}")
                fail_count += 1
        except Exception as e:
            print(f"迁移失败 {username}: {e}")
            fail_count += 1

    return success_count, fail_count


def verify_migration() -> Tuple[int, int, int]:
    """
    验证迁移结果
    返回：（已迁移数, 未迁移数, 总数）
    """
    from app.database.connection import get_collection

    collection = get_collection("user")
    total_users = collection.count_documents({})

    # 已迁移的用户（有bcrypt哈希或标记为已迁移）
    migrated = collection.count_documents({
        "$or": [
            {"password_migrated": True},
            {"password_reset_required": True},
        ]
    })

    # 未迁移的用户（仍然使用MD5）
    unmigrated = collection.count_documents({
        "password_migrated": {"$ne": True},
        "password_reset_required": {"$ne": True},
    })

    return migrated, unmigrated, total_users


def add_reset_flag_to_all_users() -> int:
    """
    为所有用户添加密码重置标志
    返回：更新的用户数
    """
    from app.database.connection import get_collection

    collection = get_collection("user")
    result = collection.update_many(
        {"password_reset_required": {"$exists": False}},
        {"$set": {"password_reset_required": True}}
    )

    return result.modified_count


def main():
    parser = argparse.ArgumentParser(description="MD5到bcrypt密码哈希迁移")
    parser.add_argument(
        "--check",
        action="store_true",
        help="检查需要迁移的用户"
    )
    parser.add_argument(
        "--migrate",
        action="store_true",
        help="执行迁移"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="试运行，不实际修改数据"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="验证迁移结果"
    )
    parser.add_argument(
        "--mark-all",
        action="store_true",
        help="为所有用户添加重置标志"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("MD5到bcrypt密码哈希迁移")
    print("=" * 60)

    if args.check:
        md5_count, total_count = check_migration_needed()
        print(f"\n总用户数: {total_count}")
        print(f"使用MD5的用户数: {md5_count}")
        print(f"需要迁移的比例: {md5_count/total_count*100:.1f}%" if total_count > 0 else "无用户")
        print("=" * 60)

    elif args.migrate:
        print("\n执行迁移...")
        success, fail = run_migration(dry_run=args.dry_run)
        print(f"\n迁移完成: {success} 成功, {fail} 失败")
        if args.dry_run:
            print("【试运行】未实际修改数据")
        print("=" * 60)

    elif args.verify:
        print("\n验证迁移结果...")
        migrated, unmigrated, total = verify_migration()
        print(f"\n总用户数: {total}")
        print(f"已迁移/已标记: {migrated}")
        print(f"未迁移: {unmigrated}")
        print("=" * 60)

    elif args.mark_all:
        print("\n为所有用户添加重置标志...")
        count = add_reset_flag_to_all_users()
        print(f"已更新 {count} 个用户")
        print("=" * 60)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
