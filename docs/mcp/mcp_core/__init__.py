"""
MCP Core Package
통신 계층 추상화 - MCP, Redis, Pulsar 지원
"""

from .core import (
    Message,
    MessageType,
    MessageBroker,
    ConnectionManager,
    MCPClient
)

from .mcp_broker import MCPBroker
from .redis_broker import RedisBroker, RedisBrokerConfig
from .pulsar_broker import PulsarBroker, PulsarBrokerConfig
from .factory import (
    BrokerFactory,
    BrokerType,
    get_default_broker,
    DEFAULT_BROKER_TYPE
)

__version__ = "1.0.0"
__all__ = [
    # Core classes
    "Message",
    "MessageType",
    "MessageBroker",
    "ConnectionManager",
    "MCPClient",
    
    # Broker implementations
    "MCPBroker",
    "RedisBroker",
    "RedisBrokerConfig",
    "PulsarBroker",
    "PulsarBrokerConfig",
    
    # Factory
    "BrokerFactory",
    "BrokerType",
    "get_default_broker",
    "DEFAULT_BROKER_TYPE"
]
