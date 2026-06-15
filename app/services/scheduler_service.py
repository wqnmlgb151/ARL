# -*- coding: utf-8 -*-
"""
ARL调度器服务
封装任务调度相关业务逻辑
"""

import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from app.core.exceptions import NotFoundException, ValidationException
from app.core.audit import audit_log
from app.database.repositories import SchedulerRepository, TaskRepository

logger = logging.getLogger(__name__)


class SchedulerStatus(Enum):
    """调度器状态枚举"""
    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"


class SchedulerService:
    """
    调度器服务

    封装任务调度的业务逻辑，包括：
    - 调度任务管理
    - 周期性任务执行
    - 任务队列管理

    用法：
        service = SchedulerService()
        scheduler = service.create_scheduler(target='example.com', interval_hours=24)
    """

    def __init__(self):
        self.repo = SchedulerRepository()
        self.task_repo = TaskRepository()

    @audit_log(action='create', resource='scheduler')
    def create_scheduler(
        self,
        target: str,
        task_type: str,
        interval_hours: int = 24,
        options: Optional[Dict[str, Any]] = None,
        created_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        创建调度任务

        Args:
            target: 扫描目标
            task_type: 任务类型
            interval_hours: 执行间隔（小时）
            options: 扫描选项
            created_by: 创建用户

        Returns:
            调度任务信息

        Raises:
            ValidationException: 参数无效
        """
        # 验证输入
        if not target:
            raise ValidationException("Target cannot be empty", field='target')

        if interval_hours < 1:
            raise ValidationException("Interval must be at least 1 hour", field='interval_hours')

        # 计算下次执行时间
        next_run = datetime.now() + timedelta(hours=interval_hours)

        # 构建调度任务文档
        scheduler_doc = {
            'target': target,
            'task_type': task_type,
            'interval_hours': interval_hours,
            'options': options or {},
            'status': SchedulerStatus.ACTIVE.value,
            'next_run': next_run,
            'last_run': None,
            'run_count': 0,
            'created_at': datetime.now(),
            'created_by': created_by
        }

        scheduler_id = self.repo.insert_one(scheduler_doc)
        logger.info(f"Scheduler created: {target} with interval {interval_hours}h")

        return scheduler_doc

    def get_scheduler(self, scheduler_id: str) -> Dict[str, Any]:
        """
        获取调度任务详情

        Args:
            scheduler_id: 调度任务ID

        Returns:
            调度任务信息

        Raises:
            NotFoundException: 调度任务不存在
        """
        scheduler = self.repo.find_by_id(scheduler_id)
        if not scheduler:
            raise NotFoundException(f"Scheduler not found: {scheduler_id}", resource_type='scheduler')

        return scheduler

    def find_by_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        根据任务ID查找调度任务

        Args:
            task_id: 任务ID

        Returns:
            调度任务信息
        """
        return self.repo.find_by_task(task_id)

    def find_active(self) -> List[Dict[str, Any]]:
        """
        查找活跃的调度任务

        Returns:
            调度任务列表
        """
        return self.repo.find_active()

    def find_due_tasks(self) -> List[Dict[str, Any]]:
        """
        查找到期的调度任务

        Returns:
            到期任务列表
        """
        return self.repo.find_due_tasks()

    def update_scheduler_status(
        self,
        scheduler_id: str,
        status: str,
        increment_run_count: bool = True,
        interval_hours: Optional[int] = None
    ) -> bool:
        """
        更新调度任务状态

        Args:
            scheduler_id: 调度任务ID
            status: 新状态
            increment_run_count: 是否增加执行次数
            interval_hours: 调度间隔（可选，避免重复查询）

        Returns:
            是否更新成功
        """
        # 获取interval_hours（优先使用传入的值）
        if interval_hours is None:
            scheduler = self.get_scheduler(scheduler_id)
            interval_hours = scheduler['interval_hours']

        update = {
            '$set': {
                'status': status,
                'last_run': datetime.now(),
                'next_run': datetime.now() + timedelta(hours=interval_hours)
            }
        }

        if increment_run_count:
            update['$inc'] = {'run_count': 1}

        return self.repo.update_by_id(scheduler_id, update)

    def pause_scheduler(self, scheduler_id: str) -> bool:
        """
        暂停调度任务

        Args:
            scheduler_id: 调度任务ID

        Returns:
            是否暂停成功
        """
        scheduler = self.get_scheduler(scheduler_id)
        if scheduler.get('status') == SchedulerStatus.PAUSED.value:
            logger.warning(f"Scheduler already paused: {scheduler_id}")
            return False

        success = self.update_scheduler_status(
            scheduler_id,
            SchedulerStatus.PAUSED.value,
            increment_run_count=False,
            interval_hours=scheduler['interval_hours']
        )

        if success:
            logger.info(f"Scheduler paused: {scheduler_id}")

        return success

    def resume_scheduler(self, scheduler_id: str) -> bool:
        """
        恢复调度任务

        Args:
            scheduler_id: 调度任务ID

        Returns:
            是否恢复成功
        """
        scheduler = self.get_scheduler(scheduler_id)
        if scheduler.get('status') != SchedulerStatus.PAUSED.value:
            logger.warning(f"Scheduler not paused: {scheduler_id}")
            return False

        # 重新计算下次执行时间
        next_run = datetime.now() + timedelta(hours=scheduler['interval_hours'])

        success = self.repo.update_by_id(scheduler_id, {
            '$set': {
                'status': SchedulerStatus.ACTIVE.value,
                'next_run': next_run
            }
        })

        if success:
            logger.info(f"Scheduler resumed: {scheduler_id}")

        return success

    def delete_scheduler(self, scheduler_id: str) -> bool:
        """
        删除调度任务

        Args:
            scheduler_id: 调度任务ID

        Returns:
            是否删除成功
        """
        scheduler = self.get_scheduler(scheduler_id)
        return self.repo.delete_by_id(scheduler_id)

    def list_schedulers(
        self,
        status: Optional[str] = None,
        target: Optional[str] = None,
        limit: int = 100,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """
        查询调度任务列表

        Args:
            status: 按状态过滤
            target: 按目标过滤
            limit: 返回数量限制
            skip: 跳过数量

        Returns:
            调度任务列表
        """
        query = {}

        if status:
            query['status'] = status
        if target:
            query['target'] = {'$regex': target, '$options': 'i'}

        return self.repo.find_many(
            query,
            sort=[('created_at', -1)],
            limit=limit,
            skip=skip
        )

    def count_schedulers(self, status: Optional[str] = None) -> int:
        """
        统计调度任务数量

        Args:
            status: 按状态过滤

        Returns:
            调度任务数量
        """
        query = {}
        if status:
            query['status'] = status

        return self.repo.count(query)

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取调度任务统计信息

        Returns:
            统计信息字典
        """
        pipeline = [
            {
                '$group': {
                    '_id': '$status',
                    'count': {'$sum': 1}
                }
            }
        ]

        try:
            result = self.repo.aggregate(pipeline)
            stats = {item['_id']: item['count'] for item in result}
            stats['total'] = sum(stats.values())
            return stats
        except Exception as e:
            logger.error(f"Failed to get scheduler statistics: {e}")
            return {'total': 0}

    def execute_scheduler(self, scheduler_id: str) -> Optional[str]:
        """
        执行调度任务

        Args:
            scheduler_id: 调度任务ID

        Returns:
            创建的任务ID

        Raises:
            NotFoundException: 调度任务不存在
        """
        scheduler = self.get_scheduler(scheduler_id)

        if scheduler.get('status') != SchedulerStatus.ACTIVE.value:
            logger.warning(f"Scheduler not active: {scheduler_id}")
            return None

        # 创建新任务
        from app.services.task_service import TaskService
        from app.core.types import TaskType

        task_service = TaskService()

        try:
            task_type = TaskType(scheduler['task_type'])
        except ValueError:
            logger.error(f"Invalid task type: {scheduler['task_type']}")
            return None

        task = task_service.create_task(
            target=scheduler['target'],
            task_type=task_type,
            options=scheduler.get('options', {}),
            created_by=scheduler.get('created_by')
        )

        # 更新调度任务状态
        self.update_scheduler_status(scheduler_id, 'active')

        logger.info(f"Scheduler executed: {scheduler_id}, task created: {task['task_id']}")

        return task['task_id']
