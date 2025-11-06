"""
Redis Broker
Redis Pub/Sub + Streams를 사용한 메시지 브로커
"""

import asyncio
import json
import logging
from typing import AsyncIterator, Optional, Dict, Any
import redis.asyncio as redis

from .core import MessageBroker, Message, MessageType

logger = logging.getLogger(__name__)


class RedisBroker(MessageBroker):
    """Redis 기반 메시지 브로커"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis: Optional[redis.Redis] = None
        self.pubsub = None
        self.connected = False
    
    async def connect(self) -> None:
        """Redis에 연결"""
        try:
            self.redis = await redis.from_url(self.redis_url)
            self.pubsub = self.redis.pubsub()
            
            # 연결 테스트
            await self.redis.ping()
            
            self.connected = True
            logger.info(f"Redis Broker connected to {self.redis_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Redis 연결 해제"""
        if self.pubsub:
            await self.pubsub.close()
        
        if self.redis:
            await self.redis.close()
        
        self.connected = False
        logger.info("Redis Broker disconnected")
    
    async def publish(self, channel: str, message: Message) -> None:
        """메시지 발행"""
        try:
            await self.redis.publish(
                f"mcp:{channel}",
                message.to_json()
            )
            logger.debug(f"Message published to {channel}")
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
    
    async def subscribe(self, channel: str) -> AsyncIterator[Message]:
        """채널 구독"""
        try:
            pubsub = self.redis.pubsub()
            await pubsub.subscribe(f"mcp:{channel}")
            
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    try:
                        msg = Message.from_json(message['data'])
                        yield msg
                    except Exception as e:
                        logger.error(f"Failed to parse message: {e}")
        
        except Exception as e:
            logger.error(f"Subscribe error: {e}")
        
        finally:
            await pubsub.close()
    
    async def request_response(
        self,
        target_agent: str,
        message: Message,
        timeout: float = 30.0
    ) -> Optional[Message]:
        """요청-응답 패턴"""
        try:
            # 응답 채널 이름
            response_channel = f"response:{message.message_id}"
            
            # 요청 발행
            await self.publish(f"requests:{target_agent}", message)
            
            # 응답 대기
            pubsub = self.redis.pubsub()
            await pubsub.subscribe(f"mcp:{response_channel}")
            
            try:
                async with asyncio.timeout(timeout):
                    async for msg in pubsub.listen():
                        if msg['type'] == 'message':
                            response = Message.from_json(msg['data'])
                            await pubsub.close()
                            return response
            
            except asyncio.TimeoutError:
                logger.error(f"Request timeout: {message.message_id}")
                await pubsub.close()
                return None
        
        except Exception as e:
            logger.error(f"Request/Response error: {e}")
            return None
    
    async def broadcast(self, message: Message) -> None:
        """모든 구독자에게 브로드캐스트"""
        try:
            await self.redis.publish("mcp:broadcast", message.to_json())
            logger.debug(f"Broadcast sent: {message.message_id}")
        except Exception as e:
            logger.error(f"Failed to broadcast: {e}")
    
    async def store_message(self, message: Message) -> None:
        """메시지 저장 (Streams)"""
        try:
            stream_name = f"mcp:stream:{message.message_type.value.lower()}"
            
            await self.redis.xadd(
                stream_name,
                {
                    "message_id": message.message_id,
                    "sender_id": message.sender_id,
                    "message_type": message.message_type.value,
                    "payload": message.to_json(),
                    "timestamp": message.timestamp
                }
            )
            
            logger.debug(f"Message stored in {stream_name}")
        
        except Exception as e:
            logger.error(f"Failed to store message: {e}")
    
    async def get_message_history(
        self,
        stream: str,
        limit: int = 100
    ) -> list[Dict[str, Any]]:
        """메시지 히스토리 조회"""
        try:
            stream_name = f"mcp:stream:{stream}"
            
            # 최신 메시지부터 조회
            messages = await self.redis.xrevrange(
                stream_name,
                count=limit
            )
            
            result = []
            for msg_id, msg_data in messages:
                result.append({
                    "id": msg_id,
                    "data": msg_data
                })
            
            return result
        
        except Exception as e:
            logger.error(f"Failed to get message history: {e}")
            return []


class RedisBrokerConfig:
    """Redis Broker 설정"""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None
    ):
        if password:
            self.redis_url = f"redis://:{password}@{host}:{port}/{db}"
        else:
            self.redis_url = f"redis://{host}:{port}/{db}"
    
    def to_url(self) -> str:
        return self.redis_url
