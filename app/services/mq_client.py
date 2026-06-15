# -*- coding: utf-8 -*-
"""
ARL 消息队列客户端封装
提供统一的消息队列接口
"""

import json
import logging
from typing import Dict, Any, Optional, Callable

logger = logging.getLogger(__name__)


class MessageQueueClient:
    """消息队列客户端"""

    def __init__(self, broker_url: str = "amqp://guest:guest@localhost:5672//"):
        """
        初始化消息队列客户端

        Args:
            broker_url: RabbitMQ 连接 URL
        """
        self.broker_url = broker_url
        self._connection = None
        self._channel = None

    def connect(self) -> bool:
        """
        连接到消息队列

        Returns:
            是否成功
        """
        try:
            import pika
            self._connection = pika.BlockingConnection(
                pika.URLParameters(self.broker_url)
            )
            self._channel = self._connection.channel()
            logger.info(f"Connected to message queue: {self.broker_url}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to message queue: {e}")
            return False

    def disconnect(self) -> None:
        """断开连接"""
        if self._connection and not self._connection.is_closed:
            self._connection.close()
            logger.info("Disconnected from message queue")

    def declare_queue(self, queue_name: str, durable: bool = True) -> bool:
        """
        声明队列

        Args:
            queue_name: 队列名称
            durable: 是否持久化

        Returns:
            是否成功
        """
        if not self._channel:
            logger.error("Not connected to message queue")
            return False

        try:
            self._channel.queue_declare(
                queue=queue_name,
                durable=durable
            )
            logger.debug(f"Queue declared: {queue_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to declare queue {queue_name}: {e}")
            return False

    def publish(self, queue_name: str, message: Dict[str, Any],
                persistent: bool = True, priority: int = 0) -> bool:
        """
        发布消息

        Args:
            queue_name: 队列名称
            message: 消息内容
            persistent: 是否持久化
            priority: 优先级

        Returns:
            是否成功
        """
        if not self._channel:
            logger.error("Not connected to message queue")
            return False

        try:
            import pika

            properties = pika.BasicProperties(
                delivery_mode=2 if persistent else 1,
                priority=priority,
                content_type='application/json'
            )

            self._channel.basic_publish(
                exchange='',
                routing_key=queue_name,
                body=json.dumps(message, default=str),
                properties=properties
            )

            logger.debug(f"Message published to {queue_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish message to {queue_name}: {e}")
            return False

    def consume(self, queue_name: str, callback: Callable,
                auto_ack: bool = False) -> None:
        """
        消费消息

        Args:
            queue_name: 队列名称
            callback: 消息处理回调函数
            auto_ack: 是否自动确认
        """
        if not self._channel:
            logger.error("Not connected to message queue")
            return

        def _callback(ch, method, properties, body):
            try:
                message = json.loads(body)
                callback(message)
                if not auto_ack:
                    ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                if not auto_ack:
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

        self._channel.basic_consume(
            queue=queue_name,
            on_message_callback=_callback,
            auto_ack=auto_ack
        )

        logger.info(f"Starting to consume messages from {queue_name}")
        self._channel.start_consuming()

    def get_queue_size(self, queue_name: str) -> int:
        """
        获取队列大小

        Args:
            queue_name: 队列名称

        Returns:
            队列中的消息数量
        """
        if not self._channel:
            return 0

        try:
            result = self._channel.queue_declare(
                queue=queue_name,
                passive=True
            )
            return result.method.message_count
        except Exception as e:
            logger.error(f"Failed to get queue size for {queue_name}: {e}")
            return 0

    def purge_queue(self, queue_name: str) -> bool:
        """
        清空队列

        Args:
            queue_name: 队列名称

        Returns:
            是否成功
        """
        if not self._channel:
            return False

        try:
            self._channel.queue_purge(queue=queue_name)
            logger.info(f"Queue purged: {queue_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to purge queue {queue_name}: {e}")
            return False

    def is_connected(self) -> bool:
        """检查是否已连接"""
        return (
            self._connection is not None and
            not self._connection.is_closed and
            self._channel is not None and
            self._channel.is_open
        )


