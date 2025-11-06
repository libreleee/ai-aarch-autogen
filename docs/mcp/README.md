# MCP (Model Context Protocol) 프로젝트 문서

**작성일**: 2025년 11월 7일  
**프로젝트**: AArch-AutoGen Multi-Agent Bridge  
**상태**: ✅ 설계 완료, 구현 준비 완료

---

## 📚 문서 목록

### 1️⃣ [01-ARCHITECTURE.md](./01-ARCHITECTURE.md)
- **MCP 기본 아키텍처 설계**
- TCP 기반 메시징 시스템
- 프로토콜 및 메시지 형식
- 컴포넌트 설계
- 보안 및 성능 요구사항

### 2️⃣ [02-OCPP-INTEGRATION.md](./02-OCPP-INTEGRATION.md)
- **MCP + OCPP 통합 아키텍처**
- VS Code 다중 창 협업 시스템
- Code → Run → Debug 워크플로우
- 실제 사용 시나리오
- 기술 스택

### 3️⃣ [03-TRANSPORT-OPTIONS.md](./03-TRANSPORT-OPTIONS.md)
- **메시지 전송 계층 비교**
- TCP vs Redis vs Pulsar
- 성능 비교표
- 선택 가이드 및 권장사항

---

## 🎯 시스템 개요

### 개념
```
VS Code 창1                      VS Code 창2
(OCPP Server +                   (OCPP Client +
 GitHub Copilot)                 Codex/Agno)
         ↓ ↑                           ↓ ↑
         └───────────┬────────────────┘
                     │
                MCP Server
            (메시지 중앙 허브)
                     │
    BROADCAST, REQUEST/RESPONSE
    Task Distribution
```

### 기능
- ✅ 실시간 메시징 (BROADCAST, REQUEST/RESPONSE)
- ✅ Agent 등록/관리 및 디스커버리
- ✅ 메시지 히스토리 및 감사 로그
- ✅ 헬스 체크 및 자동 재연결
- ✅ 우선순위 큐 및 작업 분배

---

## 🚀 빠른 시작

### Phase 1: Redis 배포 (권장)
```bash
# Redis 시작
docker run -d -p 6379:6379 redis:7-alpine

# MCP 클라이언트 라이브러리 설치
pip install redis aioredis

# MCP 서버 구현 시작
python mcp_server/redis_broker.py
```

### Phase 2: 에이전트 등록
```python
# 창 1: OCPP Server Agent
from mcp_client import MCPClient

client1 = MCPClient(broker_type='redis')
await client1.connect()
await client1.register_agent(
    agent_name="OCPP Server (Copilot)",
    agent_type="code_generator",
    capabilities=["code_generation", "testing"]
)

# 창 2: OCPP Client Agent
client2 = MCPClient(broker_type='redis')
await client2.connect()
await client2.register_agent(
    agent_name="OCPP Client (Codex)",
    agent_type="analyzer",
    capabilities=["code_analysis", "testing"]
)
```

### Phase 3: 메시지 송수신
```python
# 브로드캐스트 (1쪽에서 발행, 모두가 구독)
await client1.broadcast(
    event="code_generated",
    data={"file": "auth.py", "lines": 127}
)

# 요청/응답 (1:1 통신)
response = await client2.request(
    target_agent="OCPP Server (Copilot)",
    request_type="analyze_code",
    parameters={"file": "auth.py"}
)
```

---

## 📋 구현 로드맵

### Week 1: 기본 구현
- [ ] MCP Server Core (TCP 또는 Redis)
- [ ] Connection Manager
- [ ] Message Broker (기본)
- [ ] Unit Tests

### Week 2: 고급 기능
- [ ] Message Broker (Pub/Sub, Broadcasting)
- [ ] Message Persistence
- [ ] Health Check & Heartbeat
- [ ] Integration Tests

### Week 3: 통합 및 최적화
- [ ] OCPP 에이전트 래퍼
- [ ] Performance Tuning
- [ ] Documentation
- [ ] Demo & Validation

---

## 🔍 주요 설계 결정

### 1. 메시지 형식
```json
{
  "message_id": "uuid",           # 추적용
  "message_type": "BROADCAST",    # 메시지 타입
  "sender_id": "agent-1",         # 보낸이
  "timestamp": "ISO8601",         # 시간
  "payload": {...}                # 데이터
}
```

### 2. 메시지 타입
- **REGISTER**: 에이전트 등록
- **REQUEST**: 작업 요청
- **RESPONSE**: 응답
- **BROADCAST**: 모든 구독자에게 전파
- **HEARTBEAT**: 헬스 체크

### 3. 전송 계층 선택
- **Phase 1**: Redis (빠르고 간단)
- **Phase 2+**: Pulsar (대규모)
- **학습용**: TCP (개념 이해)

---

## 🏆 예상 효과

### Before (수동 작업)
```
개발자 1: 코드 작성 (30분)
개발자 2: 코드 리뷰 (20분)
개발자 1: 수정 (15분)
개발자 2: 테스트 (20분)
───────────────────
총 시간: 85분
```

### After (MCP 자동화)
```
개발자 1: 요구사항 정의 (5분)
MCP 자동화:
  - Copilot: 코드 생성 (자동)
  - MCP: 브로드캐스트
  - Codex: 코드 분석 (자동)
  - MCP: 응답 전송
  - Copilot: 수정 (자동)
  - MCP: 브로드캐스트
  - Codex: 테스트 (자동)
───────────────────
총 시간: 5분 + 자동화
```

**효과**: 수동 작업 94% 감소

---

## 📚 추가 참고자료

### MCP 프로토콜
- [Model Context Protocol](https://modelcontextprotocol.io/)
- 메시지 기반 통신 표준

### OCPP 프로토콜
- [Open Charge Point Protocol](https://www.openchargealliance.org/)
- EV Charging 표준 프로토콜

### 메시징 플랫폼
- **Redis**: Fast, in-memory message broker
- **Apache Pulsar**: Distributed, scalable messaging platform
- **RabbitMQ**: AMQP-based message broker

---

## ❓ FAQ

### Q: TCP vs Redis vs Pulsar 중 어떤 걸 선택해야 하나요?
**A**: 
- **지금**: Redis (빠르고 간단)
- **나중**: Pulsar (대규모)
- **학습용**: TCP (개념 이해)

### Q: 메시지 순서가 보장되나요?
**A**: Redis Streams와 Pulsar Partitions로 순서 보장 가능

### Q: 메시지 손실 가능성이 있나요?
**A**: 
- Redis: RDB/AOF로 완화 가능
- Pulsar: 디스크 기반으로 안전

### Q: 확장성은 어느 정도 되나요?
**A**:
- TCP: 제한적
- Redis: 중간 (Cluster 모드)
- Pulsar: 무제한 (Multi-broker)

### Q: 비용은 얼마나 되나요?
**A**:
- **Redis**: 무료 (오픈소스)
- **Pulsar**: 무료 (오픈소스)
- **TCP**: 무료 (구현 필요)

---

## 🤝 기여 방법

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

---

**작성자**: GitHub Copilot  
**최종 업데이트**: 2025년 11월 7일  
**상태**: ✅ 설계 완료, 구현 시작 준비 완료
