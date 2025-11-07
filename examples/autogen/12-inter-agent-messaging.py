"""
AutoGen - 에이전트 간 통신 예제 (2025년 11월 기준)

에이전트들이 비동기로 메시지를 주고받는 패턴
- 직접 메시징
- 메시지 큐
- 발행-구독 (Pub/Sub)
- 서비스 발견

실행: python examples/autogen/12-inter-agent-messaging.py
"""

import asyncio
import uuid
import json
from datetime import datetime
from typing import Dict, List, Callable, Any
from enum import Enum
from dataclasses import dataclass, asdict


# =====================================================
# 1️⃣ 메시지 정의
# =====================================================

class MessageType(Enum):
    """메시지 타입"""
    TASK = "task"
    RESULT = "result"
    ERROR = "error"
    PING = "ping"
    PONG = "pong"
    SUBSCRIBE = "subscribe"
    BROADCAST = "broadcast"


@dataclass
class Message:
    """에이전트 간 메시지"""
    message_id: str
    message_type: MessageType
    sender: str
    receiver: str  # "*" 이면 브로드캐스트
    payload: Dict[str, Any]
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        data = asdict(self)
        data['message_type'] = self.message_type.value
        return data
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


# =====================================================
# 2️⃣ 메시지 브로커 (중앙 통신 시스템)
# =====================================================

class MessageBroker:
    """
    모든 에이전트 간의 메시지를 관리하는 중앙 브로커
    - 메시지 라우팅
    - 발행-구독 관리
    - 서비스 레지스트리
    """
    
    def __init__(self):
        # 메시지 큐: {agent_id: [messages]}
        self._message_queues: Dict[str, asyncio.Queue] = {}
        
        # 구독: {topic: [agent_ids]}
        self._subscriptions: Dict[str, List[str]] = {}
        
        # 에이전트 정보: {agent_id: info}
        self._agents: Dict[str, Dict] = {}
        
        # 메시지 히스토리
        self._history: List[Message] = []
    
    async def register_agent(self, agent_id: str, capabilities: List[str] = None):
        """에이전트 등록"""
        if agent_id not in self._message_queues:
            self._message_queues[agent_id] = asyncio.Queue()
            self._agents[agent_id] = {
                "agent_id": agent_id,
                "capabilities": capabilities or [],
                "registered_at": datetime.now().isoformat()
            }
            print(f"📍 브로커: 에이전트 '{agent_id}' 등록됨")
    
    async def unregister_agent(self, agent_id: str):
        """에이전트 등록 해제"""
        if agent_id in self._message_queues:
            del self._message_queues[agent_id]
            del self._agents[agent_id]
            print(f"📍 브로커: 에이전트 '{agent_id}' 제거됨")
    
    async def send_message(self, message: Message):
        """
        메시지 전송
        - receiver가 "*"이면 모든 구독자에게 브로드캐스트
        - 아니면 특정 에이전트에게 직접 전송
        """
        self._history.append(message)
        
        if message.receiver == "*":
            # 브로드캐스트: 모든 에이전트에게
            print(f"\n📢 브로드캐스트: {message.sender} → 모두")
            print(f"   메시지: {message.payload}")
            
            for agent_id in self._message_queues:
                if agent_id != message.sender:
                    await self._message_queues[agent_id].put(message)
        else:
            # 직접 전송: 특정 에이전트에게
            if message.receiver in self._message_queues:
                print(f"\n💬 메시지: {message.sender} → {message.receiver}")
                print(f"   내용: {message.payload}")
                await self._message_queues[message.receiver].put(message)
            else:
                print(f"\n❌ 브로커: 에이전트 '{message.receiver}' 없음")
    
    async def receive_message(self, agent_id: str, timeout: float = 5.0) -> Message:
        """메시지 수신 (비동기 대기)"""
        try:
            message = await asyncio.wait_for(
                self._message_queues[agent_id].get(),
                timeout=timeout
            )
            print(f"📥 {agent_id}: 메시지 수신")
            return message
        except asyncio.TimeoutError:
            return None
    
    async def subscribe(self, agent_id: str, topic: str):
        """주제 구독"""
        if topic not in self._subscriptions:
            self._subscriptions[topic] = []
        if agent_id not in self._subscriptions[topic]:
            self._subscriptions[topic].append(agent_id)
            print(f"📌 {agent_id}: '{topic}' 구독")
    
    async def publish(self, topic: str, message: Message):
        """주제에 메시지 발행"""
        if topic in self._subscriptions:
            print(f"\n📰 발행: 주제 '{topic}'")
            for agent_id in self._subscriptions[topic]:
                await self._message_queues[agent_id].put(message)
    
    def get_agents_by_capability(self, capability: str) -> List[str]:
        """특정 능력을 가진 에이전트 조회"""
        return [
            agent_id for agent_id, info in self._agents.items()
            if capability in info.get("capabilities", [])
        ]
    
    def get_message_history(self, limit: int = 10) -> List[Message]:
        """최근 메시지 히스토리"""
        return self._history[-limit:]


