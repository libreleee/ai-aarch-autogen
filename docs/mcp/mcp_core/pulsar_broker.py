"""
Pulsar Broker
Apache Pulsar를 사용한 메시지 브로커
"""

import asyncio
import json
import logging
from typing import AsyncIterator, Optional, Dict, Any

from .core import MessageBroker, Message, MessageType

logger = logging.getLogger(__name__)


class PulsarBroker(MessageBroker):
    """Pulsar 기반 메시지 브로커"""
    
    def __init__(
        self,
        service_url: str = "pulsar://localhost:6650",
        tenant: str = "ai-aarch",
        namespace: str = "default"
    ):
        self.service_url = service_url
        self.tenant = tenant
        self.namespace = namespace
        self.client = None
        self.connected = False
        
        # Pulsar 클라이언트 임포트 (필수 설치: pip install pulsar-client)
        try:
            import pulsar
            self.pulsar = pulsar
        except ImportError:
            logger.error("Pulsar client not installed: pip install pulsar-client")
            raise
    
    async def connect(self) -> None:
        """Pulsar에 연결"""
        try:
            # Note: Pulsar 클라이언트는 동기식이므로 executor에서 실행
            loop = asyncio.get_event_loop()
            
            def _connect():
                return self.pulsar.Client(self.service_url)
            
            self.client = await loop.run_in_executor(None, _connect)
            self.connected = True
            logger.info(f"Pulsar Broker connected to {self.service_url}")
        
        except Exception as e:
            logger.error(f"Failed to connect to Pulsar: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Pulsar 연결 해제"""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.client.close)
            self.connected = False
            logger.info("Pulsar Broker disconnected")
        except Exception as e:
            logger.error(f"Failed to disconnect: {e}")
    
    def _get_topic_name(self, channel: str) -> str:
        """토픽 이름 생성"""
        return f"persistent://{self.tenant}/{self.namespace}/{channel}"
    
    async def publish(self, channel: str, message: Message) -> None:
        """메시지 발행"""
        try:
            loop = asyncio.get_event_loop()
            topic = self._get_topic_name(channel)
            
            def _publish():
                producer = self.client.create_producer(topic)
                producer.send(message.to_json().encode('utf-8'))
                producer.close()
            
            await loop.run_in_executor(None, _publish)
            logger.debug(f"Message published to {channel}")
        
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
    
    async def subscribe(self, channel: str) -> AsyncIterator[Message]:
        """채널 구독"""
        try:
            loop = asyncio.get_event_loop()
            topic = self._get_topic_name(channel)
            
            def _subscribe():
                consumer = self.client.subscribe(
                    topic,
                    subscription_name=f"sub-{channel}",
                    consumer_type=self.pulsar.ConsumerType.Shared
                )
                return consumer
            
            consumer = await loop.run_in_executor(None, _subscribe)
            
            while self.connected:
                def _receive():
                    msg = consumer.receive()
                    return msg
                
                try:
                    msg = await asyncio.wait_for(
                        loop.run_in_executor(None, _receive),
                        timeout=1.0
                    )
                    
                    try:
                        message = Message.from_json(msg.data().decode('utf-8'))
                        
                        def _ack():
                            consumer.acknowledge(msg)
                        
                        await loop.run_in_executor(None, _ack)
                        yield message
                    
                    except Exception as e:
                        logger.error(f"Failed to parse message: {e}")
                        
                        def _nack():
                            consumer.negative_acknowledge(msg)
                        
                        await loop.run_in_executor(None, _nack)
                
                except asyncio.TimeoutError:
                    continue
            
            def _close():
                consumer.close()
            
            await loop.run_in_executor(None, _close)
        
        except Exception as e:
            logger.error(f"Subscribe error: {e}")
    
    async def request_response(
        self,
        target_agent: str,
        message: Message,
        timeout: float = 30.0
    ) -> Optional[Message]:
        """요청-응답 패턴"""
        try:
            # 응답 채널 이름
            response_channel = f"response-{message.message_id}"
            
            # 요청 발행
            await self.publish(f"requests-{target_agent}", message)
            
            # 응답 대기 (최대 timeout 초)
            response_received = asyncio.Event()
            response_message = None
            
            async def wait_response():
                nonlocal response_message
                try:
                    async for msg in self.subscribe(response_channel):
                        response_message = msg
                        response_received.set()
                        break
                except Exception as e:
                    logger.error(f"Response receive error: {e}")
            
            # 응답 대기 태스크
            wait_task = asyncio.create_task(wait_response())
            
            try:
                await asyncio.wait_for(response_received.wait(), timeout=timeout)
                return response_message
            
            except asyncio.TimeoutError:
                logger.error(f"Request timeout: {message.message_id}")
                wait_task.cancel()
                return None
        
        except Exception as e:
            logger.error(f"Request/Response error: {e}")
            return None
    
    async def broadcast(self, message: Message) -> None:
        """모든 구독자에게 브로드캐스트"""
        try:
            await self.publish("broadcast", message)
            logger.debug(f"Broadcast sent: {message.message_id}")
        except Exception as e:
            logger.error(f"Failed to broadcast: {e}")
    
    async def store_message(self, message: Message) -> None:
        """메시지 저장 (Pulsar에서는 자동으로 저장)"""
        logger.debug(f"Message stored: {message.message_id}")
    
    async def get_message_history(
        self,
        stream: str,
        limit: int = 100
    ) -> list[Dict[str, Any]]:
        """메시지 히스토리 조회"""
        try:
            topic = self._get_topic_name(f"history-{stream}")
            loop = asyncio.get_event_loop()
            
            def _get_messages():
                messages = []
                try:
                    reader = self.client.create_reader(topic)
                    for _ in range(limit):
                        if reader.has_message_available():
                            msg = reader.read_next()
                            messages.append({
                                "id": msg.message_id(),
                                "data": msg.data().decode('utf-8')
                            })
                    reader.close()
                except Exception as e:
                    logger.error(f"Failed to read history: {e}")
                
                return messages
            
            return await loop.run_in_executor(None, _get_messages)
        
        except Exception as e:
            logger.error(f"Failed to get message history: {e}")
            return []


class PulsarBrokerConfig:
    """Pulsar Broker 설정"""
    
    def __init__(
        self,
        service_url: str = "pulsar://localhost:6650",
        tenant: str = "ai-aarch",
        namespace: str = "default"
    ):
        self.service_url = service_url
        self.tenant = tenant
        self.namespace = namespace
