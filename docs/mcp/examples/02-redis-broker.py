"""
Redis 브로커 사용 예제
"""

import asyncio
import logging
from mcp_core import (
    BrokerFactory,
    MCPClient,
    RedisBrokerConfig
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def producer():
    """메시지 생산자"""
    
    # Redis 브로커 생성
    broker = BrokerFactory.create_redis(
        redis_url="redis://localhost:6379"
    )
    await broker.connect()
    
    client = MCPClient(
        broker=broker,
        agent_id="producer",
        agent_name="Message Producer",
        capabilities=["publish"]
    )
    
    await client.connect()
    
    # 메시지 발행
    for i in range(5):
        await client.broadcast(
            event_type="message",
            data={"index": i, "content": f"Message {i}"}
        )
        logger.info(f"Published message {i}")
        await asyncio.sleep(1)
    
    await client.disconnect()


async def consumer():
    """메시지 소비자"""
    
    await asyncio.sleep(0.5)  # 생산자가 먼저 시작하도록
    
    # Redis 브로커 생성
    broker = BrokerFactory.create_redis(
        redis_url="redis://localhost:6379"
    )
    await broker.connect()
    
    client = MCPClient(
        broker=broker,
        agent_id="consumer",
        agent_name="Message Consumer",
        capabilities=["subscribe"]
    )
    
    await client.connect()
    
    # 채널 구독
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
        logger.info("Consumer finished")
    
    await client.disconnect()


async def main():
    """메인 실행"""
    logger.info("Redis Broker 예제 시작")
    logger.info("사전 요구사항: redis-server 실행 중")
    
    await asyncio.gather(
        producer(),
        consumer()
    )


if __name__ == "__main__":
    asyncio.run(main())