# =====================================================
# 3️⃣ 에이전트 클래스
# =====================================================

class Agent:
    """통신 가능한 에이전트"""
    
    def __init__(self, agent_id: str, broker: MessageBroker):
        self.agent_id = agent_id
        self.broker = broker
        self.inbox: Dict[str, Message] = {}
        self.response_callbacks: Dict[str, Callable] = {}
    
    async def initialize(self, capabilities: List[str] = None):
        """에이전트 초기화"""
        await self.broker.register_agent(self.agent_id, capabilities)
    
    async def send(self, receiver: str, message_type: MessageType, 
                   payload: Dict[str, Any]):
        """
        메시지 전송
        
        Args:
            receiver: 수신자 ID ("*" 이면 브로드캐스트)
            message_type: 메시지 타입
            payload: 메시지 내용
        """
        message = Message(
            message_id=str(uuid.uuid4()),
            message_type=message_type,
            sender=self.agent_id,
            receiver=receiver,
            payload=payload
        )
        await self.broker.send_message(message)
        return message.message_id
    
    async def receive(self, timeout: float = 5.0) -> Message:
        """메시지 수신"""
        return await self.broker.receive_message(self.agent_id, timeout)
    
    async def request_response(self, receiver: str, request: Dict, 
                               timeout: float = 10.0) -> Dict:
        """
        요청-응답 패턴
        1. 요청 전송
        2. 응답 대기
        """
        request_id = await self.send(
            receiver,
            MessageType.TASK,
            {**request, "request_id": str(uuid.uuid4())}
        )
        
        print(f"\n⏳ {self.agent_id}: 응답 대기 중...")
        
        response = await asyncio.wait_for(
            self.receive(timeout=timeout),
            timeout=timeout
        )
        
        if response:
            print(f"✅ {self.agent_id}: 응답 수신")
            return response.payload
        else:
            print(f"❌ {self.agent_id}: 응답 타임아웃")
            return None


# =====================================================
# 4️⃣ 예제
# =====================================================

async def example_1_direct_messaging():
    """
    예제 1: 직접 메시징
    - 에이전트 A → 에이전트 B
    - 일대일 통신
    """
    print("\n" + "="*70)
    print("예제 1️⃣ : 직접 메시징 (Direct Messaging)")
    print("="*70)
    
    broker = MessageBroker()
    
    # 1. 에이전트 생성
    agent_a = Agent("에이전트_A", broker)
    agent_b = Agent("에이전트_B", broker)
    
    await agent_a.initialize(["분석"])
    await agent_b.initialize(["리뷰"])
    
    # 2. 비동기 작업
    async def sender():
        """메시지 발신"""
        await asyncio.sleep(0.5)
        await agent_a.send(
            "에이전트_B",
            MessageType.TASK,
            {"task": "코드 리뷰 부탁"}
        )
    
    async def receiver():
        """메시지 수신"""
        message = await agent_b.receive()
        if message:
            print(f"\n🎯 {message.receiver} 받음: {message.payload['task']}")
    
    # 3. 동시 실행
    await asyncio.gather(sender(), receiver())
    
    print("\n✅ 직접 메시징 완료")


async def example_2_request_response():
    """
    예제 2: 요청-응답 패턴
    - 에이전트 A: 요청 전송 + 응답 대기
    - 에이전트 B: 요청 수신 + 응답 전송
    """
    print("\n" + "="*70)
    print("예제 2️⃣ : 요청-응답 패턴 (Request-Response)")
    print("="*70)
    
    broker = MessageBroker()
    
    # 1. 에이전트 생성
    requester = Agent("요청자", broker)
    responder = Agent("응답자", broker)
    
    await requester.initialize(["질의"])
    await responder.initialize(["답변"])
    
    # 2. 응답 처리 루프
    async def responder_loop():
        """응답자: 요청 받고 응답 전송"""
        message = await responder.receive()
        if message:
            print(f"\n🔍 {responder.agent_id}: 요청 분석 중...")
            await asyncio.sleep(1)  # 처리 시뮬레이션
            
            # 응답 전송
            await responder.send(
                message.sender,
                MessageType.RESULT,
                {"result": f"답변: {message.payload.get('question', '?')}에 대한 답변입니다"}
            )
    
    # 3. 요청 전송
    async def requester_action():
        """요청자: 질문 전송 및 응답 대기"""
        await asyncio.sleep(0.5)
        
        response = await requester.request_response(
            "응답자",
            {"question": "2+2는?"}
        )
        
        if response:
            print(f"\n💡 {requester.agent_id}: {response['result']}")
    
    # 4. 동시 실행
    await asyncio.gather(
        responder_loop(),
        requester_action()
    )
    
    print("\n✅ 요청-응답 패턴 완료")


