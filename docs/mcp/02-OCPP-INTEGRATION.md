# MCP + OCPP 통합 아키텍처: 다중 VS Code 협업 시스템

**작성일**: 2025년 11월 7일  
**목표**: VS Code 여러 창에서 OCPP 프로젝트를 AI 협업으로 개발, 실행, 디버깅

---

## 📋 시스템 개요

### 시나리오
```
┌─────────────────────────────────────────────────────────────────┐
│                    개발자 로컬 머신                              │
│                                                                 │
│  ┌──────────────────┐           ┌──────────────────┐           │
│  │  VS Code 창 1    │           │  VS Code 창 2    │           │
│  │                  │           │                  │           │
│  │  OCPP Server     │           │  OCPP Client     │           │
│  │  (CirineoS)      │  MCP      │  (agno/other)    │           │
│  │                  │◄──────────│                  │           │
│  │ • GitHub Copilot │ 통신      │ • Codex          │           │
│  │   (코드 생성)    │  & 협업   │ • Agno/Claude    │           │
│  │ • AutoGen        │           │ • FastAPI        │           │
│  │ • 실행/테스트    │           │ • 테스트 관리    │           │
│  │                  │           │                  │           │
│  └──────────────────┘           └──────────────────┘           │
│           ↑                                ↑                     │
│           │                                │                     │
│           └────────┬───────────────────┬───┘                     │
│                    │                   │                         │
│                    ↓                   ↓                         │
│           ┌───────────────────────────────────┐                 │
│           │   MCP Server (로컬 TCP)           │                 │
│           │   Port: 9999                      │                 │
│           │                                   │                 │
│           │ • Message Broker                  │                 │
│           │ • Connection Manager              │                 │
│           │ • Task Distribution               │                 │
│           │ • Message History Logging         │                 │
│           └───────────────────────────────────┘                 │
│                    ↑                   ↑                         │
└────────────────────┼───────────────────┼─────────────────────────┘
                     │                   │
                     ↓ OCPP Protocol     ↓
            (localhost:9000)    (localhost:9001)
                     │                   │
        ┌────────────────────────────────────┐
        │  Actual OCPP Services              │
        │  (Can run on same/different hosts) │
        │                                    │
        │ • OCPP Server                      │
        │ • OCPP Client/Simulator            │
        │ • Charge Point Simulator           │
        └────────────────────────────────────┘
```

---

## 🔄 워크플로우: Code → Run → Debug 루프

### 1. **코드 생성 단계** (창 1: GitHub Copilot + AutoGen)

```
개발자: "OCPP 1.6 호환 인증 핸들러 작성해줘"
    ↓
GitHub Copilot + AutoGen (창 1)
    ├─ 코드 생성
    ├─ 타입 힌팅 추가
    ├─ 주석 작성
    └─ 파일 저장
    ↓
MCP 메시지: BROADCAST "code_generated"
    ├─ event: "auth_handler_created"
    ├─ file_path: "src/handlers/auth.py"
    ├─ code_snippet: "..."
    └─ requires_review: true
    ↓
창 2 (OCPP Client)에서 자동 감지
    ├─ 코드 미리보기
    ├─ 타입 검사
    └─ 통합 테스트 검토
```

### 2. **코드 분석 및 개선** (창 2: Codex + Agno)

```
창 2 (Codex/Agno):
    ├─ 생성된 코드 분석
    │  ├─ 성능 검사
    │  ├─ 보안 검사
    │  └─ OCPP 프로토콜 준수 확인
    ├─ 개선 제안
    │  ├─ Refactoring suggestions
    │  ├─ Performance optimization
    │  └─ Security hardening
    └─ 테스트 케이스 생성
    ↓
MCP 메시지: REQUEST
    ├─ target: "server_agent"
    ├─ request_type: "code_review"
    ├─ file_path: "src/handlers/auth.py"
    ├─ analysis_type: ["performance", "security", "protocol"]
    └─ auto_fix: true
    ↓
창 1에서 응답
    ├─ 리뷰 결과 수신
    ├─ 제안된 수정 적용
    └─ 변경사항 커밋
```

### 3. **실행 및 테스트** (창 1: OCPP Server)

```
창 1에서 실행:
    ├─ OCPP Server 시작 (CirineoS 기반)
    ├─ Charge Point Simulator 연결
    └─ 통신 로그 수집
    ↓
MCP 메시지: BROADCAST "server_started"
    ├─ status: "running"
    ├─ port: 9000
    ├─ version: "1.6"
    └─ timestamp: "..."
    ↓
창 2에서 감지:
    ├─ 자동으로 OCPP Client 시작
    ├─ 테스트 요청 전송
    ├─ 응답 검증
    └─ 테스트 결과 수집
```

### 4. **디버깅 및 로깅** (양쪽 상호작용)

```
테스트 실패 발생:
    ↓
MCP 메시지: REQUEST "debug_help"
    ├─ error: "AuthenticationError: Invalid credentials"
    ├─ stacktrace: "..."
    ├─ context: "auth_handler test"
    └─ request_id: "debug-123"
    ↓
창 1 (Copilot)에서 디버깅:
    ├─ 에러 분석
    ├─ 패치 코드 생성
    ├─ 테스트 작성
    └─ 결과 전송
    ↓
MCP 메시지: RESPONSE
    ├─ request_id: "debug-123"
    ├─ solution: "..."
    ├─ fix_code: "..."
    ├─ test_code: "..."
    └─ confidence: 0.95
    ↓
창 2에서 자동 적용:
    ├─ 패치 코드 검증
    ├─ 테스트 재실행
    ├─ 결과 확인
    └─ 성공/실패 리포팅
```

