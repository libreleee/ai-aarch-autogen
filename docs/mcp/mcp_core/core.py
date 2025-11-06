"""
MCP Core: 추상화된 메시지 통신 계층
TCP, Redis, Pulsar 등을 선택하여 사용 가능
"""

import asyncio
import json
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional, AsyncIterator, Callable
from enum import Enum
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MessageType(Enum):
    """메시지 타입 정의"""
    REGISTER = "REGISTER"
    REGISTER_RESPONSE = "REGISTER_RESPONSE"
    REQUEST = "REQUEST"
    RESPONSE = "RESPONSE"
    BROADCAST = "BROADCAST"
    HEARTBEAT = "HEARTBEAT"
    HEARTBEAT_ACK = "HEARTBEAT_ACK"
    DISCONNECT = "DISCONNECT"
    ACK = "ACK"


class Message:
    """MCP 메시지 클래스"""
    
    def __init__(
        self,
        message_type: MessageType,
        sender_id: str,
        payload: Dict[str, Any],
        message_id: Optional[str] = None,
        target_agent: Optional[str] = None,
        timestamp: Optional[str] = None
    ):
        self.message_id = message_id or str(uuid.uuid4())
        self.message_type = message_type
        self.sender_id = sender_id
        self.target_agent = target_agent
        self.payload = payload
        self.timestamp = timestamp or datetime.utcnow().isoformat() + "Z"
    
    def to_dict(self) -> Dict[str, Any]:
        """메시지를 딕셔너리로 변환"""
        return {
            "message_id": self.message_id,
            "message_type": self.message_type.value,
            "sender_id": self.sender_id,
            "target_agent": self.target_agent,
            "timestamp": self.timestamp,
            "payload": self.payload
        }
    
    def to_json(self) -> str:
        """메시지를 JSON으로 변환"""
        return json.dumps(self.to_dict())
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Message":
        """딕셔너리로부터 메시지 생성"""
        return Message(
            message_type=MessageType[data["message_type"]],
            sender_id=data["sender_id"],
            payload=data.get("payload", {}),
            message_id=data.get("message_id"),
            target_agent=data.get("target_agent"),
            timestamp=data.get("timestamp")
        )
    
    @staticmethod
    def from_json(json_str: str) -> "Message":
        """JSON으로부터 메시지 생성"""
        return Message.from_dict(json.loads(json_str))


class MessageBroker(ABC):
    """메시지 브로커 추상 클래스"""
    
    @abstractmethod
    async def connect(self) -> None:
        """브로커에 연결"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """브로커 연결 해제"""
        pass
    
    @abstractmethod
    async def publish(self, channel: str, message: Message) -> None:
        """메시지 발행"""
        pass
    
    @abstractmethod
    async def subscribe(self, channel: str) -> AsyncIterator[Message]:
        """채널 구독"""
        pass
    
    @abstractmethod
    async def request_response(
        self,
        target_agent: str,
        message: Message,
        timeout: float = 30.0
    ) -> Optional[Message]:
        """요청-응답 패턴"""
        pass
    
    @abstractmethod
    async def broadcast(self, message: Message) -> None:
        """모든 구독자에게 브로드캐스트"""
        pass
    
    @abstractmethod
    async def store_message(self, message: Message) -> None:
        """메시지 저장 (히스토리)"""
        pass
    
    @abstractmethod
    async def get_message_history(
        self,
        stream: str,
        limit: int = 100
    ) -> list[Dict[str, Any]]:
        """메시지 히스토리 조회"""
        pass


class ConnectionManager:
    """에이전트 연결 관리"""
    
    def __init__(self):
        self.connections: Dict[str, Dict[str, Any]] = {}
        self.agents: Dict[str, Dict[str, Any]] = {}
    
    def register_agent(
        self,
        agent_id: str,
        agent_name: str,
        agent_type: str,
        capabilities: list[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """에이전트 등록"""
        self.agents[agent_id] = {
            "agent_name": agent_name,
            "agent_type": agent_type,
            "capabilities": capabilities,
            "status": "active",
            "connected_at": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        logger.info(f"Agent registered: {agent_id} ({agent_name})")
    
    def unregister_agent(self, agent_id: str) -> None:
        """에이전트 등록 해제"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            logger.info(f"Agent unregistered: {agent_id}")
    
    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """에이전트 조회"""
        return self.agents.get(agent_id)
    
    def get_agents_by_capability(self, capability: str) -> list[str]:
        """특정 능력을 가진 에이전트 조회"""
        return [
            agent_id for agent_id, info in self.agents.items()
            if capability in info.get("capabilities", [])
        ]
    
    def get_available_agents(self) -> Dict[str, Dict[str, Any]]:
        """사용 가능한 모든 에이전트 조회"""
        return {
            agent_id: info for agent_id, info in self.agents.items()
            if info["status"] == "active"
        }