class RedisQueueClient:
    """Redis 队列客户端（轻量级替代方案，复用 RedisManager 的连接池）"""

    def __init__(self, redis_manager=None):
        """
        初始化 Redis 队列客户端

        Args:
            redis_manager: RedisManager 实例，如果为 None 则创建新连接
        """
        self._redis_manager = redis_manager
        self._client = None

    def connect(self, host: str = "localhost", port: int = 6379, db: int = 0) -> bool:
        """
        连接到 Redis

        Args:
            host: Redis 主机
            port: Redis 端口
            db: Redis 数据库

        Returns:
            是否成功
        """
        # 优先使用已有的 RedisManager
        if self._redis_manager and self._redis_manager.enabled:
            self._client = self._redis_manager.client
            return True

        try:
            import redis
            from redis import ConnectionPool
            pool = ConnectionPool(host=host, port=port, db=db, decode_responses=True)
            self._client = redis.Redis(connection_pool=pool)
            self._client.ping()
            logger.info(f"Connected to Redis: {host}:{port}/{db}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            return False

    def disconnect(self) -> None:
        """断开连接（如果使用外部 RedisManager 则不断开）"""
        if self._client and not self._redis_manager:
            self._client.close()
            logger.info("Disconnected from Redis")

    def push(self, queue_name: str, message: Dict[str, Any]) -> bool:
        """
        推送消息到队列

        Args:
            queue_name: 队列名称
            message: 消息内容

        Returns:
            是否成功
        """
        if not self._client:
            return False

        try:
            self._client.rpush(queue_name, json.dumps(message, default=str))
            return True
        except Exception as e:
            logger.error(f"Failed to push message to {queue_name}: {e}")
            return False

    def pop(self, queue_name: str, timeout: int = 0) -> Optional[Dict[str, Any]]:
        """
        从队列弹出消息

        Args:
            queue_name: 队列名称
            timeout: 超时时间（秒），0 表示阻塞等待

        Returns:
            消息内容，超时返回 None
        """
        if not self._client:
            return None

        try:
            if timeout > 0:
                result = self._client.blpop(queue_name, timeout=timeout)
                if result:
                    return json.loads(result[1])
                return None
            else:
                result = self._client.lpop(queue_name)
                if result:
                    return json.loads(result)
                return None
        except Exception as e:
            logger.error(f"Failed to pop message from {queue_name}: {e}")
            return None

    def get_queue_size(self, queue_name: str) -> int:
        """
        获取队列大小

        Args:
            queue_name: 队列名称

        Returns:
            队列中的消息数量
        """
        if not self._client:
            return 0

        try:
            return self._client.llen(queue_name)
        except Exception as e:
            logger.error(f"Failed to get queue size for {queue_name}: {e}")
            return 0

    def clear_queue(self, queue_name: str) -> bool:
        """
        清空队列

        Args:
            queue_name: 队列名称

        Returns:
            是否成功
        """
        if not self._client:
            return False

        try:
            self._client.delete(queue_name)
            return True
        except Exception as e:
            logger.error(f"Failed to clear queue {queue_name}: {e}")
            return False

    def is_connected(self) -> bool:
        """检查是否已连接"""
        if not self._client:
            return False
        try:
            self._client.ping()
            return True
        except Exception as e:
            # Log at debug level - this is expected when MQ is unavailable
            import logging
            logging.getLogger(__name__).debug(f"MQ connection check failed: {e}")
            return False


def create_mq_client(broker_url: str = "amqp://guest:guest@localhost:5672//") -> MessageQueueClient:
    """
    创建消息队列客户端

    Args:
        broker_url: 连接 URL

    Returns:
        MessageQueueClient 实例
    """
    return MessageQueueClient(broker_url)


def create_redis_queue_client(redis_manager=None) -> RedisQueueClient:
    """
    创建 Redis 队列客户端

    Args:
        redis_manager: RedisManager 实例（可选，复用连接池）

    Returns:
        RedisQueueClient 实例
    """
    return RedisQueueClient(redis_manager)