---

## 🏗️ 기술 스택

### 창 1: OCPP Server + Code Generation
```
┌─────────────────────────────────────┐
│   VS Code + Extensions              │
│                                     │
│ • GitHub Copilot                    │
│ • Python Extensions                 │
│ • OCPP Protocol Analyzer (custom)   │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│   Python Backend                    │
│                                     │
│ • ocpp (Python OCPP library)        │
│ • CirineoS (OCPP Server framework)  │
│ • AutoGen (Multi-agent orchestration)
│ • asyncio (async I/O)               │
│ • FastAPI/Flask (API server)        │
│ • pytest (testing)                  │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│   MCP Client (Python)               │
│                                     │
│ • Connection to MCP Server          │
│ • Message handling                  │
│ • Agent registration                │
└─────────────────────────────────────┘
```

### 창 2: OCPP Client + Code Analysis
```
┌─────────────────────────────────────┐
│   VS Code + Extensions              │
│                                     │
│ • Codex/GitHub Copilot             │
│ • Code Analysis Tools (ESLint, etc.)│
│ • OCPP Protocol Debugger (custom)   │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│   Python Backend                    │
│                                     │
│ • ocpp (Python OCPP library)        │
│ • agno/Claude API                   │
│ • FastAPI (test client)             │
│ • aiohttp (async HTTP)              │
│ • pytest + hypothesis (testing)     │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│   MCP Client (Python)               │
│                                     │
│ • Connection to MCP Server          │
│ • Message handling                  │
│ • Task distribution                 │
└─────────────────────────────────────┘
```

### 중앙: MCP Server
```
┌─────────────────────────────────────┐
│   MCP Server (Python)               │
│   Port: 9999                        │
│                                     │
│ • asyncio TCP Server                │
│ • Message Broker (JSON)             │
│ • Connection Manager                │
│ • Task Queue & Distribution         │
│ • Message History & Logging         │
│ • Heartbeat & Health Check          │
└─────────────────────────────────────┘
```

---

## 📨 메시지 플로우 예제

### 예제: Code Generation + Testing 루프

#### 1️⃣ 창 1 (Server Agent) → 코드 생성 시작
```json
{
  "message_type": "BROADCAST",
  "message_id": "msg-1",
  "sender_id": "server_agent_copilot",
  "timestamp": "2025-11-07T10:30:00Z",
  "payload": {
    "event_type": "code_generation_started",
    "task_id": "task-auth-handler",
    "description": "OCPP 1.6 Authentication Handler",
    "target_file": "src/handlers/auth.py",
    "context": {
      "protocol_version": "1.6",
      "handler_type": "authorize",
      "requires_encryption": true
    }
  }
}
```

#### 2️⃣ 창 1 (Server Agent) → 코드 생성 완료
```json
{
  "message_type": "BROADCAST",
  "message_id": "msg-2",
  "sender_id": "server_agent_copilot",
  "timestamp": "2025-11-07T10:30:15Z",
  "payload": {
    "event_type": "code_generated",
    "task_id": "task-auth-handler",
    "file_path": "src/handlers/auth.py",
    "lines_of_code": 127,
    "coverage": 0.85,
    "code_snippet": "async def handle_authorize(charge_point, payload):\n    # Implementation here\n    pass",
    "requires_review": true,
    "broadcast_to": ["client_agent"]
  }
}
```

#### 3️⃣ 창 2 (Client Agent) → 수신 + 분석 시작
```json
{
  "message_type": "REQUEST",
  "message_id": "msg-3",
  "sender_id": "client_agent_codex",
  "target_agent": "mcp-server",
  "timestamp": "2025-11-07T10:30:20Z",
  "payload": {
    "action": "analyze_code",
    "reference_task_id": "task-auth-handler",
    "file_path": "src/handlers/auth.py",
    "analysis_types": [
      "performance_check",
      "security_check",
      "protocol_compliance",
      "type_safety"
    ],
    "auto_fix_suggestions": true
  }
}
```

---

## ✅ 실현 가능성 확인

| 항목 | 현재 상태 | 필요 작업 |
|------|---------|---------|
| **MCP 프로토콜** | ✅ 설계 완료 | 구현 시작 |
| **OCPP 서버/클라이언트** | ✅ 이미 있음 | 에이전트 래퍼 추가 |
| **AI 에이전트** | ✅ 가능 (Copilot/Codex/Agno) | 통합 스크립트 작성 |
| **VS Code 자동화** | ✅ VS Code API 지원 | Extension 개발 |
| **통신 인프라** | ✅ TCP/JSON 기반 | MCP 서버 구현 |

---

## 🎯 최종 워크플로우

```
1. 개발자: "OCPP 인증 로직 만들어줘"
   ↓
2. 창 1 (Copilot): 코드 생성 + 자동 배포
   ↓
3. MCP: "코드 생성됨" 브로드캐스트
   ↓
4. 창 2 (Codex): 자동으로 코드 분석 + 테스트
   ↓
5. MCP: "분석 완료, 개선 제안" 응답
   ↓
6. 창 1: 자동으로 개선 적용 + 커밋
   ↓
7. 창 2: 자동으로 통합 테스트 실행
   ↓
8. MCP: "모두 성공!" 브로드캐스트
   ↓
9. 개발자: 전체 프로세스 자동화되어 완료! ✓
```

---

**작성자**: GitHub Copilot  
**상태**: ✅ 아키텍처 설계 완료
