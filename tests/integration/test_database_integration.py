# -*- coding: utf-8 -*-
"""
数据库集成测试
测试实际的数据库连接和操作
"""
import pytest
import os
from unittest.mock import MagicMock, patch

# 标记需要数据库连接的测试
pytestmark = pytest.mark.integration


@pytest.fixture
def real_db_connection():
    """真实数据库连接（可选）"""
    # 如果没有配置真实数据库，跳过测试
    if not os.environ.get("MONGO_URL"):
        pytest.skip("未配置MONGO_URL，跳过集成测试")

    from app.database.connection import DatabaseManager
    db_manager = DatabaseManager()
    yield db_manager
    db_manager.close()


class TestDatabaseIntegration:
    """数据库集成测试"""

    def test_connect_to_database(self, real_db_connection):
        """测试连接数据库"""
        result = real_db_connection.health_check()
        assert result["status"] == "healthy"

    def test_create_and_query_document(self, real_db_connection):
        """测试创建和查询文档"""
        db = real_db_connection.get_database("arl_test")
        collection = db["test_collection"]

        # 清理
        collection.drop()

        # 插入文档
        doc = {"name": "test", "value": 123}
        result = collection.insert_one(doc)
        assert result.inserted_id is not None

        # 查询文档
        found = collection.find_one({"name": "test"})
        assert found is not None
        assert found["value"] == 123

        # 清理
        collection.drop()

    def test_update_document(self, real_db_connection):
        """测试更新文档"""
        db = real_db_connection.get_database("arl_test")
        collection = db["test_collection"]

        # 清理
        collection.drop()

        # 插入文档
        collection.insert_one({"name": "test", "value": 1})

        # 更新文档
        result = collection.update_one(
            {"name": "test"},
            {"$set": {"value": 2}}
        )
        assert result.modified_count == 1

        # 验证更新
        found = collection.find_one({"name": "test"})
        assert found["value"] == 2

        # 清理
        collection.drop()

    def test_delete_document(self, real_db_connection):
        """测试删除文档"""
        db = real_db_connection.get_database("arl_test")
        collection = db["test_collection"]

        # 清理
        collection.drop()

        # 插入文档
        collection.insert_one({"name": "test"})

        # 删除文档
        result = collection.delete_one({"name": "test"})
        assert result.deleted_count == 1

        # 验证删除
        found = collection.find_one({"name": "test"})
        assert found is None

        # 清理
        collection.drop()

    def test_bulk_operations(self, real_db_connection):
        """测试批量操作"""
        db = real_db_connection.get_database("arl_test")
        collection = db["test_collection"]

        # 清理
        collection.drop()

        # 批量插入
        docs = [{"name": f"test_{i}", "value": i} for i in range(10)]
        result = collection.insert_many(docs)
        assert len(result.inserted_ids) == 10

        # 批量查询
        found = list(collection.find({"name": {"$regex": "test_"}}))
        assert len(found) == 10

        # 清理
        collection.drop()

    def test_aggregation(self, real_db_connection):
        """测试聚合操作"""
        db = real_db_connection.get_database("arl_test")
        collection = db["test_collection"]

        # 清理
        collection.drop()

        # 插入测试数据
        docs = [
            {"category": "A", "value": 10},
            {"category": "A", "value": 20},
            {"category": "B", "value": 30},
        ]
        collection.insert_many(docs)

        # 聚合
        pipeline = [
            {"$group": {"_id": "$category", "total": {"$sum": "$value"}}}
        ]
        result = list(collection.aggregate(pipeline))

        # 验证结果
        categories = {r["_id"]: r["total"] for r in result}
        assert categories["A"] == 30
        assert categories["B"] == 30

        # 清理
        collection.drop()

    def test_index_creation(self, real_db_connection):
        """测试索引创建"""
        db = real_db_connection.get_database("arl_test")
        collection = db["test_indexed_collection"]

        # 清理
        collection.drop()

        # 创建索引
        collection.create_index("name", unique=True)
        collection.create_index([("value", -1)])

        # 验证索引
        indexes = collection.index_information()
        assert "name_1" in indexes
        assert "value_-1" in indexes

        # 清理
        collection.drop()


class TestDatabaseManagerIntegration:
    """数据库管理器集成测试"""

    def test_multiple_database_access(self, real_db_connection):
        """测试多数据库访问"""
        db1 = real_db_connection.get_database("arl_test1")
        db2 = real_db_connection.get_database("arl_test2")

        # 在两个数据库中操作
        db1["test"].insert_one({"db": "db1"})
        db2["test"].insert_one({"db": "db2"})

        # 验证数据隔离
        assert db1["test"].find_one()["db"] == "db1"
        assert db2["test"].find_one()["db"] == "db2"

        # 清理
        db1["test"].drop()
        db2["test"].drop()

    def test_collection_operations(self, real_db_connection):
        """测试集合操作"""
        collection = real_db_connection.get_collection("test_collection")

        # 清理
        collection.drop()

        # 插入
        collection.insert_one({"test": True})

        # 查询
        found = collection.find_one({"test": True})
        assert found is not None

        # 清理
        collection.drop()
