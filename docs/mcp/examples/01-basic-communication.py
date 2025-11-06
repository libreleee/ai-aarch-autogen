"""
MCP 기본 사용 예제 - 클라이언트 2개가 메시지 교환
"""

import asyncio
import logging
from mcp_core import (
    BrokerFactory,
    MCPClient,
    MessageType,
    Message
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def agent1():
    """Agent 1: 코드 생성기"""
    
    # MCP 브로커 선택 (기본: MCP TCP)
    broker = BrokerFactory.create("mcp", host="127.0.0.1", port=9999)
    await broker.connect()
    
    # 클라이언트 생성
    client = MCPClient(
        broker=broker,
        agent_id="agent-1",
        agent_name="Copilot Generator",
        agent_type="code_generator",
        capabilities=["code_generation", "testing"]
    )
    
    await client.connect()
    
    # 에이전트 등록
    await client.register()
    
    # 코드 생성 브로드캐스트
    await client.broadcast(
        event_type="code_generated",
        data={
            "file": "auth.py",
            "lines": 127,
            "language": "python"
        }
    )
    
    # Agent 2에 요청
    logger.info("Agent 1: 코드 분석 요청 전송...")
    response = await client.send_request(
        target_agent="agent-2",
        request_type="analyze_code",
        parameters={"file": "auth.py"}
    )
    
    if response:
        logger.info(f"Agent 1: 응답 수신 - {response.payload}")
    else:
        logger.warning("Agent 1: 응답 타임아웃")
    
    # 구독
    async def handle_broadcast(message: Message):
        if message.message_type == MessageType.BROADCAST:
            logger.info(f"Agent 1: 브로드캐스트 수신 - {message.payload}")
    
    # 백그라운드 구독
    asyncio.create_task(client.subscribe("broadcast", handle_broadcast))
    
    await asyncio.sleep(5)
    await client.disconnect()


async def agent2():
    """Agent 2: 코드 분석기"""
    
    await asyncio.sleep(1)  # Agent 1이 먼저 시작하도록
    
    # Redis 브로커 (선택)
    # broker = BrokerFactory.create("redis", redis_url="redis://localhost:6379")
    
    # MCP 브로커
    broker = BrokerFactory.create("mcp", host="127.0.0.1", port=9999)
    await broker.connect()
    
    # 클라이언트 생성
    client = MCPClient(
        broker=broker,
        agent_id="agent-2",
        agent_name="Codex Analyzer",
        agent_type="analyzer",
        capabilities=["code_analysis", "testing"]
    )
    
    await client.connect()
    
    # 에이전트 등록
    await client.register()
    
    # 브로드캐스트 구독
    async def handle_broadcast(message: Message):
        if message.message_type == MessageType.BROADCAST:
            logger.info(f"Agent 2: 브로드캐스트 수신 - {message.payload}")
    
    asyncio.create_task(client.subscribe("broadcast", handle_broadcast))
    
    # 요청 대기 및 응답
    logger.info("Agent 2: 요청 대기 중...")
    
    await asyncio.sleep(10)
    await client.disconnect()


async def main():
    """메인 실행"""
    
    # 두 에이전트 동시 실행
    await asyncio.gather(
        agent1(),
        agent2()
    )


if __name__ == "__main__":
    asyncio.run(main())
