"""
Pulsar 브로커 사용 예제
"""

import asyncio
import logging
from mcp_core import (
    BrokerFactory,
    MCPClient,
    PulsarBrokerConfig
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def publisher():
    """메시지 발행자"""
    
    # Pulsar 브로커 생성
    broker = BrokerFactory.create_pulsar(
        service_url="pulsar://localhost:6650",
        tenant="ai-aarch",
        namespace="default"
    )
    await broker.connect()
    
    client = MCPClient(
        broker=broker,
        agent_id="publisher",
        agent_name="Pulsar Publisher",
        capabilities=["publish"]
    )
    
    await client.connect()
    
    # 메시지 발행
    for i in range(5):
        await client.broadcast(
            event_type="topic_message",
            data={"index": i, "content": f"Pulsar Message {i}"}
        )
        logger.info(f"Published message {i}")
        await asyncio.sleep(1)
    
    await client.disconnect()


async def subscriber():
    """메시지 구독자"""
    
    await asyncio.sleep(0.5)  # 발행자가 먼저 시작하도록
    
    # Pulsar 브로커 생성
    broker = BrokerFactory.create_pulsar(
        service_url="pulsar://localhost:6650",
        tenant="ai-aarch",
        namespace="default"
    )
    await broker.connect()
    
    client = MCPClient(
        broker=broker,
        agent_id="subscriber",
        agent_name="Pulsar Subscriber",
        capabilities=["subscribe"]
    )
    
    await client.connect()
    
    # 토픽 구독
    message_count = 0
    
    async def handle_message(message):
        nonlocal message_count
        message_count += 1
        logger.info(f"Received: {message.payload}")
        
        if message_count >= 5:
            asyncio.current_task().cancel()
    
    try:
        await client.subscribe("broadcast", handle_message)
    except asyncio.CancelledError:
        logger.info("Subscriber finished")
    
    await client.disconnect()


async def main():
    """메인 실행"""
    logger.info("Pulsar Broker 예제 시작")
    logger.info("사전 요구사항: Pulsar 서버 실행 중")
    
    await asyncio.gather(
        publisher(),
        subscriber()
    )


if __name__ == "__main__":
    asyncio.run(main())