class MCPClient:
    """MCP 클라이언트"""
    
    def __init__(
        self,
        broker: MessageBroker,
        agent_id: Optional[str] = None,
        agent_name: str = "Agent",
        agent_type: str = "generic",
        capabilities: Optional[list[str]] = None
    ):
        self.broker = broker
        self.agent_id = agent_id or str(uuid.uuid4())
        self.agent_name = agent_name
        self.agent_type = agent_type
        self.capabilities = capabilities or []
        self.pending_requests: Dict[str, asyncio.Future] = {}
        self.subscriptions: Dict[str, Callable] = {}
    
    async def connect(self) -> None:
        """브로커에 연결"""
        await self.broker.connect()
        logger.info(f"Client connected: {self.agent_id}")
    
    async def disconnect(self) -> None:
        """연결 해제"""
        await self.broker.disconnect()
        logger.info(f"Client disconnected: {self.agent_id}")
    
    async def register(self) -> bool:
        """에이전트 등록"""
        message = Message(
            message_type=MessageType.REGISTER,
            sender_id=self.agent_id,
            payload={
                "agent_name": self.agent_name,
                "agent_type": self.agent_type,
                "capabilities": self.capabilities
            }
        )
        
        try:
            response = await self.broker.request_response(
                "mcp-server",
                message
            )
            if response and response.payload.get("status") == "success":
                logger.info(f"Agent registered: {self.agent_id}")
                return True
        except Exception as e:
            logger.error(f"Registration failed: {e}")
        
        return False
    
    async def send_request(
        self,
        target_agent: str,
        request_type: str,
        parameters: Optional[Dict[str, Any]] = None,
        timeout: float = 30.0
    ) -> Optional[Message]:
        """요청 전송"""
        message = Message(
            message_type=MessageType.REQUEST,
            sender_id=self.agent_id,
            target_agent=target_agent,
            payload={
                "request_type": request_type,
                "parameters": parameters or {}
            }
        )
        
        try:
            response = await self.broker.request_response(
                target_agent,
                message,
                timeout=timeout
            )
            return response
        except asyncio.TimeoutError:
            logger.error(f"Request timeout: {target_agent}")
            return None
    
    async def broadcast(
        self,
        event_type: str,
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """이벤트 브로드캐스트"""
        message = Message(
            message_type=MessageType.BROADCAST,
            sender_id=self.agent_id,
            payload={
                "event_type": event_type,
                "data": data or {}
            }
        )
        
        await self.broker.broadcast(message)
        await self.broker.store_message(message)
        logger.info(f"Broadcast sent: {event_type}")
    
    async def subscribe(
        self,
        channel: str,
        handler: Callable[[Message], None]
    ) -> None:
        """채널 구독"""
        self.subscriptions[channel] = handler
        logger.info(f"Subscribed to: {channel}")
        
        async for message in self.broker.subscribe(channel):
            try:
                await handler(message) if asyncio.iscoroutinefunction(handler) else handler(message)
            except Exception as e:
                logger.error(f"Handler error: {e}")
    
    async def send_heartbeat(self) -> None:
        """헬스 체크 전송"""
        message = Message(
            message_type=MessageType.HEARTBEAT,
            sender_id=self.agent_id,
            payload={
                "status": "alive",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        await self.broker.publish("heartbeat", message)
