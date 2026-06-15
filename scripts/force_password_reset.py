# -*- coding: utf-8 -*-
"""
强制所有用户重置密码脚本

使用方法：
    python scripts/force_password_reset.py --check    # 检查需要重置的用户
    python scripts/force_password_reset.py --reset    # 标记所有用户需要重置密码
    python scripts/force_password_reset.py --dry-run  # 试运行
"""

import argparse
import sys
from pathlib import Path

# 修复Windows编码问题
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 项目根目录
BASE_DIR = Path(__file__).parent.parent
APP_DIR = BASE_DIR / "app"


def get_user_collection():
    """获取用户集合"""
    from app.database.connection import get_collection
    return get_collection("user")


def check_users():
    """检查用户密码状态"""
    collection = get_user_collection()
    total = collection.count_documents({})
    
    # 使用 bcrypt 哈希的用户（以 $2b$ 开头）
    bcrypt_users = collection.count_documents({
        "password": {"$regex": r"^\$2[aby]\$"}
    })
    
    # 使用旧版 MD5 哈希的用户（32位十六进制）
    md5_users = collection.count_documents({
        "password": {"$regex": r"^[a-f0-9]{32}$"}
    })
    
    # 其他格式
    other_users = total - bcrypt_users - md5_users
    
    print(f"总用户数: {total}")
    print(f"bcrypt 用户: {bcrypt_users}")
    print(f"MD5 用户: {md5_users}")
    print(f"其他格式用户: {other_users}")
    
    return md5_users + other_users


def mark_for_reset(dry_run=False):
    """标记所有用户需要重置密码"""
    collection = get_user_collection()
    
    # 查找所有非 bcrypt 哈希的用户
    users = collection.find({
        "password": {"$not": {"$regex": r"^\$2[aby]\$"}}
    })
    
    count = 0
    for user in users:
        if not dry_run:
            collection.update_one(
                {"_id": user["_id"]},
                {
                    "$set": {
                        "password_reset_required": True,
                        "password": None  # 清除旧密码
                    }
                }
            )
        count += 1
        print(f"{'[DRY-RUN] ' if dry_run else ''}Marked user: {user.get('username')}")
    
    return count


def main():
    parser = argparse.ArgumentParser(description="强制用户重置密码")
    parser.add_argument("--check", action="store_true", help="检查用户密码状态")
    parser.add_argument("--reset", action="store_true", help="标记用户需要重置密码")
    parser.add_argument("--dry-run", action="store_true", help="试运行")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("强制密码重置工具")
    print("=" * 60)
    
    if args.check:
        print("\n检查用户密码状态...")
        reset_count = check_users()
        print(f"\n需要重置密码的用户: {reset_count}")
    
    elif args.reset:
        print("\n标记用户需要重置密码...")
        count = mark_for_reset(dry_run=args.dry_run)
        print(f"\n已标记 {count} 个用户需要重置密码")
        if args.dry_run:
            print("[DRY-RUN] 未实际修改数据")
    
    else:
        parser.print_help()
    
    print("=" * 60)


if __name__ == "__main__":
    main()
