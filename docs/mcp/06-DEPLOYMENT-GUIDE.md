# MCP 설정 및 배포 가이드

**작성일**: 2025년 11월 7일  
**상태**: ✅ 완료  
**버전**: 1.0.0

---

## 목차

1. [개요](#개요)
2. [환경 준비](#환경-준비)
3. [MCP TCP 배포](#mcp-tcp-배포-기본)
4. [Redis 배포](#redis-배포)
5. [Pulsar 배포](#pulsar-배포)
6. [설정 관리](#설정-관리)
7. [모니터링 및 로깅](#모니터링-및-로깅)
8. [문제 해결](#문제-해결)
9. [성능 튜닝](#성능-튜닝)
10. [마이그레이션 가이드](#마이그레이션-가이드)

---

## 개요

MCP 시스템을 로컬, 개발, 프로덕션 환경에 배포하는 방법을 설명합니다.

### 환경별 추천 설정

| 환경 | 브로커 | 이유 |
|------|-------|------|
| **로컬 개발** | MCP | 의존성 없음, 빠른 시작 |
| **팀 개발** | Redis | 여러 개발자 간 메시지 공유 |
| **스테이징** | Redis | 프로덕션과 유사하지만 단순함 |
| **프로덕션** | Pulsar | 고가용성, 확장성, 메시지 보존 |

---

## 환경 준비

### 1. Python 환경

```bash
# Python 3.8 이상 필요
python --version

# 가상환경 생성
python -m venv venv

# 활성화 (Windows)
venv\Scripts\activate

# 활성화 (macOS/Linux)
source venv/bin/activate
```

### 2. 의존성 설치

```bash
# 기본 (MCP TCP만 사용)
pip install asyncio

# Redis 사용시 추가
pip install redis

# Pulsar 사용시 추가
pip install pulsar-client

# 모두 설치
pip install redis pulsar-client

# 개발 용도
pip install pytest pytest-asyncio black isort mypy
```

### 3. 코드 준비

```bash
# 작업 디렉토리
mkdir -p projects/mcp-system
cd projects/mcp-system

# MCP 코어 복사
cp -r /path/to/docs/mcp/mcp_core ./

# 예제 복사
cp -r /path/to/docs/mcp/examples ./
```

---

## MCP TCP 배포 (기본)

### 1. 로컬 개발

**설정 파일**: `config.py`

```python
# config.py
import os

# MCP TCP 설정
BROKER_TYPE = "mcp"
MCP_HOST = os.getenv("MCP_HOST", "127.0.0.1")
MCP_PORT = int(os.getenv("MCP_PORT", 9999))

# 로깅
LOG_LEVEL = "INFO"
LOG_FILE = "mcp.log"

# 에이전트
AGENT_ID = os.getenv("AGENT_ID", "agent-1")
AGENT_NAME = os.getenv("AGENT_NAME", "Default Agent")
HEARTBEAT_INTERVAL = 30  # 초
```

**시작 스크립트**: `start_mcp.py`

```python
# start_mcp.py
import asyncio
import logging
from docs.mcp.mcp_core import BrokerFactory, MCPClient
from config import (
    BROKER_TYPE, MCP_HOST, MCP_PORT,
    AGENT_ID, AGENT_NAME, LOG_LEVEL
)

# 로깅 설정
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    # 1. 브로커 생성
    logger.info(f"브로커 생성: {BROKER_TYPE}")
    broker = BrokerFactory.create(
        BROKER_TYPE,
        host=MCP_HOST,
        port=MCP_PORT
    )
    
    # 2. 브로커 연결
    await broker.connect()
    logger.info(f"브로커 연결 ({MCP_HOST}:{MCP_PORT})")
    
    # 3. 클라이언트 생성
    client = MCPClient(
        broker=broker,
        agent_id=AGENT_ID,
        agent_name=AGENT_NAME,
        capabilities=["sample"]
    )
    
    # 4. 클라이언트 연결
    await client.connect()
    await client.register()
    logger.info(f"에이전트 등록: {AGENT_ID}")
    
    # 5. 헬스 체크 루프
    try:
        while True:
            await client.send_heartbeat()
            await asyncio.sleep(30)
    except KeyboardInterrupt:
        logger.info("종료 중...")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
```

**실행**:

```bash
# 기본 설정
python start_mcp.py

# 환경 변수로 설정
MCP_HOST=0.0.0.0 MCP_PORT=9999 python start_mcp.py

# 여러 에이전트 실행
AGENT_ID=copilot-1 python start_mcp.py &
AGENT_ID=analyzer-1 python start_mcp.py &
AGENT_ID=tester-1 python start_mcp.py &
```

### 2. Docker 없이 실행

**시스템 서비스 (systemd)**: `mcp.service`

```ini
# /etc/systemd/system/mcp.service
[Unit]
Description=MCP Broker Service
After=network.target

[Service]
Type=simple
User=mcp
WorkingDirectory=/opt/mcp
Environment="MCP_PORT=9999"
ExecStart=/opt/mcp/venv/bin/python start_mcp.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**설치 및 실행**:

```bash
# 파일 복사
sudo cp mcp.service /etc/systemd/system/

# 권한 설정
sudo systemctl daemon-reload
sudo systemctl enable mcp
sudo systemctl start mcp

# 상태 확인
sudo systemctl status mcp
```

---

## Redis 배포

### 1. Docker로 Redis 실행

```bash
# Redis 서버 시작
docker run -d \
  --name mcp-redis \
  -p 6379:6379 \
  -v redis_data:/data \
  redis:7-alpine \
  redis-server \
    --appendonly yes \
    --maxmemory 512mb \
    --maxmemory-policy allkeys-lru

# 상태 확인
docker logs mcp-redis

# 연결 테스트
redis-cli ping
# 응답: PONG
```

### 2. Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    container_name: mcp-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: >
      redis-server
        --appendonly yes
        --maxmemory 512mb
        --maxmemory-policy allkeys-lru
        --save 60 1000
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

volumes:
  redis_data:
    driver: local
```

**실행**:

```bash
docker-compose up -d
docker-compose logs redis
docker-compose down
```

### 3. Redis 설정

**설정 파일**: `config.py`

```python
# config.py
BROKER_TYPE = "redis"

# Redis 설정
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

def build_redis_url():
    """Redis URL 생성"""
    if REDIS_PASSWORD:
        return f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
    return f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

REDIS_URL = build_redis_url()
```

### 4. 모니터링

```bash
# Redis CLI 접속
redis-cli

# 메모리 사용량
redis-cli INFO memory

# 연결된 클라이언트
redis-cli CLIENT LIST

# 스트림 조회
redis-cli XRANGE mcp:stream:broadcast - +

# 채널 구독 상태
redis-cli PUBSUB CHANNELS

# DB 크기
redis-cli DBSIZE
```

---

## Pulsar 배포

### 1. Docker로 Pulsar 실행

```bash
# Pulsar 서버 시작
docker run -d \
  --name mcp-pulsar \
  -p 6650:6650 \
  -p 8080:8080 \
  apachepulsar/pulsar:latest \
  bin/pulsar standalone

# 로그 확인
docker logs mcp-pulsar

# 관리자 콘솔
# http://localhost:8080/admin/v2/brokers
```

### 2. Docker Compose (권장)

```yaml
# docker-compose.yml
version: '3.8'

services:
  pulsar:
    image: apachepulsar/pulsar:latest
    container_name: mcp-pulsar
    ports:
      - "6650:6650"    # Broker
      - "8080:8080"    # Admin
    volumes:
      - pulsar_data:/pulsar/data
    command: bin/pulsar standalone
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/admin/v2/brokers"]
      interval: 30s
      timeout: 10s
      retries: 5
    restart: unless-stopped

volumes:
  pulsar_data:
    driver: local
```

### 3. Pulsar 설정

**설정 파일**: `config.py`

```python
# config.py
BROKER_TYPE = "pulsar"

# Pulsar 설정
PULSAR_SERVICE_URL = os.getenv(
    "PULSAR_SERVICE_URL",
    "pulsar://localhost:6650"
)
PULSAR_TENANT = os.getenv("PULSAR_TENANT", "ai-aarch")
PULSAR_NAMESPACE = os.getenv("PULSAR_NAMESPACE", "default")
PULSAR_AUTH_TOKEN = os.getenv("PULSAR_AUTH_TOKEN", None)
```

### 4. 테넌트 및 네임스페이스 초기화

```bash
# 테넌트 생성
docker exec mcp-pulsar bin/pulsar-admin tenants create ai-aarch

# 네임스페이스 생성
docker exec mcp-pulsar bin/pulsar-admin namespaces create ai-aarch/default

# 토픽 생성 (선택)
docker exec mcp-pulsar bin/pulsar-admin topics create \
  persistent://ai-aarch/default/requests

# 토픽 목록 확인
docker exec mcp-pulsar bin/pulsar-admin topics list ai-aarch/default
```

### 5. 모니터링

```bash
# Pulsar CLI 실행
docker exec -it mcp-pulsar bin/pulsar-client

# 토픽 통계
docker exec mcp-pulsar bin/pulsar-admin topics stats \
  persistent://ai-aarch/default/requests

# 구독자 목록
docker exec mcp-pulsar bin/pulsar-admin topics subscriptions \
  persistent://ai-aarch/default/requests

# 메시지 조회
docker exec mcp-pulsar bin/pulsar-client \
  consume -s test-subscription \
  persistent://ai-aarch/default/requests
```

---

## 설정 관리

### 1. 환경 변수

```bash
# MCP
export MCP_HOST=0.0.0.0
export MCP_PORT=9999

# Redis
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_PASSWORD=secret123

# Pulsar
export PULSAR_SERVICE_URL=pulsar://localhost:6650
export PULSAR_TENANT=ai-aarch
export PULSAR_NAMESPACE=default

# 공통
export BROKER_TYPE=redis
export LOG_LEVEL=INFO
export AGENT_ID=agent-1
```

### 2. .env 파일

```bash
# .env
BROKER_TYPE=redis

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Logging
LOG_LEVEL=INFO
LOG_FILE=mcp.log
```

**로드**:

```python
from dotenv import load_dotenv
import os

load_dotenv('.env')

BROKER_TYPE = os.getenv("BROKER_TYPE", "mcp")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
```

### 3. 설정 파일 (config.json)

```json
{
  "broker": {
    "type": "redis",
    "redis": {
      "host": "localhost",
      "port": 6379,
      "db": 0,
      "password": null
    }
  },
  "logging": {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "mcp.log",
    "max_size": 10485760,
    "backup_count": 5
  },
  "agent": {
    "id": "agent-1",
    "name": "Default Agent",
    "heartbeat_interval": 30
  }
}
```

**로드**:

```python
import json

with open('config.json') as f:
    config = json.load(f)

BROKER_TYPE = config['broker']['type']
```

---

## 모니터링 및 로깅

### 1. 로깅 설정

```python
# logging_config.py
import logging
from logging.handlers import RotatingFileHandler

def setup_logging(level=logging.INFO, log_file="mcp.log"):
    """로깅 설정"""
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    # 파일 핸들러
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)  # 파일에는 모든 로그
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    
    # 핸들러 추가
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

# 사용
logger = setup_logging(log_file="mcp.log")
logger.info("시스템 시작")
```

### 2. 모니터링 스크립트

```python
# monitor.py
import asyncio
import logging
from docs.mcp.mcp_core import BrokerFactory

logger = logging.getLogger(__name__)

async def monitor_health(broker_type="redis"):
    """브로커 상태 모니터링"""
    broker = BrokerFactory.create(broker_type)
    
    try:
        await broker.connect()
        logger.info(f"✓ {broker_type} 브로커 연결 성공")
    except Exception as e:
        logger.error(f"✗ {broker_type} 브로커 연결 실패: {e}")
        return
    finally:
        await broker.disconnect()

async def main():
    for broker_type in ["mcp", "redis", "pulsar"]:
        await monitor_health(broker_type)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 문제 해결

### 1. MCP TCP 연결 오류

```bash
# 포트 확인
netstat -an | grep 9999

# 방화벽 확인 (Windows)
netsh advfirewall firewall show rule name="MCP TCP"

# 방화벽 열기 (Windows)
netsh advfirewall firewall add rule \
  name="MCP TCP" \
  dir=in \
  action=allow \
  protocol=tcp \
  localport=9999
```

**해결책**:

```python
# 연결 재시도
import asyncio
from docs.mcp.mcp_core import MCPBroker

async def connect_with_retry(host, port, max_retries=3):
    broker = MCPBroker(host=host, port=port)
    
    for attempt in range(max_retries):
        try:
            await broker.connect()
            return broker
        except ConnectionError as e:
            logger.warning(f"시도 {attempt+1}/{max_retries} 실패: {e}")
            await asyncio.sleep(2 ** attempt)  # 지수 백오프
    
    raise ConnectionError(f"{max_retries}회 재시도 후 실패")
```

### 2. Redis 연결 오류

```bash
# Redis 상태 확인
redis-cli ping

# 메모리 부족
redis-cli INFO memory

# 연결 수 초과
redis-cli CLIENT LIST | wc -l
```

**해결책**:

```python
# Redis 설정 조정
broker_config = {
    "redis_url": "redis://localhost:6379",
    "socket_connect_timeout": 5,
    "socket_timeout": 5,
    "connection_pool_kwargs": {
        "max_connections": 50,
        "retry_on_timeout": True
    }
}
```

### 3. Pulsar 연결 오류

```bash
# Pulsar 상태 확인
curl -s http://localhost:8080/admin/v2/brokers

# 테넌트/네임스페이스 확인
docker exec mcp-pulsar bin/pulsar-admin tenants list
docker exec mcp-pulsar bin/pulsar-admin namespaces list ai-aarch
```

**해결책**:

```python
# 테넌트 자동 생성
import subprocess

def ensure_pulsar_namespace():
    """필요한 네임스페이스 보장"""
    try:
        subprocess.run([
            "docker", "exec", "mcp-pulsar",
            "bin/pulsar-admin", "tenants", "create", "ai-aarch"
        ], check=True)
    except subprocess.CalledProcessError:
        pass  # 이미 존재
```

---

## 성능 튜닝

### 1. MCP TCP 튜닝

```python
# 버퍼 크기 조정
class MCPBroker(MessageBroker):
    def __init__(self, host="127.0.0.1", port=9999):
        self.buffer_size = 65536  # 64KB
        self.max_connections = 100
```

### 2. Redis 튜닝

```bash
# Redis 메모리 설정
redis-cli CONFIG SET maxmemory 1gb
redis-cli CONFIG SET maxmemory-policy allkeys-lru

# AOF 비활성화 (성능 중시)
redis-cli CONFIG SET appendonly no

# 저장 간격 조정
redis-cli CONFIG SET save "60 1000"  # 60초에 1000개 변경
```

### 3. Pulsar 튜닝

```bash
# 메시지 배치 크기
docker exec mcp-pulsar \
  bin/pulsar-admin brokers update-dynamic-config \
    --set "bindingMaxMessageSize=5242880"

# 처리량 증가
docker exec mcp-pulsar \
  bin/pulsar-admin brokers update-dynamic-config \
    --set "maxConcurrentLookupRequests=10000"
```

---

## 마이그레이션 가이드

### MCP → Redis 마이그레이션

```python
# 1단계: Redis 시작
docker run -d --name mcp-redis -p 6379:6379 redis:7-alpine

# 2단계: 설정 변경
BROKER_TYPE = "redis"

# 3단계: 코드 변경 없음 (같은 API)
broker = BrokerFactory.create("redis")

# 4단계: 테스트
await broker.connect()
# 기존 코드와 동일하게 작동
```

### Redis → Pulsar 마이그레이션

```python
# 1단계: Pulsar 시작
docker run -d --name mcp-pulsar \
  -p 6650:6650 -p 8080:8080 \
  apachepulsar/pulsar:latest \
  bin/pulsar standalone

# 2단계: 네임스페이스 생성
docker exec mcp-pulsar \
  bin/pulsar-admin namespaces create ai-aarch/default

# 3단계: 설정 변경
BROKER_TYPE = "pulsar"

# 4단계: 기존 메시지 전이
# Redis Streams → Pulsar Topics
async def migrate_messages():
    redis_broker = BrokerFactory.create("redis")
    pulsar_broker = BrokerFactory.create("pulsar")
    
    await redis_broker.connect()
    await pulsar_broker.connect()
    
    # 히스토리 조회
    messages = await redis_broker.get_message_history("broadcast")
    
    # Pulsar에 저장
    for msg in messages:
        await pulsar_broker.store_message(msg)
```

---

**작성자**: GitHub Copilot  
**상태**: ✅ 완료  
**버전**: 1.0.0