async def example_3_broadcast():
    """
    예제 3: 브로드캐스트
    - 한 에이전트에서 모든 다른 에이전트에게 메시지 발송
    - 일대다 통신
    """
    print("\n" + "="*70)
    print("예제 3️⃣ : 브로드캐스트 (Broadcast)")
    print("="*70)
    
    broker = MessageBroker()
    
    # 1. 에이전트 생성 (공지자 + 수신자들)
    publisher = Agent("공지자", broker)
    subscribers = [
        Agent(f"구독자_{i}", broker)
        for i in range(3)
    ]
    
    await publisher.initialize(["공지"])
    for sub in subscribers:
        await sub.initialize(["수신"])
    
    # 2. 수신자 루프
    async def subscriber_loop(agent: Agent):
        """구독자: 메시지 수신 대기"""
        message = await agent.receive()
        if message:
            print(f"📬 {agent.agent_id}: '{message.payload['content']}' 수신")
    
    # 3. 브로드캐스트 발송
    async def broadcast_action():
        """공지자: 모두에게 메시지 발송"""
        await asyncio.sleep(0.5)
        await publisher.send(
            "*",  # 모두에게
            MessageType.BROADCAST,
            {"content": "🔴 긴급 공지: 시스템 점검 예정"}
        )
    
    # 4. 모든 구독자가 수신하도록 동시 실행
    tasks = [subscriber_loop(sub) for sub in subscribers]
    tasks.append(broadcast_action())
    
    await asyncio.gather(*tasks)
    
    print("\n✅ 브로드캐스트 완료")


async def example_4_service_discovery():
    """
    예제 4: 서비스 발견
    - 능력(capability)으로 에이전트 검색
    - 자동 라우팅
    """
    print("\n" + "="*70)
    print("예제 4️⃣ : 서비스 발견 (Service Discovery)")
    print("="*70)
    
    broker = MessageBroker()
    
    # 1. 다양한 능력의 에이전트 생성
    agents = [
        ("분석기", ["분석", "통계"]),
        ("코더", ["코딩", "디버그"]),
        ("리뷰어", ["리뷰", "QA"]),
        ("문서작성", ["문서", "영어"]),
    ]
    
    agent_objs = {}
    for agent_id, capabilities in agents:
        agent = Agent(agent_id, broker)
        await agent.initialize(capabilities)
        agent_objs[agent_id] = agent
    
    # 2. 능력 검색
    print("\n🔍 서비스 발견:")
    
    finding_capability = "코딩"
    coding_agents = broker.get_agents_by_capability(finding_capability)
    print(f"  '{finding_capability}' 가능한 에이전트: {coding_agents}")
    
    finding_capability = "리뷰"
    review_agents = broker.get_agents_by_capability(finding_capability)
    print(f"  '{finding_capability}' 가능한 에이전트: {review_agents}")
    
    # 3. 자동 라우팅 (예: 코딩 작업 필요 → 코더에게 할당)
    if coding_agents:
        target = coding_agents[0]
        print(f"\n🎯 라우팅: 코딩 작업 → {target}")
        
        # 메시지 전송
        await agent_objs["분석기"].send(
            target,
            MessageType.TASK,
            {"task": "Python 함수 작성"}
        )
        
        # 대기
        await asyncio.sleep(1)
    
    print("\n✅ 서비스 발견 완료")


async def example_5_message_history():
    """
    예제 5: 메시지 히스토리
    - 모든 메시지 기록
    - 감사 추적(audit trail)
    - 재생(replay) 가능
    """
    print("\n" + "="*70)
    print("예제 5️⃣ : 메시지 히스토리 (Message History)")
    print("="*70)
    
    broker = MessageBroker()
    
    # 1. 에이전트 생성 및 메시지 전송
    agents = [Agent(f"agent_{i}", broker) for i in range(3)]
    for agent in agents:
        await agent.initialize()
    
    # 2. 여러 메시지 전송
    print("📨 메시지 전송:")
    for i in range(5):
        await agents[0].send(
            agents[1].agent_id,
            MessageType.TASK,
            {"data": f"데이터_{i}", "sequence": i}
        )
        await asyncio.sleep(0.1)
    
    # 3. 히스토리 조회
    print("\n📊 메시지 히스토리:")
    history = broker.get_message_history(limit=5)
    
    for msg in history:
        print(f"  [{msg.sender}] → [{msg.receiver}]")
        print(f"    타입: {msg.message_type.value}")
        print(f"    내용: {msg.payload}")
        print()
    
    print("✅ 메시지 히스토리 완료")


# =====================================================
# 5️⃣ 메인
# =====================================================

async def main():
    """모든 예제 실행"""
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║            AutoGen 에이전트 간 통신 예제                    ║
║      Inter-Agent Messaging Patterns in 2025                ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    try:
        await example_1_direct_messaging()
        await example_2_request_response()
        await example_3_broadcast()
        await example_4_service_discovery()
        await example_5_message_history()
        
        print("\n" + "="*70)
        print("✅ 모든 예제 완료!")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ 오류: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
