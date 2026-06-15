# -*- coding: utf-8 -*-
"""
ARL任务服务
封装任务相关业务逻辑
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.types import TaskStatus, TaskType
from app.core.exceptions import NotFoundException, ValidationException
from app.core.audit import audit_log
from app.database.repositories import TaskRepository

logger = logging.getLogger(__name__)


class TaskService:
    """
    任务服务

    封装任务管理的业务逻辑，包括：
    - 任务创建
    - 任务状态更新
    - 任务查询
    - 任务取消

    用法：
        service = TaskService()
        task = service.create_task(target='example.com', task_type=TaskType.DOMAIN)
    """

    def __init__(self):
        self.repo = TaskRepository()

    @audit_log(action='create', resource='task')
    def create_task(
        self,
        target: str,
        task_type: TaskType,
        options: Optional[Dict[str, Any]] = None,
        created_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        创建新任务

        Args:
            target: 扫描目标（域名/IP/URL）
            task_type: 任务类型
            options: 扫描选项
            created_by: 创建用户

        Returns:
            任务信息字典

        Raises:
            ValidationException: 参数无效
        """
        # 验证输入
        if not target:
            raise ValidationException("Target cannot be empty", field='target')

        # 生成任务ID
        task_id = str(uuid.uuid4())

        # 构建任务文档
        task_doc = {
            'task_id': task_id,
            'target': target,
            'task_type': task_type.value,
            'status': TaskStatus.PENDING.value,
            'options': options or {},
            'created_at': datetime.now(),
            'created_by': created_by,
            'result_count': 0
        }

        # 插入数据库
        task_doc_id = self.repo.insert_one(task_doc)

        logger.info(f"Task created: {task_id} for {target}")
        return task_doc

    def get_task(self, task_id: str) -> Dict[str, Any]:
        """
        获取任务详情

        Args:
            task_id: 任务ID

        Returns:
            任务信息字典

        Raises:
            NotFoundException: 任务不存在
        """
        task = self.repo.find_by_task_id(task_id)
        if not task:
            raise NotFoundException(f"Task not found: {task_id}", resource_type='task')
        return task

    def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        error_message: Optional[str] = None,
        result_count: Optional[int] = None
    ) -> bool:
        """
        更新任务状态

        Args:
            task_id: 任务ID
            status: 新状态
            error_message: 错误消息（可选）
            result_count: 结果数量（可选）

        Returns:
            是否更新成功
        """
        update = {
            '$set': {
                'status': status.value,
                'updated_at': datetime.now()
            }
        }

        if status == TaskStatus.COMPLETED:
            update['$set']['completed_at'] = datetime.now()

        if error_message:
            update['$set']['error_message'] = error_message

        if result_count is not None:
            update['$set']['result_count'] = result_count

        success = self.repo.update_one({'task_id': task_id}, update)

        if success:
            logger.info(f"Task status updated: {task_id} -> {status.value}")
        else:
            logger.warning(f"Task not found for status update: {task_id}")

        return success

    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务

        Args:
            task_id: 任务ID

        Returns:
            是否取消成功

        Raises:
            NotFoundException: 任务不存在
        """
        task = self.get_task(task_id)

        # 只能取消待执行或运行中的任务
        current_status = task.get('status')
        if current_status not in [TaskStatus.PENDING.value, TaskStatus.RUNNING.value]:
            raise ValidationException(
                f"Cannot cancel task with status: {current_status}",
                field='status'
            )

        return self.update_task_status(task_id, TaskStatus.CANCELLED)

    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        target: Optional[str] = None,
        created_by: Optional[str] = None,
        limit: int = 100,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """
        查询任务列表

        Args:
            status: 按状态过滤
            target: 按目标过滤
            created_by: 按创建用户过滤
            limit: 返回数量限制
            skip: 跳过数量

        Returns:
            任务列表
        """
        query = {}

        if status:
            query['status'] = status.value
        if target:
            query['target'] = {'$regex': target, '$options': 'i'}
        if created_by:
            query['created_by'] = created_by

        return self.repo.find_many(
            query,
            sort=[('created_at', -1)],
            limit=limit,
            skip=skip
        )

    def count_tasks(
        self,
        status: Optional[TaskStatus] = None,
        created_by: Optional[str] = None
    ) -> int:
        """
        统计任务数量

        Args:
            status: 按状态过滤
            created_by: 按创建用户过滤

        Returns:
            任务数量
        """
        query = {}

        if status:
            query['status'] = status.value
        if created_by:
            query['created_by'] = created_by

        return self.repo.count(query)

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取任务统计信息

        Returns:
            统计信息字典
        """
        return self.repo.get_statistics()

    def delete_task(self, task_id: str) -> bool:
        """
        删除任务

        Args:
            task_id: 任务ID

        Returns:
            是否删除成功
        """
        task = self.get_task(task_id)
        return self.repo.delete_by_id(str(task['_id']))
