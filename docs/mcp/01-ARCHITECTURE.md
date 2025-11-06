# MCP (Model Context Protocol) 서버 설계 문서

**작성일**: 2025년 11월 7일  
**프로젝트**: AArch-AutoGen Multi-Agent Bridge  
**목표**: VS Code 다중 창 간 협업 통신 시스템 구축

---

## 📋 목차

1. [개요](#개요)
2. [아키텍처](#아키텍처)
3. [프로토콜 설계](#프로토콜-설계)
4. [메시지 형식](#메시지-형식)
5. [기능명세](#기능명세)
6. [구현 계획](#구현-계획)
7. [보안 고려사항](#보안-고려사항)
8. [성능 요구사항](#성능-요구사항)

---

## 개요

### 목적
- VS Code의 여러 창(또는 워크스페이스)에서 실행되는 여러 AI 에이전트들 간에 실시간으로 통신
- Worker Agent 패턴을 기반으로 한 효율적인 작업 분배 및 조율
- MCP 표준 프로토콜을 따르는 통신 방식 구현

### 주요 특징
- **표준 기반**: MCP(Model Context Protocol) 준수
- **비동기 통신**: asyncio 기반 논블로킹 I/O
- **안정적 메시징**: JSON 기반 메시지 프로토콜 with 재전송 메커니즘
- **확장 가능**: 새로운 메시지 타입 및 핸들러 추가 용이

### 사용 사례
```
VS Code 창1 (Copilot CLI Agent)
    ↓
MCP Server (중앙 조율)
    ↑ ↓ ↓
VS Code 창2 (Analysis Agent) | VS Code 창3 (Refactoring Agent) | VS Code 창4 (Testing Agent)
```

---

## 아키텍처

### 1. 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP Server (Central Hub)                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           Message Broker & Router                    │  │
│  │  - Message Queue Management                          │  │
│  │  - Request/Response Routing                          │  │
│  │  - Broadcast/Multicast Support                       │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │        Connection Manager & Agent Registry           │  │
│  │  - Agent Connection Tracking                         │  │
│  │  - Health Check & Heartbeat                          │  │
│  │  - Capability Discovery                              │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │        Persistence Layer & State Management          │  │
│  │  - Message History                                   │  │
│  │  - Agent State                                       │  │
│  │  - Transaction Log                                   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
         ↑         ↑         ↑         ↑
         │         │         │         │
       TCP       TCP       TCP       TCP
     Port1     Port2     Port3     Port4
         │         │         │         │
    VS Code   VS Code   VS Code   VS Code
    Client1   Client2   Client3   Client4
```

### 2. 컴포넌트별 설계

#### 2.1 MCP Server Core
```python
class MCPServer:
    - host: str                         # 바인딩 호스트
    - port: int                         # 바인딩 포트
    - message_broker: MessageBroker     # 메시지 브로커
    - connection_manager: ConnectionManager
    - start()                           # 서버 시작
    - stop()                            # 서버 종료
    - run()                             # 메인 루프
```

#### 2.2 Connection Manager
```python
class ConnectionManager:
    - connections: dict[str, ClientConnection]
    - agents: dict[str, AgentInfo]
    - add_connection()                  # 연결 추가
    - remove_connection()               # 연결 제거
    - get_agent()                       # 에이전트 조회
    - broadcast_heartbeat()             # 헬스 체크
    - get_available_agents()            # 사용 가능한 에이전트 목록
```

#### 2.3 Message Broker
```python
class MessageBroker:
    - message_queue: asyncio.Queue
    - routing_rules: dict              # 라우팅 규칙
    - process_message()                # 메시지 처리
    - route_message()                  # 메시지 라우팅
    - broadcast()                      # 브로드캐스트
    - unicast()                        # 유니캐스트
```

#### 2.4 Client Connection Handler
```python
class ClientConnection:
    - client_id: str                   # 고유 클라이언트 식별자
    - agent_id: str                    # 에이전트 ID
    - reader: asyncio.StreamReader
    - writer: asyncio.StreamWriter
    - read_message()                   # 메시지 읽기
    - write_message()                  # 메시지 쓰기
    - heartbeat()                      # 헬스 체크
```

---

## 프로토콜 설계

### 1. 연결 수명 주기

```
Client                          Server
  │
  ├─────────CONNECT───────────→  (TCP Connection)
  │                              (Connection Handler 생성)
  │
  ├─────────REGISTER───────────→  (Agent 정보 등록)
  │                              (Connection Manager에 추가)
  │
  ├◄──────REGISTER_RESPONSE──────  (등록 확인)
  │
  ├─────────REQUEST───────────→  (작업 요청)
  │                              (Message Router로 라우팅)
  │
  ├◄──────RESPONSE─────────────  (응답)
  │
  │ [헬스체크 반복]
  ├─────────HEARTBEAT──────────→
  ├◄──────HEARTBEAT_ACK────────
  │
  ├─────────DISCONNECT────────→  (연결 종료)
  │                              (정리)
  └
```

### 2. 메시지 프로토콜

#### 메시지 래퍼 (Envelope)
```
┌─────────────────────────────────────────┐
│  4 bytes: Total Length (Big Endian)    │
├─────────────────────────────────────────┤
│  JSON Payload (UTF-8 Encoded)          │
│  {                                      │
│    "message_id": "uuid",               │
│    "message_type": "...",              │
│    "sender_id": "agent-1",             │
│    "timestamp": "ISO8601",             │
│    "payload": {...}                    │
│  }                                      │
└─────────────────────────────────────────┘
```

#### 메시지 재전송 메커니즘
```
1. Client 보냄: REQUEST (message_id=msg-123)
2. Server 받음: 처리 시작
3. Server 응답: ACK (message_id=msg-123)
4. Client 받음: ACK 수신하면 타임아웃 취소

타임아웃 시나리오:
- Client 재전송 MAX_RETRIES까지
- Server 응답이 없으면 실패
```

---

## 메시지 형식

### 1. 기본 메시지 타입

#### REGISTER (클라이언트 등록)
```json
{
  "message_type": "REGISTER",
  "message_id": "uuid-1",
  "sender_id": "client-1",
  "timestamp": "2025-11-07T10:30:00Z",
  "payload": {
    "agent_name": "Copilot CLI Agent",
    "agent_type": "code_generator",
    "capabilities": ["code_generation", "analysis", "refactoring"],
    "version": "1.0.0"
  }
}
```

#### REGISTER_RESPONSE (등록 응답)
```json
{
  "message_type": "REGISTER_RESPONSE",
  "message_id": "uuid-1",
  "sender_id": "mcp-server",
  "timestamp": "2025-11-07T10:30:01Z",
  "payload": {
    "status": "success",
    "agent_id": "agent-uuid-xxx",
    "message": "Agent registered successfully"
  }
}
```

#### REQUEST (작업 요청)
```json
{
  "message_type": "REQUEST",
  "message_id": "uuid-2",
  "sender_id": "agent-1",
  "target_agent": "agent-2",
  "timestamp": "2025-11-07T10:30:02Z",
  "payload": {
    "request_type": "analyze_code",
    "parameters": {
      "code": "...",
      "language": "python"
    }
  }
}
```

#### RESPONSE (요청 응답)
```json
{
  "message_type": "RESPONSE",
  "message_id": "uuid-2",
  "sender_id": "agent-2",
  "timestamp": "2025-11-07T10:30:05Z",
  "payload": {
    "status": "success",
    "result": {
      "analysis": "...",
      "issues": [],
      "suggestions": []
    }
  }
}
```

#### HEARTBEAT (헬스 체크)
```json
{
  "message_type": "HEARTBEAT",
  "message_id": "uuid-3",
  "sender_id": "agent-1",
  "timestamp": "2025-11-07T10:30:30Z",
  "payload": {
    "status": "alive",
    "uptime": 1234,
    "active_tasks": 3
  }
}
```

#### HEARTBEAT_ACK (헬스 체크 응답)
```json
{
  "message_type": "HEARTBEAT_ACK",
  "message_id": "uuid-3",
  "sender_id": "mcp-server",
  "timestamp": "2025-11-07T10:30:30Z",
  "payload": {
    "status": "acknowledged"
  }
}
```

#### BROADCAST (브로드캐스트)
```json
{
  "message_type": "BROADCAST",
  "message_id": "uuid-4",
  "sender_id": "agent-1",
  "timestamp": "2025-11-07T10:30:35Z",
  "payload": {
    "broadcast_type": "task_completed",
    "data": {
      "task_id": "task-123",
      "result": "success"
    }
  }
}
```

#### DISCONNECT (연결 종료)
```json
{
  "message_type": "DISCONNECT",
  "message_id": "uuid-5",
  "sender_id": "agent-1",
  "timestamp": "2025-11-07T10:30:40Z",
  "payload": {
    "reason": "normal_shutdown"
  }
}
```

---

## 기능명세

### 1. 핵심 기능

#### 1.1 Agent Discovery (에이전트 탐색)
```python
# 서버가 관리하는 에이전트 목록 조회
Request: {
  "message_type": "QUERY",
  "target_agent": "mcp-server",
  "payload": {
    "query_type": "list_agents",
    "filter": {"capability": "code_generation"}
  }
}

Response: {
  "message_type": "RESPONSE",
  "payload": {
    "agents": [
      {
        "agent_id": "agent-1",
        "agent_name": "Copilot CLI Agent",
        "capabilities": ["code_generation"],
        "status": "active"
      },
      ...
    ]
  }
}
```

#### 1.2 Task Distribution (작업 분배)
```python
# 특정 조건을 만족하는 에이전트에 작업 분배
# - Capability 기반 분배
# - Load Balancing 적용
# - Round-Robin 또는 Least-Loaded 전략
```

#### 1.3 Request/Response Pattern
```python
# 요청-응답 쌍 관리
# - message_id로 추적
# - 타임아웃 처리
# - 재전송 메커니즘
```

#### 1.4 Pub/Sub Pattern
```python
# 특정 메시지 타입 구독
# - Agent가 특정 이벤트 구독 가능
# - Server가 이벤트 발생 시 모든 구독자에게 전파
```

#### 1.5 Connection Management
```python
# 연결 상태 관리
# - 자동 재연결 기능
# - Idle 연결 정리
# - Connection Pool 관리
```

### 2. 고급 기능

#### 2.1 Agent Clustering
```python
# 여러 Agent의 협업 작업 조율
# - Agent Group 생성
# - Group 내 메시지 라우팅
# - Group Task Distribution
```

#### 2.2 Message Priority Queue
```python
# 메시지 우선순위 관리
# - HIGH, NORMAL, LOW 우선순위
# - Priority Queue로 관리
```

#### 2.3 Transaction Support
```python
# 분산 트랜잭션 지원
# - BEGIN_TRANSACTION
# - COMMIT
# - ROLLBACK
```

---

## 구현 계획

### Phase 1: 기본 서버 구현 (1-2일)
1. **MCP Server Core**
   - 기본 TCP 서버 구현
   - 비동기 연결 처리
   - 메시지 읽기/쓰기

2. **Connection Manager**
   - 연결 추가/제거
   - Agent 등록/관리
   - Heartbeat 구현

3. **Message Broker (Simple)**
   - 기본 메시지 라우팅
   - 유니캐스트 메시징

### Phase 2: 고급 기능 (2-3일)
1. **Message Broker (Advanced)**
   - 브로드캐스트
   - 구독 메커니즘

2. **Reliability Features**
   - 메시지 재전송
   - 타임아웃 처리
   - 에러 복구

3. **Persistence**
   - 메시지 로그
   - Agent 상태 저장
   - 트랜잭션 로그

### Phase 3: 통합 및 테스트 (1-2일)
1. **VS Code 클라이언트**
   - MCP 클라이언트 라이브러리
   - VS Code 확장 통합

2. **테스트 및 검증**
   - 단위 테스트
   - 통합 테스트
   - 부하 테스트

---

## 보안 고려사항

### 1. 인증 및 권한
- **Token-based Authentication**: JWT 토큰 사용
- **Capability-based Authorization**: 에이전트 능력에 따른 권한 제어

### 2. 암호화
- **TLS/SSL**: TCP 연결 암호화
- **Message Signing**: 메시지 무결성 검증

### 3. 입력 검증
- **Schema Validation**: JSON 스키마 검증
- **Injection Prevention**: SQL/Command Injection 방지

### 4. 감시 및 로깅
- **Access Logging**: 모든 연결/메시지 로그
- **Audit Trail**: 변경 이력 기록

---

## 성능 요구사항

### 1. 처리량
- **최소 100 concurrent connections**
- **1000+ messages/sec** 처리 능력

### 2. 지연시간
- **메시지 라우팅**: < 10ms
- **Heartbeat 응답**: < 100ms

### 3. 신뢰성
- **메시지 전달 확률**: > 99.9%
- **Server Availability**: > 99.5% (월간)

### 4. 확장성
- **수평적 확장**: 다중 서버 인스턴스 지원
- **로드 밸런싱**: Round-robin 또는 가중치 기반

---

## 다음 단계

1. **기본 프로토콜 구현**: TCP 서버 + 메시지 프로토콜
2. **Connection Manager 구현**: 에이전트 등록/관리
3. **Message Broker 구현**: 기본 라우팅
4. **VS Code 클라이언트 개발**: MCP 클라이언트 라이브러리
5. **통합 테스트**: 다중 클라이언트 시나리오

---

**작성자**: GitHub Copilot  
**버전**: 1.0 (Design Document)  
**상태**: ✅ 설계 완료, 구현 준비 완료
