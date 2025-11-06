"""
Broker Factory
브로커 선택 및 생성
"""

import logging
from enum import Enum
from typing import Optional, Dict, Any

from .core import MessageBroker
from .mcp_broker import MCPBroker
from .redis_broker import RedisBroker, RedisBrokerConfig
from .pulsar_broker import PulsarBroker, PulsarBrokerConfig

logger = logging.getLogger(__name__)


class BrokerType(Enum):
    """지원하는 브로커 타입"""
    MCP = "mcp"           # TCP 기반 (기본)
    REDIS = "redis"       # Redis Pub/Sub + Streams
    PULSAR = "pulsar"     # Apache Pulsar


class BrokerFactory:
    """메시지 브로커 팩토리"""
    
    _brokers = {
        BrokerType.MCP: MCPBroker,
        BrokerType.REDIS: RedisBroker,
        BrokerType.PULSAR: PulsarBroker
    }
    
    @staticmethod
    def create(
        broker_type: str = "mcp",
        **config: Any
    ) -> MessageBroker:
        """브로커 생성
        
        Args:
            broker_type: 브로커 타입 (mcp, redis, pulsar)
            **config: 브로커별 설정
        
        Returns:
            MessageBroker 인스턴스
        """
        
        try:
            # 브로커 타입 변환
            if isinstance(broker_type, str):
                broker_type = BrokerType(broker_type.lower())
            
            if broker_type not in BrokerFactory._brokers:
                raise ValueError(f"Unsupported broker type: {broker_type}")
            
            broker_class = BrokerFactory._brokers[broker_type]
            logger.info(f"Creating {broker_type.value} broker with config: {config}")
            
            return broker_class(**config)
        
        except Exception as e:
            logger.error(f"Failed to create broker: {e}")
            raise
    
    @staticmethod
    def create_mcp(
        host: str = "127.0.0.1",
        port: int = 9999
    ) -> MCPBroker:
        """MCP 브로커 생성"""
        logger.info(f"Creating MCP broker on {host}:{port}")
        return MCPBroker(host=host, port=port)
    
    @staticmethod
    def create_redis(
        redis_url: str = "redis://localhost:6379"
    ) -> RedisBroker:
        """Redis 브로커 생성"""
        logger.info(f"Creating Redis broker: {redis_url}")
        return RedisBroker(redis_url=redis_url)
    
    @staticmethod
    def create_redis_with_config(config: RedisBrokerConfig) -> RedisBroker:
        """Redis 브로커 생성 (설정 객체)"""
        logger.info(f"Creating Redis broker with config")
        return RedisBroker(redis_url=config.to_url())
    
    @staticmethod
    def create_pulsar(
        service_url: str = "pulsar://localhost:6650",
        tenant: str = "ai-aarch",
        namespace: str = "default"
    ) -> PulsarBroker:
        """Pulsar 브로커 생성"""
        logger.info(f"Creating Pulsar broker: {service_url}")
        return PulsarBroker(
            service_url=service_url,
            tenant=tenant,
            namespace=namespace
        )
    
    @staticmethod
    def create_pulsar_with_config(config: PulsarBrokerConfig) -> PulsarBroker:
        """Pulsar 브로커 생성 (설정 객체)"""
        logger.info(f"Creating Pulsar broker with config")
        return PulsarBroker(
            service_url=config.service_url,
            tenant=config.tenant,
            namespace=config.namespace
        )
    
    @staticmethod
    def get_supported_brokers() -> list[str]:
        """지원하는 브로커 목록"""
        return [broker_type.value for broker_type in BrokerType]


# 기본 브로커 설정 (환경 변수 또는 설정 파일에서 로드 가능)
DEFAULT_BROKER_TYPE = "mcp"
DEFAULT_BROKER_CONFIG = {}


def get_default_broker() -> MessageBroker:
    """기본 브로커 반환"""
    return BrokerFactory.create(DEFAULT_BROKER_TYPE, **DEFAULT_BROKER_CONFIG)
