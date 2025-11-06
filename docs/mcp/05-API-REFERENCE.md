# MCP API 레퍼런스 (완전한 문서)

**작성일**: 2025년 11월 7일  
**상태**: ✅ 완료  
**버전**: 1.0.0

---

## 목차

1. [개요](#개요)
2. [데이터 타입](#데이터-타입)
3. [MessageType Enum](#messagetype-enum)
4. [Message 클래스](#message-클래스)
5. [MessageBroker (ABC)](#messagebroker-abc)
6. [MCPClient 클래스](#mcpclient-클래스)
7. [ConnectionManager 클래스](#connectionmanager-클래스)
8. [브로커 구현체](#브로커-구현체)
9. [BrokerFactory](#brokerfactory)
10. [에러 처리](#에러-처리)

---

## 개요

MCP 코어 라이브러리의 모든 공개 API를 정의하고 설명합니다.

```python
# 기본 임포트
from docs.mcp.mcp_core import (
    # 기본 타입
    Message,
    MessageType,
    
    # 인터페이스
    MessageBroker,
    
    # 구현체
    MCPBroker,
    RedisBroker,
    PulsarBroker,
    MCPClient,
    ConnectionManager,
    
    # 팩토리
    BrokerFactory,
    
    # 설정
    RedisBrokerConfig,
    PulsarBrokerConfig,
)
```

---

## 데이터 타입

### BrokerType

```python
class BrokerType(Enum):
    """지원하는 브로커 타입"""
    MCP = "mcp"           # TCP 기반 (기본값)
    REDIS = "redis"       # Redis Pub/Sub
    PULSAR = "pulsar"     # Apache Pulsar
```

### AgentStatus

```python
class AgentStatus(Enum):
    """에이전트 상태"""
    IDLE = "idle"
    PROCESSING = "processing"
    ERROR = "error"
    DISCONNECTED = "disconnected"
```

---

## MessageType Enum

**역할**: 메시지 타입을 정의합니다

```python
class MessageType(Enum):
    """MCP 메시지 타입"""
    
    # 에이전트 등록
    REGISTER = "register"
    """
    용도: 에이전트 시스템 참여 신청
    페이로드: {
        "agent_name": str,
        "agent_type": str,
        "capabilities": List[str]
    }
    """
    
    # 요청-응답
    REQUEST = "request"
    """
    용도: 다른 에이전트에 특정 작업 요청
    페이로드: {
        "request_type": str,
        "parameters": Dict,
        "timeout": float (optional)
    }
    """
    
    RESPONSE = "response"
    """
    용도: REQUEST에 대한 응답
    페이로드: {
        "request_id": str (상관 ID),
        "status": "success" | "error",
        "result": Dict (optional),
        "error": str (optional)
    }
    """
    
    # 브로드캐스트
    BROADCAST = "broadcast"
    """
    용도: 모든 에이전트에게 이벤트 전파
    페이로드: {
        "event_type": str,
        "data": Dict
    }
    """
    
    # 헬스 체크
    HEARTBEAT = "heartbeat"
    """
    용도: 정기적 생존 신호
    페이로드: {
        "status": "alive" | "error",
        "timestamp": ISO8601
    }
    """
    
    HEARTBEAT_ACK = "heartbeat_ack"
    """
    용도: HEARTBEAT 확인
    페이로드: {
        "received": bool
    }
    """
    
    # 연결 종료
    DISCONNECT = "disconnect"
    """
    용도: 시스템에서 탈출
    페이로드: {
        "reason": str (optional)
    }
    """
    
    # 시스템 확인
    ACK = "ack"
    """
    용도: 메시지 수신 확인
    페이로드: {
        "message_id": str (확인 메시지 ID),
        "received": bool
    }
    """
```

---

## Message 클래스

**역할**: MCP 메시지를 표현하는 데이터 모델

### 생성자

```python
class Message:
    def __init__(
        self,
        message_type: MessageType,
        sender_id: str,
        payload: Dict[str, Any],
        target_agent: Optional[str] = None,
        message_id: Optional[str] = None,
        timestamp: Optional[str] = None
    ):
        """
        매개변수:
            message_type: MessageType enum 값
            sender_id: 발신자 에이전트 ID
            payload: 메시지 데이터 (Dict)
            target_agent: 수신 에이전트 ID (선택적, None = 브로드캐스트)
            message_id: 고유 메시지 ID (자동 생성, 선택적)
            timestamp: ISO8601 타임스탬프 (자동 생성, 선택적)
        
        예제:
            message = Message(
                message_type=MessageType.REQUEST,
                sender_id="copilot-1",
                target_agent="analyzer-1",
                payload={
                    "request_type": "analyze_code",
                    "parameters": {"file": "auth.py"}
                }
            )
        """
```

### 속성

```python
@property
def message_id(self) -> str:
    """고유 메시지 ID (UUID4)"""
    
@property
def message_type(self) -> MessageType:
    """메시지 타입"""
    
@property
def sender_id(self) -> str:
    """발신자 ID"""
    
@property
def target_agent(self) -> Optional[str]:
    """대상 에이전트 ID (None = 브로드캐스트)"""
    
@property
def payload(self) -> Dict[str, Any]:
    """메시지 페이로드"""
    
@property
def timestamp(self) -> str:
    """ISO8601 형식 타임스탬프"""
```

### 메서드

```python
def to_dict(self) -> Dict[str, Any]:
    """
    메시지를 Dict로 변환
    
    반환값:
        {
            "message_id": "550e8400-e29b-41d4-a716-446655440000",
            "message_type": "request",
            "sender_id": "copilot-1",
            "target_agent": "analyzer-1",
            "timestamp": "2025-11-07T14:30:00Z",
            "payload": {...}
        }
    
    예제:
        message = Message(...)
        data = message.to_dict()
        print(data["message_id"])  # UUID 문자열
    """

def to_json(self) -> str:
    """
    메시지를 JSON 문자열로 변환
    
    반환값: JSON 문자열 (UTF-8)
    
    예제:
        json_str = message.to_json()
        # 네트워크 전송 가능
    """

@classmethod
def from_dict(cls, data: Dict[str, Any]) -> "Message":
    """
    Dict로부터 Message 생성
    
    매개변수:
        data: 메시지 Dict
    
    반환값: Message 인스턴스
    
    예제:
        data = json.loads(json_str)
        message = Message.from_dict(data)
    """

@classmethod
def from_json(cls, json_str: str) -> "Message":
    """
    JSON 문자열로부터 Message 생성
    
    매개변수:
        json_str: JSON 문자열
    
    반환값: Message 인스턴스
    
    예외:
        json.JSONDecodeError: JSON 형식 오류
        ValueError: 필수 필드 누락
    
    예제:
        message = Message.from_json(received_json)
    """
```

---

## MessageBroker (ABC)

**역할**: 모든 브로커가 구현해야 할 인터페이스 정의

### 추상 메서드

```python
from abc import ABC, abstractmethod

class MessageBroker(ABC):
    """메시지 브로커 추상 기본 클래스"""
    
    @abstractmethod
    async def connect(self) -> None:
        """
        브로커에 연결
        
        책임:
            - 네트워크 연결 수립
            - 리소스 초기화
            - 필요시 인증 수행
        
        예외:
            ConnectionError: 연결 실패
            asyncio.TimeoutError: 타임아웃
        
        예제:
            broker = MCPBroker()
            await broker.connect()  # TCP 서버 시작
        """
    
    @abstractmethod
    async def disconnect(self) -> None:
        """
        브로커 연결 해제
        
        책임:
            - 활성 연결 종료
            - 리소스 해제
            - 정리 작업 수행
        """
    
    @abstractmethod
    async def publish(
        self,
        channel: str,
        message: Message
    ) -> None:
        """
        채널에 메시지 발행
        
        매개변수:
            channel: 채널 이름
            message: 발행할 Message
        
        예외:
            RuntimeError: 브로커 미연결
            ValueError: 잘못된 채널명
        
        예제:
            await broker.publish("code_generation", message)
        """
    
    @abstractmethod
    async def subscribe(
        self,
        channel: str
    ) -> AsyncIterator[Message]:
        """
        채널 구독 (비동기 생성자)
        
        매개변수:
            channel: 구독할 채널
        
        반환값: 메시지를 생성하는 AsyncIterator
        
        예외:
            RuntimeError: 브로커 미연결
        
        예제:
            async for message in broker.subscribe("broadcasts"):
                print(f"수신: {message.message_type}")
        """
    
    @abstractmethod
    async def request_response(
        self,
        target_agent: str,
        message: Message,
        timeout: float = 30.0
    ) -> Message:
        """
        요청-응답 패턴 구현
        
        매개변수:
            target_agent: 대상 에이전트 ID
            message: 요청 메시지 (MessageType.REQUEST)
            timeout: 응답 대기 시간 (초)
        
        반환값: 응답 Message (MessageType.RESPONSE)
        
        예외:
            asyncio.TimeoutError: 타임아웃
            RuntimeError: 대상 에이전트 미응답
        
        예제:
            request = Message(MessageType.REQUEST, "agent-1", ...)
            response = await broker.request_response("agent-2", request)
        """
    
    @abstractmethod
    async def broadcast(
        self,
        message: Message
    ) -> None:
        """
        모든 구독자에게 브로드캐스트
        
        매개변수:
            message: 브로드캐스트 메시지 (MessageType.BROADCAST)
        
        예외:
            RuntimeError: 브로커 미연결
        
        예제:
            msg = Message(MessageType.BROADCAST, "agent-1", {...})
            await broker.broadcast(msg)
        """
    
    @abstractmethod
    async def store_message(
        self,
        message: Message
    ) -> None:
        """
        메시지 저장 (히스토리)
        
        매개변수:
            message: 저장할 메시지
        
        참고:
            - MCP: 지원 안 함 (메모리 부족)
            - Redis: Streams 사용
            - Pulsar: 자동 저장
        
        예제:
            await broker.store_message(message)
        """
    
    @abstractmethod
    async def get_message_history(
        self,
        stream: str,
        limit: int = 100
    ) -> List[Message]:
        """
        메시지 히스토리 조회
        
        매개변수:
            stream: 스트림 이름 (예: "broadcast")
            limit: 최대 반환 개수
        
        반환값: Message 리스트 (오래된 순서)
        
        예제:
            messages = await broker.get_message_history("broadcast", limit=50)
            for msg in messages:
                print(msg.sender_id)
        """
```

---

## MCPClient 클래스

**역할**: 에이전트를 위한 통일된 클라이언트 인터페이스

### 생성자

```python
class MCPClient:
    def __init__(
        self,
        broker: MessageBroker,
        agent_id: str,
        agent_name: str,
        agent_type: str = "general",
        capabilities: List[str] = None
    ):
        """
        매개변수:
            broker: MessageBroker 인스턴스 (MCP, Redis, Pulsar)
            agent_id: 고유 에이전트 ID (e.g., "copilot-1")
            agent_name: 사람이 읽을 수 있는 이름
            agent_type: 에이전트 타입 (e.g., "code_generator", "analyzer")
            capabilities: 에이전트 능력 리스트
        
        예제:
            broker = await BrokerFactory.create_mcp()
            client = MCPClient(
                broker=broker,
                agent_id="copilot-1",
                agent_name="Code Generator",
                agent_type="code_generator",
                capabilities=["python", "javascript", "type_hints"]
            )
        """
```

### 메서드

```python
async def connect(self) -> None:
    """
    브로커에 연결
    
    예외:
        ConnectionError: 브로커 연결 실패
    
    예제:
        await client.connect()
    """

async def disconnect(self) -> None:
    """
    브로커에서 연결 해제
    
    예제:
        await client.disconnect()
    """

async def register(self) -> None:
    """
    시스템에 에이전트 등록
    
    책임:
        - ConnectionManager에 등록
        - REGISTER 메시지 전송
        - 등록 확인 대기
    
    예외:
        RuntimeError: 등록 실패
    
    예제:
        await client.register()
    """

async def send_request(
    self,
    target_agent: str,
    request_type: str,
    parameters: Dict[str, Any],
    timeout: float = 30.0
) -> Dict[str, Any]:
    """
    다른 에이전트에 요청 전송
    
    매개변수:
        target_agent: 대상 에이전트 ID
        request_type: 요청 타입 (e.g., "analyze_code", "review_pr")
        parameters: 요청 매개변수 Dict
        timeout: 응답 대기 시간 (초)
    
    반환값: 응답 결과 Dict
    
    예외:
        asyncio.TimeoutError: 타임아웃
        RuntimeError: 에이전트 미응답
    
    예제:
        result = await client.send_request(
            target_agent="analyzer-1",
            request_type="analyze_code",
            parameters={"file": "auth.py", "check_security": True},
            timeout=60.0
        )
        print(result["analysis"])
    """

async def broadcast(
    self,
    event_type: str,
    data: Dict[str, Any]
) -> None:
    """
    모든 에이전트에게 이벤트 브로드캐스트
    
    매개변수:
        event_type: 이벤트 타입 (e.g., "code_generated", "tests_passed")
        data: 이벤트 데이터 Dict
    
    예제:
        await client.broadcast(
            event_type="code_generated",
            data={
                "file": "auth.py",
                "lines": 127,
                "language": "python"
            }
        )
    """

async def subscribe(
    self,
    channel: str,
    handler: Callable[[Message], Awaitable[None]]
) -> None:
    """
    채널 구독 및 핸들러 등록
    
    매개변수:
        channel: 구독할 채널 이름
        handler: 메시지 처리 비동기 함수 (Message 입력)
    
    책임:
        - 채널 구독 (브로커)
        - 수신 메시지 핸들러로 전달
        - 오류 처리 및 재연결
    
    예제:
        async def handle_broadcast(message: Message):
            print(f"이벤트: {message.payload['event_type']}")
        
        await client.subscribe("broadcasts", handle_broadcast)
    """

async def send_heartbeat(self) -> None:
    """
    정기적 생존 신호 전송
    
    책임:
        - HEARTBEAT 메시지 발송
        - ConnectionManager 상태 갱신
        - 타임아웃 검사
    
    예제:
        # 30초마다 실행
        while True:
            await client.send_heartbeat()
            await asyncio.sleep(30)
    """

async def get_agents_by_capability(
    self,
    capability: str
) -> List[Dict[str, Any]]:
    """
    특정 능력을 가진 에이전트 목록 조회
    
    매개변수:
        capability: 찾을 능력 이름
    
    반환값: 에이전트 정보 Dict 리스트
    
    예제:
        agents = await client.get_agents_by_capability("code_review")
        for agent in agents:
            print(f"{agent['agent_name']} (ID: {agent['agent_id']})")
    """
```

---

## ConnectionManager 클래스

**역할**: 에이전트 연결 상태 및 메타데이터 관리

### 메서드

```python
class ConnectionManager:
    
    def register_agent(
        self,
        agent_id: str,
        agent_name: str,
        agent_type: str,
        capabilities: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> None:
        """
        에이전트 등록
        
        매개변수:
            agent_id: 고유 에이전트 ID
            agent_name: 에이전트 이름
            agent_type: 에이전트 타입
            capabilities: 능력 리스트
            metadata: 추가 메타데이터
        
        예외:
            ValueError: agent_id 중복
        
        예제:
            cm = ConnectionManager()
            cm.register_agent(
                agent_id="copilot-1",
                agent_name="Code Generator",
                agent_type="code_generator",
                capabilities=["python", "documentation"],
                metadata={"version": "1.0", "model": "gpt-4"}
            )
        """
    
    def unregister_agent(self, agent_id: str) -> None:
        """
        에이전트 등록 해제
        
        매개변수:
            agent_id: 제거할 에이전트 ID
        
        예외:
            ValueError: agent_id 미등록
        """
    
    def get_agent(self, agent_id: str) -> Dict[str, Any]:
        """
        에이전트 정보 조회
        
        반환값:
            {
                "agent_id": str,
                "agent_name": str,
                "agent_type": str,
                "capabilities": List[str],
                "status": AgentStatus,
                "metadata": Dict,
                "registered_at": str (ISO8601)
            }
        
        예외:
            ValueError: agent_id 미등록
        """
    
    def get_agents_by_capability(
        self,
        capability: str
    ) -> List[Dict[str, Any]]:
        """
        특정 능력을 가진 에이전트 조회
        
        매개변수:
            capability: 찾을 능력
        
        반환값: 에이전트 정보 Dict 리스트
        
        예제:
            agents = cm.get_agents_by_capability("code_review")
        """
    
    def get_available_agents(self) -> List[Dict[str, Any]]:
        """
        모든 활성(상태=IDLE) 에이전트 조회
        
        반환값: 에이전트 정보 Dict 리스트
        """
    
    def update_agent_status(
        self,
        agent_id: str,
        status: AgentStatus
    ) -> None:
        """
        에이전트 상태 업데이트
        
        매개변수:
            agent_id: 대상 에이전트 ID
            status: 새 상태 (AgentStatus enum)
        """
```

---

## 브로커 구현체

### MCPBroker

```python
class MCPBroker(MessageBroker):
    """TCP 기반 MCP 브로커 (기본값)"""
    
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 9999
    ):
        """
        매개변수:
            host: 바인드할 호스트
            port: 바인드할 포트
        """
    
    # 모든 MessageBroker 추상 메서드 구현
```

**특징**:
- TCP 소켓 기반
- 메시지 길이(4바이트) + JSON 패턷
- 클라이언트별 핸들러

### RedisBroker

```python
class RedisBroker(MessageBroker):
    """Redis Pub/Sub + Streams 브로커"""
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        db: int = 0
    ):
        """
        매개변수:
            redis_url: Redis 연결 URL
            db: 데이터베이스 번호
        """
    
    # 모든 MessageBroker 추상 메서드 구현

class RedisBrokerConfig:
    """Redis 브로커 설정"""
    host: str = "localhost"
    port: int = 6379
    password: Optional[str] = None
    db: int = 0
    decode_responses: bool = True
    
    def build_url(self) -> str:
        """Redis URL 생성"""
        # redis://password@host:port/db
```

**특징**:
- Pub/Sub: `mcp:{channel}`
- Streams: `mcp:stream:{type}`
- 메시지 히스토리 지원

### PulsarBroker

```python
class PulsarBroker(MessageBroker):
    """Apache Pulsar 브로커"""
    
    def __init__(
        self,
        service_url: str = "pulsar://localhost:6650",
        tenant: str = "ai-aarch",
        namespace: str = "default",
        auth_token: Optional[str] = None
    ):
        """
        매개변수:
            service_url: Pulsar 브로커 URL
            tenant: Pulsar 테넌트
            namespace: Pulsar 네임스페이스
            auth_token: 인증 토큰 (선택적)
        """
    
    # 모든 MessageBroker 추상 메서드 구현

class PulsarBrokerConfig:
    """Pulsar 브로커 설정"""
    service_url: str = "pulsar://localhost:6650"
    tenant: str = "ai-aarch"
    namespace: str = "default"
    auth_token: Optional[str] = None
    operation_timeout_seconds: int = 30
```

**특징**:
- 토픽: `persistent://{tenant}/{namespace}/{topic}`
- 자동 메시지 저장
- 수평적 확장

---

## BrokerFactory

**역할**: 브로커 생성 및 설정

```python
class BrokerFactory:
    """브로커 팩토리"""
    
    @staticmethod
    def create(
        broker_type: str,
        **config
    ) -> MessageBroker:
        """
        브로커 생성 (주요 팩토리 메서드)
        
        매개변수:
            broker_type: "mcp" | "redis" | "pulsar"
            **config: 브로커별 설정
        
        반환값: MessageBroker 인스턴스
        
        예외:
            ValueError: 지원하지 않는 브로커 타입
        
        예제:
            # MCP (기본)
            broker = BrokerFactory.create("mcp")
            
            # Redis
            broker = BrokerFactory.create(
                "redis",
                redis_url="redis://localhost:6379"
            )
            
            # Pulsar
            broker = BrokerFactory.create(
                "pulsar",
                service_url="pulsar://localhost:6650"
            )
        """
    
    @staticmethod
    def create_mcp(
        host: str = "127.0.0.1",
        port: int = 9999
    ) -> MCPBroker:
        """MCP 브로커 생성"""
    
    @staticmethod
    def create_redis(
        redis_url: str = "redis://localhost:6379",
        db: int = 0
    ) -> RedisBroker:
        """Redis 브로커 생성"""
    
    @staticmethod
    def create_pulsar(
        service_url: str = "pulsar://localhost:6650",
        tenant: str = "ai-aarch",
        namespace: str = "default"
    ) -> PulsarBroker:
        """Pulsar 브로커 생성"""
    
    @staticmethod
    def get_supported_brokers() -> List[str]:
        """
        지원하는 브로커 타입 리스트
        
        반환값: ["mcp", "redis", "pulsar"]
        """
```

---

## 에러 처리

### 공통 예외

```python
# 연결 오류
class ConnectionError(Exception):
    """브로커 연결 실패"""

# 타임아웃
class asyncio.TimeoutError:
    """응답 대기 중 시간 초과"""

# 런타임 오류
class RuntimeError(Exception):
    """브로커 미연결 또는 대상 미응답"""

# 값 오류
class ValueError(Exception):
    """잘못된 입력 (ID 중복, 잘못된 타입 등)"""
```

### 예외 처리 패턴

```python
import asyncio

try:
    await client.send_request(
        target_agent="agent-2",
        request_type="analyze",
        parameters={"file": "test.py"},
        timeout=30.0
    )
except asyncio.TimeoutError:
    logger.warning("Agent 미응답 (30초 초과)")
except RuntimeError as e:
    logger.error(f"에이전트 오류: {e}")
except Exception as e:
    logger.exception(f"예상치 못한 오류: {e}")
```

---

## 사용 패턴

### 패턴 1: 기본 요청-응답

```python
async def main():
    # 브로커 생성
    broker = BrokerFactory.create("mcp")
    await broker.connect()
    
    # 클라이언트 생성
    client = MCPClient(
        broker=broker,
        agent_id="requester",
        agent_name="Request Handler",
        capabilities=["request_handling"]
    )
    
    await client.connect()
    await client.register()
    
    # 요청 전송
    response = await client.send_request(
        target_agent="worker",
        request_type="process",
        parameters={"data": "input"},
        timeout=30.0
    )
    
    print(response)
    await client.disconnect()
```

### 패턴 2: 브로드캐스트 및 구독

```python
async def main():
    broker = BrokerFactory.create("redis")
    await broker.connect()
    
    # 발신자
    sender = MCPClient(broker=broker, agent_id="sender", ...)
    
    # 수신자
    receiver = MCPClient(broker=broker, agent_id="receiver", ...)
    
    async def handle_event(message: Message):
        print(f"이벤트 수신: {message.payload}")
    
    # 구독
    await receiver.subscribe("broadcasts", handle_event)
    
    # 발신
    await sender.broadcast(
        event_type="task_completed",
        data={"task_id": "123"}
    )
```

### 패턴 3: 정기적 헬스 체크

```python
async def heartbeat_loop(client: MCPClient):
    """30초마다 헬스 체크"""
    while True:
        try:
            await client.send_heartbeat()
            await asyncio.sleep(30)
        except Exception as e:
            logger.error(f"헬스 체크 실패: {e}")
            await asyncio.sleep(5)
```

---

**작성자**: GitHub Copilot  
**상태**: ✅ 완료  
**버전**: 1.0.0
