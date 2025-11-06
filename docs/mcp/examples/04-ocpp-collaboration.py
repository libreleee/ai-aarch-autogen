"""
OCPP 서버/클라이언트 협업 예제
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


async def ocpp_server_agent():
    """OCPP Server Agent (Copilot)"""
    
    broker = BrokerFactory.create("mcp", host="127.0.0.1", port=9999)
    await broker.connect()
    
    client = MCPClient(
        broker=broker,
        agent_id="ocpp-server",
        agent_name="OCPP Server (Copilot)",
        agent_type="code_generator",
        capabilities=["code_generation", "server_management", "testing"]
    )
    
    await client.connect()
    await client.register()
    
    logger.info("=== OCPP Server Agent 시작 ===")
    
    # 1단계: 코드 생성 시작 알림
    await client.broadcast(
        event_type="code_generation_started",
        data={
            "task_id": "task-auth-handler",
            "description": "OCPP 1.6 Authentication Handler",
            "target_file": "src/handlers/auth.py"
        }
    )
    
    logger.info("1️⃣  코드 생성 시작 브로드캐스트 전송")
    await asyncio.sleep(1)
    
    # 2단계: 코드 생성 완료 알림
    await client.broadcast(
        event_type="code_generated",
        data={
            "task_id": "task-auth-handler",
            "file_path": "src/handlers/auth.py",
            "lines_of_code": 127,
            "coverage": 0.85
        }
    )
    
    logger.info("2️⃣  코드 생성 완료 브로드캐스트 전송")
    
    # 3단계: 클라이언트의 분석 결과 대기
    logger.info("3️⃣  클라이언트의 분석 결과 대기 중...")
    
    # 5단계: 서버 시작 알림
    await asyncio.sleep(2)
    await client.broadcast(
        event_type="server_started",
        data={
            "host": "127.0.0.1",
            "port": 9000,
            "protocol_version": "1.6",
            "status": "ready"
        }
    )
    
    logger.info("5️⃣  OCPP Server 시작 알림 전송")
    
    # 7단계: 테스트 결과 수신 대기
    logger.info("7️⃣  클라이언트의 테스트 결과 대기 중...")
    
    await asyncio.sleep(5)
    
    logger.info("=== OCPP Server Agent 종료 ===")
    await client.disconnect()


async def ocpp_client_agent():
    """OCPP Client Agent (Codex/Agno)"""
    
    await asyncio.sleep(0.5)  # Server가 먼저 시작
    
    broker = BrokerFactory.create("mcp", host="127.0.0.1", port=9999)
    await broker.connect()
    
    client = MCPClient(
        broker=broker,
        agent_id="ocpp-client",
        agent_name="OCPP Client (Codex)",
        agent_type="analyzer",
        capabilities=["code_analysis", "testing", "client_management"]
    )
    
    await client.connect()
    await client.register()
    
    logger.info("\n=== OCPP Client Agent 시작 ===")
    
    # 2단계: 코드 생성 완료 감지 및 분석 시작
    logger.info("2️⃣  서버의 코드 생성 완료 감지")
    await asyncio.sleep(0.5)
    
    logger.info("3️⃣  코드 분석 시작...")
    
    # 4단계: 분석 결과 전송
    await client.broadcast(
        event_type="code_analyzed",
        data={
            "task_id": "task-auth-handler",
            "analysis_results": {
                "performance": {"score": 8.5},
                "security": {"score": 9.0},
                "protocol_compliance": {"score": 10.0}
            }
        }
    )
    
    logger.info("4️⃣  코드 분석 완료 브로드캐스트 전송")
    
    # 6단계: 서버 시작 감지 및 테스트 시작
    logger.info("6️⃣  서버 시작 감지, 테스트 시작...")
    await asyncio.sleep(1)
    
    # 8단계: 테스트 결과 전송
    await client.broadcast(
        event_type="tests_completed",
        data={
            "passed": 6,
            "failed": 0,
            "duration_ms": 2341,
            "coverage": 0.92
        }
    )
    
    logger.info("8️⃣  테스트 결과 브로드캐스트 전송")
    
    await asyncio.sleep(2)
    
    logger.info("=== OCPP Client Agent 종료 ===")
    await client.disconnect()


async def monitor():
    """모니터: 모든 메시지 추적"""
    
    await asyncio.sleep(0.2)
    
    broker = BrokerFactory.create("mcp", host="127.0.0.1", port=9999)
    await broker.connect()
    
    client = MCPClient(
        broker=broker,
        agent_id="monitor",
        agent_name="Monitor",
        agent_type="monitor",
        capabilities=["monitoring"]
    )
    
    await client.connect()
    
    logger.info("\n📊 === 모니터 시작 ===\n")
    
    event_count = 0
    
    async def handle_event(message: Message):
        nonlocal event_count
        event_count += 1
        
        if message.message_type == MessageType.BROADCAST:
            event = message.payload.get("event_type", "unknown")
            logger.info(f"📢 Event #{event_count}: {event} from {message.sender_id}")
    
    try:
        await client.subscribe("broadcast", handle_event)
    except asyncio.CancelledError:
        pass
    
    await client.disconnect()


async def main():
    """메인 실행"""
    
    logger.info("\n" + "="*60)
    logger.info("MCP OCPP 협업 시스템 시뮬레이션")
    logger.info("="*60 + "\n")
    
    # 세 개의 에이전트 동시 실행
    # 모니터는 백그라운드에서 실행
    monitor_task = asyncio.create_task(monitor())
    
    await asyncio.gather(
        ocpp_server_agent(),
        ocpp_client_agent(),
        return_exceptions=True
    )
    
    monitor_task.cancel()
    try:
        await monitor_task
    except asyncio.CancelledError:
        pass
    
    logger.info("\n" + "="*60)
    logger.info("시뮬레이션 완료")
    logger.info("="*60)


if __name__ == "__main__":
    asyncio.run(main())
