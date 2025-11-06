# MCP 예제 가이드

**작성일**: 2025년 11월 7일  
**목표**: MCP 코어 라이브러리 사용 예제 및 실행 방법

---

## 📁 예제 목록

### 1️⃣ [01-basic-communication.py](./01-basic-communication.py)
**MCP 기본 통신 예제**

두 개의 에이전트가 MCP를 통해 메시지를 교환합니다.

```bash
# 실행
cd docs/mcp/examples
python 01-basic-communication.py
```

**기능**:
- Agent 1: 코드 생성 및 브로드캐스트
- Agent 2: 요청 수신 및 응답
- MCP TCP 브로커 사용

---

### 2️⃣ [02-redis-broker.py](./02-redis-broker.py)
**Redis 브로커 사용 예제**

Redis Pub/Sub를 사용한 메시징 시스템입니다.

```bash
# 사전 요구사항: Redis 서버 실행
docker run -d -p 6379:6379 redis:7-alpine

# Python 라이브러리 설치
pip install redis aioredis

# 실행
python 02-redis-broker.py
```

**기능**:
- Producer: 메시지 발행
- Consumer: 메시지 구독
- Redis Pub/Sub 기반

---

### 3️⃣ [03-pulsar-broker.py](./03-pulsar-broker.py)
**Pulsar 브로커 사용 예제**

Apache Pulsar를 사용한 분산 메시징 시스템입니다.

```bash
# 사전 요구사항: Pulsar 서버 실행
docker run -d -p 6650:6650 apachepulsar/pulsar:latest bin/pulsar standalone

# Python 라이브러리 설치
pip install pulsar-client

# 실행
python 03-pulsar-broker.py
```

**기능**:
- Publisher: 토픽에 메시지 발행
- Subscriber: 토픽 구독
- Pulsar 토픽 기반

---

### 4️⃣ [04-ocpp-collaboration.py](./04-ocpp-collaboration.py)
**OCPP 협업 시뮬레이션** ⭐ 권장

VS Code 다중 창에서 OCPP 프로젝트를 협업으로 개발하는 시나리오입니다.

```bash
# 실행
python 04-ocpp-collaboration.py
```

**시나리오**:
```
OCPP Server Agent (Copilot):
  1️⃣  코드 생성 시작
  2️⃣  코드 생성 완료 알림
  5️⃣  서버 시작 알림
  
OCPP Client Agent (Codex):
  3️⃣  코드 분석 시작
  4️⃣  분석 결과 전송
  6️⃣  테스트 시작
  8️⃣  테스트 결과 전송
  
Monitor: 전체 과정 추적
```

---

## 🚀 빠른 시작

### Step 1: MCP 코어 설치
```bash
# 워크스페이스 루트에서
pip install -e .
```

### Step 2: 기본 예제 실행 (MCP TCP)
```bash
cd docs/mcp/examples
python 01-basic-communication.py
```

**출력 예시**:
```
INFO:__main__:Agent 1: 코드 분석 요청 전송...
INFO:__main__:Agent 1: 응답 수신 - {'status': 'success', 'analysis': '...'}
```

### Step 3: Redis 예제 실행
```bash
# 터미널 1: Redis 시작
docker run -d -p 6379:6379 redis:7-alpine

# 터미널 2: 예제 실행
pip install redis aioredis
python 02-redis-broker.py
```

### Step 4: OCPP 협업 시뮬레이션 실행
```bash
python 04-ocpp-collaboration.py
```

---

## 🔧 브로커 선택 방법

### MCP (TCP) - 기본값
```python
from mcp_core import BrokerFactory

broker = BrokerFactory.create("mcp", host="127.0.0.1", port=9999)
```

### Redis
```python
broker = BrokerFactory.create("redis", redis_url="redis://localhost:6379")
```

### Pulsar
```python
broker = BrokerFactory.create(
    "pulsar",
    service_url="pulsar://localhost:6650",
    tenant="ai-aarch",
    namespace="default"
)
```

---

## 📊 예제별 기능 비교

| 예제 | 브로커 | 기능 | 복잡도 |
|------|--------|------|--------|
| 01-basic | MCP | 기본 통신 | ⭐ |
| 02-redis | Redis | Pub/Sub | ⭐⭐ |
| 03-pulsar | Pulsar | 분산 메시징 | ⭐⭐⭐ |
| 04-ocpp | MCP | 협업 시뮬레이션 | ⭐⭐ |

---

## 💡 예제 수정 및 실험

### 예제 1: 커스텀 메시지 추가
```python
await client.broadcast(
    event_type="custom_event",
    data={"key": "value"}
)
```

### 예제 2: 요청-응답 패턴
```python
response = await client.send_request(
    target_agent="agent-2",
    request_type="analyze",
    parameters={"file": "test.py"}
)
```

### 예제 3: 에이전트 등록
```python
client = MCPClient(
    broker=broker,
    agent_id="my-agent",
    agent_name="My Custom Agent",
    agent_type="custom",
    capabilities=["capability1", "capability2"]
)
```

---

## 🐛 문제 해결

### "Connection refused" 에러
```bash
# MCP TCP 포트 확인
netstat -an | grep 9999

# Redis 연결 확인
redis-cli ping

# Pulsar 연결 확인
curl http://localhost:8080/
```

### "Module not found" 에러
```bash
# 의존성 설치
pip install redis aioredis pulsar-client
```

### 메시지가 수신되지 않음
1. 브로커가 실행 중인지 확인
2. 채널 이름 확인
3. 구독 시간 초 확인

---

## 🎯 다음 단계

1. **예제 실행 및 이해**: 01 → 02 → 03 → 04 순서로
2. **커스텀 예제 작성**: 4번 예제를 기반으로 수정
3. **실제 프로젝트 적용**: OCPP 서버/클라이언트 통합

---

## 📚 추가 자료

- [MCP 아키텍처](../01-ARCHITECTURE.md)
- [OCPP 통합](../02-OCPP-INTEGRATION.md)
- [전송 옵션 비교](../03-TRANSPORT-OPTIONS.md)

---

**작성자**: GitHub Copilot  
**상태**: ✅ 예제 완료, 실행 준비 완료
